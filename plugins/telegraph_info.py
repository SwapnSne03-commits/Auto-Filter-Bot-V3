import os
import asyncio
import tempfile
import aiofiles

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegraph import Telegraph
from pymediainfo import MediaInfo


telegraph = Telegraph()
telegraph.create_account(short_name="FileInfoBot")


# ======================================
# format helper
# ======================================
def fmt(lang):
    return lang or "Unknown"


# ======================================
# CALLBACK
# ======================================
@Client.on_callback_query(filters.regex("^trackinfo$"))
async def telegraph_file_info(client, query):

    await query.answer("🔍 Scanning file...")

    tmp = os.path.join(tempfile.gettempdir(), f"info_{query.id}.tmp")

    try:
        # 🔥 only few MB download (VERY FAST)
        async with aiofiles.open(tmp, "wb") as f:
            async for chunk in client.stream_media(query.message, limit=4):
                await f.write(chunk)

        media = await asyncio.to_thread(MediaInfo.parse, tmp)

        audios = []
        subs = []
        video = []

        for t in media.tracks:

            if t.track_type == "Video":
                video.append(f"{t.format} {t.width}x{t.height}")

            elif t.track_type == "Audio":
                audios.append(fmt(t.language))

            elif t.track_type in ("Text", "Subtitle"):
                subs.append(fmt(t.language))

        # =================================
        # TELEGRAPH PAGE BUILD
        # =================================
        html = "<h3>📊 File Tracks Info</h3>"

        if video:
            html += "<b>Video</b><br>"
            for v in video:
                html += f"• {v}<br>"

        if audios:
            html += "<br><b>Audio</b><br>"
            for a in set(audios):
                html += f"• {a}<br>"

        if subs:
            html += "<br><b>Subtitles</b><br>"
            for s in set(subs):
                html += f"• {s}<br>"

        page = telegraph.create_page(
            title="File Info",
            html_content=html
        )

        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View File Info", url=page["url"])]
            ])
        )

    except Exception as e:
        await query.answer("❌ Failed to read info", show_alert=True)

    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
