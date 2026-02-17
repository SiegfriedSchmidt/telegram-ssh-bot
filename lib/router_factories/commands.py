import asyncio
import os
import time

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, BufferedInputFile, ReplyKeyboardRemove
from aiogram.utils.chat_action import ChatActionMiddleware

from lib.api.gemini_api import gemini_api
from lib.api.geoip_api import geoip
from lib.api.joke_api import get_joke
from lib.api.meme_api import get_meme
from lib.bot_commands import text_bot_commands
from lib.database import Database
from lib.downloader import downloader
from lib.init import data_folder_path, videos_file_path
from lib.keyboards.switch_host_keyboard import get_switch_host_keyboard
from lib.logger import log_stream
from lib.matplotlib_tables import create_table_matplotlib
from lib.otp_manager import otp_manager, OTP_ACCESS_GRANTED_HOURS
from lib.ssh_manager import ssh_manager
from lib.states.confirmation_state import ConfirmationState
from lib.states.ssh_session_state import SSHSessionState
from lib.states.switch_state import SwitchState
from lib.utils.utils import get_args, large_respond, run_in_thread, get_dir_size, clear_dir_contents


def create_router():
    router = Router()
    router.message.middleware(ChatActionMiddleware())

    @router.message(Command("h"))
    async def h_cmd(message: types.Message):
        await message.answer(text_bot_commands)

    @router.message(Command("stats"))
    async def stats_cmd(message: types.Message, database: Database):
        answer = await message.answer("gathering statistics...")
        host = database.get_host(message.from_user.id)
        containers_ps, containers_stats, ram, cpu, uptime = await run_in_thread(ssh_manager[host].get_stats)

        containers_data = {}
        for c in containers_ps:
            containers_data[c["Names"]] = c

        for c in containers_stats:
            containers_data[c["Name"]] |= c

        headers = ["Name", "Image", "CPUPerc", "MemUsage", "Status"]
        data = []
        for c in containers_data.values():
            data.append([c["Name"], c["Image"], c["CPUPerc"], c["MemUsage"].split(' /')[0], c["Status"]])

        table_containers_image = create_table_matplotlib(data, headers)
        file = BufferedInputFile(table_containers_image.read(), filename="img.png")

        await answer.delete()
        await message.answer_photo(file, caption=f'Stats {time.strftime("%Y-%m-%d %H:%M:%S")}')

    @router.message(Command("projects"))
    async def projects_cmd(message: types.Message, database: Database):
        host = database.get_host(message.from_user.id)
        docker_projects = ssh_manager[host].get_docker_projects()
        await message.answer('\n'.join(docker_projects))

    @router.message(Command("up"))
    async def up_cmd(message: types.Message, command: CommandObject, database: Database):
        args = get_args(command)
        if len(args) == 0:
            return await message.answer('too few args!')

        if len(args) > 1:
            return await message.answer('too many args!')

        host = database.get_host(message.from_user.id)
        error = ssh_manager[host].up_project(args[0])

        if error:
            return await message.answer(error)
        return await message.answer('good')

    @router.message(Command("down"))
    async def down_cmd(message: types.Message, command: CommandObject, database: Database):
        args = get_args(command)
        if len(args) == 0:
            return await message.answer('too few args!')

        if len(args) > 1:
            return await message.answer('too many args!')

        if args[0] == "telegram-ssh-bot":
            return await message.answer("Nah, you won't do that!")

        host = database.get_host(message.from_user.id)
        error = ssh_manager[host].down_project(args[0])

        if error:
            return await message.answer(error)
        return await message.answer('good')

    @router.message(Command("prune"))
    async def prune_cmd(message: types.Message, database: Database):
        host = database.get_host(message.from_user.id)
        result = ssh_manager[host].docker_prune()
        if result:
            return await message.answer(result)
        return await message.answer('no output')

    @router.message(Command("update"))
    async def update_cmd(message: types.Message, state: FSMContext):
        await state.set_state(ConfirmationState.update_confirmation)
        return await message.answer('Do you want to continue (y/n)?')

    @router.message(ConfirmationState.update_confirmation)
    async def update(message: types.Message, database: Database, state: FSMContext):
        if message.text == "y":
            await message.answer('performing image update...')
            host = database.get_host(message.from_user.id)
            ssh_manager[host].update()
        else:
            await message.answer('abort')
        return await state.clear()

    @router.message(Command("reboot"), flags={'otp': True})
    async def reboot_cmd(message: types.Message, state: FSMContext):
        await state.set_state(ConfirmationState.reboot_confirmation)
        return await message.answer('Do you want to continue (y/n)?')

    @router.message(ConfirmationState.reboot_confirmation)
    async def reboot(message: types.Message, database: Database, state: FSMContext):
        if message.text.lower() == "bipki":
            await message.answer('performing reboot...')
            host = database.get_host(message.from_user.id)
            ssh_manager[host].reboot()
        else:
            await message.answer('abort')
        return await state.clear()

    @router.message(Command("upload_faq"))
    async def upload_faq_cmd(message: types.Message):
        if not message.reply_to_message:
            return await message.answer("You should reply to a message with document.")
        if not message.reply_to_message.document:
            return await message.answer("You should reply to a message containing document.")

        doc = message.reply_to_message.document
        file = await message.bot.get_file(doc.file_id)
        downloaded_file = await message.bot.download_file(file.file_path)

        with open(f"{data_folder_path}/faq.md", "wb") as f:
            f.write(downloaded_file.read())

        return await message.answer('Saved faq.')

    @router.message(Command("faq"))
    async def faq_cmd(message: types.Message):
        if not os.path.exists(f"{data_folder_path}/faq.md"):
            return await message.answer("'faq.md' not found.")

        document = FSInputFile(f"{data_folder_path}/faq.md", filename="faq.md")
        return await message.answer_document(document, caption=f"FAQ")

    @router.message(Command("joke"))
    async def joke_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if len(args) > 1:
            return await message.answer('too many args!')

        try:
            joke_type = args[0] if len(args) == 1 else None
            joke = await get_joke(joke_type)
        except Exception as e:
            return await message.answer(str(e))
        return await message.answer(joke)

    @router.message(Command("meme"))
    async def meme_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if len(args) > 1:
            return await message.answer('too many args!')

        try:
            meme_subreddit = args[0] if len(args) == 1 else None
            url, caption = await get_meme(meme_subreddit)
        except Exception as e:
            return await message.answer(str(e))

        try:
            if url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                await message.answer_photo(url, caption=caption)
            elif url.endswith('.gif'):
                await message.answer_animation(url, caption=caption)
            elif url.endswith(('.mp4', '.gifv', '.webm')):
                await message.answer_video(url, caption=caption)
        except TelegramBadRequest:
            await asyncio.sleep(1)
            await message.answer(f"{url}\n\n{caption}", disable_web_page_preview=False)

        return None

    @router.message(Command("logs"))
    async def logs_cmd(message: types.Message):
        file = BufferedInputFile(log_stream.get_file().read(), filename="logs.txt")
        return await message.answer_document(file)

    @router.message(Command("ask"))
    async def ask_cmd(message: types.Message, command: CommandObject):
        args = command.args
        if not args:
            return await message.answer("You need to specify a query.")

        answer = await message.answer('asking...')
        response = await gemini_api.ask(args)
        await large_respond(message, response)
        return await answer.delete()

    @router.message(Command("curl"), flags={'otp': True})
    async def curl_cmd(message: types.Message, database: Database, command: CommandObject):
        host = database.get_host(message.from_user.id)
        result, error = ssh_manager[host].curl(command.args)
        if not result:
            return await message.answer(error)
        return await message.answer(result)

    @router.message(Command("geoip"))
    async def geoip_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if len(args) == 0:
            return await message.answer('too few args!')

        if len(args) > 1:
            return await message.answer('too many args!')

        try:
            json = await geoip(args[0])
            text = '\n'.join(f"{key}: {val}" for key, val in json.items())
        except Exception as e:
            return await message.answer(str(e))
        return await message.answer(text)

    @router.message(Command("torip"))
    async def torip_cmd(message: types.Message, database: Database):
        host = database.get_host(message.from_user.id)
        result, error = ssh_manager[host].curl('eth0.me --connect-timeout 5 --proxy http://192.168.192.1:18082')
        if not result:
            return await message.answer(error)

        try:
            json = await geoip(result)
            text = '\n'.join(f"{key}: {val}" for key, val in json.items())
        except Exception as e:
            return await message.answer(str(e))

        return await message.answer(text)

    @router.message(Command("del"))
    async def del_cmd(message: types.Message):
        if not message.reply_to_message:
            return await message.answer("You need to reply to a message to delete.")

        try:
            return await message.reply_to_message.delete()
        except Exception:
            return await message.answer("I have no permission to delete this message.")

    @router.message(Command("openconnect"))
    async def openconnect_cmd(message: types.Message, command: CommandObject, database: Database):
        args = get_args(command)
        if len(args) == 0 or len(args) > 1 or args[0] not in ['status', 'restart', 'stop', 'start']:
            return await message.answer('invalid syntax, openconnect status|restart|stop|start')

        host = database.get_host(message.from_user.id)
        result, error = ssh_manager[host].openconnect(command.args)
        if not result:
            return await message.answer(error)
        return await large_respond(message, result)

    @router.message(Command("access"))
    async def access_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if len(args) != 1:
            return await message.answer('invalid syntax, you must provide only valid OTP code.')

        result = otp_manager.authenticate(message.from_user.id, args[0])
        if result:
            return await message.answer(result)
        return await message.answer(f'Access granted for {OTP_ACCESS_GRANTED_HOURS} hours.')

    def stdout_callback_generator(message: types.Message):
        async def stdout_callback(chunk: str):
            if not chunk:
                return
            try:
                await message.answer(f'```bash\n{chunk}```', parse_mode='Markdown')
            except Exception:
                pass

        return stdout_callback

    @router.message(Command("activate"), flags={'otp': True})
    async def activate_cmd(message: types.Message, state: FSMContext, database: Database):
        await state.set_state(SSHSessionState.session_activated)
        host = database.get_host(message.from_user.id)
        ssh_session = ssh_manager.interactive_session(host)
        await ssh_session.connect(stdout_callback_generator(message))
        await state.update_data(ssh_session=ssh_session)
        return await message.answer(f'SSH session activated! To deactivate enter /deactivate\n')

    @router.message(Command("download"))
    async def download_cmd(message: types.Message, command: CommandObject):
        args = get_args(command)
        if message.reply_to_message:
            url = message.reply_to_message.text
        elif len(args) == 1:
            url = args[0]
        else:
            return await message.answer('There is no url to download!')

        answer = await message.answer("Downloading...")
        result, error = await run_in_thread(downloader.download, url)
        if error:
            return await answer.edit_text(f"Download failed: {error}")

        filepath, info = result
        filename = os.path.basename(filepath)
        video = FSInputFile(filepath, filename=filename)
        await answer.delete()
        return await message.answer_video(video, caption=filename)

    @router.message(Command("clear_videos"))
    async def clear_videos_cmd(message: types.Message, state: FSMContext):
        space = round(get_dir_size(videos_file_path) / 1024 / 1024, 1)
        if space < 1:
            return await message.answer("Directory is empty.")
        await state.set_state(ConfirmationState.clear_videos_confirmation)
        return await message.answer(f'Do you want to delete all videos (y/n)? Space will be freed: {space} MB.')

    @router.message(ConfirmationState.clear_videos_confirmation)
    async def clear_videos(message: types.Message, state: FSMContext):
        if message.text.lower() == "y":
            files = clear_dir_contents(videos_file_path)
            text = '\n'.join(map(lambda t: f"{t[0]}: {round(t[1] / 1024 / 1024, 1)} MB", files))
            await message.answer(f'Files deleted:\n{text}')
        else:
            await message.answer('abort')
        return await state.clear()

    @router.message(Command("switch"))
    async def switch_cmd(message: types.Message, state: FSMContext):
        await state.set_state(SwitchState.switching)
        await message.answer(
            f"Choose host:",
            reply_markup=get_switch_host_keyboard(ssh_manager.get_hosts())
        )

    @router.message(SwitchState.switching)
    async def switch(message: types.Message, database: Database, state: FSMContext):
        await state.clear()
        result = database.set_host(message.from_user.id, message.text)
        if not result:
            return await message.answer('This host does not exist!', reply_markup=ReplyKeyboardRemove())
        return await message.answer(f'Host has been switched!', reply_markup=ReplyKeyboardRemove())

    @router.message(Command("niggachain"))
    async def chain_cmd(message: types.Message):
        return await message.answer('https://www.youtube-nocookie.com/embed/8V1eO0Ztuis')

    @router.message(Command("gamble"))
    async def gamble_cmd(message: types.Message):
        dice_msg = await message.answer_dice(emoji="🎰")
        result = dice_msg.dice.value

        if result == 64:
            await message.answer(f"🎉 **JACKPOT!** You win 1000 coins! 🎉. {result}")
        elif result >= 60:
            await message.answer(f"🌟 **Big win!** +500 coins! 🌟. {result}")
        elif result >= 50:
            await message.answer(f"✨ Nice win! +100 coins! ✨. {result}")
        else:
            await message.answer(f"😢 Better luck next time!. {result}")

    return router
