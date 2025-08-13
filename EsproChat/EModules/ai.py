from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from pymongo import MongoClient
import asyncio
import re
import logging
from datetime import datetime
import random

# -------------------- Config --------------------
BOT_USERNAME = "MissEsproBot"
OWNER_ID = 7666870729
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------- MongoDB --------------------
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data
stickerdb = mongo.StickerDB.sticker_data  # Sticker ↔ text storage

# -------------------- Helper Functions --------------------
async def is_message_for_someone_else(client, message: Message):
    bot_id = (await client.get_me()).id
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user and replied_user.id != bot_id:
            return True
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset:entity.offset + entity.length]
                if mention_text.lower() != f"@{BOT_USERNAME.lower()}":
                    return True
    return False

def contains_link(text: str):
    return bool(re.search(r"(https?://|t\.me/|www\.)\S+", text.lower()))

async def get_or_learn_answer(client, user_input: str, message: Message):
    # Check MongoDB first
    data = chatdb.find_one({"question": user_input})
    if data:
        return data["answer"]

    # GPT fallback
    prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi mein do. Sirf 1-2 line likho.

User: {message.text}
Espro:
"""
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )
        final_answer = response.strip()
    except Exception as e:
        logging.exception("GPT fallback error")
        final_answer = None

    if final_answer:
        chatdb.update_one(
            {"question": user_input},
            {"$set": {"answer": final_answer, "updated_at": datetime.utcnow()}},
            upsert=True
        )

    return final_answer

# -------------------- Sticker/Text Handler --------------------
@app.on_message((filters.text | filters.sticker) & ~filters.command)
async def smart_bot_handler(client, message: Message):
    try:
        if await is_message_for_someone_else(client, message):
            return

        if message.text and contains_link(message.text):
            return

        # Typing action for natural feel
        await message.chat.send_chat_action(ChatAction.TYPING)
        await asyncio.sleep(1)

        # ---------------- Handle Replies ----------------
        if message.reply_to_message:
            replied_msg = message.reply_to_message

            # If replying to bot → respond with stored sticker/text
            if replied_msg.from_user and replied_msg.from_user.is_self:
                key = None
                if message.text:
                    key = message.text.lower()
                    is_chat = list(stickerdb.find({"word": key}))
                elif message.sticker:
                    key = message.sticker.file_unique_id
                    is_chat = list(stickerdb.find({"word": key}))
                else:
                    return

                matches = [x['text'] for x in is_chat]
                if matches:
                    selected = random.choice(matches)
                    data = stickerdb.find_one({"text": selected})
                    if data['check'] == "sticker":
                        await message.reply_sticker(selected)
                    else:
                        await message.reply_text(selected)
                else:
                    # fallback to GPT if text
                    if message.text:
                        answer = await get_or_learn_answer(client, message.text.lower(), message)
                        if answer:
                            await message.reply(answer)

            # Learn new relation if replying to another user
            else:
                if message.sticker and replied_msg.text:
                    stickerdb.insert_one({
                        "word": replied_msg.text.lower(),
                        "text": message.sticker.file_id,
                        "check": "sticker",
                        "id": message.sticker.file_unique_id
                    })
                elif message.text and replied_msg.sticker:
                    stickerdb.insert_one({
                        "word": replied_msg.sticker.file_unique_id,
                        "text": message.text,
                        "check": "text"
                    })

        # ---------------- New Messages ----------------
        else:
            # Sticker
            if message.sticker:
                is_chat = list(stickerdb.find({"word": message.sticker.file_unique_id}))
                matches = [x['text'] for x in is_chat]
                if matches:
                    selected = random.choice(matches)
                    data = stickerdb.find_one({"text": selected})
                    if data['check'] == "sticker":
                        await message.reply_sticker(selected)
                    else:
                        await message.reply_text(selected)

            # Text
            elif message.text:
                answer = await get_or_learn_answer(client, message.text.lower(), message)
                if answer:
                    await message.reply(answer)

    except Exception:
        logging.exception("Error in smart_bot_handler")
        await message.reply("😓 Kuch galti ho gayi...")

# -------------------- /teach Command --------------------
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /teach use kar sakta hai.")

    try:
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            return await message.reply("❌ Format:\n`/teach question | answer`")

        question, answer = text.split("|", 1)
        question = " ".join(question.split()).lower()
        answer = answer.strip()

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer, "updated_at": datetime.utcnow()}},
            upsert=True
        )

        await message.reply("✅ Bot ne naya jawab yaad kar liya!")

    except Exception:
        logging.exception("Error in /teach command")
        await message.reply("😓 Kuch galti ho gayi...")

logging.info("✅ Espro Chat Bot (Text + Sticker) Running...")
