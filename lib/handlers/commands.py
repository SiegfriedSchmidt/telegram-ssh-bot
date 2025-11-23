import os

from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, BufferedInputFile

from lib.api.joke_api import get_joke
from lib.api.meme_api import get_meme
from lib.database import Database
from lib.init import data_folder_path
from lib.logger import log_stream
from lib.states.confirmation_state import ConfirmationState
from lib.utils.utils import get_args

router = Router()


@router.message(Command("h"))
async def h(message: types.Message, state: FSMContext):
    await message.answer('''
/h
/ps
/projects
/up {project_name:required}
/down {project_name:required}
/update
/reboot
/prune
/htop
/upload_faq
/faq
/joke {joke_type:optional}
/meme {subreddit:optional}
/logs
'''
                         )


@router.message(Command("ps"))
async def ps(message: types.Message, database: Database, state: FSMContext):
    containers_json = database.ssh_manager.get_docker_ps()
    pad = len(max(containers_json, key=lambda c: len(c['Image']))['Image'])
    containers = [f"{c["Image"].ljust(pad, ' ')} {c['Names']}" for c in containers_json]
    await message.answer(f"```docker\n{'\n\n'.join(containers)}```", parse_mode='MarkdownV2')


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


@router.message(Command("htop"))
async def htop(message: types.Message, database: Database, state: FSMContext):
    result = database.ssh_manager.htop()
    return await message.answer(result)


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

    if url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
        await message.answer_photo(url, caption=caption, parse_mode="Markdown")
    elif url.lower().endswith(('.mp4', '.gifv', '.webm')):
        await message.answer_video(url, caption=caption, parse_mode="Markdown")
    else:
        await message.answer(f"{caption}\n\n{url}", parse_mode="Markdown", disable_web_page_preview=False)

    return None


@router.message(Command("logs"))
async def logs(message: types.Message):
    file = BufferedInputFile(log_stream.get_file().read(), filename="logs.txt")
    return await message.answer_document(file)


@router.message(Command("niggachain"))
async def chain(message: types.Message):
    return await message.answer('https://www.youtube-nocookie.com/embed/8V1eO0Ztuis')
