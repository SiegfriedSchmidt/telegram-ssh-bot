from aiogram import Router, types
from aiogram.types import ReactionTypeEmoji

from lib.middlewares.user_middleware import UserMiddleware


def create_router():
    router = Router()
    router.message.middleware(UserMiddleware())

    @router.message_reaction()
    async def reaction_handler(event: types.MessageReactionUpdated):
        if any(reaction.emoji == "🐳" for reaction in event.new_reaction):
            await event.bot.set_message_reaction(event.chat.id, event.message_id, [ReactionTypeEmoji(emoji="🐳")])

    return router
