import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import pytz
from datetime import datetime
from EsproChat import app

# Timezone
IST = pytz.timezone("Asia/Kolkata")

# Format Time
def get_time():
    now = datetime.now(IST)
    return now.strftime("%I:%M %p")

# Format Date
def get_date():
    now = datetime.now(IST)
    return now.strftime("%d/%m/%Y")

# Temp store image
temp_img = {}

# Save image
@app.on_message(filters.group & filters.media)
async def save_temp_image(_, message):
    if message.chat.id not in temp_img:
        temp_img[message.chat.id] = await message.download()

# Welcome System
@app.on_message(filters.new_chat_members)
async def welcome_msg(_, message):
    chat = message.chat
    user = message.from_user

    # Prepare Variables
    title = chat.title
    mention = user.mention
    user_id = user.id
    username = f"@{user.username}" if user.username else "N/A"
    time_now = get_time()
    date_now = get_date()

    # Welcome Text
    text = f"""
<b>┏━───〔👋 𝙉𝙚𝙬 𝙈𝙚𝙢𝙗𝙚𝙧 𝙅𝙤𝙞𝙣𝙚𝙙 〕───━┓</b>

<b>🥀 Name :</b> {mention}
<b>🆔 ID :</b> <code>{user_id}</code>
<b>✯ Username :</b> {username}

<b>🏡 Group :</b> {title}
<b>⏰ Time :</b> {time_now}
<b>📅 Date :</b> {date_now}

<b>✨ Welcome to the group! Enjoy your stay.</b>

<b>┗━──────────────━┛</b>
"""

    # Correct Buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💓 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 💓", callback_data="welcome_btn")]
    ])

    # Send Welcome With Image Or Simple Message
    if chat.id in temp_img:
        await message.reply_photo(
            photo=temp_img[chat.id],
            caption=text,
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            text,
            reply_markup=buttons
        )
