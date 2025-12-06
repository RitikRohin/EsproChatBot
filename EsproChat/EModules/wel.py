# ==================================
#    FINAL WELCOME MODULE (EsproChat)
# ==================================

from EsproChat import app
from pyrogram import Client, filters, enums
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
from logging import getLogger
# import os # File cleanup is removed as requested

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
    Generates the welcome image dynamically with a solid color background.
    """
    # 💥 CHANGE: Dynamically creating a deep indigo background (1280x720)
    BG_WIDTH, BG_HEIGHT = 1280, 720
    # Deep Indigo/Purple Color
    background = Image.new('RGB', (BG_WIDTH, BG_HEIGHT), color='#2C003E') 
    
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp, brightness_factor=brightness_factor) 
    
    # PFP size and position adjusted for the simple center (e.g., center of 1280x720)
    PFP_SIZE = 380
    pfp = pfp.resize((PFP_SIZE, PFP_SIZE)) 
    
    # Calculating the center position for PFP: (BG_WIDTH/2 - PFP_SIZE/2, BG_HEIGHT/2 - PFP_SIZE/2)
    PFP_X = (BG_WIDTH // 2) - (PFP_SIZE // 2) 
    PFP_Y = (BG_HEIGHT // 2) - (PFP_SIZE // 2)
    pfp_position = (PFP_X, PFP_Y) # Should be around (450, 170)
    
    draw = ImageDraw.Draw(background)

    # Drawing a simple white border circle around the PFP
    BORDER_SIZE = PFP_SIZE + 20
    BORDER_X = (BG_WIDTH // 2) - (BORDER_SIZE // 2)
    BORDER_Y = (BG_HEIGHT // 2) - (BORDER_SIZE // 2)
    draw.ellipse((BORDER_X, BORDER_Y, BORDER_X + BORDER_SIZE, BORDER_Y + BORDER_SIZE), 
                 outline='white', width=5)
    
    background.paste(pfp, pfp_position, pfp)
    
    # Saving file with .png extension
    file_path = f"downloads/welcome#{id}.png" 
    background.save(file_path) 
    return file_path

def gen_thumb(image_path, uid):
    """Generates a 320x320 thumbnail from the welcome image."""
    try:
        img = Image.open(image_path)
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
        # NOTE: Default PFP (upic.png) must still be available locally, 
        # or you can replace this with another dynamically generated image.
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
        
    # File cleanup logic is intentionally removed.
