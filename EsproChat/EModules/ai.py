from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from pymongo import MongoClient, ASCENDING
import g4f
import asyncio
import re
import random
import os

# --- Config ---
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729
MONGO_URI = os.environ.get("MONGO_URI") or "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"

# --- Pyrogram App ---
app = Client("EsproChatBot",
             api_id=int(os.environ.get("API_ID", 12345)),
             api_hash=os.environ.get("API_HASH", "hash"),
             bot_token=os.environ.get("BOT_TOKEN", "token"))

# --- MongoDB setup ---
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data       # For GPT Q&A
stickerdb = mongo.StickerDB.sticker_data  # For sticker/text replies
stickerdb.create_index([("word", ASCENDING), ("text", ASCENDING)], unique=True)

# --- Helper Functions ---
def is_message_for_someone_else(message: Message):
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user and not replied_user.is_self:
            return True
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset:entity.offset+entity.length]
                if mention_text.lower() != f"@{BOT_USERNAME.lower()}":
                    return True
    return False

def contains_link(text):
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|[\w\-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store))"
    return bool(re.search(link_pattern, text.lower()))

# --- GPT-based Smart Reply ---
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message):
        return
    if contains_link(message.text):
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)
    user_input = message.text.strip().lower()

    # Check MongoDB first
    data = chatdb.find_one({"question": user_input})
    if data:
        return await message.reply(data["answer"])

    # GPT fallback
    prompt = f"""Tum ek real ladki ho. Har reply chhoti aur friendly Hindi mein do. Sirf 1-2 line likho.

User: {message.text}
Espro:
"""
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )
        final_answer = response.strip()
        if final_answer:
            chatdb.update_one({"question": user_input},
                              {"$set": {"answer": final_answer}}, upsert=True)
            await message.reply(final_answer)
        else:
            await message.reply("😓 Mujhe jawab nahi mila...")
    except Exception as e:
        await message.reply(f"😓 Error:\n{str(e)}")

# --- Sticker/Text Reply Handler ---
@app.on_message((filters.sticker | filters.text) & ~filters.bot)
async def sticker_ai_reply(client, message: Message):
    bot_id = (await app.get_me()).id

    async def mongo_find(query):
        return await asyncio.to_thread(lambda: list(stickerdb.find(query)))

    async def mongo_find_one(query):
        return await asyncio.to_thread(lambda: stickerdb.find_one(query))

    async def mongo_upsert(doc):
        await asyncio.to_thread(lambda: stickerdb.update_one(
            {"word": doc["word"], "text": doc["text"]}, {"$set": doc}, upsert=True))

    # Replying to a message
    if message.reply_to_message:
        replied = message.reply_to_message

        if replied.from_user and replied.from_user.id == bot_id:
            content = message.text if message.text else message.sticker.file_unique_id
            matches = await mongo_find({"word": content})
            if matches:
                choice = random.choice(matches)
                if choice["check"] == "sticker":
                    await message.reply_sticker(choice["text"])
                else:
                    await message.reply_text(choice["text"])
        else:
            if message.sticker and replied.text:
                await mongo_upsert({
                    "word": replied.text.strip(),
                    "text": message.sticker.file_id,
                    "check": "sticker",
                    "id": message.sticker.file_unique_id
                })
            elif message.text and replied.sticker:
                await mongo_upsert({
                    "word": replied.sticker.file_unique_id,
                    "text": message.text.strip(),
                    "check": "text"
                })
    # Direct sticker/text without reply
    else:
        content = message.text if message.text else message.sticker.file_unique_id
        matches = await mongo_find({"word": content})
        if matches:
            choice = random.choice(matches)
            if choice["check"] == "sticker":
                await message.reply_sticker(choice["text"])
            else:
                await message.reply_text(choice["text"])

# --- /teach Command ---
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /teach use kar sakta hai.")

    try:
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            return await message.reply("❌ Format:\n`/teach question | answer`")
        question, answer = text.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()
        chatdb.update_one({"question": question}, {"$set": {"answer": answer}}, upsert=True)
        await message.reply("✅ Bot ne naya jawab yaad kar liya!")
    except Exception as e:
        await message.reply(f"😓 Error:\n{str(e)}")

