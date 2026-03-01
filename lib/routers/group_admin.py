from lib.config_reader import config
from lib.router_factories import admin_commands, ssh_session
from aiogram import F, Router

router = Router()
router.message.filter(
    F.chat.type.in_(["group", "supergroup"]),
    F.chat.id.in_(config.group_ids),
    F.from_user.id.in_(config.admin_ids)
)

router.include_routers(
    ssh_session.create_router(),
    admin_commands.create_router()
)
