from pyrogram import Client, filters
from pyrogram.types import Message
from EsproChat import app
from config import LOGGER_ID as LOG_GROUP_ID
from EsproChat.Db import get_served_chats, remove_served_chat, add_served_chat
import requests

@app.on_message(filters.new_chat_members, group=2)
async def on_new_chat_members(client: Client, message: Message):
    if (await client.get_me()).id in [user.id for user in message.new_chat_members]:
        added_by = message.from_user.mention if message.from_user else "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"

        # Fetch neko image
        response = requests.get("https://nekos.best/api/v2/neko").json()
        image_url = response["results"][0]["url"]

        served_chats = len(await get_served_chats())
        chat_id = message.chat.id

        # ✅ Generate Group Link Safely
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            try:
                # Try exporting invite link (only if bot is admin)
                chat_link = await client.export_chat_invite_link(chat_id)
            except:
                chat_link = "Private Group"

        msg = (
            f"❄️ <b><u>ʙᴏᴛ #ᴀᴅᴅᴇᴅ ᴛᴏ ɴᴇᴡ ɢʀᴏᴜᴘ </u></b> \n\n"
            f"┏━━━━━━━━━━━━━━━━━┓\n"
            f"┣★ **ᴄʜᴀᴛ** › : {message.chat.title}\n"
            f"┣★ **ᴄʜᴀᴛ ɪᴅ** › : {chat_id}\n"
            f"┣★ **ᴄʜᴀᴛ ᴜɴᴀᴍᴇ** › : @{message.chat.username or 'N/A'}\n"
            f"┣★ **ɢʀᴏᴜᴘ ʟɪɴᴋ** › : {chat_link}\n"
            f"┣★ **ᴛᴏᴛᴀʟ ᴄʜᴀᴛ** › : {served_chats}\n"
            f"┣★ **ᴀᴅᴅᴇᴅ ʙʏ** › : {added_by}\n"
            f"┗━━━━━━━━━★ "
        )

        await app.send_photo(LOG_GROUP_ID, photo=image_url, caption=msg)
        await add_served_chat(chat_id)


@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    if (await app.get_me()).id == message.left_chat_member.id:
        remove_by = message.from_user.mention if message.from_user else "𝐔ɴᴋɴᴏᴡɴ 𝐔sᴇʀ"
        title = message.chat.title
        chat_id = message.chat.id

        response = requests.get("https://nekos.best/api/v2/neko").json()
        image_url = response["results"][0]["url"]

        left = (
            f"❄️ <b><u>ʙᴏᴛ #ʟᴇғᴛ_ɢʀᴏᴜᴘ </u></b> \n\n"
            f"๏ ɢʀᴏᴜᴘ ɴᴀᴍᴇ ➠ {title}\n"
            f"๏ ɢʀᴏᴜᴘ ɪᴅ ➠ {chat_id}\n"
            f"๏ ʙᴏᴛ ʀᴇᴍᴏᴠᴇᴅ ʙʏ ➠ {remove_by}\n"
        )

        await app.send_photo(LOG_GROUP_ID, photo=image_url, caption=left)
        await remove_served_chat(chat_id)
