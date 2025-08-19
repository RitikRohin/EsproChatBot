from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import random

from EsproChat import app  # Assuming 'app' is your Client instance
from config import MONGO_URL

# ---------------- MongoDB setup ----------------
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["Word"]
chatai = db["WordDb"]

# Ensure unique index to prevent duplicates
try:
    chatai.create_index(
        [("word", 1), ("text", 1), ("check", 1)],
        unique=True
    )
except Exception as e:
    print(f"Index creation skipped or already exists: {e}")


# ---------------- Sticker Handler ----------------
@app.on_message(filters.sticker & ~filters.bot)
async def sticker_reply(client: Client, message: Message):
    """
    Sticker Auto-reply & Learning
    """

    # Case 1: Auto-reply if message is not a reply
    if not message.reply_to_message:
        key = message.sticker.file_unique_id
        matches = list(chatai.find({"word": key, "check": "sticker"}).limit(10))

        if matches:
            chosen = random.choice(matches)
            try:
                await message.reply_sticker(chosen["text"])  # text = file_id of reply sticker
            except Exception as e:
                print(f"Failed to send sticker: {e}")
        else:
            print(f"No sticker reply found for {key}")
        return

    # Case 2: Learn sticker-to-sticker replies
    reply_msg = message.reply_to_message

    # Prevent self-learning (ignore if replying to bot itself)
    me = await client.get_me()
    if reply_msg.from_user and reply_msg.from_user.id == me.id:
        return

    # Only learn sticker-to-sticker
    if reply_msg.sticker and message.sticker:
        word = reply_msg.sticker.file_unique_id   # input sticker (unique id)
        response = message.sticker.file_id        # reply sticker (file id for sending)

        try:
            chatai.insert_one({
                "word": word,
                "text": response,
                "check": "sticker"
            })
            print(f"✅ Learned sticker pair: {word} -> {response}")
        except DuplicateKeyError:
            print("⚠️ Sticker pair already exists")
        except Exception as e:
            print(f"Insert error: {e}")
