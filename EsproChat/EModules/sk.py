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

    # Case 1: Auto reply from DB (Sticker without reply)
    if not message.reply_to_message:
        key = message.sticker.file_unique_id
        match = list(chatai.aggregate([
            {"$match": {"word": key, "check": "sticker"}},
            {"$sample": {"size": 1}}
        ]))

        if match:
            file_id = match[0]["text"]

            await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
            await asyncio.sleep(random.uniform(1.0, 3.0))
            sent = await message.reply_sticker(file_id)

            log.info(f"✅ Sent sticker reply for {key}")
            return

        # ---------------- If no DB match → Reply from Sticker Pack ----------------
        if message.sticker.set_name:
            try:
                stickers = await fetch_sticker_set(client.bot_token, message.sticker.set_name)
                if stickers:
                    random_sticker = random.choice(stickers)

                    await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    sent = await message.reply_sticker(random_sticker["file_id"])

                    log.info(f"✅ Auto-replied from sticker pack {message.sticker.set_name}")
                else:
                    log.info("⚠️ Sticker set fetch failed")
            except Exception as e:
                log.error(f"❌ Failed to fetch sticker set: {e}")
        else:
            log.info("⚠️ Sticker has no set_name (custom/one-time sticker)")
        return

    # Case 2: Learning new sticker pair (only if replying to Bot's sticker)
    reply_msg = message.reply_to_message

    # Ignore if replying to another user (not bot)
    if not reply_msg.from_user or reply_msg.from_user.id != me.id:
        log.info("⚠️ Ignored: User replied to another user, not bot")
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

        # Bot should also reply back for this sticker B
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
            log.info(f"✅ Sent reply for learned sticker {key}")
        else:
            if message.sticker.set_name:
                try:
                    stickers = await fetch_sticker_set(client.bot_token, message.sticker.set_name)
                    if stickers:
                        random_sticker = random.choice(stickers)
                        await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
                        await asyncio.sleep(random.uniform(1.0, 2.0))
                        await message.reply_sticker(random_sticker["file_id"])
                        log.info(f"✅ Auto-replied (learn mode) from sticker pack {message.sticker.set_name}")
                except Exception as e:
                    log.error(f"❌ Failed to fetch sticker set: {e}")
