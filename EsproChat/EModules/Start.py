from EsproChat import app
from pyrogram import Client, filters
from EsproChat.Db import get_served_chats, get_served_users, add_served_user, add_served_chat
import requests 
from Murali import Owner
from pyrogram.enums import ChatType
import random 
from config import OWNER_ID, LOGGER_ID
import asyncio
from EsproChat.Strings import START_TEXT, START_BUTTON
from pyrogram.types import InlineKeyboardMarkup

# Emoji list
EMOJIOS = [
    "💣", "💥", "🪄", "🎋", "✨", "🦹", "🌺", "🍀", "💞", "🎁", "💌", "🧨", "⚡", "🤡", "👻",
    "🎃", "🎩", "🕊", "🍭", "🐻", "🦄", "🐼", "🐰", "🌸", "🌈", "🌟", "🌼", "🐱", "🐶", "🐨",
    "🐥", "🎮", "🎵", "📚", "🎨", "☕", "🍕", "🍦", "🍰", "🎈", "🎉", "🐤", "🍬"
]

# Sticker list
STICKER = [
    "CAACAgUAAx0CfAEyWgAClxdl9Gg4N-HyCImjGFXOQSHz50MD9wACzgoAAgrrYVWxPZWXGNr8SjQE",
    "CAACAgUAAx0CfAEyWgAClx1l9Gh9PHZKDIw8qbacmxzRD1QNAAOcDQAC0YVxVQijiuf_CF8_NAQ",
    "CAACAgUAAx0CfAEyWgAClyJl9Giplzk45LHa3SWbl30VQud5sgACJAgAAkemgVWsjZK8lbezvDQE",
    "CAACAgUAAx0CfAEyWgACmzZl-DHnr2MOLOPp34onib6dzUFjZgACQAgAApt6iFXzn_VE52urQDQE",
    "CAACAgUAAx0CfAEyWgAClydl9GjEpP5YDBYtPn-g8aC55Mmw_wACyQwAApDeqFbZJHowNnvidjQE",
    "CAACAgUAAx0CbEz78AABAQsvZfP2vNspUQkhtlqbZvDVUTvtIeIAApwNAALRhXFVCKOK5_8IXz8eBA",
    "CAACAgUAAx0CffjZyQACKoZmInOTHCv5lfpO580Y_UPEeUveYAAClAgAAspLwVT1oL4z_bhK7x4E",
    "CAACAgUAAx0CffjZyQACKo5mInRgNfyhH-Y3tKwKyj4_RoKu9gACsgYAAtAF2VYY6HZG8DUiyh4E",
    "CAACAgUAAx0CffjZyQACKoVmInNNz2YqgVIOm0b_XNASdarg0QAC9QkAAlTOgFSpIzlJ8dofZR4E",
    "CAACAgUAAx0CffjZyQACKohmInOZTlDo3YUTGWNdt1-8QFvrhQACqgwAArC9oFRVcuyU8PCqFR4E",
    "CAACAgUAAx0CffjZyQACKopmInPJwawFfy9z96S23cRxc5iI3QACegsAAtFEoVSKNlWkZeVvBh4E",
    "CAACAgUAAx0CffjZyQACKodmInOY37YoG7I-Mn9VbHbcE1VkYgACWAcAAmF4oFRci8T1o_XfEh4E",
    "CAACAgUAAx0CffjZyQACKotmInP5P_GvgKU67nB3ZXDU5UHdwQACBAkAAmGTqFTyMEUMwHr2WB4E",
    "CAACAgUAAx0CfAEyWgAClyxl9GkdhdvG8gmelpuDDXW43GdyYgACDAkAAgYmmVWwda82o5ssVx4E",
    "CAACAgQAAx0CfAEyWgACly9l9GoPSnyCro7QrrIPDIMl0VJNvAACKAwAArq5EFDBJa4kfYMtSB4E",
    "CAACAgUAAx0CfAEyWgAClzJl9Gphz8y2LOZXS_g4SBfUPQwAAeIAAs0EAAISTXlWi28Xpyv5nuUeBA"
]

# Photo list
PHOTOS = [
    "https://telegra.ph/file/018d6002a0ad3aee739f4.jpg",
    "https://telegra.ph/file/9d1b413d24ef703e931e3.jpg",
    "https://telegra.ph/file/035f1b9835c47f45952f7.jpg",
    "https://telegra.ph/file/ca93aeef2e7b45918b668.jpg",
    "https://telegra.ph/file/be64889b9a092f05bb51e.jpg",
    "https://telegra.ph/file/b75e6977d0fa2d5d78b0f.jpg",
    "https://telegra.ph/file/7a07ef4fd40ad2eb20c35.jpg",
    "https://telegra.ph/file/cc7adb01901d0e3d2ed3c.jpg",
    "https://telegra.ph/file/38e76bbfb4666757186f1.jpg",
    "https://telegra.ph/file/602b29a89fca3129194be.jpg",
    "https://telegra.ph/file/71d6213be9255750453a6.jpg",
    "https://telegra.ph/file/7576d27e926a634add7f4.jpg",
    "https://telegra.ph/file/c15485da3d83eb47ad0ff.jpg",
    "https://telegra.ph/file/2c46895723d637de84918.jpg",
    "https://telegra.ph/file/148858c4837e90c9cae49.jpg",
    "https://telegra.ph/file/aa5556e11d949e5f095c5.jpg",
    "https://telegra.ph/file/dd4479290dc8aecd5ed26.jpg",
    "https://telegra.ph/file/7226a80d33f1d9e9051a4.jpg",
    "https://telegra.ph/file/903078ebee2327f8a433c.jpg",
    "https://telegra.ph/file/f5e17db4530f3afb7df29.jpg"
]

# /start command
@app.on_cmd("start")
async def startbot(client, message):
    try:
        # 1. Welcome photo
        photo = await message.reply_photo(
            photo=random.choice(PHOTOS),
            caption=f"Hᴇʟʟᴏ {message.from_user.mention} 👋"
        )
        await asyncio.sleep(2)
        await photo.delete()

        # 2. Emoji pair
        emj = await message.reply_text(f"{random.choice(EMOJIOS)} {random.choice(EMOJIOS)}")
        await asyncio.sleep(1.3)
        await emj.delete()

        # 3. "let me start..."
        let = await message.reply_text("ʟᴇᴛ ᴍᴇ sᴛᴀʀᴛ...")
        await asyncio.sleep(1.5)
        await let.delete()

        # 4. 4 stickers with delay
        for _ in range(4):
            stkr = await message.reply_sticker(random.choice(STICKER))
            await asyncio.sleep(0.8)
            await stkr.delete()

        # 5. Final welcome with neko image
        neko = requests.get("https://nekos.best/api/v2/neko").json()
        neko_img = neko["results"][0]["url"]

        try:
            await app.resolve_peer(OWNER_ID[0])
            OWNER = OWNER_ID[0]
        except:
            OWNER = OWNER_ID[0]

        await message.reply_photo(
            photo=neko_img,
            caption=START_TEXT.format(message.from_user.mention, app.mention),
            reply_markup=START_BUTTON(OWNER),
        )

        # Log to DB
        try:
            if message.chat.type == ChatType.PRIVATE:
                await add_served_user(message.from_user.id)
            else:
                await add_served_chat(message.chat.id)
        except:
            pass

        await app.send_message(
            LOGGER_ID,
            f"🔔 ɴᴇᴡ /start ʙʏ {message.from_user.mention}\n"
            f"🆔: `{message.from_user.id}`\n"
            f"👤: @{message.from_user.username or 'NoUsername'}"
        )
    except Exception as e:
        print(f"[ERROR in /start] {e}")


# /stats command
@app.on_cmd("stats")
async def statsbot(client, message):
    if message.from_user.id not in Owner and message.from_user.id not in OWNER_ID:
        return

    neko = requests.get("https://nekos.best/api/v2/neko").json()
    neko_url = neko["results"][0]["url"]

    users = len(await get_served_users())
    chats = len(await get_served_chats())

    await message.reply_photo(
        photo=neko_url,
        caption=f"""✨ ᴛᴏᴛᴀʟ ꜱᴛᴀᴛꜱ ᴏꜰ {app.mention}:

👥 ᴜꜱᴇʀꜱ: {users}
💬 ᴄʜᴀᴛꜱ: {chats}
"""
            )
