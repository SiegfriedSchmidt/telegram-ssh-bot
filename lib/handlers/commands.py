from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext

from lib.database import Database

router = Router()


@router.message(Command("help"))
async def help(message: types.Message, state: FSMContext):
    await message.answer('''
/help
/ps
/projects
/start project_name
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


@router.message(Command("start"))
async def start_project(message: types.Message, command: CommandObject, database: Database, state: FSMContext):
    args = command.args.split()
    if len(args) > 1:
        return await message.answer('too many args!')

    error = database.ssh_manager.start_projects(args[0])

    if error:
        return await message.answer(error)
    return await message.answer('good')


@router.message(Command("prune"))
async def prune(message: types.Message, command: CommandObject, database: Database, state: FSMContext):
    result = database.ssh_manager.docker_prune()
    if result:
        return await message.answer(result)
    return await message.answer('no output')
