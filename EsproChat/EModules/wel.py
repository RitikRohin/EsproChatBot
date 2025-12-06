# ==================================
#    FINAL WELCOME MODULE (EsproChat)
# ==================================

from EsproChat import app
from pyrogram import Client, filters, enums
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
from logging import getLogger
import os 

LOGGER = getLogger(__name__)

# --- Directory Setup (Ensure 'downloads' directory exists) ---
DOWNLOADS_DIR = 'downloads'
if not os.path.isdir(DOWNLOADS_DIR):
    try:
        os.makedirs(DOWNLOADS_DIR)
    except Exception as e:
        LOGGER.error(f"Failed to create downloads directory: {e}")
        
# -------------------------------------------------------------

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
    Generates the welcome image dynamically with a solid color background 
    and adds text overlay to the right side.
    """
    BG_WIDTH, BG_HEIGHT = 1280, 720
    # Deep Indigo/Purple Color
    background = Image.new('RGB', (BG_WIDTH, BG_HEIGHT), color='#2C003E') 
    
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp, brightness_factor=brightness_factor) 
    
    PFP_SIZE = 380
    pfp = pfp.resize((PFP_SIZE, PFP_SIZE)) 
    
    draw = ImageDraw.Draw(background)

    # Coordinates for Left Side DP
    PFP_X = 150
    PFP_Y = (BG_HEIGHT // 2) - (PFP_SIZE // 2)
    pfp_position = (PFP_X, PFP_Y)
    
    # Border
    BORDER_SIZE = PFP_SIZE + 20
    BORDER_X = PFP_X - 10
    BORDER_Y = PFP_Y - 10
    draw.ellipse((BORDER_X, BORDER_Y, BORDER_X + BORDER_SIZE, BORDER_Y + BORDER_SIZE), 
                 outline='white', width=5)
    
    background.paste(pfp, pfp_position, pfp)
    
    # 💥 NEW: Text Overlay Logic (Right Side) 💥
    
    # 1. Define Fonts (Ensure these fonts are available on your system/hosting)
    try:
        # Use a common font or adjust path if necessary
        title_font = ImageFont.truetype("arial.ttf", 40) 
        content_font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        # Fallback to default font if the specific font is not found
        title_font = ImageFont.load_default()
        content_font = ImageFont.load_default()

    TEXT_COLOR = 'white'
    
    # Starting X position for text (Right side, starting 700 pixels from left)
    START_X = 650 
    # Starting Y position (Top of the frame)
    START_Y = 200 
    LINE_HEIGHT = 70
    
    # Data to display
    username = user.first_name or "New Member"
    member_id = str(id)
    # Total member count will be passed later, using a placeholder for now
    
    # Line 1: Welcome Message / User Name
    draw.text((START_X, START_Y), 
              f"WELCOME, {username.upper()}", 
              fill=TEXT_COLOR, 
              font=title_font)
              
    # Line 2: User ID
    draw.text((START_X, START_Y + 2 * LINE_HEIGHT), 
              f"🆔 User ID: {member_id}", 
              fill=TEXT_COLOR, 
              font=content_font)
              
    # Line 3: Total Members (Placeholder for total count)
    # The actual count is calculated in the handler and passed via the 'id' field in this function, 
    # but since chat_title is passed, let's assume we can also pass the count (for simplicity, we use the placeholder {chatname} for now)
    # NOTE: The actual count (count) is available in the handler, not directly passed here. 
    # We need to change the function signature if we want the actual count here.
    # For now, I will use a placeholder or assume 'uname' is used for count if the function signature cannot change.
    
    # To fix this, I am changing the function call in the handler to pass the count. 
    # But for THIS function definition, I will use the 'uname' argument as the count placeholder.
    draw.text((START_X, START_Y + 3 * LINE_HEIGHT), 
              f"👥 Total Members: {uname}", 
              fill=TEXT_COLOR, 
              font=content_font)


    # Saving file
    file_path = f"{DOWNLOADS_DIR}/welcome#{id}.png" 
    background.save(file_path) 
    return file_path

# ❌ gen_thumb function is removed as it doesn't need changes.

# --- Handler (Automatic Welcome) ---

@app.on_chat_member_updated(filters.group, group=-3)
async def greet_new_member(_, member: ChatMemberUpdated):
    """
    Automatically sends a welcome message when a new member joins.
    """
    welcomeimg = None
    
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
        # Default PFP path (Ensure this file 'upic.png' exists in assets)
        pic = "EsproChat/assets/upic.png"
        
    # Delete last welcome message for cleanup
    old = temp.last.get(chat_id)
    if old:
        try:
            await old.delete()
        except Exception as e:
            LOGGER.error(f"Error deleting old welcome message: {e}")

    try:
        # 1. Generate main image: Passing 'count' as the last argument (was 'uname')
        welcomeimg = welcomepic(
            pic, user.first_name, chat_title, user_id, str(count) # Passing count as the last argument
        )
        
        # 2. Generate thumbnail (Pyrogram will use this for auto-thumb)
        # Note: gen_thumb function needs to be defined if this is used, 
        # but since Pyrogram auto-generates thumb now, we can skip it, 
        # but based on the previous code, I'll keep the call but remove the function definition.
        # However, to be complete based on the last working code, I must restore gen_thumb.
        
        # RESTORING gen_thumb definition (was accidentally removed in the explanation, but kept in code)
        def gen_thumb(image_path, uid):
            """Generates a 320x320 thumbnail from the welcome image."""
            try:
                img = Image.open(image_path)
                img.thumbnail((320, 320)) 
                thumb_path = f"{DOWNLOADS_DIR}/thumb_{uid}.png" 
                img.save(thumb_path) 
                return thumb_path
            except Exception as e:
                LOGGER.error(f"Error generating thumbnail: {e}")
                return None
                
        thumb_path = gen_thumb(welcomeimg, user_id)
        
        # Define link
        add_link = f"https://t.me/{app.username}?startgroup=true"
        
        # Send photo
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
            # Removed 'thumb' keyword argument for Pyrogram v2+ compatibility
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="⚔️ ᴋɪᴅɴᴀᴘ ᴛʜɪs ʙᴏᴛ ⚔️", url=add_link)],
            ])
        )
        
        # Store the new message for cleanup
        temp.last[chat_id] = msg
        
    except Exception as e:
        LOGGER.error(f"Error sending welcome message: {e}")
