from aiogram import types
from aiogram.types import LinkPreviewOptions, FSInputFile, InputMediaVideo
from lib.downloader import downloader
from lib.keyboards.link_keyboard import get_link_keyboard
from lib.utils.general_utils import run_in_thread


async def download_video(message: types.Message, url: str):
    answer = await message.reply("Downloading...")
    result, error = await run_in_thread(downloader.download, url)
    if error:
        return await answer.edit_text(f"Download failed: {error}")

    filepath, filename, server_url, info = result
    if server_url:
        # media = InputMediaVideo(media=server_url, caption=filename, supports_streaming=True)
        return await answer.edit_text(
            filename,
            link_preview_options=LinkPreviewOptions(
                url=server_url,
                is_disabled=False,
                prefer_large_media=True,
                show_above_text=True
            ),
            reply_markup=get_link_keyboard(server_url)
        )
    else:
        video = FSInputFile(filepath, filename=filename)
        media = InputMediaVideo(media=video, caption=filename)
        return await answer.edit_media(media)
