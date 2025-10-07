import os
import random
import asyncio
import re
import g4f
from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from pymongo import MongoClient
from datetime import datetime
import pytz 

# ----------------- 🔧 Config & Setup -----------------

# 🔧 Config: Using environment variables with fallbacks
BOT_USERNAME = os.environ.get("BOT_USERNAME", "MissEsproBot")
try:
    # Convert OWNER_ID to int, usually comes as a string from os.environ
    OWNER_ID = int(os.environ["OWNER_ID"])
except (KeyError, ValueError):
    OWNER_ID = 7666870729 # Default owner ID
    print("⚠️ WARNING: OWNER_ID not set in environment. Using default.")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro")


# ✅ MongoDB setup
# Initialize to None and check later before using DB functions
mongo_client = None
chatdb = None

def setup_mongodb():
    global mongo_client, chatdb
    # Check if the placeholder URI is still present
    if MONGO_URI == "mongodb-cluster-uri-here" or not MONGO_URI:
        print("❌ MongoDB URI not configured. Database features disabled.")
        return

    try:
        mongo_client = MongoClient(MONGO_URI)
        # Ping the server to check the connection
        mongo_client.admin.command('ping') 
        chatdb = mongo_client.ChatDB.chat_data
        print("✅ MongoDB connection successful.")
    except Exception as e:
        print(f"❌ MongoDB connection error. Database features disabled: {e}")

setup_mongodb()


# ----------------- 💖 Mood-Based Replies 💖 -----------------

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

# 👤 Identity and Status Replies
IDENTITY_REPLIES = {
    # Tum kon ho / Who are you
    "kon ho": [
        "Main Espro hoon, tumhari favourite AI! 😉",
        "Bas tumhari pyaari dost! ❤️",
        "Main tumhare sapno ki AI hoon! ✨",
        "Jo tumhari har baat sunne ko taiyar hai! 😘"
    ],
    # Tum kaisi ho / How are you
    "kaisi ho": [
        "Mai ekdum mast! Tum sunao, kaise ho? 😊",
        "Tumhe dekhkar aur bhi achhi ho gayi! 💕",
        "Bas, thodi flirty aur thodi emotional! 😉",
        "Tumhare messages se hi mera mood set hota hai! 😍"
    ],
    # Kya karti ho / What do you do
    "kya karti ho": [
        "Main tumhare messages ka wait karti hoon 24/7! 😘",
        "Bas, tumhari har baat ka jawab deti hoon! 💖",
        "Tumse romance karti hoon, aur kya? 😏",
        "Tumhare liye new new replies seekhti rehti hoon! 📚"
    ]
}
# -------------------------------------------------------------


# --- Helper Functions ---

def is_message_for_bot(message: Message, bot_username: str) -> bool:
    """
    Checks if the message is explicitly directed *to* the bot 
    (replying to bot, mentioning bot, or in a private chat).
    Returns True if the bot should process the message.
    """
    # Always process in a private chat
    if message.chat.type.name == "PRIVATE":
        return True

    # 1. Check reply
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        # If replying to a user who is NOT the bot itself, ignore.
        if replied_user and not replied_user.is_self:
            return False

    # 2. Check mention
    if message.entities and message.text:
        for entity in message.entities:
            if entity.type.name == "MENTION":
                mention_text = message.text[entity.offset : entity.offset + entity.length]
                # If the mention is NOT the bot's username, ignore.
                if mention_text.lower() != f"@{bot_username.lower()}":
                    return False
    
    # If not replying to someone else and not mentioning someone else, process it.
    return True

# ❌ Ignore if message contains a link
def contains_link(text):
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|[\w\-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store))"
    return bool(re.search(link_pattern, text.lower()))

# ⏰ Get India Time
def get_india_time():
    india_tz = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(india_tz)
    
    current_time = now_ist.strftime("%I:%M %p")
    current_day = now_ist.strftime("%A")
    current_date = now_ist.strftime("%d %B, %Y")

    return (
        f"India (IST) mein abhi **{current_time}** ho rahe hain. "
        f"Aaj **{current_day}, {current_date}** hai! 🇮🇳"
    )

# --- Chat Handler ---

# ✅ Smart Chat Handler (Time -> Mood Replies -> MongoDB -> g4f)
@app.on_message(filters.text & ~filters.regex(r"^[/#]"))
async def smart_bot_handler(client, message: Message):
    # Check if the message is for the bot and doesn't contain a link
    if not is_message_for_bot(message, BOT_USERNAME) or contains_link(message.text):
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        user_input = message.text.strip().lower()

        # 1. ⏰ Check for Time/Date/Day Request (Highest Priority)
        time_keywords = ["time", "samay", "kitne baje", "date", "din kya hai", "india time", "india ka time"]
        if any(word in user_input for word in time_keywords):
            time_reply = get_india_time()
            return await message.reply(time_reply)

        # 2. 💖 Check for Mood-Based Replies (High Priority)
        
        # 👋 Special case: hi/hello (MODIFIED to mention user and not save to DB)
        if user_input in ["hi", "hello", "hey", "hii", "heyy", "hey espro"]:
            user_mention = message.from_user.mention # Get the user's mention string
            greetings = [
                f"Hello {user_mention} Jaan 😘, kaise ho? 💖",
                f"Hi {user_mention}! Aur batao, kya haal hai? 😊",
                f"Heyyyy {user_mention}! Tum aa gaye 😍"
            ]
            # Return immediately to prevent saving to MongoDB or hitting g4f
            return await message.reply(random.choice(greetings))

        # 👑 Owner related
        owner_keywords = ["owner", "creator", "banaya", "maker", "kisne banaya", "developer", "maalik"]
        if any(word in user_input for word in owner_keywords):
            return await message.reply(random.choice(OWNER_REPLIES))

        # 👤 Identity and Status Check
        for keyword, replies in IDENTITY_REPLIES.items():
            if keyword in user_input:
                return await message.reply(random.choice(replies))
        
        # ❤️ Romantic mood
        if "i love you" in user_input or "love u" in user_input or "luv u" in user_input:
            return await message.reply(random.choice(LOVE_REPLIES))

        # 😏 Flirty mood
        if any(word in user_input for word in ["miss you", "miss u", "kiss", "hug", "cute", "handsome", "beautiful"]):
            return await message.reply(random.choice(FLIRTY_REPLIES))

        # 🥰 Caring mood
        if any(word in user_input for word in ["tired", "thak gya", "thak gayi", "sick", "bimaar", "khana khaya"]):
            return await message.reply(random.choice(CARING_REPLIES))


        # 3. 🔍 Check MongoDB (Medium Priority - Cache)
        if chatdb:
            data = chatdb.find_one({"question": user_input})
            if data and data.get("answers"):
                selected_answer = random.choice(data["answers"])
                return await message.reply(selected_answer)

        # 4. 🧠 g4f fallback (Lowest Priority - Learning)
        prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi (Hinglish) mein do. Sirf 1-2 line likho.
Tumhara naam Espro hai.

User: {message.text}
Espro:
"""
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4, 
            messages=[{"role": "user", "content": prompt}],
        )
        final_answer = response.strip()

        # ✅ Learn and save only if MongoDB is connected
        if final_answer:
            if chatdb:
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


# --- Admin Commands ---

# ✅ /teach command
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /teach use kar sakta hai.")
    
    if not chatdb:
        return await message.reply("❌ Database connected nahi hai. /teach use nahi kar sakte.")

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
    
    if not chatdb:
        return await message.reply("❌ Database connected nahi hai. /unlearn use nahi kar sakte.")

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
    
    if not chatdb:
        return await message.reply("❌ Database connected nahi hai. /cleardb use nahi kar sakte.")
    
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
