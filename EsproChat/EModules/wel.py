# ==================================
#    FINAL WELCOME MODULE (EsproChat)
# ==================================

from EsproChat import app
from pyrogram import Client, filters, enums
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
from logging import getLogger
# import os # os import removed

LOGGER = getLogger(__name__)

# --- Temporary Storage (Used only for deleting the previous welcome message) ---
class temp:
    """Stores the last sent welcome message for cleanup."""
    last = {}
    
# --- Image Processing Functions ---

def circle(pfp, size=(500, 500), brightness_factor=1.3):
    """Makes the profile picture circular and enhances brightness."""
    try:
        resize_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resize_filter = Image.ANTIALIAS
        
    pfp = pfp.resize(size, resize_filter).convert("RGBA")
    pfp = ImageEnhance.Brightness(pfp).enhance(brightness_factor)
    
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, resize_filter)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    
    pfp.putalpha(mask)
    return pfp

def welcomepic(pic, user, chatname, id, uname, brightness_factor=1.3):
    """
    Generates the welcome image using the custom background.
    """
    # NOTE: Assumes the file is named wel_new.png in the assets folder
    background = Image.open("EsproChat/assets/wel_new.png") 
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp, brightness_factor=brightness_factor) 
    
    pfp = pfp.resize((380, 380)) 
    
    draw = ImageDraw.Draw(background)

    pfp_position = (490, 260) 
    background.paste(pfp, pfp_position, pfp)
    
    # Saving file with .png extension
    file_path = f"downloads/welcome#{id}.png" 
    background.save(file_path) 
    return file_path

def gen_thumb(image_path, uid):
    """Generates a 320x320 thumbnail from the welcome image."""
    try:
        img = Image.open(image_path)
        # Resizing to fit Telegram's standard thumbnail size
        img.thumbnail((320, 320)) 
        
        # Saving file with .png extension
        thumb_path = f"downloads/thumb_{uid}.png" 
        img.save(thumb_path) 
        return thumb_path
    except Exception as e:
        LOGGER.error(f"Error generating thumbnail: {e}")
        return None

# --- Handler (Automatic Welcome) ---

@app.on_chat_member_updated(filters.group, group=-3)
async def greet_new_member(_, member: ChatMemberUpdated):
    """
    Automatically sends a welcome message when a new member joins.
    """
    welcomeimg = None
    thumb_path = None
    
    chat_id = member.chat.id
    
    if not (member.new_chat_member and not member.old_chat_member):
        return

    if not member.new_chat_member.user:
        return 
        
    user = member.new_chat_member.user
    user_id = user.id
    chat_title = member.chat.title
    count = await app.get_chat_members_count(chat_id)
    
    # Download PFP
    try:
        pic_filename = f"pp{user_id}" 
        pic = await app.download_media(
            user.photo.big_file_id, file_name=pic_filename
        )
    except AttributeError:
        pic = "EsproChat/assets/upic.png"
        
    # Delete last welcome message for cleanup
    old = temp.last.get(chat_id)
    if old:
        try:
            await old.delete()
        except Exception as e:
            LOGGER.error(f"Error deleting old welcome message: {e}")

    try:
        # 1. Generate main image
        welcomeimg = welcomepic(
            pic, user.first_name, chat_title, user_id, user.username
        )
        
        # 2. Generate thumbnail
        thumb_path = gen_thumb(welcomeimg, user_id)
        
        # Define link
        add_link = f"https://t.me/{app.username}?startgroup=true"
        
        # Send photo with THUMBNAIL
        msg = await app.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=f"""
👋 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {chat_title}** 🌹

**━━━━━━━━━━━━━━━━━━━━**

👑 **ɴᴇᴡ ᴍᴇᴍʙᴇʀ:** {user.mention}
✨ **ɪᴅ:** `{user_id}`
🌐 **ᴜsᴇʀɴᴀᴍᴇ:** @{user.username or 'Not Set'}
👥 **ᴛᴏᴛᴀʟ ᴍᴇᴍʙᴇʀs:** `{count}`

**━━━━━━━━━━━━━━━━━━━━**
""",
            thumb=thumb_path,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="⚔️ ᴋɪᴅɴᴀᴘ ᴛʜɪs ʙᴏᴛ ⚔️", url=add_link)],
            ])
        )
        
        # Store the new message for cleanup
        temp.last[chat_id] = msg
        
    except Exception as e:
        LOGGER.error(f"Error sending welcome message: {e}")
        
    # finally: # Removed 'finally' block and file cleanup logic
    #     if welcomeimg and os.path.exists(welcomeimg):
    #         os.remove(welcomeimg)
    #     if thumb_path and os.path.exists(thumb_path):
    #         os.remove(thumb_path)
    #     if pic != "EsproChat/assets/upic.png" and os.path.exists(pic):
    #          os.remove(pic)
