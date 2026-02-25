from lib.config_reader import config
from lib.router_factories import general_commands
from aiogram import F, Router

router = Router()
router.message.filter(
    F.chat.type.in_(["group", "supergroup"]),
    F.chat.id.in_(config.group_ids),
)

router.include_routers(general_commands.create_router())
