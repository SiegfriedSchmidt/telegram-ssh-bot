from lib.downloader import downloader
from lib.utils.general_utils import run_in_thread
from lib.config_reader import config
from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

router = Router()
router.inline_query.filter(
    F.from_user.id.in_(config.admin_ids)
)


async def show_invalid(inline_query: InlineQuery, text: str) -> None:
    await inline_query.answer(results=[
        InlineQueryResultArticle(
            id="default",
            title="Invalid",
            input_message_content=InputTextMessageContent(message_text=text),
        )
    ])


@router.inline_query()
async def inline_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()

    if not query:
        return await show_invalid(inline_query, "No query provided")

    args = query.split()
    if len(args) != 2 or args[0] != "download":
        return await show_invalid(inline_query, "Not enough arguments or invalid command")

    url = args[1]
    result, error = await run_in_thread(downloader.download, url)
    if error:
        return await show_invalid(inline_query, "Error occurred while downloading")

    filepath, filename, server_url, info = result
    if not server_url:
        return await show_invalid(inline_query, "Error occurred while downloading")

    results = [
        InlineQueryResultArticle(
            id="1",
            title=f"Open Video",
            description="Click to open video",
            # thumbnail_url="https://picsum.photos/200",
            input_message_content=InputTextMessageContent(
                message_text=f"Open Video: {server_url}"
            ),
        )
    ]

    return await inline_query.answer(results=results)
