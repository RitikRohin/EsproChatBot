import logging
import asyncio
import random
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from config import MONGO_URL
from EsproChat import app   # pyrogram Client instance

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("StickerBot")

# ---------------- MongoDB ----------------
mongo = MongoClient(MONGO_URL)
db = mongo["Word"]
chatai = db["WordDb"]

# ensure unique index
chatai.create_index([("word", 1), ("text", 1), ("check", 1)], unique=True)


# ---------------- Helper: Fetch sticker set via Bot API ----------------
async def fetch_sticker_set(bot_token: str, set_name: str):
    url = f"https://api.telegram.org/bot{bot_token}/getStickerSet?name={set_name}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if data.get("ok"):
                return data["result"]["stickers"]
            return None


# ---------------- Sticker Handler ----------------
@app.on_message(filters.sticker & ~filters.bot)
async def sticker_reply(client: Client, message: Message):
    me = await client.get_me()

    # ---------------- Case 2: Learning (reply to bot's sticker) ----------------
    if message.reply_to_message and message.reply_to_message.sticker:
        # only if reply is to bot's sticker
        if message.reply_to_message.from_user and message.reply_to_message.from_user.id == me.id:
            key = message.sticker.file_unique_id

            # First check DB
            match = list(chatai.aggregate([
                {"$match": {"word": key, "check": "sticker"}},
                {"$sample": {"size": 1}}
            ]))

            if match:
                file_id = match[0]["text"]
                await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
                await asyncio.sleep(random.uniform(1.0, 2.5))
                await message.reply_sticker(file_id)
            else:
                # Fallback: from sticker pack
                if message.sticker.set_name:
                    try:
                        stickers = await fetch_sticker_set(client.bot_token, message.sticker.set_name)
                        if stickers:
                            random_sticker = random.choice(stickers)
                            await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
                            await asyncio.sleep(random.uniform(1.0, 2.0))
                            await message.reply_sticker(random_sticker["file_id"])
                    except Exception as e:
                        log.error(f"❌ Failed to fetch sticker set: {e}")

            # Save learning pair (X → B)
            try:
                chatai.insert_one({
                    "word": message.reply_to_message.sticker.file_unique_id,
                    "text": message.sticker.file_id,
                    "check": "sticker"
                })
                log.info("✅ Learned pair: %s -> %s",
                         message.reply_to_message.sticker.file_unique_id,
                         message.sticker.file_id)
            except DuplicateKeyError:
                log.info("⚠️ Duplicate pair skipped")
        else:
            log.info("⏩ Ignored sticker reply (because it was replying to another user)")
        return

    # ---------------- Case 1: Normal Sticker (no reply) ----------------
    key = message.sticker.file_unique_id
    match = list(chatai.aggregate([
        {"$match": {"word": key, "check": "sticker"}},
        {"$sample": {"size": 1}}
    ]))

    if match:
        file_id = match[0]["text"]
        await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
        await asyncio.sleep(random.uniform(1.0, 3.0))
        await message.reply_sticker(file_id)
        log.info(f"✅ Sent sticker reply for {key}")
    else:
        if message.sticker.set_name:
            try:
                stickers = await fetch_sticker_set(client.bot_token, message.sticker.set_name)
                if stickers:
                    random_sticker = random.choice(stickers)
                    await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    await message.reply_sticker(random_sticker["file_id"])
                    log.info(f"✅ Auto-replied from sticker pack {message.sticker.set_name}")
            except Exception as e:
                log.error(f"❌ Failed to fetch sticker set: {e}")
