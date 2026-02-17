from lib.config_reader import config
from lib.routers import messages
from lib.router_factories import commands, ssh_session
from aiogram import F, Router

router = Router()
router.message.filter(F.chat.type.in_(["group", "supergroup"]), F.chat.id == config.group_id)
router.include_routers(
    ssh_session.create_router(),
    commands.create_router(),
    messages.router
)
