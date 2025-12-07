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
    Generates the welcome image dynamically.
    Uses 'EsproChat/assets/wel2.png' as the background if available, 
    otherwise uses a solid color. PFP is moved to the left side.
    """
    
    BG_WIDTH, BG_HEIGHT = 1280, 720
    resize_filter = Image.Resampling.LANCZOS # Define filter once
    
    # --- Background Selection (Using the provided path as a background) ---
    background_path = "EsproChat/assets/wel2.png"
    try:
        # Try loading the provided PNG as background
        background = Image.open(background_path).convert('RGB')
        background = background.resize((BG_WIDTH, BG_HEIGHT), resize_filter)
    except FileNotFoundError:
        LOGGER.warning(f"Background image {background_path} not found. Using solid color.")
        # Fallback to Deep Indigo/Purple Color
        background = Image.new('RGB', (BG_WIDTH, BG_HEIGHT), color='#2C003E') 
    except Exception as e:
        LOGGER.error(f"Error loading background image: {e}")
        background = Image.new('RGB', (BG_WIDTH, BG_HEIGHT), color='#2C003E') 
        
    # --- PFP Processing ---
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp, brightness_factor=brightness_factor) 
    
    # PFP size and position
    PFP_SIZE = 380
    pfp = pfp.resize((PFP_SIZE, PFP_SIZE), resize_filter) 
    
    PFP_X = int(BG_WIDTH * 0.10)  
    PFP_Y = (BG_HEIGHT // 2) - (PFP_SIZE // 2)
    pfp_position = (PFP_X, PFP_Y)
    
    draw = ImageDraw.Draw(background)

    # Drawing a simple white border circle around the PFP
    BORDER_SIZE = PFP_SIZE + 20
    BORDER_X = PFP_X - 10 
    BORDER_Y = PFP_Y - 10 
    
    # Draw the white border ellipse
    draw.ellipse((BORDER_X, BORDER_Y, BORDER_X + BORDER_SIZE, BORDER_Y + BORDER_SIZE), 
                 outline='white', width=5)
    
    # Paste the PFP
    background.paste(pfp, pfp_position, pfp)
    
    # --- LOGO OVERLAY ADDITION (Example Placeholder) ---
    # To add a logo (e.g., logo.png) on top of the background image:
    try:
        logo_path = "EsproChat/assets/wel2.png" # Assuming your logo is here
        logo = Image.open(logo_path).convert("RGBA")
        
        LOGO_SIZE = 200 # Set your desired logo size
        logo = logo.resize((LOGO_SIZE, LOGO_SIZE), resize_filter)
        
        # Position: Top Right Corner (50px margin)
        LOGO_X = BG_WIDTH - LOGO_SIZE - 50 
        LOGO_Y = 50 
        
        background.paste(logo, (LOGO_X, LOGO_Y), logo)
        
    except FileNotFoundError:
        # LOGGER.warning("Logo PNG file not found. Skipping overlay.")
        pass # Silently skip if logo is not mandatory
    except Exception as e:
        LOGGER.error(f"Error adding logo overlay: {e}")
    # ----------------------------------------------------
    
    # Saving file
    file_path = f"{DOWNLOADS_DIR}/welcome#{id}.png" 
    background.save(file_path) 
    return file_path

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
    
    try:
        count = await app.get_chat_members_count(chat_id)
    except Exception as e:
        LOGGER.warning(f"Could not get member count: {e}")
        count = "Unknown"

    # Download PFP
    try:
        pic_filename = f"pp{user_id}" 
        # Use full path to save temporary downloaded files
        temp_pic_path = os.path.join(DOWNLOADS_DIR, pic_filename) 
        pic = await app.download_media(
            user.photo.big_file_id, file_name=temp_pic_path
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
        # 1. Generate main image
        welcomeimg = welcomepic(
            pic, user.first_name, chat_title, user_id, user.username
        )
        
        # Define link
        add_link = f"https://t.me/{app.username}?startgroup=true"
        
        # Send photo 
        msg = await app.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=f"""
<blockquote>👋 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {chat_title}** 🌹</blockquote>
<blockquote>**━━━━━━━━━━━━━━━━━━━━**
👑 **ɴᴇᴡ ᴍᴇᴍʙᴇʀ:** {user.mention}
✨ **ɪᴅ:** `{user_id}`
🌐 **ᴜsᴇʀɴᴀᴍᴇ:** @{user.username or 'Not Set'}
👥 **ᴛᴏᴛᴀʟ ᴍᴇᴍʙᴇʀs:** `{count}`
**━━━━━━━━━━━━━━━━━━━━**</blockquote>
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="⚔️ ᴋɪᴅɴᴀᴘ ᴛʜɪs ʙᴏᴛ ⚔️", url=add_link)],
            ])
        )
        
        # Store the new message for cleanup
        temp.last[chat_id] = msg
        
    except Exception as e:
        LOGGER.error(f"Error sending welcome message: {e}")
    finally:
        # Clean up downloaded PFP file after use (if not using the default 'upic.png')
        if pic and "pp" in os.path.basename(pic):
            try:
                os.remove(pic)
            except Exception as e:
                LOGGER.error(f"Error deleting temporary PFP file: {e}")
        
