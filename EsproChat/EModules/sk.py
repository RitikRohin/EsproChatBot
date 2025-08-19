from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import random
from EsproChat import app  # Assuming 'app' is your Client instance
from config import MONGO_URL

# MongoDB setup
mongo_client = MongoClient(MONGO_URL)
chatai = mongo_client["Word"]["WordDb"]

# Optional: Ensure a unique index to prevent duplicate entries
try:
    chatai.create_index(
        [("word", 1), ("text", 1), ("check", 1)],
        unique=True
    )
except Exception as e:
    print(f"Index creation skipped or already exists: {e}")

@app.on_message(filters.sticker & ~filters.bot)
async def sticker_reply(client: Client, message: Message):
    # Case 1: Auto-reply if no reply_to_message
    if not message.reply_to_message:
        key = message.sticker.file_unique_id
        matches = list(chatai.find({"word": key, "check": "sticker"}).limit(10))
        if matches:
            chosen = random.choice(matches)
            await message.reply_sticker(chosen["text"])
        return

    # Case 2: Learn sticker -> sticker replies
    reply_msg = message.reply_to_message

    # Prevent learning if replying to the bot itself
    me = await client.get_me()
    if reply_msg.from_user and reply_msg.from_user.id == me.id:
        return

    # Only learn sticker-to-sticker replies
    if reply_msg.sticker and message.sticker:
        word = reply_msg.sticker.file_unique_id
        response = message.sticker.file_id

        # Insert only if the pair doesn't already exist
        try:
            chatai.insert_one({
                "word": word,
                "text": response,
                "check": "sticker"
            })
            print(f"Learned sticker pair: {word} -> {response}")
        except Exception as e:
            # Likely duplicate due to unique index
            print(f"Duplicate or insert error: {e}")
