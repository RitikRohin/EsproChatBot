from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
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

# ✅ Smart Chat Handler (DM + Groups)
@app.on_message(filters.text & (filters.private | filters.group) & ~filters.regex(r"^/") & ~filters.regex(r"^\s*#"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message):
        return  # ❌ Ignore replies or mentions

    if contains_link(message.text):
        return  # ❌ Ignore messages with links

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        user_input = message.text.strip().lower()
        mention = message.from_user.mention  # user mention

        # 🔍 Check MongoDB for stored answers
        data = chatdb.find_one({"question": user_input})
        if data and "answers" in data and data["answers"]:
            return await message.reply(f"{mention} {random.choice(data['answers'])}")

        # 🧠 Generate AI response (short answer)
        prompt = f"""
Tum ek real ladki ho. Har reply ladki ki jesa Hindi mein do. 
Sirf 1-2 shabd ka chhota reply do. Har bar alag jawab hona chahiye. 
Thoda random behave karo.

User: {message.text}
Espro:
"""

        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )

        final_answer = (response or "").strip()

        # ✅ Learn and save new answer
        if final_answer:
            chatdb.update_one(
                {"question": user_input},
                {"$push": {"answers": final_answer}},  # multiple answers store karo
                upsert=True
            )
            await message.reply(f"{mention} {final_answer}")
        else:
            await message.reply(f"{mention} 😓 Mujhe jawab nahi mila...")

    except Exception as e:
        await message.reply(f"{mention} 😓 Error:\n" + str(e))

# ✅ /teach command (owner only)
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
            {"$push": {"answers": answer}},  # multiple answers store karo
            upsert=True
        )

        await message.reply("✅ Bot ne naya jawab yaad kar liya!")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
