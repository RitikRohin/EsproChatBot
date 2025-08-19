import aiohttp
import os
from PIL import Image
import moviepy.editor as mp
from time import time
from collections import defaultdict

from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

nekos_api = "https://nekos.best/api/v2/neko"
authorized_users = set(AUTH_USERS)
nsfw_enabled = defaultdict(lambda: True)
user_spam_tracker = defaultdict(int)
user_messages = defaultdict(list)

# 🔁 Convert webp to jpg
async def convert_to_jpg(file_path):
    try:
        img = Image.open(file_path).convert("RGB")
        jpg_path = file_path.replace(".webp", ".jpg")
        img.save(jpg_path)
        return jpg_path
    except Exception as e:
        print(f"[ERROR] Convert to JPG failed: {e}")
        return file_path

# 🔁 Convert webm to mp4
async def convert_video_to_mp4(file_path):
    try:
        clip = mp.VideoFileClip(file_path)
        mp4_path = file_path.replace(".webm", ".mp4")
        clip.write_videofile(mp4_path, codec='libx264', audio=False)
        return mp4_path
    except Exception as e:
        print(f"[ERROR] Convert to MP4 failed: {e}")
        return file_path

# ✅ Get neko image
async def get_neko_image():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(nekos_api, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["results"][0]["url"]
    except:
        return "https://nekos.best/api/v2/neko/0001.png"

# ✅ Sightengine NSFW check
async def check_nsfw(file_path: str):
    url = "https://api.sightengine.com/1.0/check.json"
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("media", f, filename="file.jpg", content_type="image/jpeg")
                form.add_field("models", "nudity,wad,offensive")
                form.add_field("api_user", SIGHTENGINE_API_USER)
                form.add_field("api_secret", SIGHTENGINE_API_SECRET)
                async with session.post(url, data=form, timeout=25) as resp:
                    result = await resp.json()
                    print("[DEBUG] NSFW API result:", result)
                    return result
    except Exception as e:
        print(f"[ERROR] Sightengine API: {e}")
        return None

# ✅ Delete user messages
async def delete_user_messages(client, chat_id, user_id):
    if user_messages[(chat_id, user_id)]:
        for msg_id in user_messages[(chat_id, user_id)]:
            try:
                await client.delete_messages(chat_id, msg_id)
            except:
                pass
        user_messages[(chat_id, user_id)].clear()

# ✅ NSFW Detector Main
@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker))
async def nsfw_guard(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return

    if message.caption and message.caption.startswith("/"):
        return

    user_messages[(chat_id, user.id)].append(message.id)
    if len(user_messages[(chat_id, user.id)]) > 20:
        user_messages[(chat_id, user.id)].pop(0)

    if not nsfw_enabled[chat_id]:
        return

    if user.id in OWNER_ID or user.id in authorized_users:
        return

    file_path = await message.download()
    print("[DEBUG] File downloaded:", file_path)

    # Convert formats
    if message.sticker:
        if message.sticker.is_video:
            file_path = await convert_video_to_mp4(file_path)
        elif not message.sticker.is_animated:
            file_path = await convert_to_jpg(file_path)

    result = await check_nsfw(file_path)

    try:
        os.remove(file_path)
    except:
        pass

    if not result:
        return

    # Scores
    nudity = float(result.get("nudity", {}).get("raw", 0))
    partial = float(result.get("nudity", {}).get("partial", 0))
    sexual = float(result.get("nudity", {}).get("sexual_activity", 0))
    weapon = float(result.get("weapon", 0))
    alcohol = float(result.get("alcohol", 0))
    drugs = float(result.get("drugs", 0))
    offensive = float(result.get("offensive", {}).get("prob", 0))

    is_nsfw = (
        nudity > 0.3 or
        partial > 0.3 or
        sexual > 0.15 or
        weapon > 0.6 or
        alcohol > 0.6 or
        drugs > 0.3 or
        offensive > 0.3
    )

    if is_nsfw:
        user_spam_tracker[user.id] += 1
        await delete_user_messages(client, chat_id, user.id)

        neko_img = await get_neko_image()
        media_type = (
            "Photo" if message.photo else
            "Video Sticker" if message.sticker and message.sticker.is_video else
            "GIF Sticker" if message.sticker and message.sticker.is_animated else
            "GIF" if message.animation else
            "Video" if message.video else
            "Sticker"
        )

        caption = (
            f"🚫 **NSFW Content Removed**\n\n"
            f"👤 User: {user.mention}\n"
            f"🆔 ID: `{user.id}`\n"
            f"📎 Type: `{media_type}`\n\n"
            f"🔍 **Scores:**\n"
            f"Nudity: `{nudity*100:.1f}%`\n"
            f"Partial: `{partial*100:.1f}%`\n"
            f"Sexual: `{sexual*100:.1f}%`\n"
            f"Weapon: `{weapon*100:.1f}%`\n"
            f"Alcohol: `{alcohol*100:.1f}%`\n"
            f"Drugs: `{drugs*100:.1f}%`\n"
            f"Offensive: `{offensive*100:.1f}%`"
        )

        try:
            await message.reply_photo(
                photo=neko_img,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{client.me.username}?startgroup=true")]]
                )
            )
        except:
            await message.reply(caption)

# ✅ /nsfw on/off
@app.on_message(filters.command("nsfw") & filters.group)
async def toggle_nsfw(client, message: Message):
    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("❌ Only admins can toggle NSFW filter.")

    if len(message.command) < 2:
        state = "enabled" if nsfw_enabled[message.chat.id] else "disabled"
        return await message.reply(f"ℹ️ NSFW filter is currently **{state}**.")

    state = message.command[1].lower()
    nsfw_enabled[message.chat.id] = (state == "on")
    await message.reply(f"✅ NSFW filter is now **{'enabled' if state == 'on' else 'disabled'}**.")

# ✅ /authorize
@app.on_message(filters.command("authorize") & filters.user(OWNER_ID))
async def authorize_user(client, message: Message):
    target_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        arg = message.command[1]
        if arg.isdigit():
            target_id = int(arg)
        else:
            try:
                user_obj = await client.get_users(arg)
                target_id = user_obj.id
            except:
                return await message.reply("❌ Invalid username or user not found.")

    if not target_id:
        return await message.reply("Reply or provide valid user ID/username.")

    authorized_users.add(target_id)
    await message.reply(f"✅ User `{target_id}` has been authorized.")

# ✅ /unauthorize
@app.on_message(filters.command("unauthorize") & filters.user(OWNER_ID))
async def unauthorize_user(client, message: Message):
    target_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        arg = message.command[1]
        if arg.isdigit():
            target_id = int(arg)
        else:
            try:
                user_obj = await client.get_users(arg)
                target_id = user_obj.id
            except:
                return await message.reply("❌ Invalid username or user not found.")

    if not target_id:
        return await message.reply("Reply or provide valid user ID/username.")

    if target_id in authorized_users:
        authorized_users.remove(target_id)
        await message.reply(f"❌ User `{target_id}` authorization removed.")
    else:
        await message.reply("User is not authorized.")
