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
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|[\w\-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store))"
    return bool(re.search(link_pattern, text.lower()))

# ✅ Smart Chat Handler (GPT only, works in group + DM)
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    # ❌ Ignore agar dusre user ko reply/mention ho
    if is_message_for_someone_else(message):
        return  

    # ❌ Ignore agar non-text ho
    if not message.text:
        return  

    # ❌ Ignore agar message link ho
    if contains_link(message.text):
        return  

    # ❌ Ignore agar message '#' se start ho
    if message.text.strip().startswith("#"):
        return  

    # ✅ Typing action
    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        user_input = message.text.strip()

        # 🧠 GPT Prompt
        prompt = f"""
Tum ek real ladki ho. Reply hamesha user ki language me do.
Reply short (1-2 line) aur friendly ho.
Har baar thoda different wording use karo taki repeat na lage.
Thoda natural aur human jaise feel ho.

User: {user_input}
Espro:
"""

        # 🎯 GPT Response
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,  # 🔥 Higher = more random replies
        )

        # 📝 Response handle
        if isinstance(response, dict) and "choices" in response:
            final_answer = response["choices"][0]["message"]["content"].strip()
        else:
            final_answer = str(response).strip()

        # ✅ Reply
        if final_answer:
            await message.reply(final_answer)
        else:
            await message.reply("😓 Mujhe jawab nahi mila...")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
