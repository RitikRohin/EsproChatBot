from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
import random
import time
import asyncio
from config import MONGO_URL
from EsproChat import app

# --- MongoDB Setup ---
MONGO_DB_NAME = "GameEconomyDB"
STARTING_BALANCE = 500

try:
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client[MONGO_DB_NAME]
    users_collection = db["users"]
    print("MongoDB connection successful.")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    exit(1)

# --- Database Functions (Async) ---

async def get_user_data(user_id: int, username: str):
    """User ka data fetch karta hai. Agar user nahi hai, toh use banata hai."""
    
    # User ko MongoDB se khojo
    user_data = await users_collection.find_one({"_id": user_id})
    
    if user_data is None:
        # Naya user document banao
        new_user = {
            "_id": user_id,
            "username": username,
            "balance": STARTING_BALANCE,
            "status": "alive",
            "protection_cooldown": 0,
            "global_rank": 0 # Rank later calculate hoga
        }
        await users_collection.insert_one(new_user)
        return new_user
    
    # Agar username update hua ho toh update karo
    if user_data.get("username") != username:
         await users_collection.update_one(
            {"_id": user_id},
            {"$set": {"username": username}}
         )
         user_data['username'] = username # Return ke liye update karo
         
    return user_data

async def update_user_balance(user_id: int, amount: int):
    """User ke balance ko update karta hai."""
    
    # $inc operator se balance ko increase/decrease karo
    result = await users_collection.update_one(
        {"_id": user_id},
        {"$inc": {"balance": amount}}
    )
    
    # Naya balance fetch karo
    updated_data = await users_collection.find_one({"_id": user_id}, {"balance": 1})
    return updated_data.get("balance")

async def update_user_status_or_cooldown(user_id: int, key: str, value):
    """User ka status ya protection cooldown update karta hai."""
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {key: value}}
    )

# --- Command Handlers ---


@app.on_message(filters.command("bal"))
async def balance_dikhao(client: Client, message: Message):
    """User ka ya reply kiye gaye user ka balance aur status dikhata hai."""
    target_user = message.from_user
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        
    username = target_user.username or target_user.first_name
    user_data = await get_user_data(target_user.id, username)
    
    # Global Rank fetch karna (Toprich se calculate hoga, yahan sirf placeholder)
    # MongoDB aggregation use hoti hai rank ke liye, jo complex hai.
    # Abhi ke liye, ye rank hardcode hai ya 0. Real implementation mein aggregation lagegi.
    # Example: rank = await users_collection.count_documents({"balance": {"$gt": user_data['balance']}}) + 1
    rank = 16325 # Image se liya gaya example rank
    
    await message.reply_text(
        f"👤 **Name:** {target_user.first_name}\n"
        f"💰 **Total Balance:** ${user_data['balance']}\n"
        f"🌍 **Global Rank:** {rank}\n"
        f"❤️ **Status:** {user_data['status'].capitalize()}",
        quote=True
    )
    
@app.on_message(filters.command("kill"))
async def kill_karo(client: Client, message: Message):
    """Reply kiye gaye user ko 'dead' karta hai aur killer ko paisa milta hai."""
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("Kripya us user ke message par reply karein jise 'kill' karna hai.")
        return

    killer_user = message.from_user
    target_user = message.reply_to_message.from_user
    
    if killer_user.id == target_user.id:
        await message.reply_text("Self-kill allowed nahi hai! 😉")
        return
        
    target_data = await get_user_data(target_user.id, target_user.first_name)
    
    if target_data['status'] == 'dead':
        await message.reply_text(f"{target_user.first_name} toh pehle se hi 'dead' hai. 🧟")
        return

    # Kill successful: status change karo aur killer ko paisa do
    earned_money = random.randint(150, 200) # Random kamai
    
    await update_user_status_or_cooldown(target_user.id, 'status', 'dead')
    new_killer_balance = await update_user_balance(killer_user.id, earned_money)

    await message.reply_text(
        f"💀 **{killer_user.first_name}** ne **{target_user.first_name}** ko 'killed' kar diya!\n"
        f"💵 **Earned:** **${earned_money}**\n"
        f"Aapka naya balance: **${new_killer_balance}**",
        quote=True
    )

@app.on_message(filters.command("rob"))
async def rob_karo(client: Client, message: Message):
    """Ek user se paisa chori karta hai (Robbery)."""
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("Kripya us user ke message par reply karein jise rob karna hai. Example: `/rob 50`")
        return

    robber_user = message.from_user
from pyrogram import Client, filters
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
import random
import time
import asyncio
from typing import Dict, Any

# --- CONFIG & SETUP (Importing from config.py) ---
try:
    from config import MONGO_URL, OWNER_ID
except ImportError:
    print("FATAL ERROR: config.py file not found or MONGO_URL/OWNER_ID not defined inside it!")
    exit(1)

# Placeholder: Replace with your actual app initialization if needed
# from EsproChat import app
app = Client(":memory:") 

MONGO_DB_NAME = "GameEconomyDB"
STARTING_BALANCE = 500

# --- MongoDB Setup ---
try:
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client[MONGO_DB_NAME]
    users_collection = db["users"]
    print("MongoDB connection successful.")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    # exit(1) # Uncomment to stop the bot if DB connection fails

# --- Utility Functions ---

def is_owner(user_id: int) -> bool:
    """Checks if the given user ID is the bot owner's ID."""
    return user_id == OWNER_ID

async def get_user_data(user_id: int, username: str) -> Dict[str, Any]:
    """User ka data fetch karta hai. Agar user nahi hai, toh use banata hai."""
    
    user_data = await users_collection.find_one({"_id": user_id})
    
    if user_data is None:
        new_user = {
            "_id": user_id,
            "username": username,
            "balance": STARTING_BALANCE,
            "status": "alive",
            "protection_cooldown": 0,
            "global_rank": 0,
            # New fields initialized
            "daily_claim_cooldown": 0, 
            "work_cooldown": 0 
        }
        await users_collection.insert_one(new_user)
        return new_user
    
    # Ensure all required fields exist for old users
    # This migration logic is important for smooth updates
    if "daily_claim_cooldown" not in user_data:
        user_data["daily_claim_cooldown"] = 0
    if "work_cooldown" not in user_data:
        user_data["work_cooldown"] = 0
    
    # Username update karo agar change hua ho
    if user_data.get("username") != username:
         await users_collection.update_one(
            {"_id": user_id},
            {"$set": {"username": username}}
         )
         user_data['username'] = username
         
    return user_data

async def update_user_balance(user_id: int, amount: int) -> int:
    """User ke balance ko update karta hai aur naya balance return karta hai."""
    
    await users_collection.update_one(
        {"_id": user_id},
        {"$inc": {"balance": amount}}
    )
    
    updated_data = await users_collection.find_one({"_id": user_id}, {"balance": 1})
    return updated_data.get("balance", 0)

async def update_user_status_or_cooldown(user_id: int, key: str, value: Any):
    """User ka status ya protection cooldown update karta hai."""
    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {key: value}}
    )

# -------------------------------------------------------------
## Command Handlers
# -------------------------------------------------------------

@app.on_message(filters.command("bal"))
async def balance_dikhao(client: Client, message: Message):
    """User ka ya reply kiye gaye user ka balance aur status dikhata hai."""
    target_user = message.from_user
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        
    username = target_user.username or target_user.first_name
    user_data = await get_user_data(target_user.id, username)
    
    rank = 16325 # Placeholder
    
    await message.reply_text(
        f"👤 **Name:** {target_user.first_name}\n"
        f"💰 **Total Balance:** ${user_data['balance']}\n"
        f"🌍 **Global Rank:** {rank}\n"
        f"❤️ **Status:** {user_data['status'].capitalize()}",
        quote=True
    )

---

@app.on_message(filters.command("daily"))
async def daily_reward(client: Client, message: Message):
    """Har 24 ghante mein ek baar daily bonus claim karo."""
    user_id = message.from_user.id
    current_time = int(time.time())
    DAILY_COOLDOWN = 86400  # 24 hours in seconds
    REWARD_AMOUNT = random.randint(700, 1200) 
    
    user_data = await get_user_data(user_id, message.from_user.first_name)
    
    if user_data['status'] == 'dead':
        await message.reply_text("आप 'dead' हैं! '/kill' होने के बाद आप कमाई कमांड इस्तेमाल नहीं कर सकते।", quote=True)
        return
        
    last_claim_time = user_data.get('daily_claim_cooldown', 0)
    
    if (current_time - last_claim_time) < DAILY_COOLDOWN:
        remaining_time = last_claim_time + DAILY_COOLDOWN - current_time
        hours = remaining_time // 3600
        minutes = (remaining_time % 3600) // 60
        
        await message.reply_text(
            f"⏳ **Ruko!** Aapne pehle hi aaj ka daily bonus claim kar liya hai.\n"
            f"Baki samay: **{hours} hours** aur **{minutes} minutes**.",
            quote=True
        )
        return
        
    # Reward do aur cooldown update karo
    new_balance = await update_user_balance(user_id, REWARD_AMOUNT)
    await update_user_status_or_cooldown(user_id, 'daily_claim_cooldown', current_time)
    
    await message.reply_text(
        f"🎁 **Daily Reward Claimed!**\n"
        f"Aapko **${REWARD_AMOUNT}** mile hain.\n"
        f"Aapka naya balance: **${new_balance}**",
        quote=True
    )

---

@app.on_message(filters.command("work"))
async def work_attempt(client: Client, message: Message):
    """User kam karke paisa kamata hai ya fine lagwa leta hai (1 min cooldown)."""
    user_id = message.from_user.id
    current_time = int(time.time())
    WORK_COOLDOWN = 60 # 1 minute in seconds
    
    user_data = await get_user_data(user_id, message.from_user.first_name)
    
    if user_data['status'] == 'dead':
        await message.reply_text("आप 'dead' हैं! कृपया Revive Kit खरीदें या इंतजार करें।", quote=True)
        return

    last_work_time = user_data.get('work_cooldown', 0)
    
    if (current_time - last_work_time) < WORK_COOLDOWN:
        remaining_time = last_work_time + WORK_COOLDOWN - current_time
        await message.reply_text(f"🚧 **Work Cooldown!** Agle kaam ke liye **{remaining_time} seconds** ruko.", quote=True)
        return

    # Cooldown set karo
    await update_user_status_or_cooldown(user_id, 'work_cooldown', current_time)
    
    # 70% Success Rate
    if random.random() < 0.70:
        # Success (Work)
        earned = random.randint(150, 450)
        new_balance = await update_user_balance(user_id, earned)
        
        success_messages = [
            "Aapne delivery ka kaam successfully complete kiya aur **${earned}** kamaye.",
            "Aapne stock market mein chota sa risk liya aur **${earned}** ka profit kamaya.",
            "Kisi ne aapko online tip di, aur aapne **${earned}** kama liye."
        ]
        
        await message.reply_text(
            f"✅ **Success!** {random.choice(success_messages).replace('{earned}', str(earned))}\n"
            f"Aapka naya balance: **${new_balance}**",
            quote=True
        )
    else:
        # Failure (Crime/Mistake) - Penalty or Loss
        penalty = random.randint(100, 300)
        
        if user_data['balance'] < penalty:
            penalty = user_data['balance'] 
            
        new_balance = await update_user_balance(user_id, -penalty)
        
        fail_messages = [
            "Police ne aapko bina helmet ke pakad liya! **${penalty}** ka fine laga.",
            "Stock market mein bada loss hua! Aapne **${penalty}** kho diye.",
            "Aapne galti se pura data delete kar diya. Maalik ne **${penalty}** salary kaat li."
        ]
        
        await message.reply_text(
            f"❌ **Failure!** {random.choice(fail_messages).replace('{penalty}', str(penalty))}\n"
            f"Aapka naya balance: **${new_balance}**",
            quote=True
        )

---

@app.on_message(filters.command("kill"))
async def kill_karo(client: Client, message: Message):
    """Reply kiye gaye user ko 'dead' karta hai aur killer ko paisa milta hai."""
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("Kripya us user ke message par reply karein jise 'kill' karna hai.", quote=True)
        return

    killer_user = message.from_user
    target_user = message.reply_to_message.from_user
    
    # --- PROTECTION CHECKS ---
    if is_owner(target_user.id):
        await message.reply_text("⛔ **Bot Owner** ko kill karne ki permission nahi hai. Security breach! 🚫", quote=True)
        return
        
    if killer_user.id == target_user.id:
        await message.reply_text("Self-kill allowed nahi hai! 😉", quote=True)
        return

    me = await client.get_me()
    if target_user.id == me.id:
        await message.reply_text("Mujhe mar ke kya ukhar loge 🤨", quote=True)
        return
    if target_user.is_bot:
        await message.reply_text("Ham garib logo ko kill nahi karte hai 🤝", quote=True)
        return
    # -------------------------
        
    target_data = await get_user_data(target_user.id, target_user.first_name)
    
    if target_data['status'] == 'dead':
        await message.reply_text(f"{target_user.first_name} toh pehle se hi 'dead' hai. 🧟", quote=True)
        return

    # Kill successful logic
    earned_money = random.randint(150, 200)
    
    await update_user_status_or_cooldown(target_user.id, 'status', 'dead')
    new_killer_balance = await update_user_balance(killer_user.id, earned_money)

    await message.reply_text(
        f"💀 **{killer_user.first_name}** ne **{target_user.first_name}** ko 'killed' kar diya!\n"
        f"💵 **Earned:** **${earned_money}**\n"
        f"Aapka naya balance: **${new_killer_balance}**",
        quote=True
    )

---

@app.on_message(filters.command("rob"))
async def rob_karo(client: Client, message: Message):
    """Ek user se paisa chori karta hai (Robbery)."""
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("Kripya us user ke message par reply karein jise rob karna hai. Example: `/rob 50`", quote=True)
        return

    robber_user = message.from_user
    target_user = message.reply_to_message.from_user
    
    # --- PROTECTION CHECKS ---
    if is_owner(target_user.id):
        await message.reply_text("Abe sale/sali tumko koi or nahi mila vo mera owner hai", quote=True)
        return

    if target_user.is_bot:
        await message.reply_text("Bots se paisa nahi chori kar sakte. 🚫", quote=True)
        return
    
    if robber_user.id == target_user.id:
        await message.reply_text("Self-robbery se kya milega? Kuch nahi. 😆", quote=True)
        return
    # -------------------------

    # Amount parse karo
    try:
        amount_str = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "50"
        amount = int(amount_str)
    except (ValueError, IndexError):
         await message.reply_text("Kripya sahi amount dein. Example: `/rob 100`", quote=True)
         return

    if amount <= 0:
        await message.reply_text("Robbery amount 0 se zyada honi chahiye.", quote=True)
        return

    robber_data = await get_user_data(robber_user.id, robber_user.first_name)
    target_data = await get_user_data(target_user.id, target_user.first_name)
    
    MIN_BALANCE_FOR_ROB = 100
    if robber_data['balance'] < MIN_BALANCE_FOR_ROB:
        await message.reply_text(f"Robbery karne ke liye aapke paas kam se kam **${MIN_BALANCE_FOR_ROB}** hone chahiye.", quote=True)
        return
    
    if target_data['status'] == 'dead':
        await message.reply_text(f"{target_user.first_name} 'dead' hai. 'Dead' logo ko rob nahi kiya jaa sakta.", quote=True)
        return
    
    current_time = int(time.time())
    if target_data['protection_cooldown'] > current_time:
        remaining_time = target_data['protection_cooldown'] - current_time
        minutes = remaining_time // 60
        await message.reply_text(f"🚨 **Robbery failed!** {target_user.first_name} abhi **Protected** hai. ({minutes} min remaining)", quote=True)
        return
    
    stolen_amount = min(amount, target_data['balance'])

    if stolen_amount <= 0:
        await message.reply_text(f"Target ({target_user.first_name}) ke paas chori karne ke liye paisa hi nahi hai. Balance: ${target_data['balance']}.", quote=True)
        return

    # Robbery success rate (70% chance of success)
    if random.random() < 0.70:
        # Success
        await update_user_balance(target_user.id, -stolen_amount)
        new_robber_balance = await update_user_balance(robber_user.id, stolen_amount)
        
        await message.reply_text(
            f"💰 **Success!** {robber_user.first_name} ne **{target_user.first_name}** se **${stolen_amount}** rob kiye!\n"
            f"Aapka naya balance: **${new_robber_balance}**",
            quote=True
        )
    else:
        # Failure: Robber ko penalty
        penalty = int(robber_data['balance'] * 0.10)
        penalty = max(10, min(penalty, 100))
        new_robber_balance = await update_user_balance(robber_user.id, -penalty)
        
        await message.reply_text(
            f"❌ **Robbery failed!** Police ne tumhe pakad liya! Tumhe **${penalty}** ka penalty laga hai.\n"
            f"Tumhara naya balance: **${new_robber_balance}**",
            quote=True
        )

---

@app.on_message(filters.command("give"))
async def give_money(client: Client, message: Message):
    """Reply kiye gaye user ko apna balance transfer karta hai."""
    
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("Kripya us user ke message par reply karein jise paisa dena hai. Example: `/give 100`", quote=True)
        return

    sender_user = message.from_user
    receiver_user = message.reply_to_message.from_user
    
    # Amount parse karo
    try:
        amount_str = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "0"
        amount = int(amount_str)
    except (ValueError, IndexError):
         await message.reply_text("Kripya sahi amount dein. Example: `/give 500`", quote=True)
         return
         
    # Basic Checks
    if amount <= 0:
        await message.reply_text("Transfer amount 0 se zyada honi chahiye.", quote=True)
        return
        
    if sender_user.id == receiver_user.id:
        await message.reply_text("Aap khud ko paisa transfer nahi kar sakte. 😅", quote=True)
        return
        
    if receiver_user.is_bot:
        await message.reply_text("Aap bots ko paisa nahi de sakte. 🤖", quote=True)
        return
        
    # Fetch Data (Ensure both users exist)
    sender_data = await get_user_data(sender_user.id, sender_user.first_name)
    await get_user_data(receiver_user.id, receiver_user.first_name)
    
    # Sender Balance Check
    if sender_data['balance'] < amount:
        await message.reply_text(
            f"Aapke paas itna paisa nahi hai. Aapka current balance: **${sender_data['balance']}**.",
            quote=True
        )
        return

    # Transaction Successful
    new_sender_balance = await update_user_balance(sender_user.id, -amount) 
    await update_user_balance(receiver_user.id, amount)
    
    await message.reply_text(
        f"💸 **Transaction Successful!**\n"
        f"**${amount}** balance **{receiver_user.first_name}** ko transfer kar diya gaya hai.\n\n"
        f"👤 **Aapka naya balance:** **${new_sender_balance}**",
        quote=True
    )

---

@app.on_message(filters.command("protect"))
async def protect_karo(client: Client, message: Message):
    """User khud ko robbery se protect karta hai (cooldown set karta hai)."""
    user_id = message.from_user.id
    protection_duration = 3600 # 1 ghanta
    current_time = int(time.time())
    
    user_data = await get_user_data(user_id, message.from_user.first_name)
    
    if user_data['protection_cooldown'] > current_time:
        remaining_time = user_data['protection_cooldown'] - current_time
        minutes = remaining_time // 60
        await message.reply_text(f"Tum pehle se hi Protected ho. Baki samay: **{minutes} minutes**.", quote=True)
        return
        
    # Naya protection time set karo
    new_protection_time = current_time + protection_duration
    await update_user_status_or_cooldown(user_id, 'protection_cooldown', new_protection_time)
    
    await message.reply_text(
        f"🛡️ **Protection Active!**\n"
        f"Aap agle **1 ghante** tak robbery se surakshit hain.",
        quote=True
    )

---

@app.on_message(filters.command("toprich"))
async def toprich_list(client: Client, message: Message):
    """Top 10 sabse ameer users ki list dikhata hai."""
    
    top_users_cursor = users_collection.find({}) \
        .sort("balance", -1) \
        .limit(10)
        
    top_users = await top_users_cursor.to_list(length=10)
    
    if not top_users:
        await message.reply_text("Database mein koi user nahi mila.", quote=True)
        return
        
    response = "👑 **Top 10 Richest Users Globally** 💰\n\n"
    for i, user in enumerate(top_users):
        name = user.get('username', f"User {user['_id']}")
        balance = user.get('balance', 0)
        status = user.get('status', 'alive')
        
        status_icon = "💀" if status == 'dead' else "🟢"
        
        response += f"**{i+1}.** {name} ({status_icon}) - **${balance}**\n"
        
    await message.reply_text(response, quote=True)


# Bot shuru karo
if __name__ == "__main__":
    print("Bot shuru ho raha hai... (Bot is starting with MongoDB)")
    # app.run() # Uncomment this line to start your actual Pyrogram client
