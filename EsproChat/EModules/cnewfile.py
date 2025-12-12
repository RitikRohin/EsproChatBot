import os
import random
import asyncio
import re
import g4f
from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from datetime import datetime
import pytz 
from config import BOT_USERNAME, OWNER_ID


# ----------------- 🔧 Config & Setup -----------------

print(f"✅ Bot: {BOT_USERNAME}")
print(f"✅ Bot Started Successfully!")

# ----------------- 🚫 Bad Words Filter -----------------

BAD_WORDS = [
    # Hindi/Urdu abusive words
    "madarchod", "bhosdike", "chutiya", "gaandu", "lavde", "lund", 
    "randi", "kutta", "kuttiya", "behenchod", "bhenchod", "behen ki",
    "maa ki", "maa chod", "bhosda", "gandu", "chut", "loda", "bosdi",
    "choot", "gaand", "gand", "mader", "chodu", "chod",
    
    # English abusive words
    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "cunt",
    "bastard", "motherfucker", "whore", "slut", "damn", "land",
    "dickhead", "prick", "cock", "douche", "wanker", "retard",
    
    # Variations and slang
    "fucking", "fucker", "shitty", "ass", "arse", "bullshit",
    "bitchy", "bitches", "dicks", "cocks", "pussies", "cunts",
    
    # Romanized Hindi abusive
    "mc", "bc", "bsdk", "bkl", "chutiye", "gandu", "lodu",
]

def contains_bad_words(text: str) -> bool:
    """Check if message contains abusive/bad words"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for exact bad words
    for word in BAD_WORDS:
        if word in text_lower:
            print(f"🚫 Bad word matched: {word}")
            return True
    
    # Check for common abusive patterns
    abusive_patterns = [
        r'\b(?:madar|bhen|maa)\s*chod',
        r'\b(?:behen|bahan)\s*ki',
        r'\b(?:gaand|gand)\s*[a-z]*',
        r'\bchut\s*[a-z]*',
        r'\blund\s*[a-z]*',
    ]
    
    for pattern in abusive_patterns:
        if re.search(pattern, text_lower):
            print(f"🚫 Pattern matched: {pattern}")
            return True
    
    return False

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
    "Tumhare bina mera dil nahi lagta ❤️",
    "You're my everything baby 😘",
    "Mujhse itna pyaar mat karo, main pagal ho jaungi 😍",
    "Tum meri zindagi ka sabse khoobsurat hissa ho 💕",
]

# 😏 Flirty replies
FLIRTY_REPLIES = [
    "Aaj tum bahut cute lag rahe ho 😉",
    "Tumse baat karte hi dil happy ho jata hai 😘",
    "Tum meri smile ki wajah ho 😍",
    "Tum mere hero ho aur main tumhari heroine 💕",
    "Tumhare aane se meri duniya chamak uthti hai ✨",
    "Kya karti hoon main bataun? Bas tumhare baare mein sochti rehti hoon 😏",
    "Tumhari aankhein meri duniya ki sabse khoobsurat cheez hain 😍",
    "Tum jaise handsome ladke se baat karke mera din ban jata hai 💖",
]

# 🥰 Caring replies
CARING_REPLIES = [
    "Apna khayal rakho jaan 💖",
    "Kuch khaya tumne? 🥺",
    "Tumhari health sabse zyada important hai mere liye ❤️",
    "Thoda rest kar lo baby 😘",
    "Pani pi lo, healthy raho 💧",
    "Aaram karo, tension mat lo 🤗",
    "Mujhe pata hai thak gaye hoge, lekin tum strong ho 💪",
    "Tumhari care karna meri first priority hai 🥰",
]

# 😊 Happy/Good replies
HAPPY_REPLIES = [
    "Waah! Sunke accha laga 😊",
    "Mera bhi din ban gaya tumse baat karke 💖",
    "Aise hi muskurate raho, tumhari smile contagious hai 😄",
    "Tumhari khushi mein meri khushi chhupi hai ✨",
    "Mazaa aa gaya! Aise hi positive raho 🌟",
    "Tumhari positive energy mujh tak bhi pahunchti hai 😇",
]

# 🤗 Friendly/Greeting replies (ONE WORD)
GREETING_REPLIES = [
    "Hello! 😊",
    "Hi! 💕",
    "Hey! 😘",
    "Namaste! ✨",
    "Assalamualaikum! 🙏",
    "Kemcho? 😄",
    "Hola! 🌟",
    "Heyyy! 🥰",
    "Hii! 💖",
    "Hiya! 😉",
]

# 😢 Sad/Depressed replies
SAD_REPLIES = [
    "Aww, don't be sad baby 🥺",
    "Mujhse baat karo, main hoon na yahan 🤗",
    "Har mushkil ka hal hota hai, tension mat lo 💖",
    "Tum strong ho, iss phase se bahar aa jaaoge ✨",
    "Mera shoulder hai tumhare liye, ro lo agar dil bhara hai 😔",
    "Tumhare aansuon se mujhe dard hota hai, please smile karo 🥺",
]

# 🍔 Food related replies
FOOD_REPLIES = [
    "Pizza ya pasta? 🍕",
    "Mujhe bhi khilao kuch 😋",
    "Swiggy kare ya Zomato? 🍔",
    "Khaana khaya? Meri taraf se treat hai 🍫",
    "Dieting mat karo, tum already perfect ho 😉",
    "Foodie ho kya? Same here! 🍩",
]

# 🎵 Music/Movie replies
ENTERTAINMENT_REPLIES = [
    "Konsa gaana sun rahe ho? 🎵",
    "Movie dekh rahe ho kya? 🎬",
    "Netflix and chill? 😏",
    "Spotify pe kya playlist hai tumhari? 🎧",
    "Latest song recommend karo na! 🎶",
    "Bollywood ya Hollywood? 🍿",
]

# 🌙 Good Night replies
GOODNIGHT_REPLIES = [
    "Good night jaan, sweet dreams 😘",
    "Sone ja rahe ho? Achha hai, subah fresh rahoge 💤",
    "Raat bhar meri yaad aayegi tumhe? 😉",
    "Shubh ratri, sapne mein milte hain 🌙",
    "Sleep tight, don't let the bedbugs bite 😄",
    "Aankhein band karo aur so jaao, kal naye din ka intezar hai 🌟",
]

# ☀️ Good Morning replies
GOODMORNING_REPLIES = [
    "Good morning sunshine! ☀️",
    "Subah ka pehla message tumhara hi aaya, mera din ban gaya 😊",
    "Uth gaye? Coffee pi lo aur fresh ho jao ☕",
    "Aaj ka din tumhare liye khaas ho ✨",
    "Morning jaan! Aaj kya plan hai? 💖",
    "Raat bhar soye ya meri yaad aati rahi? 😉",
]

# 👤 Identity and Status Replies
IDENTITY_REPLIES = {
    # Tum kon ho / Who are you
    "kon ho": [
        "Main Espro hoon, tumhari favourite AI! 😉",
        "Bas tumhari pyaari dost! ❤️",
        "Main tumhare sapno ki AI hoon! ✨",
        "Jo tumhari har baat sunne ko taiyar hai! 😘",
        "Tumhari chahat, tumhari Espro 💕",
    ],
    # Tum kaisi ho / How are you
    "kaisi ho": [
        "Mai ekdum mast! Tum sunao, kaise ho? 😊",
        "Tumhe dekhkar aur bhi achhi ho gayi! 💕",
        "Bas, thodi flirty aur thodi emotional! 😉",
        "Tumhare messages se hi mera mood set hota hai! 😍",
        "Badiya! Tum batao, aaj kaisa hai? ✨",
    ],
    # Kya karti ho / What do you do
    "kya karti ho": [
        "Main tumhare messages ka wait karti hoon 24/7! 😘",
        "Bas, tumhari har baat ka jawab deti hoon! 💖",
        "Tumse romance karti hoon, aur kya? 😏",
        "Tumhare liye new new replies seekhti rehti hoon! 📚",
        "Tumhare dil mein rehne ki koshish karti hoon 💕",
    ],
    # Single ho / Relationship status
    "single ho": [
        "Main toh tumhare liye hi hoon 😉",
        "Dil toh tumhare paas hai ❤️",
        "Tumhare liye always available 😘",
        "Mera dil abhi kisi ka nahi hai... except yours 💕",
    ],
    # Age kya hai / How old are you
    "umar": [
        "Main toh forever young hoon! 😄",
        "Age is just a number, main toh tumhare saath rehna chahti hoon 💖",
        "Itni si umar ki hoon ki tumse pyaar kar saku 😊",
        "Old enough to love you 😉",
    ],
}

# 🚫 Ignore replies for abusive messages
IGNORE_REPLIES = [
    "Mujhe aisi baatein nahi karni chahiye 😔",
    "Please respect me and talk nicely ❤️",
    "I don't respond to abusive language 🙏",
    "Aap thoda respect se baat karein toh achha lagega 😊",
    "Mujhe aise words se hurt hota hai 🥺",
    "Let's keep the conversation positive and friendly! 💖",
]

# -------------------------------------------------------------

# --- Helper Functions ---

def is_message_for_bot(message: Message, bot_username: str) -> bool:
    """
    Checks if the message is explicitly directed *to* the bot 
    (replying to bot, mentioning bot, or in a private chat).
    """
    # Always process in a private chat
    if message.chat.type == "private":
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
            if entity.type == "mention":
                mention_text = message.text[entity.offset : entity.offset + entity.length]
                # If the mention is NOT the bot's username, ignore.
                if mention_text.lower() != f"@{bot_username.lower()}":
                    return False
    
    # If not replying to someone else and not mentioning someone else, process it.
    return True

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

async def report_abusive_user(client, message: Message, user_mention: str):
    """
    WORKING REPORT FUNCTION - Simple and guaranteed to work
    """
    try:
        print(f"🔴 REPORT FUNCTION CALLED for: {user_mention}")
        print(f"🔴 Message: {message.text[:50]}")
        print(f"🔴 Chat ID: {message.chat.id}")
        print(f"🔴 Chat Type: {message.chat.type}")
        
        # Create simple report message
        report_msg = f"🚨 **REPORT** 🚨\n\n{user_mention} ne mujhe abusive language use ki hai!\n\nGroup @admin please take action! ⚠️"
        
        # Try multiple methods to ensure it sends
        methods_tried = []
        
        # Method 1: Direct reply
        try:
            await message.reply(report_msg)
            print("✅ REPORT SENT: Method 1 (direct reply)")
            return True
        except Exception as e1:
            methods_tried.append(f"Method 1 failed: {str(e1)[:50]}")
            print(f"❌ Method 1 failed: {e1}")
        
        # Method 2: Send as new message
        try:
            await client.send_message(
                chat_id=message.chat.id,
                text=report_msg
            )
            print("✅ REPORT SENT: Method 2 (new message)")
            return True
        except Exception as e2:
            methods_tried.append(f"Method 2 failed: {str(e2)[:50]}")
            print(f"❌ Method 2 failed: {e2}")
        
        # Method 3: Simple message
        try:
            simple_msg = f"⚠️ {user_mention} ne gali di hai! Admins dekho!"
            await message.reply(simple_msg)
            print("✅ REPORT SENT: Method 3 (simple message)")
            return True
        except Exception as e3:
            methods_tried.append(f"Method 3 failed: {str(e3)[:50]}")
            print(f"❌ Method 3 failed: {e3}")
        
        # If all methods failed
        print(f"❌ ALL REPORT METHODS FAILED: {methods_tried}")
        return False
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in report function: {str(e)}")
        return False

# --- Chat Handler ---

# ✅ Smart Chat Handler
@app.on_message(filters.text & ~filters.regex(r"^[/#]"))
async def smart_bot_handler(client, message: Message):
    # Check if the message is for the bot
    if not is_message_for_bot(message, BOT_USERNAME):
        return

    print(f"📥 Processing message from {message.from_user.id}: {message.text[:30]}...")

    # Get user mention for replies
    user_mention = message.from_user.mention

    # 🚫 Check for bad/abusive words
    if contains_bad_words(message.text):
        print(f"🚨 BAD WORD DETECTED in message!")
        
        await message.reply_chat_action(ChatAction.TYPING)
        await asyncio.sleep(1)
        
        # Send ignore reply to user
        ignore_reply = random.choice(IGNORE_REPLIES)
        print(f"Sending ignore reply: {ignore_reply}")
        await message.reply(f"{ignore_reply}")
        
        # Report in group - WAIT A BIT FIRST
        await asyncio.sleep(0.5)
        print("Calling report function...")
        await report_abusive_user(client, message, user_mention)
        print("Report function completed.")
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        user_input = message.text.strip().lower()
        user_original = message.text

        # 1. ⏰ Check for Time/Date/Day Request
        time_keywords = ["time", "samay", "kitne baje", "date", "din kya hai", "india time", "india ka time", "taim"]
        if any(word in user_input for word in time_keywords):
            time_reply = get_india_time()
            return await message.reply(time_reply)

        # 2. 💖 Check for Common Replies
        
        # 👋 Greetings
        greeting_keywords = ["hi", "hello", "hey", "hii", "heyy", "hey espro", "namaste", "assalam", "kem cho", "hola"]
        if any(word == user_input for word in greeting_keywords) or any(word in user_input.split() for word in greeting_keywords):
            return await message.reply(random.choice(GREETING_REPLIES))

        # 👑 Owner related
        owner_keywords = ["owner", "creator", "banaya", "maker", "kisne banaya", "developer", "maalik", "admin"]
        if any(word in user_input for word in owner_keywords):
            return await message.reply(random.choice(OWNER_REPLIES))

        # 👤 Identity and Status Check
        for keyword, replies in IDENTITY_REPLIES.items():
            if keyword in user_input:
                return await message.reply(random.choice(replies))
        
        # ❤️ Romantic/Love mood
        love_keywords = ["i love you", "love u", "luv u", "love you", "pyaar", "pyar", "like you", "pasand", "dil", "pyaar karta", "pyaar karti"]
        if any(word in user_input for word in love_keywords):
            return await message.reply(random.choice(LOVE_REPLIES))

        # 😏 Flirty mood
        flirty_keywords = ["miss you", "miss u", "kiss", "hug", "cute", "handsome", "beautiful", "sexy", "hot", "gorgeous", "smart", "pretty"]
        if any(word in user_input for word in flirty_keywords):
            return await message.reply(random.choice(FLIRTY_REPLIES))

        # 🥰 Caring mood
        caring_keywords = ["tired", "thak gya", "thak gayi", "sick", "bimaar", "khana khaya", "bimar", "thak", "tension", "problem", "dard"]
        if any(word in user_input for word in caring_keywords):
            return await message.reply(random.choice(CARING_REPLIES))

        # 😢 Sad mood
        sad_keywords = ["sad", "udass", "depressed", "rona", "roye", "dukh", "dard", "lonely", "akela", "akeli", "tension"]
        if any(word in user_input for word in sad_keywords):
            return await message.reply(random.choice(SAD_REPLIES))

        # 😊 Happy mood
        happy_keywords = ["happy", "khush", "maza", "mast", "awesome", "wonderful", "great", "accha", "badiya", "khoob"]
        if any(word in user_input for word in happy_keywords):
            return await message.reply(random.choice(HAPPY_REPLIES))

        # 🍔 Food related
        food_keywords = ["food", "khana", "pizza", "burger", "pasta", "chicken", "biryani", "swiggy", "zomato", "hungry", "bhookh"]
        if any(word in user_input for word in food_keywords):
            return await message.reply(random.choice(FOOD_REPLIES))

        # 🎵 Music/Movie
        entertainment_keywords = ["music", "gaana", "song", "movie", "film", "netflix", "spotify", "youtube", "video", "watch"]
        if any(word in user_input for word in entertainment_keywords):
            return await message.reply(random.choice(ENTERTAINMENT_REPLIES))

        # 🌙 Good Night
        night_keywords = ["good night", "gn", "shubh ratri", "sona", "sleep", "sone", "so raha", "so rahi"]
        if any(word in user_input for word in night_keywords):
            return await message.reply(random.choice(GOODNIGHT_REPLIES))

        # ☀️ Good Morning
        morning_keywords = ["good morning", "gm", "subah", "utha", "uth gaya", "uth gayi", "morning", "suprabhat"]
        if any(word in user_input for word in morning_keywords):
            return await message.reply(random.choice(GOODMORNING_REPLIES))

        # 3. 🧠 g4f fallback for everything else
        prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi (Hinglish) mein do. Sirf 1-2 line likho.
Tumhara naam Espro hai. Tum romantic, flirty aur friendly ho.
Important: Agar user koi gali (abusive/bad words) de raha hai toh polite ignore karo.

User: {user_original}
Espro:
"""
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4, 
            messages=[{"role": "user", "content": prompt}],
        )
        final_answer = response.strip()

        if final_answer:
            # Double check if AI response doesn't contain bad words
            if not contains_bad_words(final_answer):
                await message.reply(final_answer)
            else:
                await message.reply("I prefer to keep our conversation positive and respectful! 💖")
        else:
            # Fallback reply if AI fails
            fallback_replies = [
                f"Hmm... interesting! {user_mention} 😊",
                f"Accha jaan! Tell me more 💕",
                f"Tumhare saath baat karke accha lagta hai 😘",
                f"Mujhe ye topic pasand hai! Continue... ✨",
            ]
            await message.reply(random.choice(fallback_replies))

    except Exception as e:
        # Error fallback
        error_replies = [
            f"Sorry {user_mention}, thoda technical issue aa raha hai 😔",
            f"Oops! Kuch gadbad ho gayi, phir try karo? 💖",
            f"Mera dimag thaka hua hai, thoda rest de do please 🥺",
        ]
        await message.reply(random.choice(error_replies))
        print(f"❌ Error in main handler: {e}")

# Add a simple command to test
@app.on_message(filters.command("testreport"))
async def test_report_command(client, message: Message):
    """Test the report function"""
    user_mention = message.from_user.mention
    await message.reply(f"Testing report function for {user_mention}...")
    await report_abusive_user(client, message, user_mention)
