from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from pymongo import MongoClient

# ✅ Config
BOT_USERNAME = "MissEsproBot"  # 👈 without @
OWNER_ID = 7666870729  # 👈 Replace with your Telegram user ID
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"  # 👈 Replace this

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data

# ❌ Agar message kisi aur ko reply/mention karta hai (bot ko chhodkar), to ignore karo
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

# ✅ Main handler
@app.on_message(filters.text & ~filters.regex(r"^/"))  # Ignore commands
async def smart_bot_handler(client, message: Message):
    if message.chat.type == "private":
        pass
    elif message.chat.type in ("group", "supergroup"):
        if is_message_for_someone_else(message):
            return

    await message.reply_chat_action(ChatAction.TYPING)

    try:
        user_input = message.text.strip().lower()

        # 🔎 Check MongoDB
        data = chatdb.find_one({"question": user_input})
        if data:
            await message.reply(data["answer"])
            return

        # 💬 Prompt for GPT
        prompt = f"""
Tum ek reyal ladki ho jitna ek ladki ke aandar hota hai tumare aandar hona chahiye Har reply 1 ya 2 line ka hi do. Friendly aur normal Hindi me baat karo.

User: {message.text}
Espro:
"""
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo,
            messages=[{"role": "user", "content": prompt}],
        )

        final_answer = response.strip()

        # ✅ Save to MongoDB
        chatdb.insert_one({"question": user_input, "answer": final_answer})
        await message.reply(final_answer)

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

# ✅ /teach command to manually teach the bot
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    # ✅ Check if sender is owner or admin
    is_owner = message.from_user.id == OWNER_ID
    is_admin = False

    if message.chat.type != "private":
        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            is_admin = member.status in ("administrator", "creator")
        except:
            pass

    if not (is_owner or is_admin or message.chat.type == "private"):
        return await message.reply("❌ Sirf owner ya admin hi /teach use kar sakta hai.")

    try:
        # ✅ Parse question | answer
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            return await message.reply("❌ Format galat hai!\nUse this format:\n`/teach question | answer`")

        question, answer = text.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()

        # ✅ Update or insert
        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply("✅ Bot ne naya jawab yaad kar liya!")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
