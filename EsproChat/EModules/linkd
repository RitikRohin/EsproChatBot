from pyrogram import Client, filters
from pyrogram.types import Message
import re
from EsproChat import app
# Regex to match ANY link
link_regex = r"(https?://\S+|www\.\S+|t\.me/\S+|\S+\.(com|in|net|org|me|link|xyz|live|app|shop|site|co|uk|io|tv)(\/\S*)?)"

@app.on_message(filters.group & filters.text, group=5)
async def delete_all_links(client: Client, message: Message):
    # Check if the message has a link
    if re.search(link_regex, message.text):
        try:
            # Check if the sender is not admin
            user = await client.get_chat_member(message.chat.id, message.from_user.id)
            if user.status not in ("administrator", "creator"):
                await message.delete()
                print(f"🔗 Deleted link from: {message.from_user.first_name}")
        except Exception as e:
            print(f"Error deleting message: {e}")
