import re
from pyrogram import filters
from EsproChat import app   # app already project me bana hai

# Regex to detect any kind of link in bio
link_pattern = re.compile(r"(http[s]?://|www\.|t\.me|telegram\.me|bit\.ly|tinyurl\.com)", re.IGNORECASE)

@app.on_message(filters.text & filters.group)
async def delete_if_bio_has_link(client, message):
    try:
        print(f"📩 Message from {message.from_user.first_name}: {message.text}")  # Debug

        user = await client.get_users(message.from_user.id)

        bio_text = user.bio or ""   # agar bio None hai to empty string le lo
        print(f"🔎 {user.first_name}'s bio: {bio_text}")  # Debug

        if link_pattern.search(bio_text):
            await message.delete()
            print(f"❌ Deleted message from {user.first_name} (bio has link)")
        else:
            print(f"✅ Allowed message from {user.first_name} (no link in bio)")

    except Exception as e:
        print("⚠️ Error:", e)
