import os

from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from lib.database import Database
from lib.init import data_folder_path
from lib.states.confirmation_state import ConfirmationState

router = Router()


@router.message(Command("h"))
async def help(message: types.Message, state: FSMContext):
    await message.answer('''
/h
/ps
/projects
/up project_name
/down project_name
/update
/reboot
/prune
/htop
/upload_faq
/faq
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
    args = command.args.split()
    if len(args) > 1:
        return await message.answer('too many args!')

    error = database.ssh_manager.up_project(args[0])

    if error:
        return await message.answer(error)
    return await message.answer('good')


@router.message(Command("down"))
async def down_project(message: types.Message, command: CommandObject, database: Database, state: FSMContext):
    args = command.args.split()
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
async def upload_faq(message: types.Message, database: Database, state: FSMContext):
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
async def faq(message: types.Message, database: Database, state: FSMContext):
    if not os.path.exists(f"{data_folder_path}/faq.md"):
        return await message.answer("'faq.md' not found.")

    document = FSInputFile(f"{data_folder_path}/faq.md", filename="faq.md")
    return await message.answer_document(document, caption=f"FAQ")


@router.message(Command("niggachain"))
async def meme(message: types.Message, state: FSMContext):
    return await message.answer('https://www.youtube-nocookie.com/embed/8V1eO0Ztuis')
