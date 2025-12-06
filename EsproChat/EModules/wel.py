# --- Imports ---
from EsproChat import app # Assuming DAXXMUSIC is your bot instance
from pyrogram.errors import RPCError
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Union, Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
import random
from pyrogram import Client, filters, enums
from pyrogram.types import Message
import asyncio, os
from logging import getLogger



LOGGER = getLogger(__name__)

# --- Dummy Database Class for Welcome Status ---

class WelDatabase:
    """Simulates a database to store welcome status (on/off) for chats."""
    def __init__(self):
        self.data = {} 

    async def find_one(self, chat_id):
        return chat_id in self.data

    async def add_wlcm(self, chat_id):
        if chat_id not in self.data:
            self.data[chat_id] = {"state": "on"}

    async def rm_wlcm(self, chat_id):
        if chat_id in self.data:
            del self.data[chat_id]

wlcm = WelDatabase()

# --- Temporary Storage Class ---

class temp:
    """Temporary storage for state variables, especially for deleting previous messages."""
    MELCOW = {} # Dictionary to store the last sent welcome message object

# --- Image Processing Functions ---

def circle(pfp, size=(500, 500), brightness_factor=10):
    """Crops the profile picture into a circle and adjusts brightness."""
    # Using LANCZOS for high-quality resampling
    pfp = pfp.resize(size, Image.Resampling.LANCZOS).convert("RGBA") 
    pfp = ImageEnhance.Brightness(pfp).enhance(brightness_factor)
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.Resampling.LANCZOS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

def welcomepic(pic, user, chatname, id, uname, brightness_factor=1.3):
    """Creates the final welcome image by pasting pfp onto a background."""
    # NOTE: Ensure 'DAXXMUSIC/assets/wel2.png' and 'DAXXMUSIC/assets/font.ttf' exist in your file system.
    background = Image.open("EsproChat/assets/wel2.png")
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp, brightness_factor=brightness_factor) 
    pfp = pfp.resize((635, 635))
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype('EsproChat/assets/font.ttf', size=70)
    
    # Original text drawing logic (used primarily for ID, although the coordinate 2999 is highly off-screen)
    draw.text((2999, 450), f'ID: {id}', fill=(255, 255, 255), font=font)

    pfp_position = (332, 323)
    background.paste(pfp, pfp_position, pfp)
    filename = f"downloads/welcome#{id}.png"
    background.save(filename)
    return filename

# --- Command Handler: /welcome [on|off] ---

@app.on_message(filters.command("welcome") & ~filters.private)
async def auto_state(_, message: Message):
    """Allows admins to turn the welcome feature on or off in a group."""
    usage = "**ᴜsᴀɢᴇ:**\n**⦿ /welcome [on|off]**"
    if len(message.command) == 1:
        return await message.reply_text(usage)
    
    chat_id = message.chat.id
    user = await app.get_chat_member(message.chat.id, message.from_user.id)
    
    # Check if the user is an admin or owner
    if user.status in (
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
    ):
        A = await wlcm.find_one(chat_id)
        state = message.text.split(None, 1)[1].strip().lower()
        if state == "off":
            if A:
                await message.reply_text("**ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴀʟʀᴇᴀᴅʏ ᴅɪsᴀʙʟᴇᴅ !**")
            else:
                await wlcm.add_wlcm(chat_id)
                await message.reply_text(f"**ᴅɪsᴀʙʟᴇᴅ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ɪɴ** {message.chat.title}")
        elif state == "on":
            if not A:
                await message.reply_text("**ᴇɴᴀʙʟᴇ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ.**")
            else:
                await wlcm.rm_wlcm(chat_id)
                await message.reply_text(f"**ᴇɴᴀʙʟᴇᴅ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ɪɴ ** {message.chat.title}")
        else:
            await message.reply_text(usage)
    else:
        await message.reply("**sᴏʀʀʏ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴇɴᴀʙʟᴇ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ!**")


# --- Handler for New Member Joining ---

@app.on_chat_member_updated(filters.group, group=-3)
async def greet_new_member(_, member: ChatMemberUpdated):
    """Sends a welcome message when a new member joins."""
    chat_id = member.chat.id
    count = await app.get_chat_members_count(chat_id)
    A = await wlcm.find_one(chat_id)
    if A:
        return # Exit if Welcome is disabled

    user = member.new_chat_member.user if member.new_chat_member else member.from_user
    
    # Check if a user has truly joined (not an update or kick/ban)
    if member.new_chat_member and not member.old_chat_member and member.new_chat_member.status != enums.ChatMemberStatus.BANNED:
    
        try:
            # Download user profile picture
            pic = await app.download_media(
                user.photo.big_file_id, file_name=f"pp{user.id}.png"
            )
        except AttributeError:
            # Default picture if none is found
            pic = "EsproCust/assets/upic.png"
        
        # Delete the previous welcome message to avoid spam
        if (temp.MELCOW).get(f"welcome-{member.chat.id}") is not None:
            try:
                await temp.MELCOW[f"welcome-{member.chat.id}"].delete()
            except Exception as e:
                LOGGER.error(e)
                
        try:
            # Create welcome image
            welcomeimg = welcomepic(
                pic, user.first_name, member.chat.title, user.id, user.username
            )
            
            # Inline buttons setup
            button_text = "๏ ᴠɪᴇᴡ ɴᴇᴡ ᴍᴇᴍʙᴇʀ ๏"
            add_button_text = "๏ ᴋɪᴅɴᴀᴘ ᴍᴇ ๏"
            deep_link = f"tg://openmessage?user_id={user.id}"
            add_link = f"https://t.me/{app.username}?startgroup=true"
            
            # Send the welcome photo and caption
            temp.MELCOW[f"welcome-{member.chat.id}"] = await app.send_photo(
                member.chat.id,
                photo=welcomeimg,
                caption=f"""
**❅────✦ ᴡᴇʟᴄᴏᴍᴇ ✦────❅**

▰▰▰▰▰▰▰▰▰▰▰▰▰
**➻ ɴᴀᴍᴇ »** {user.mention}
**➻ ɪᴅ »** `{user.id}`
**➻ ᴜ_ɴᴀᴍᴇ »** @{user.username or "N/A"}
**➻ ᴛᴏᴛᴀʟ ᴍᴇᴍʙᴇʀs »** {count}
▰▰▰▰▰▰▰▰▰▰▰▰▰

**❅─────✧❅✦❅✧─────❅**
""",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(button_text, url=deep_link)],
                    [InlineKeyboardButton(text=add_button_text, url=add_link)],
                ])
            )
        except Exception as e:
            LOGGER.error(f"Error sending welcome message: {e}")
  
