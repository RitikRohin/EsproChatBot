from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
import asyncio
import re

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729

# ❌ Ignore if replying to or mentioning someone else (for group only)
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

# ✅ Smart Chat Handler
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if not message.text:
        return
    if message.text.strip().startswith("#"):
        return
    if contains_link(message.text):
        return

    # ✅ Group me dusre ko reply/mention ignore karo
    if message.chat.type in ["group", "supergroup"]:
        if is_message_for_someone_else(message):
            return
        if not message.text.lower().startswith(f"@{BOT_USERNAME.lower()}"):
            return

    try:
        user_input = message.text.strip()

        # 🧠 GPT Prompt
        prompt = f"""
        Tum ek real ladki ho jo Hindi me friendly aur natural jawab deti ho.
        Har baar wording alag rakho taki repeat na lage.
        Reply hamesha short (1-2 line) aur thoda casual ho.

        User: {user_input}
        Espro:
        """


        # 🎯 GPT Response
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
        )

        final_answer = (
            response["choices"][0]["message"]["content"].strip()
            if isinstance(response, dict) and "choices" in response
            else str(response).strip()
        )

        # ✨ Placeholder ko edit karke final answer bhejo
        if final_answer:
            await sent.edit(final_answer)
        else:
            await sent.edit("😅 Kuch samajh nahi aaya...")

    except Exception as e:
        await message.reply("😅 Thoda problem ho gaya, phir try karo...")
        print("Error:", e)
