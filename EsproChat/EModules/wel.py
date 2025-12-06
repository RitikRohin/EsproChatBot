# ============================
#       CLEAN WELCOME CODE
# ============================

from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from logging import getLogger

LOGGER = getLogger(__name__)


# -------------- TEMP STORAGE --------------

class Temp:
    """Stores the last welcome message ID for each chat for deletion."""
    last = {}

temp = Temp()


# ------------- IMAGE FUNCTIONS -------------

def circle(pfp, size=(500, 500), brightness=10):
    """
    Processes the profile picture (pfp) to make it circular and adjust brightness.
    
    Args:
        pfp (PIL.Image): The input profile picture image object.
        size (tuple): The desired size for the circular image.
        brightness (int): Enhancement factor for brightness.
        
    Returns:
        PIL.Image: The processed circular and transparent image.
    """
    pfp = pfp.resize(size).convert("RGBA")
    # Enhance brightness
    pfp = ImageEnhance.Brightness(pfp).enhance(brightness)

    # Create a circular mask
    mask = Image.new("L", (size[0]*3, size[1]*3), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0]*3, size[1]*3), fill=255)
    mask = mask.resize(size)
    
    # Apply the mask to make the corners transparent
    pfp.putalpha(mask)
    return pfp


def make_welcome(pic, name, chat, uid):
    """
    Generates the final welcome image by overlaying the user's DP on the background.
    
    Args:
        pic (str): Path to the user's downloaded profile picture.
        name (str): User's first name (not used in image generation, but kept for context).
        chat (str): Chat title (not used in image generation, but kept for context).
        uid (int): User ID, used for saving the unique image file.
        
    Returns:
        str: The file path to the generated welcome image.
    """
    # Load background image
    bg = Image.open("EsproChat/assets/wel2.png")
    
    # Load and process profile picture
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((635, 635))

    # Paste the circular DP onto the background at (332, 323)
    bg.paste(pfp, (332, 323), pfp)

    # Save the final image
    path = f"downloads/welcome_{uid}.png"
    bg.save(path)
    return path


# ------------ NEW MEMBER JOIN HANDLER ------------

@app.on_chat_member_updated(filters.group, group=-5)
async def welcome(_, u: ChatMemberUpdated):
    """Handles new member joins, generates, and sends the welcome message."""

    # block if not a new member (i.e., if it's a status change or a user leaving)
    if not u.new_chat_member or u.old_chat_member:
        return

    chat = u.chat.id
    user = u.new_chat_member.user

    # Get total members
    total = await app.get_chat_members_count(chat)

    # get user pfp or default
    try:
        pic = await app.download_media(
            user.photo.big_file_id,
            file_name=f"pfp_{user.id}.png"
        )
    except Exception as e:
        LOGGER.error(f"Error downloading PFP for {user.id}: {e}")
        pic = "EsproChat/assets/upic.png"

    # delete last welcome message for cleanup
    old = temp.last.get(chat)
    if old:
        try:
            await old.delete()
        except Exception as e:
            LOGGER.error(f"Error deleting old welcome message in chat {chat}: {e}")
            pass

    # generate welcome image
    img = make_welcome(pic, user.first_name, u.chat.title, user.id)

    # buttons for the message
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 View Member", url=f"tg://user?id={user.id}")],
        [InlineKeyboardButton("➕ Add Bot", url=f"https://t.me/{app.username}?startgroup=true")]
    ])

    # send the welcome message
    msg = await app.send_photo(
        chat,
        img,
        caption=f"""
**❅────✦ ᴡᴇʟᴄᴏᴍᴇ ✦────❅**

**➻ Name:** {user.mention}
**➻ ID:** `{user.id}`
**➻ Username:** @{user.username or 'N/A'}
**➻ Total Members:** {total}

❅─────✧❅✦❅✧─────❅
""",
        reply_markup=buttons
    )

    # Store the new message for future deletion
    temp.last[chat] = msg
