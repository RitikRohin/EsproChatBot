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
    mongo_client = AsyncIOMotorClient(MONGO_URI)
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
    target_user = message.reply_to_message.from_user
    
    if robber_user.id == target_user.id:
        await message.reply_text("Self-robbery se kya milega? Kuch nahi. 😆")
        return
    
    # Amount parse karo
    try:
        amount = int(message.text.split()[1])
    except:
         amount = 50 # Agar amount nahi diya toh default 50 rob karein

    if amount <= 0:
        await message.reply_text("Robbery amount 0 se zyada honi chahiye.")
        return

    robber_data = await get_user_data(robber_user.id, robber_user.first_name)
    target_data = await get_user_data(target_user.id, target_user.first_name)
    
    # Checks
    if target_data['status'] == 'dead':
        await message.reply_text(f"{target_user.first_name} 'dead' hai. 'Dead' logo ko rob nahi kiya jaa sakta.")
        return
    
    current_time = int(time.time())
    if target_data['protection_cooldown'] > current_time:
        await message.reply_text(f"🚨 **Robbery failed!** {target_user.first_name} abhi **Protected** hai.")
        return
    
    if target_data['balance'] < amount:
        await message.reply_text(f"Target ({target_user.first_name}) ke paas itna paisa nahi hai. Unka balance: ${target_data['balance']}.")
        return

    # Robbery success rate (70% chance of success)
    if random.random() < 0.70:
        # Success
        stolen_amount = amount
        
        # Balance update karo
        await update_user_balance(target_user.id, -stolen_amount)
        new_robber_balance = await update_user_balance(robber_user.id, stolen_amount)
        
        await message.reply_text(
            f"💰 **Success!** {robber_user.first_name} ne **{target_user.first_name}** se **${stolen_amount}** rob kiye!\n"
            f"Aapka naya balance: **${new_robber_balance}**"
        )
    else:
        # Failure: Robber ko penalty
        penalty = int(robber_data['balance'] * 0.10)
        penalty = max(10, min(penalty, 100))
        new_robber_balance = await update_user_balance(robber_user.id, -penalty)
        
        await message.reply_text(
            f"❌ **Robbery failed!** Police ne tumhe pakad liya! Tumhe **${penalty}** ka penalty laga hai.\n"
            f"Tumhara naya balance: **${new_robber_balance}**"
        )
        
@app.on_message(filters.command("protect"))
async def protect_karo(client: Client, message: Message):
    """User khud ko robbery se protect karta hai (cooldown set karta hai)."""
    user_id = message.from_user.id
    protection_duration = 3600 # 1 ghanta
    current_time = int(time.time())
    
    user_data = await get_user_data(user_id, message.from_user.first_name)
    
    if user_data['protection_cooldown'] > current_time:
        remaining_time = user_data['protection_cooldown'] - current_time
        await message.reply_text(f"Tum pehle se hi Protected ho. Baki samay: **{remaining_time // 60} minutes**.")
        return
        
    # Naya protection time set karo
    new_protection_time = current_time + protection_duration
    await update_user_status_or_cooldown(user_id, 'protection_cooldown', new_protection_time)
    
    await message.reply_text(
        f"🛡️ **Protection Active!**\n"
        f"Aap agle **1 ghante** tak robbery se surakshit hain."
    )

# --- Top Rich Command Example ---

@app.on_message(filters.command("toprich"))
async def toprich_list(client: Client, message: Message):
    """Top 10 sabse ameer users ki list dikhata hai."""
    
    # MongoDB aggregation ka use karke top users find karo
    top_users_cursor = users_collection.find({}) \
        .sort("balance", -1) \
        .limit(10)
        
    top_users = await top_users_cursor.to_list(length=10)
    
    if not top_users:
        await message.reply_text("Database mein koi user nahi mila.")
        return
        
    response = "👑 **Top 10 Richest Users Globally** 💰\n\n"
    for i, user in enumerate(top_users):
        name = user.get('username', f"User {user['_id']}")
        balance = user.get('balance', 0)
        response += f"**{i+1}.** {name} - **${balance}**\n"
        
    await message.reply_text(response)


# Bot shuru karo
if __name__ == "__main__":
    print("Bot shuru ho raha hai... (Bot is starting with MongoDB)")
    
