from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from pymongo import MongoClient
import asyncio
import re

from config import BOT_USERNAME, OWNER_ID, MONGO_URI

mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data

# ... baaki code same as previous full file ...
# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data

# ❌ Ignore if replying to or mentioning someone else
def is_message_for_someone_else(message: Message):
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user and not replied_user.is_self:
            return True

    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset : entity.offset + entity.length]
                if mention_text.lower() != f"@{BOT_USERNAME.lower()}":
                    return True
    return False

# ❌ Ignore if message contains a link
def contains_link(text):
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|[\w\-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store))"
    return bool(re.search(link_pattern, text.lower()))

# ✅ Smart Chat Handler for normal text messages (no commands)
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    # Ignore replies or mentions for someone else
    if is_message_for_someone_else(message):
        return

    # Ignore messages with links
    if contains_link(message.text):
        return

    # Ignore messages containing '#' anywhere
    if "#" in message.text:
        return

    # Ignore very short or empty messages
    user_input = message.text.strip().lower()
    if len(user_input) < 2:
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        # Check MongoDB for existing Q&A
        data = chatdb.find_one({"question": user_input})
        if data:
            return await message.reply(data["answer"], quote=True)

        # GPT fallback prompt (short, friendly Hindi)
        prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi mein do. Sirf 1-2 line likho.

User: {message.text}
Espro:
"""

        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )

        final_answer = response.strip()

        # Save to MongoDB if got answer
        if final_answer:
            chatdb.update_one(
                {"question": user_input},
                {"$set": {"answer": final_answer}},
                upsert=True
            )
            await message.reply(final_answer, quote=True)
        else:
            await message.reply("😓 Mujhe jawab nahi mila...", quote=True)

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e), quote=True)

# ✅ /teach command to manually add Q&A (owner only)
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /teach use kar sakta hai.", quote=True)

    try:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            return await message.reply("❌ Format:\n`/teach question | answer`", quote=True)

        text = parts[1]
        if "|" not in text:
            return await message.reply("❌ Format:\n`/teach question | answer`", quote=True)

        question, answer = text.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply("✅ Bot ne naya jawab yaad kar liya!", quote=True)

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e), quote=True)

# ✅ Save sticker replies (when replying to a sticker with text or sticker)
@app.on_message(filters.reply & (filters.text | filters.sticker))
async def save_sticker_reply(client, message: Message):
    replied_msg = message.reply_to_message
    if replied_msg and replied_msg.sticker:
        sticker_id = replied_msg.sticker.file_id

        if message.sticker:
            response_data = {"type": "sticker", "content": message.sticker.file_id}
        else:
            text = message.text.strip()
            if not text:
                return  # Ignore empty replies
            response_data = {"type": "text", "content": text}

        chatdb.update_one(
            {"sticker_file_id": sticker_id},
            {"$set": {"response": response_data}},
            upsert=True
        )
        await message.reply("✅ Sticker reply yaad ho gaya!", quote=True)

# ✅ Reply to stickers based on saved response (quote original sticker message)
@app.on_message(filters.sticker)
async def sticker_reply_handler(client, message: Message):
    sticker_id = message.sticker.file_id
    data = chatdb.find_one({"sticker_file_id": sticker_id})

    if data and "response" in data:
        resp = data["response"]
        if resp["type"] == "text":
            await message.reply(resp["content"], quote=True)
        elif resp["type"] == "sticker":
            await message.reply_sticker(resp["content"], quote=True)
