import asyncio
import time
from io import BytesIO
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from aiogram.utils.chat_action import ChatActionMiddleware
from rcon.source import rcon
from lib.bot_commands import text_bot_admin_commands
from lib.callbacks.switch_host_callback import SwitchHostCallback
from lib.keyboards.switch_host_keyboard import get_switch_host_keyboard
from lib.logger import log_stream
from lib.matplotlib_tables import create_table_matplotlib
from lib.middlewares.user_middleware import UserMiddleware
from lib.models import TerminalType
from lib.ssh_commands import SSHCommands
from lib.ssh_manager import ssh_manager
from lib.states.confirmation_state import ConfirmationState
from lib.states.ssh_session_state import SSHSessionState
from lib.temporal_storage import User
from lib.utils.general_utils import run_in_thread
from lib.utils.regex_utils import is_valid_mac_address
from lib.utils.message_utils import get_args, large_respond
from lib.config_reader import config

router = Router()
router.message.filter(F.from_user.id.in_(config.admin_ids))
router.message.middleware(ChatActionMiddleware())
router.message.middleware(UserMiddleware())
router.callback_query.middleware(UserMiddleware())


# react on docker
@router.message(F.text.lower().contains("docker") | F.text.lower().contains("докер") | (F.sticker.emoji == "🐳"))
async def docker_message(message: types.Message):
    await message.react([types.ReactionTypeEmoji(emoji='🐳')])


@router.message(Command("h"))
async def h_cmd(message: types.Message):
    await message.answer(text_bot_admin_commands)


@router.message(Command("stats"))
async def stats_cmd(message: types.Message, user: User, ssh: SSHCommands):
    answer = await message.answer("gathering statistics...")
    containers_ps, containers_stats, ram, cpu, uptime = await run_in_thread(ssh.get_stats)

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
    await message.answer_photo(
        file, caption=f'Stats <b>{user.host}</b> {time.strftime("%Y-%m-%d %H:%M:%S")}',
        parse_mode="html"
    )


@router.message(Command("projects"))
async def projects_cmd(message: types.Message, ssh: SSHCommands):
    docker_projects = ssh.get_docker_projects()
    await message.answer('\n'.join(docker_projects))


@router.message(Command("up"))
async def up_cmd(message: types.Message, command: CommandObject, ssh: SSHCommands):
    args = get_args(command, 1, 1)
    error = ssh.up_project(args[0])
    if error:
        return await message.answer(error)
    return await message.answer('good')


@router.message(Command("down"))
async def down_cmd(message: types.Message, command: CommandObject, ssh: SSHCommands):
    args = get_args(command, 1, 1)
    if args[0] == config.bot_project_name:
        return await message.answer("Nah, you won't do that!")

    error = ssh.down_project(args[0])
    if error:
        return await message.answer(error)
    return await message.answer('good')


@router.message(Command("prune"))
async def prune_cmd(message: types.Message, ssh: SSHCommands):
    result = ssh.docker_prune()
    return await large_respond(message, result)


@router.message(Command("update"))
async def update_cmd(message: types.Message, command: CommandObject, ssh: SSHCommands, state: FSMContext):
    args = get_args(command, 0, 1)
    project = args[0] if len(args) > 0 else config.bot_project_name
    all_projects = ssh.get_docker_projects()
    if project not in all_projects:
        return await message.answer(f"Project {project} not found!")

    await state.set_state(ConfirmationState.update_confirmation)
    await state.set_data({"project": project})
    return await message.answer(f'Do you want to update {project} (y/n)?')


@router.message(ConfirmationState.update_confirmation)
async def update(message: types.Message, ssh: SSHCommands, state: FSMContext):
    project_name = (await state.get_data())["project"]
    await state.clear()
    if message.text == "y":
        await message.answer('performing project update...')
        bot_update_log_file = ssh.update(project_name)

        async def callback(text: str):
            await large_respond(message, text)

        asyncio.create_task(ssh.follow_file(bot_update_log_file, callback, 5))
    else:
        await message.answer('abort')


@router.message(Command("reboot"))
async def reboot_cmd(message: types.Message, state: FSMContext):
    await state.set_state(ConfirmationState.reboot_confirmation)
    return await message.answer('Do you want to continue (y/n)?')


@router.message(ConfirmationState.reboot_confirmation)
async def reboot(message: types.Message, ssh: SSHCommands, state: FSMContext):
    if message.text.lower() == "bipki":
        await message.answer('performing reboot...')
        ssh.reboot()
    else:
        await message.answer('abort')
    return await state.clear()


@router.message(Command("logs"))
async def logs_cmd(message: types.Message):
    file = BufferedInputFile(log_stream.get_file().read(), filename="logs.txt")
    return await message.answer_document(file)


@router.message(Command("curl"))
async def curl_cmd(message: types.Message, ssh: SSHCommands, command: CommandObject):
    result, error = ssh.curl(command.args)
    if not result:
        return await message.answer(error)
    return await message.answer(result)


@router.message(Command("openconnect"))
async def openconnect_cmd(message: types.Message, command: CommandObject, ssh: SSHCommands):
    args = get_args(command, 1, 1)
    if args[0] not in ['status', 'restart', 'stop', 'start']:
        return await message.answer('invalid syntax, openconnect status|restart|stop|start')

    result, error = ssh.openconnect(args[0])
    if not result:
        return await large_respond(message, error)
    return await large_respond(message, result)


def stdout_callback_image_generator(message: types.Message):
    async def stdout_callback(chunk: BytesIO):
        try:
            input_file = BufferedInputFile(chunk.read(), filename="terminal.png")
            await message.answer_photo(input_file)
        except Exception as e:
            await message.answer(str(e))

    return stdout_callback


def stdout_callback_text_generator(message: types.Message):
    async def stdout_callback(chunk: str):
        if not chunk:
            return
        try:
            await message.answer(f'```bash\n{chunk}```', parse_mode='Markdown')
        except Exception as e:
            await message.answer(str(e))

    return stdout_callback


@router.message(Command("activate"))
async def activate_cmd(message: types.Message, state: FSMContext, user: User, command: CommandObject):
    terminal_type = 'text'
    args = get_args(command, 0, 1)
    if len(args) == 1:
        terminal_type = args[0]
        if terminal_type not in TerminalType:
            return await message.answer('Invalid terminal type! Should be text|image.')

    await message.answer(f'SSH session activated in {terminal_type} terminal! To deactivate enter /deactivate\n')
    await state.set_state(SSHSessionState.session_activated)
    ssh_session = ssh_manager.interactive_session(user.host, terminal_type)
    await ssh_session.connect(
        stdout_callback_text_generator(message) if terminal_type == TerminalType.text else
        stdout_callback_image_generator(message)
    )
    return await state.update_data(ssh_session=ssh_session)


@router.message(Command("switch"))
async def switch_cmd(message: types.Message):
    await message.answer(
        f"Available hosts",
        reply_markup=get_switch_host_keyboard(ssh_manager.get_hosts())
    )


@router.callback_query(SwitchHostCallback.filter())
async def switch(callback: types.CallbackQuery, callback_data: SwitchHostCallback, user: User):
    user.host = callback_data.host
    return await callback.answer(f'Host has been switched to {user.host}!')


@router.message(Command("wol"))
async def wol_cmd(message: types.Message, command: CommandObject, ssh: SSHCommands):
    args = get_args(command, 1, 1)
    if not is_valid_mac_address(args[0]):
        return await message.answer('invalid syntax, wakeonlan {mac address}')

    result, error = ssh.wakeonlan(args[0])
    if not result:
        return await large_respond(message, error)
    return await large_respond(message, result)


@router.message(Command("follow_file"))
async def follow_file_cmd(message: types.Message, command: CommandObject, ssh: SSHCommands):
    args = get_args(command, 1, 1)

    async def callback(text: str):
        await message.answer(text)

    location = args[0]
    asyncio.create_task(ssh.follow_file(location, callback))
    return await message.answer(f'File "{location}" following activated! To deactivate do /unfollow_file')


@router.message(Command("unfollow_file"))
async def unfollow_file_cmd(message: types.Message, ssh: SSHCommands):
    if not ssh.following_file:
        return await message.answer('You are not following any file right now!')
    ssh.unfollow()
    return await message.answer(f'File following deactivated!')


@router.message(Command("rcon_follow"))
async def rcon_follow_cmd(message: types.Message, user: User, ssh: SSHCommands):
    rcon_settings = ssh_manager.get_host(user.host).rcon
    if rcon_settings is None:
        return await message.answer("RCON settings not set!")

    rcon_text = '[Server thread/INFO] [net.minecraft.server.MinecraftServer/]:'
    rcon_text_len = len(rcon_text)

    async def callback(text: str):
        lines_raw = text.split('\n')
        lines = []
        for line_raw in lines_raw:
            idx = line_raw.find(rcon_text)
            if idx != -1:
                line = line_raw[idx + rcon_text_len:]
                if len(line) > 0:
                    lines.append(line)

        if len(lines) > 0:
            await large_respond(message, lines)

    asyncio.create_task(ssh.follow_file(rcon_settings.rcon_logs_path, callback))
    return await message.answer(f'Rcon following activated! To deactivate do /unfollow_file')


@router.message(Command('rcon'))
async def rcon_cmd(message: types.Message, command: CommandObject, user: User):
    args = get_args(command, 1)
    rcon_settings = ssh_manager.get_host(user.host).rcon
    if rcon_settings is None:
        return await message.answer("RCON settings not set!")

    response = await rcon(*args, host=rcon_settings.address, port=rcon_settings.port, passwd=rcon_settings.password)
    if response:
        await message.answer(response)
    return None
