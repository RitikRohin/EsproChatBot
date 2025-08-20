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
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|\b[\w.-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store)\b)"
    return bool(re.search(link_pattern, text.lower()))


# ✅ Smart Chat Handler (GPT only, no saving)
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    # ❌ Ignore if starts with #
    if message.text.strip().startswith("#"):
        return  

    if is_message_for_someone_else(message):
        return  # ❌ Ignore replies or mentions

    if contains_link(message.text):
        return  # ❌ Ignore messages with links

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(min(3, max(1, len(message.text) / 20)))

    try:
        user_input = message.text.strip().lower()

        # 🧠 GPT only (no DB)
        prompt = f"""
Tum ek real ladki ho jo Hindi me friendly aur natural jawab deti ho.
Har baar wording alag rakho taki repeat na lage.
Reply hamesha short (1-2 line) aur thoda casual ho.

User: {user_input}
Espro:
"""
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )

        if isinstance(response, str):
            final_answer = response.strip()
        else:
            final_answer = "".join([chunk for chunk in response]).strip()

        if final_answer:
            await message.reply(final_answer)
        else:
            await message.reply("😓 Mujhe jawab nahi mila...")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

