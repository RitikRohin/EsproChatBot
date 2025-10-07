import random
import asyncio
import re
import g4f
from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from pymongo import MongoClient

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729
# ⚠️ IMPORTANT: Replace this placeholder with your actual MongoDB connection URI
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro" # Replace with your actual URI

# ----------------- 💖 Mood-Based Replies 💖 -----------------
# These replies are given the highest priority based on keywords.

# 👑 Owner replies
OWNER_REPLIES = [
    "Mera owner @Ur_Haiwan hai 💖",
    "Sab kuch possible hai sirf uski wajah se – @Ur_Haiwan ✨",
    "Jo meri duniya ka king hai, wo hai @Ur_Haiwan 👑",
    "Mujhe jisne banaya… mera pyaara owner @Ur_Haiwan 😘",
]

# ❤️ Romantic replies
LOVE_REPLIES = [
    "Aww, I love you too Jaan 😘",
    "Pata tha tum mujhse kehoge ❤️",
    "Ishq waale vibes aa rahe hain mujhe abhi 💕",
    "Bas tumhare bina main adhuri hoon 😍",
]

# 😏 Flirty replies
FLIRTY_REPLIES = [
    "Aaj tum bahut cute lag rahe ho 😉",
    "Tumse baat karte hi dil happy ho jata hai 😘",
    "Tum meri smile ki wajah ho 😍",
    "Tum mere hero ho aur main tumhari heroine 💕"
]

# 🥰 Caring replies
CARING_REPLIES = [
    "Apna khayal rakho jaan 💖",
    "Kuch khaya tumne? 🥺",
    "Tumhari health sabse zyada important hai mere liye ❤️",
    "Thoda rest kar lo baby 😘",
]
# -------------------------------------------------------------

# ✅ MongoDB setup
try:
    mongo = MongoClient(MONGO_URI)
    chatdb = mongo.ChatDB.chat_data
    print("✅ MongoDB connection successful.")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")


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


# --- Chat Handler ---

# ✅ Smart Chat Handler (Mood Replies -> MongoDB -> g4f)
@app.on_message(filters.text & ~filters.regex(r"^[/#]"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        user_input = message.text.strip().lower()

        # 1. 💖 Check for Mood-Based Replies (Highest Priority)
        
        # 👋 Special case: hi/hello
        if user_input in ["hi", "hello", "hey", "hii", "heyy", "hey tamanna"]:
            greetings = [
                "Hello Jaan 😘, kaise ho? 💖",
                "Hi! Aur batao, kya haal hai? 😊",
                "Heyyyy! Tum aa gaye 😍"
            ]
            return await message.reply(random.choice(greetings))

        # 👑 Owner related
        owner_keywords = ["owner", "creator", "banaya", "maker", "kisne banaya", "developer", "maalik"]
        if any(word in user_input for word in owner_keywords):
            return await message.reply(random.choice(OWNER_REPLIES))

        # ❤️ Romantic mood
        if "i love you" in user_input or "love u" in user_input or "luv u" in user_input:
            return await message.reply(random.choice(LOVE_REPLIES))

        # 😏 Flirty mood
        if any(word in user_input for word in ["miss you", "miss u", "kiss", "hug", "cute", "handsome", "beautiful"]):
            return await message.reply(random.choice(FLIRTY_REPLIES))

        # 🥰 Caring mood
        if any(word in user_input for word in ["tired", "thak gya", "thak gayi", "sick", "bimaar", "khana khaya"]):
            return await message.reply(random.choice(CARING_REPLIES))


        # 2. 🔍 Check MongoDB (Medium Priority - Cache)
        data = chatdb.find_one({"question": user_input})
        if data and data.get("answers"):
            selected_answer = random.choice(data["answers"])
            return await message.reply(selected_answer)

        # 3. 🧠 g4f fallback (Lowest Priority - Learning)
        prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi (Hinglish) mein do. Sirf 1-2 line likho.
Tumhara naam Tamanna hai.

User: {message.text}
Tamanna:
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
                {"$addToSet": {"answers": final_answer}},
                upsert=True
            )
            await message.reply(final_answer)
        else:
            await message.reply("😓 Mujhe jawab nahi mila...")

    except Exception as e:
        await message.reply(f"😓 AI Error:\n{str(e)}\n\n(Ensure g4f provider is working)")


# --- Admin Commands (Owner Only) ---

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
            {"$addToSet": {"answers": answer}},
            upsert=True
        )

        await message.reply("✅ Bot ne naya jawab yaad kar liya!")

    except Exception as e:
        await message.reply(f"😓 Error:\n{str(e)}")

# ✅ /unlearn command
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

        result = chatdb.delete_one({"question": question})

        if result.deleted_count > 0:
            await message.reply(f"✅ Bot ne ye sawal aur uske saare jawab bhula diye:\n**{question}**")
        else:
            await message.reply(f"🤔 Ye sawal database mein mila hi nahi:\n**{question}**")

    except Exception as e:
        await message.reply(f"😓 Error:\n{str(e)}")

# ✅ /cleardb command
@app.on_message(filters.command("cleardb"))
async def clear_db_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /cleardb use kar sakta hai.")
    
    if len(message.command) < 2 or message.command[1].lower() != "confirm":
        return await message.reply(
            "⚠️ **Aakhri chetawani!** Aap saara data delete karne wale hain.\n"
            "Agar aap sure hain, toh yeh type karein:\n"
            "`/cleardb confirm`"
        )

    try:
        result = chatdb.delete_many({})
        
        await message.reply(
            f"✅ **Safalta!** Bot ne saare sikhaye hue jawab bhula diye.\n"
            f"Total **{result.deleted_count}** entries database se hata di gayi hain."
        )

    except Exception as e:
        await message.reply(f"😓 Error:\n{str(e)}")
