# filename: sticker_bot.py
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import logging
import asyncio

from config import MONGO_URL
from EsproChat import app   # your pyrogram Client


# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("StickerBot")


# ---------------- MongoDB ----------------
mongo = MongoClient(MONGO_URL)
db = mongo["Word"]
chatai = db["WordDb"]

# ensure unique index
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
            # fake effect → typing action before sending sticker
            await app.send_chat_action(message.chat.id, "typing")
            await asyncio.sleep(1.5)  # delay for effect
            await message.reply_sticker(file_id)
            log.info(f"✅ Sent sticker reply for {key}")
        else:
            log.info(f"⚠️ No sticker reply found for {key}")
        return

    # Case 2: Learning
    reply_msg = message.reply_to_message

    me = await client.get_me()
    if reply_msg.from_user and reply_msg.from_user.id == me.id:
        return

    if reply_msg.sticker and message.sticker:
        try:
            chatai.insert_one({
                "word": reply_msg.sticker.file_unique_id,
                "text": message.sticker.file_id,
                "unique": message.sticker.file_unique_id,
                "check": "sticker"
            })
            log.info("✅ Learned pair: %s -> %s",
                     reply_msg.sticker.file_unique_id,
                     message.sticker.file_id)
        except DuplicateKeyError:
            log.info("⚠️ Duplicate pair skipped")
