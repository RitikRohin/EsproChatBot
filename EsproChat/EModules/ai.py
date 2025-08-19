from EsproChat import app
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.enums import ChatAction
import g4f
from pymongo import MongoClient
import asyncio
import re
import random

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data      # For text chat responses
chatai = mongo.Word.WordDb           # For sticker replies

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

# ✅ Smart Chat Handler
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(random.uniform(0.5, 1.5))

    try:
        user_input = message.text.strip().lower()

        # 🔍 Check MongoDB first
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

        final_answer = str(response).strip()  # ensure it's a string

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

# ✅ Sticker Reply & Learning
@app.on_message(filters.sticker & ~filters.private)
async def sticker_reply(client, message: Message):
    try:
        getme = await client.get_me()
        bot_id = getme.id

        # Agar bot ko reply kiya jaa raha hai
        if message.reply_to_message and message.reply_to_message.from_user.id == bot_id:
            await message.chat.send_action(ChatAction.TYPING)
            await asyncio.sleep(random.uniform(0.5, 1.5))

            query_word = None
            if message.reply_to_message.sticker:
                query_word = message.reply_to_message.sticker.file_unique_id

            if query_word:
                results = list(chatai.find({"word": query_word}))
                if results:
                    chosen = random.choice(results)
                    if chosen['check'] == "sticker":
                        await message.reply_sticker(chosen['text'])
                    else:
                        await message.reply_text(chosen['text'])

        # Agar user kisi human message ko reply kar raha hai → learn
        elif message.reply_to_message:
            if message.sticker:
                query_word = None
                if message.reply_to_message.sticker:
                    query_word = message.reply_to_message.sticker.file_unique_id
                elif message.reply_to_message.text:
                    query_word = message.reply_to_message.text.strip().lower()

                if query_word:
                    record = chatai.find_one({
                        "word": query_word,
                        "text": message.sticker.file_id
                    })
                    if not record:
                        chatai.insert_one({
                            "word": query_word,
                            "text": message.sticker.file_id,
                            "check": "sticker"
                        })
    except Exception as e:
        print(f"Sticker handler error: {e}")
