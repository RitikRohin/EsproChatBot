import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import pytz
from datetime import datetime
from EsproChat import app

# Timezone
IST = pytz.timezone("Asia/Kolkata")

def get_time():
    return datetime.now(IST).strftime("%I:%M %p")

def get_date():
    return datetime.now(IST).strftime("%d/%m/%Y")

# Temp store group image & last message
temp_img = {}
last_welcome = {}


# Save latest image in group
@app.on_message(filters.group & filters.photo)
async def save_temp_image(_, message):
    temp_img[message.chat.id] = await message.download()


# Welcome message
@app.on_message(filters.new_chat_members)
async def welcome_msg(_, message):

    chat = message.chat
    user = message.new_chat_members[0]  # TRUE NEW MEMBER

    # Delete old welcome
    if chat.id in last_welcome:
        try:
            await last_welcome[chat.id].delete()
        except:
            pass

    title = chat.title
    mention = user.mention
    user_id = user.id
    username = f"@{user.username}" if user.username else "N/A"

    time_now = get_time()
    date_now = get_date()

    # Welcome Text
    text = f"""
<b>┏━───〔👋 NEW MEMBER JOINED 〕───━┓</b>

<b>🥀 Name :</b> {mention}
<b>🆔 ID :</b> <code>{user_id}</code>
<b>✯ Username :</b> {username}

<b>🏡 Group :</b> {title}
<b>⏰ Time :</b> {time_now}
<b>📅 Date :</b> {date_now}

<b>✨ Welcome to the group! Enjoy your stay.</b>

<b>┗━──────────────━┛</b>
"""

    # Buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💓 WELCOME 💓", url=f"tg://user?id={user.id}")]
    ])

    # Send with image (if available)
    if chat.id in temp_img:
        msg = await app.send_photo(
            chat_id=chat.id,
            photo=temp_img[chat.id],
            caption=text,
            reply_markup=buttons
        )

    else:
        msg = await app.send_message(
            chat_id=chat.id,
            text=text,
            reply_markup=buttons
        )

    # Save last welcome message for auto delete
    last_welcome[chat.id] = msg
