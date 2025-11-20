from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext

from lib.database import Database
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
/prune
'''
                         )


@router.message(Command("ps"))
async def ps(message: types.Message, database: Database, state: FSMContext):
    containers = database.ssh_manager.get_docker_ps()
    await message.answer('\n'.join(containers))


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


@router.message(Command("niggachain"))
async def meme(message: types.Message, state: FSMContext):
    return await message.answer('https://www.youtube-nocookie.com/embed/8V1eO0Ztuis')
