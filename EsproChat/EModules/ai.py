from EsproChat import app
from pyrogram import filters, enums
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
chatdb = mongo.ChatDB.chat_data
chatai = mongo.Word.WordDb  # Sticker/Text DB for stickers

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

# ✅ Smart Chat Handler - text only, ignore #messages
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message):
        return
    if contains_link(message.text):
        return
    if message.text.strip().startswith("#"):  # ❌ Ignore messages starting with #
        return

    # 🤖 Bot reply to user text
    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

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
async def sticker_handler(client, message: Message):
    try:
        if not message.reply_to_message:
            return

        reply_to = message.reply_to_message
        bot_id = (await client.get_me()).id

        # ✅ Learning: User replies to human sticker (NOT bot), and replied message must be a sticker
        if reply_to.from_user.id != bot_id:
            # 🧠 Allow only if replied to a sticker
            if reply_to.sticker:
                key = reply_to.sticker.file_unique_id
                chatai.insert_one({
                    "word": key,
                    "text": message.sticker.file_id,
                    "check": "sticker"
                })
            return

        # 🤖 Reply mode: Bot’s own sticker received a sticker reply
        if reply_to.sticker:
            key = reply_to.sticker.file_unique_id
            results = list(chatai.find({"word": key, "check": "sticker"}))
            if results:
                chosen = random.choice(results)
                await message.reply_sticker(chosen["text"])

    except Exception as e:
        await message.reply(f"😓 Sticker error:\n{str(e)}")

# ✅ Text Reply to Sticker Handler
@app.on_message(filters.text & ~filters.command(["each"]))
async def sticker_text_handler(client, message: Message):
    try:
        if not message.reply_to_message:
            return

        reply_to = message.reply_to_message
        bot_id = (await client.get_me()).id

        # ✅ Learning: Replying to a human sticker with text
        if reply_to.sticker and reply_to.from_user.id != bot_id:
            key = reply_to.sticker.file_unique_id
            chatai.insert_one({
                "word": key,
                "text": message.text.strip(),
                "check": "text"
            })
            return

        # 🤖 Reply Mode: Replying to bot’s sticker with text message
        if reply_to.sticker and reply_to.from_user.id == bot_id:
            key = reply_to.sticker.file_unique_id
            results = list(chatai.find({"word": key, "check": "text"}))
            if results:
                chosen = random.choice(results)
                await message.reply(chosen["text"])

    except Exception as e:
        await message.reply(f"😓 Text-on-sticker error:\n{str(e)}")
