import random 
from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from pymongo import MongoClient
import asyncio
import re

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro" # Replace with your actual URI

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
# Note: Ensure the connection details (MONGO_URI) are correct.
chatdb = mongo.ChatDB.chat_data

# --- Helper Functions ---

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

# --- Chat Handlers ---

# ✅ Smart Chat Handler (Uses 'answers' list and random choice)
@app.on_message(filters.text & ~filters.regex(r"^[/#]"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message):
        return

    if contains_link(message.text):
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        user_input = message.text.strip().lower()

        # 🔍 Check MongoDB: 'answers' list से रैंडम जवाब चुनें
        data = chatdb.find_one({"question": user_input})
        if data and data.get("answers"):
            selected_answer = random.choice(data["answers"])
            return await message.reply(selected_answer)

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

        # ✅ Learn and save: नया जवाब 'answers' लिस्ट में $addToSet से जोड़ें
        if final_answer:
            chatdb.update_one(
                {"question": user_input},
                {"$addToSet": {"answers": final_answer}}, 
                upsert=True
            )
            await message.reply(final_answer)
        else:
            await message.reply("😓 Mujhe jawab nahi mila...")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

# --- Admin Commands ---

# ✅ /teach command (Updates 'answers' list)
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

        # $addToSet का उपयोग करके 'answers' लिस्ट में नया जवाब जोड़ें
        chatdb.update_one(
            {"question": question},
            {"$addToSet": {"answers": answer}},
            upsert=True
        )

        await message.reply("✅ Bot ne naya jawab yaad kar liya!")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

# ✅ /unlearn command (Deletes a specific question)
@app.on_message(filters.command("unlearn") & filters.text)
async def unlearn_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /unlearn use kar sakta hai.")

    try:
        try:
            question = message.text.split(" ", 1)[1]
            question = question.strip().lower()
        except IndexError:
            return await message.reply("❌ Format:\n`/unlearn question`\nExample: `/unlearn hii`")

        # MongoDB से सवाल को हटाएँ
        result = chatdb.delete_one({"question": question})

        if result.deleted_count > 0:
            await message.reply(f"✅ Bot ne ye sawal aur uske saare jawab bhula diye:\n**{question}**")
        else:
            await message.reply(f"🤔 Ye sawal database mein mila hi nahi:\n**{question}**")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

# ✅ /cleardb command (Deletes all learned data)
@app.on_message(filters.command("cleardb"))
async def clear_db_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /cleardb use kar sakta hai.")
    
    # ⚠️ सुरक्षा जांच: पुष्टि (confirmation) के बिना डिलीट न करें
    if len(message.command) < 2 or message.command[1].lower() != "confirm":
        return await message.reply(
            "⚠️ **Aakhri chetawani!** Aap saara data delete karne wale hain.\n"
            "Agar aap sure hain, toh yeh type karein:\n"
            "`/cleardb confirm`"
        )

    try:
        # MongoDB से सारे डॉक्यूमेंट्स डिलीट करें
        result = chatdb.delete_many({})
        
        await message.reply(
            f"✅ **Safalta!** Bot ne saare sikhaye hue jawab bhula diye.\n"
            f"Total **{result.deleted_count}** entries database se hata di gayi hain."
        )

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
