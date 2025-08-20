# filename: sticker_bot.py
import logging
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from config import MONGO_URL
from EsproChat import app   # your pyrogram Client


# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("StickerBot")


# ---------------- MongoDB ----------------
mongo = MongoClient(MONGO_URL)
db = mongo["Word"]
chatai = db["WordDb"]

# ensure unique index (word + text + check combination)
chatai.create_index([("word", 1), ("text", 1), ("check", 1)], unique=True)


# ---------------- Sticker Handler ----------------
@app.on_message(filters.sticker & ~filters.bot)
async def sticker_reply(client: Client, message: Message):

    # Case 1: Auto reply
    if not message.reply_to_message:
        key = message.sticker.file_unique_id
        match = list(chatai.aggregate([
            {"$match": {"word": key, "check": "sticker"}},
            {"$sample": {"size": 1}}
        ]))

        if match:
            file_id = match[0]["text"]

            # Step 1: Show "choosing sticker..."
            await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)

            # Step 2: Random delay (1–3 sec) for natural effect
            await asyncio.sleep(random.uniform(1.0, 3.0))

            # Step 3: Reply with sticker
            await message.reply_sticker(file_id)

            log.info(f"✅ Sent sticker reply for {key}")
        else:
            log.info(f"⚠️ No sticker reply found for {key}")
        return

    # Case 2: Learning new sticker pair
    reply_msg = message.reply_to_message

    me = await client.get_me()
    if reply_msg.from_user and reply_msg.from_user.id == me.id:
        return

    if reply_msg.sticker and message.sticker:
        try:
            chatai.insert_one({
                "word": reply_msg.sticker.file_unique_id,
                "text": message.sticker.file_id,
                "check": "sticker"
            })
            log.info("✅ Learned pair: %s -> %s",
                     reply_msg.sticker.file_unique_id,
                     message.sticker.file_id)
        except DuplicateKeyError:
            log.info("⚠️ Duplicate pair skipped")
