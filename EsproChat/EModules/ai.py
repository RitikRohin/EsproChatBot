from EsproChat import app  # Make sure this exists
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from pymongo import MongoClient
import asyncio
import re
import g4f
from datetime import datetime

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data
stickerdb = mongo.ChatDB.sticker_data

# ❌ Ignore if replying to or mentioning someone else
def is_message_for_someone_else(message: Message):
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user and not replied_user.is_self:
            return True
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset:entity.offset + entity.length]
                if mention_text.lower() != f"@{BOT_USERNAME.lower()}":
                    return True
    return False

# ❌ Ignore if message contains a link
def contains_link(text):
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|[\w\-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store))"
    return bool(re.search(link_pattern, text.lower()))

# ✅ Text Handler
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        user_input = message.text.strip().lower()

        # 🔍 Check MongoDB
        data = chatdb.find_one({"question": user_input})
        if data:
            return await message.reply(data["answer"])

        # 🧠 GPT fallback
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

        # ✅ Learn and save
        if final_answer:
            chatdb.update_one(
                {"question": user_input},
                {"$set": {"answer": final_answer}},
                upsert=True
            )
            await message.reply(final_answer)
        else:
            await message.reply("😓 Mujhe jawab nahi mila...")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

# ✅ /teach command
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

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply("✅ Bot ne naya jawab yaad kar liya!")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

# ✅ Sticker Handler
@app.on_message(filters.sticker)
async def handle_sticker(client, message: Message):
    sticker_id = message.sticker.file_unique_id

    # 🔍 Check DB
    data = stickerdb.find_one({"sticker_id": sticker_id})
    if data:
        if data["answer"].startswith("[Sticker: "):
            sticker_file_id = data["answer"].split(": ")[1][:-1]
            return await message.reply_sticker(sticker_file_id)
        else:
            return await message.reply(data["answer"])

    # 👀 Wait for reply from user
    if message.reply_to_message and message.reply_to_message.text:
        reply_text = message.reply_to_message.text.strip()

        stickerdb.update_one(
            {"sticker_id": sticker_id},
            {"$set": {"answer": reply_text}},
            upsert=True
        )
        return await message.reply("✅ Maine is sticker ka jawab yaad kar liya!")

    await message.reply("🤔 Is sticker ka jawab mujhe nahi pata.")

# ✅ Sticker Reply Learning
@app.on_message(filters.reply & (filters.text | filters.sticker))
async def handle_reply_to_sticker(client, message: Message):
    replied = message.reply_to_message

    if replied.sticker:
        sticker_id = replied.sticker.file_unique_id

        if message.text:
            answer = message.text.strip()
        elif message.sticker:
            answer = f"[Sticker: {message.sticker.file_id}]"
        else:
            return

        stickerdb.update_one(
            {"sticker_id": sticker_id},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply("✅ Sticker ka jawab yaad ho gaya!")

# ✅ Manual teach sticker command
@app.on_message(filters.command("teach_sticker") & filters.reply)
async def manual_teach_sticker(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi is command ko use kar sakta hai.")

    replied = message.reply_to_message
    if not replied.sticker:
        return await message.reply("❌ Reply kisi sticker par karo.")

    try:
        text = message.text.split(" ", 1)[1].strip()
        sticker_id = replied.sticker.file_unique_id

        stickerdb.update_one(
            {"sticker_id": sticker_id},
            {"$set": {"answer": text}},
            upsert=True
        )
        await message.reply("✅ Sticker ka custom jawab set ho gaya!")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
