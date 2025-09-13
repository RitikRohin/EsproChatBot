from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction, ParseMode
from pyrogram.types import Message
import g4f
import asyncio
import re

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
SPECIFIC_USER_ID = 7666870729  # Boss ka Telegram ID

# ❌ Ignore if replying to or mentioning someone else
def is_message_for_someone_else(message: Message):
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user and not replied_user.is_self:
            return True

    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset: entity.offset + entity.length]
                if mention_text.casefold() != f"@{BOT_USERNAME.casefold()}":
                    return True
    return False

# ❌ Ignore if message contains a link
def contains_link(text):
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|\S+\.\w{2,})"
    return bool(re.search(link_pattern, text.lower()))

# ✅ Smart Chat Handler (AI replies fast)
@app.on_message(filters.text & ~filters.regex(r"^[/#]"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    await message.reply_chat_action(ChatAction.TYPING)

    prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi mein do. Sirf 1-2 line likho or reply repeat nahin hona chahie.

User: {message.text}
Espro:
"""

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: g4f.ChatCompletion.create(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": prompt}],
            )
        )
        final_answer = response.strip() if response else "😅 Mujhe samajh nahi aaya..."

        # 👑 Agar Boss message kare to uska naam clickable mention ho
        if message.from_user.id == SPECIFIC_USER_ID:
            boss_name = message.from_user.first_name
            if message.from_user.last_name:
                boss_name += f" {message.from_user.last_name}"

            if message.from_user.username:
                final_answer = f"[{boss_name}](https://t.me/{message.from_user.username}) {final_answer}"
            else:
                final_answer = f"{boss_name} {final_answer}"

        await message.reply(final_answer, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
