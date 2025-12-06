# ============================
#       CLEAN WELCOME CODE
# ============================

from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
from logging import getLogger

LOGGER = getLogger(__name__)

# ---------------- DATABASE ----------------

class WelDB:
    def __init__(self):
        self.data = {}

    async def is_disabled(self, chat_id):
        return chat_id in self.data

    async def disable(self, chat_id):
        self.data[chat_id] = True

    async def enable(self, chat_id):
        if chat_id in self.data:
            del self.data[chat_id]

wlcm = WelDB()

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

    font = ImageFont.truetype("EsproChat/assets/font.ttf", 70)
    draw = ImageDraw.Draw(bg)

    path = f"downloads/welcome_{uid}.png"
    bg.save(path)
    return path


# ----------- /welcome on/off -------------

@app.on_message(filters.command("welcome") & filters.group)
async def switch_welcome(_, m: Message):

    if len(m.command) == 1:
        return await m.reply("**Use:** /welcome on | off")

    state = m.command[1].lower()
    chat = m.chat.id
    admin = await app.get_chat_member(chat, m.from_user.id)

    if admin.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await m.reply("Admins Only ⚠️")

    if state == "off":
        await wlcm.disable(chat)
        return await m.reply("❌ Welcome Disabled")

    if state == "on":
        await wlcm.enable(chat)
        return await m.reply("✅ Welcome Enabled")

    await m.reply("**Use:** /welcome on | off")


# ------------ NEW MEMBER JOIN ------------

@app.on_chat_member_updated(filters.group, group=-5)
async def welcome(_, u: ChatMemberUpdated):

    chat = u.chat.id

    if await wlcm.is_disabled(chat):
        return

    if not u.new_chat_member or u.old_chat_member:
        return

    user = u.new_chat_member.user
    total = await app.get_chat_members_count(chat)

    try:
        pic = await app.download_media(user.photo.big_file_id, file_name=f"pfp_{user.id}.png")
    except:
        pic = "EsproChat/assets/upic.png"

    # delete old welcome
    old = temp.last.get(chat)
    if old:
        try:
            await old.delete()
        except:
            pass

    # image generate
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
