from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from g4f.models import gpt_4
from pymongo import MongoClient
import asyncio
import re

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data
chatdb.create_index("question", unique=True)

# ✅ Main smart reply handler
@app.on_message(filters.text & ~filters.command(["teach"]))
async def smart_bot_handler(client, message: Message):
    if message.from_user and message.from_user.is_bot:
        return

    # ✅ Check chat type
    if message.chat.type == "private":
        pass  # Always respond in private
    elif message.chat.type in ("group", "supergroup"):
        bot_user = await client.get_me()
        is_mentioned = f"@{BOT_USERNAME.lower()}" in message.text.lower()
        is_replied_to_bot = (
            message.reply_to_message and
            message.reply_to_message.from_user and
            message.reply_to_message.from_user.id == bot_user.id
        )
        if not (is_mentioned or is_replied_to_bot):
            return  # ❌ Ignore messages not meant for bot

    # ❌ Ignore messages containing links
    if re.search(r'https?://|www\.', message.text.lower()):
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(min(3, max(1, len(message.text) * 0.03)))  # Typing delay

    try:
        user_input = message.text.strip().lower()

        # 🔍 Check in MongoDB
        data = chatdb.find_one({"question": user_input})
        if data:
            return await message.reply(data["answer"])

        # 🧠 GPT Prompt
        prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi mein do. Sirf 1-2 line likho.

User: {message.text}
Espro:
"""

        response = g4f.ChatCompletion.create(
            model=gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )

        final_answer = response.strip()

        if final_answer:
            # ✅ Save reply
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

# ✅ /teach command to manually teach bot
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    is_owner = message.from_user.id == OWNER_ID
    is_admin = False

    # ✅ Check admin
    if message.chat.type != "private":
        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            is_admin = member.status in ("administrator", "creator")
        except:
            pass

    if not (is_owner or is_admin or message.chat.type == "private"):
        return await message.reply("❌ Sirf owner ya admin hi /teach use kar sakta hai.")

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
