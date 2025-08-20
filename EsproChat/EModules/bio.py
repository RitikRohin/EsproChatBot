import re
from pyrogram import Client, filters
from EsproChat import app


# Regex to detect any kind of link in bio
link_pattern = re.compile(r"(http[s]?://|www\.|t\.me|telegram\.me|bit\.ly|tinyurl\.com)", re.IGNORECASE)

@app.on_message(filters.text & ~filters.edited)
async def delete_if_bio_has_link(client, message):
    try:
        # Get full user info
        user = await client.get_users(message.from_user.id)

        # Check if bio contains a link
        if user.bio and link_pattern.search(user.bio):
            await message.delete()
            print(f"❌ Deleted message from {user.first_name} (bio has link: {user.bio})")
        

    except Exception as e:
        print("⚠️ Error:", e)
