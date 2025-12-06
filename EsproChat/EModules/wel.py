from EsproChat import app
from pyrogram import Client, filters, enums
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
from os import getLogger

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
    """Generates the welcome image with DP overlay."""
    background = Image.open("EsproChat/assets/wel2.png")
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp, brightness_factor=brightness_factor) 
    pfp = pfp.resize((635, 635))
    
    draw = ImageDraw.Draw(background)

    pfp_position = (332, 323)
    background.paste(pfp, pfp_position, pfp)
    
    file_path = f"downloads/welcome#{id}.png"
    background.save(file_path)
    return file_path

# --- Handler (Automatic Welcome) ---

@app.on_chat_member_updated(filters.group, group=-3)
async def greet_new_member(_, member: ChatMemberUpdated):
    """Automatically sends a welcome message when a new member joins."""

    chat_id = member.chat.id
    
    if not (member.new_chat_member and not member.old_chat_member and member.new_chat_member.status != enums.ChatMemberStatus.KICKED):
        return

    user = member.new_chat_member.user
    # Get the chat title dynamically
    chat_title = member.chat.title
    count = await app.get_chat_members_count(chat_id)
    
    try:
        pic = await app.download_media(
            user.photo.big_file_id, file_name=f"pp{user.id}.png"
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
        # Generate image
        welcomeimg = welcomepic(
            pic, user.first_name, chat_title, user.id, user.username
        )
        
        # Define link
        add_link = f"https://t.me/{app.username}?startgroup=true"
        
        # Send photo and caption
        msg = await app.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=f"""
👋 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {chat_title}** 🌹

**━━━━━━━━━━━━━━━━━━━━**

👑 **ɴᴇᴡ ᴍᴇᴍʙᴇʀ:** {user.mention}
✨ **ɪᴅ:** `{user.id}`
🌐 **ᴜsᴇʀɴᴀᴍᴇ:** @{user.username or 'Not Set'}
👥 **ᴛᴏᴛᴀʟ ᴍᴇᴍʙᴇʀs:** `{count}`

**━━━━━━━━━━━━━━━━━━━━**
""",
            # Markup contains only the "Kidnap Me" button
            reply_markup=InlineKeyboardMarkup([
                # Button text changed for better styling
                [InlineKeyboardButton(text="⚔️ ᴋɪᴅɴᴀᴘ ᴛʜɪs ʙᴏᴛ ⚔️", url=add_link)],
            ])
        )
        
        # Store the new message for cleanup
        temp.last[chat_id] = msg
        
    except Exception as e:
        LOGGER.error(f"Error sending welcome message: {e}")
