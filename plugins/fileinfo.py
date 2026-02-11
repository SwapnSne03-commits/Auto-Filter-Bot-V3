import os
import asyncio
import tempfile
import pycountry

from pymediainfo import MediaInfo
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================================
# 🔹 Clean Language Name
# =========================================
def clean_lang(code):
    if not code:
        return "Unknown"

    try:
        lang = (
            pycountry.languages.get(alpha_2=code.lower())
            or pycountry.languages.get(alpha_3=code.lower())
        )
        if lang:
            return lang.name
    except:
        pass

    return code.upper()


# =========================================
# 🔹 Format duration
# =========================================
def format_duration(ms):
    if not ms:
        return "Unknown"

    sec = int(ms) // 1000
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02}:{m:02}:{s:02}"


# =========================================
# 🔹 Beautiful Info Builder
# =========================================
def build_caption(info):

    return (
        "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>𝗙𝗜𝗟𝗘 𝗜𝗡𝗙𝗢</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        f"📺 <b>Resolution :</b> {info['resolution']}\n"
        f"⏱ <b>Duration :</b> {info['duration']}\n\n"

        f"🔊 <b>Audio ({len(info['audios'])}) :</b>\n"
        f"➤ {' | '.join(info['audios']) if info['audios'] else 'None'}\n"
        f"🎙 <b>Default :</b> {info['default_audio'] or '—'}\n\n"

        f"💬 <b>Subtitles ({len(info['subs'])}) :</b>\n"
        f"➤ {' | '.join(info['subs']) if info['subs'] else 'None'}\n"
        f"⚡ <b>Forced :</b> {info['forced_sub'] or '—'}\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━"
    )


# =========================================
# 🔥 CALLBACK HANDLER
# =========================================
@Client.on_callback_query(filters.regex("^fileinfo#"))
async def file_info_handler(client, query):

    await query.answer("🔍 Scanning file...")

    file_id = query.data.split("#")[1]

    path = await client.download_media(
        file_id,
        file_name=os.path.join(tempfile.gettempdir(), "fileinfo_temp")
    )

    try:
        media = await asyncio.to_thread(MediaInfo.parse, path)

        audios = []
        subs = []
        default_audio = None
        forced_sub = None
        resolution = "Unknown"
        duration = "Unknown"

        for t in media.tracks:

            if t.track_type == "Video":
                if t.width:
                    resolution = f"{t.width}x{t.height}"
                duration = format_duration(t.duration)

            elif t.track_type == "Audio":
                lang = clean_lang(t.language)
                if lang not in audios:
                    audios.append(lang)

                if getattr(t, "default", "") == "Yes":
                    default_audio = lang

            elif t.track_type == "Text":
                lang = clean_lang(t.language)
                if lang not in subs:
                    subs.append(lang)

                if getattr(t, "forced", "") == "Yes":
                    forced_sub = lang


        info = {
            "resolution": resolution,
            "duration": duration,
            "audios": audios,
            "subs": subs,
            "default_audio": default_audio,
            "forced_sub": forced_sub
        }

        pretty_info = build_caption(info)

        # =================================
        # 🔥 KEEP OLD CAPTION + ADD INFO
        # =================================
        old_caption = query.message.caption or ""
        new_caption = f"{old_caption}{pretty_info}"

        btn = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ 𝗖𝗹𝗼𝘀𝗲", callback_data="close")
            ]
        ])

        await query.message.edit_caption(
            caption=new_caption,
            reply_markup=btn
        )

    except Exception:
        await query.answer("❌ Failed to read file info", show_alert=True)

    finally:
        if os.path.exists(path):
            os.remove(path)
