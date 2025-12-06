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
    last = {}

temp = Temp()


# ------------- IMAGE FUNCTIONS -------------

def circle(pfp, size=(500, 500), brightness=10):
    pfp = pfp.resize(size).convert("RGBA")
    pfp = ImageEnhance.Brightness(pfp).enhance(brightness)

    mask = Image.new("L", (size[0]*3, size[1]*3), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0]*3, size[1]*3), fill=255)
    mask = mask.resize(size)
    pfp.putalpha(mask)
    return pfp


def make_welcome(pic, name, chat, uid):
    bg = Image.open("EsproChat/assets/wel2.png")
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((635, 635))

    bg.paste(pfp, (332, 323), pfp)

    path = f"downloads/welcome_{uid}.png"
    bg.save(path)
    return path


# ------------ NEW MEMBER JOIN ------------

@app.on_chat_member_updated(filters.group, group=-5)
async def welcome(_, u: ChatMemberUpdated):

    # block if not a new member
    if not u.new_chat_member or u.old_chat_member:
        return

    chat = u.chat.id
    user = u.new_chat_member.user

    total = await app.get_chat_members_count(chat)

    # get user pfp or default
    try:
        pic = await app.download_media(
            user.photo.big_file_id,
            file_name=f"pfp_{user.id}.png"
        )
    except:
        pic = "EsproChat/assets/upic.png"

    # delete last welcome message
    old = temp.last.get(chat)
    if old:
        try:
            await old.delete()
        except:
            pass

    # generate welcome image
    img = make_welcome(pic, user.first_name, u.chat.title, user.id)

    # buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 View Member", url=f"tg://user?id={user.id}")],
        [InlineKeyboardButton("➕ Add Bot", url=f"https://t.me/{app.username}?startgroup=true")]
    ])

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

    temp.last[chat] = msg
