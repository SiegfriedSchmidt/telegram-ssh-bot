import asyncio
import os
import time

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, BufferedInputFile

from lib.api.joke_api import get_joke
from lib.api.meme_api import get_meme
from lib.database import Database
from lib.init import data_folder_path
from lib.logger import log_stream
from lib.matplotlib_tables import create_table_matplotlib
from lib.states.confirmation_state import ConfirmationState
from lib.utils.utils import get_args

router = Router()


@router.message(Command("h"))
async def h(message: types.Message, state: FSMContext):
    await message.answer('''
/h
/projects
/up {project_name:required}
/down {project_name:required}
/update
/reboot
/prune
/stats
/upload_faq
/faq
/joke {joke_type:optional}
/meme {subreddit:optional}
/logs
'''
                         )


@router.message(Command("stats"))
async def stats(message: types.Message, database: Database, state: FSMContext):
    answer = await message.answer("gathering statistics...")
    containers_ps, containers_stats, htop = database.ssh_manager.get_stats()

    containers_data = {}
    for c in containers_ps:
        containers_data[c["Names"]] = c

    for c in containers_stats:
        containers_data[c["Name"]] |= c

    headers = ["Name", "Image", "CPUPerc", "MemUsage", "Status"]
    data = []
    for c in containers_data.values():
        data.append([c["Name"], c["Image"], c["CPUPerc"], c["MemUsage"].split(' /')[0], c["Status"]])

    table_containers_image = create_table_matplotlib(data, headers, f'Stats {time.strftime("%Y-%m-%d %H:%M:%S")}')
    file = BufferedInputFile(table_containers_image.read(), filename="img.png")

    await answer.delete()
    await message.answer_photo(file)


@router.message(Command("projects"))
async def projects(message: types.Message, database: Database, state: FSMContext):
    docker_projects = database.ssh_manager.get_docker_projects()
    await message.answer('\n'.join(docker_projects))


@router.message(Command("up"))
async def up_project(message: types.Message, command: CommandObject, database: Database, state: FSMContext):
    args = get_args(command)
    if len(args) == 0:
        return await message.answer('too few args!')

    if len(args) > 1:
        return await message.answer('too many args!')

    error = database.ssh_manager.up_project(args[0])

    if error:
        return await message.answer(error)
    return await message.answer('good')


@router.message(Command("down"))
async def down_project(message: types.Message, command: CommandObject, database: Database, state: FSMContext):
    args = get_args(command)
    if len(args) == 0:
        return await message.answer('too few args!')

    if len(args) > 1:
        return await message.answer('too many args!')

    if args[0] == "telegram-ssh-bot":
        return await message.answer("Nah, you won't do that!")

    error = database.ssh_manager.down_project(args[0])

    if error:
        return await message.answer(error)
    return await message.answer('good')


@router.message(Command("prune"))
async def prune(message: types.Message, database: Database, state: FSMContext):
    result = database.ssh_manager.docker_prune()
    if result:
        return await message.answer(result)
    return await message.answer('no output')


@router.message(Command("update"))
async def update_ask(message: types.Message, database: Database, state: FSMContext):
    await state.set_state(ConfirmationState.update_confirmation)
    return await message.answer('Do you want to continue (y/n)?')


@router.message(ConfirmationState.update_confirmation)
async def update(message: types.Message, database: Database, state: FSMContext):
    if message.text == "y":
        await message.answer('performing image update...')
        database.ssh_manager.update()
    else:
        await message.answer('abort')
    return await state.clear()


@router.message(Command("reboot"))
async def reboot_ask(message: types.Message, database: Database, state: FSMContext):
    await state.set_state(ConfirmationState.reboot_confirmation)
    return await message.answer('Do you want to continue (y/n)?')


@router.message(ConfirmationState.reboot_confirmation)
async def reboot(message: types.Message, database: Database, state: FSMContext):
    if message.text.lower() == "bipki":
        await message.answer('performing reboot...')
        database.ssh_manager.reboot()
    else:
        await message.answer('abort')
    return await state.clear()


@router.message(Command("upload_faq"))
async def upload_faq(message: types.Message):
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
async def faq(message: types.Message):
    if not os.path.exists(f"{data_folder_path}/faq.md"):
        return await message.answer("'faq.md' not found.")

    document = FSInputFile(f"{data_folder_path}/faq.md", filename="faq.md")
    return await message.answer_document(document, caption=f"FAQ")


@router.message(Command("joke"))
async def joke1(message: types.Message, command: CommandObject):
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
async def meme1(message: types.Message, command: CommandObject):
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
async def logs(message: types.Message):
    file = BufferedInputFile(log_stream.get_file().read(), filename="logs.txt")
    return await message.answer_document(file)


@router.message(Command("niggachain"))
async def chain(message: types.Message):
    return await message.answer('https://www.youtube-nocookie.com/embed/8V1eO0Ztuis')
