from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import json, os, requests, random

API_ID = 12380656  # apna api id
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "8036448926:AAF7KoFuX0BdcGE9yWWWVTBsHMbMoLYSn74"
OWNER_ID = 7666870729  # apna telegram id

app = Client("CcProMax", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

PREMIUM_FILE = "premium.json"
BINS_FILE = "bins.json"
PREMIUM_USERS = {}

# 🔹 Load/Save Premium
def load_premium():
    global PREMIUM_USERS
    if os.path.exists(PREMIUM_FILE):
        with open(PREMIUM_FILE, "r") as f:
            PREMIUM_USERS = json.load(f)

def save_premium():
    with open(PREMIUM_FILE, "w") as f:
        json.dump(PREMIUM_USERS, f, indent=4)

load_premium()


# 🔹 BIN management
def load_bins():
    if os.path.exists(BINS_FILE):
        with open(BINS_FILE, "r") as f:
            return json.load(f)
    return ["454327", "529750", "601120", "379852", "222300"]

def save_bins(bins):
    with open(BINS_FILE, "w") as f:
        json.dump(bins, f, indent=4)


# 🔹 Home Menu
def home_menu(user_id):
    expiry = PREMIUM_USERS.get(str(user_id))
    if expiry:
        expiry_time = datetime.fromisoformat(expiry)
        if expiry_time > datetime.now():
            premium_status = "✅ Active"
            valid_till = expiry_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            premium_status = "❌ Not Active"
            valid_till = "N/A"
    else:
        premium_status = "❌ Not Active"
        valid_till = "N/A"

    text = (
        f"👋 Hello Cc ProMax!\n\n"
        f"💳 Welcome to Cc ProMax Bot\n"
        f"⚡ Premium Status: {premium_status}\n"
        f"⏳ Valid Till: {valid_till}\n\n"
        f"⭐ Premium users can use /ccgen\n"
        f"⚠️ All cards are test cards and cannot be used for real transactions."
    )

    buttons = [
        [InlineKeyboardButton("⚡ Commands", callback_data="commands"),
         InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("💳 Buy Premium", callback_data="buy")]
    ]

    return text, buttons


# 🔹 Start Command
@app.on_message(filters.command("start"))
async def start(_, m):
    text, buttons = home_menu(m.from_user.id)
    await m.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# 🔹 Callback Handling
@app.on_callback_query()
async def callbacks(_, query):
    user_id = query.from_user.id
    data = query.data

    if data == "home":
        text, buttons = home_menu(user_id)
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "commands":
        text = (
            "⚡ **Available Commands**\n\n"
            "/start - Open main menu\n"
            "/ccgen - Generate test credit cards (Premium)\n"
            "/premium - Check your premium status\n"
        )
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="home")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "about":
        text = (
            "ℹ️ **About Cc ProMax Bot**\n\n"
            "This bot generates test credit cards for educational and testing purposes only.\n"
            "⚠️ These cards do not work for real transactions!"
        )
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="home")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "buy":
        text = (
            "💳 **Buy Premium Plans**\n\n"
            "🗓 1 Month – ₹800\n"
            "🗓 2 Months – ₹1500\n"
            "🗓 3 Months – ₹2200\n"
            "🗓 6 Months – ₹3500\n"
            "🗓 12 Months (1 Year) – ₹5000\n\n"
            "⚡ Contact @yourusername to upgrade."
        )
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="home")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# 🔹 Premium Command
@app.on_message(filters.command("premium"))
async def premium_status(_, m):
    user_id = str(m.from_user.id)
    expiry = PREMIUM_USERS.get(user_id)
    if expiry:
        expiry_time = datetime.fromisoformat(expiry)
        if expiry_time > datetime.now():
            await m.reply_text(f"⭐ Premium Status: ✅ Active\n⏳ Valid Till: {expiry}")
        else:
            await m.reply_text("⭐ Premium Status: ❌ Not Active\n⏳ Valid Till: N/A")
    else:
        await m.reply_text("⭐ Premium Status: ❌ Not Active\n⏳ Valid Till: N/A")


# 🔹 Activate Premium (owner only)
@app.on_message(filters.command("activate"))
async def activate_premium(_, m):
    if m.from_user.id != OWNER_ID:
        return await m.reply_text("❌ Only owner can activate premium!")

    if len(m.command) < 3:
        return await m.reply_text("⚠️ Usage: /activate <user_id> <days>")

    target_id = m.command[1]
    days = int(m.command[2])
    expiry = datetime.now() + timedelta(days=days)
    PREMIUM_USERS[target_id] = expiry.isoformat()
    save_premium()

    await m.reply_text(f"✅ Premium activated for {target_id} till {expiry}")


# 🔹 Luhn Generator
def generate_luhn(bin_code):
    number = [int(x) for x in bin_code]
    while len(number) < 15:
        number.append(random.randint(0, 9))
    checksum = 0
    reverse = number[::-1]
    for i, n in enumerate(reverse):
        if i % 2 == 0:
            n = n * 2
            if n > 9:
                n -= 9
        checksum += n
    last_digit = (10 - (checksum % 10)) % 10
    number.append(last_digit)
    return ''.join(map(str, number))


# 🔹 CC Generator (Premium only)
@app.on_message(filters.command("ccgen"))
async def ccgen(_, m):
    user_id = str(m.from_user.id)

    # Premium check
    expiry = PREMIUM_USERS.get(user_id)
    if not expiry or datetime.fromisoformat(expiry) < datetime.now():
        return await m.reply_text("❌ You are not a Premium user!\nBuy premium to use /ccgen")

    # BIN pick
    bins = load_bins()
    bin_code = random.choice(bins)

    # 🔍 Binlist API
    try:
        res = requests.get(f"https://lookup.binlist.net/{bin_code}")
        data = res.json()
        scheme = data.get("scheme", "N/A").title()
        card_type = data.get("type", "N/A").title()
        brand = data.get("brand", "N/A").title()
        country = data.get("country", {}).get("name", "N/A")
        bank = data.get("bank", {}).get("name", "N/A")
    except:
        scheme = card_type = brand = country = bank = "N/A"

    # Generate CCs with details
    msg = f"💳 **Generated Cards (BIN: {bin_code})**\n\n"
    for _ in range(5):
        cc_num = generate_luhn(bin_code)
        mm = str(random.randint(1, 12)).zfill(2)
        yy = str(random.randint(25, 30))
        cvv = str(random.randint(100, 999))

        msg += (
            f"**{cc_num}|{mm}|{yy}|{cvv}**\n"
            f"🏦 Bank: {bank}\n"
            f"🌍 Country: {country}\n"
            f"💳 Scheme: {scheme}\n"
            f"💠 Type: {card_type}\n"
            f"⭐ Brand: {brand}\n\n"
        )

    await m.reply_text(msg)


# 🔹 Owner command to import BINs
@app.on_message(filters.command("importbin"))
async def import_bins(_, m):
    if m.from_user.id != OWNER_ID:
        return await m.reply_text("❌ Only owner can import BINs!")

    if len(m.command) < 2:
        return await m.reply_text("⚠️ Usage: /importbin 454327,529750,601120")

    bins = m.command[1].split(",")
    save_bins(bins)
    await m.reply_text(f"✅ Imported {len(bins)} BINs successfully!")


print("✅ Bot Started")
app.run()