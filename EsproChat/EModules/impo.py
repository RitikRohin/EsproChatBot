from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from pyrogram.enums import ChatMemberStatus
import asyncio

from EsproChat import app


# Helper: check admin rights
async def is_admin(chat_id, user_id):
    member = await app.get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]


# Ban user
@app.on_message(filters.command("ban") & filters.group)
async def ban_user(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Sirf admin kar sakte hai")
    if not message.reply_to_message:
        return await message.reply("Reply karo us user ke message par jise ban karna hai")
    try:
        await app.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply(f"🚫 [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id}) ban ho gaya")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")


# Unban user
@app.on_message(filters.command("unban") & filters.group)
async def unban_user(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Sirf admin kar sakte hai")
    if len(message.command) < 2:
        return await message.reply("Usage: /unban user_id")
    try:
        await app.unban_chat_member(message.chat.id, int(message.command[1]))
        await message.reply("✅ User unban ho gaya")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")


# Mute chat
@app.on_message(filters.command("mutechat") & filters.group)
async def mute_chat(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Sirf admin kar sakte hai")
    if not message.reply_to_message:
        return await message.reply("Reply karo us user ke message par jise mute karna hai")
    try:
        await app.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            ChatPermissions()
        )
        await message.reply(f"🔇 [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id}) chat mute ho gaya")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")


# Unmute chat
@app.on_message(filters.command("unmutechat") & filters.group)
async def unmute_chat(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply("❌ Sirf admin kar sakte hai")
    if not message.reply_to_message:
        return await message.reply("Reply karo us user ke message par jise unmute karna hai")
    try:
        await app.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.reply(f"🔊 [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id}) chat unmute ho gaya")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")


# VC join/leave notifications
@app.on_chat_member_updated()
async def vc_notify(_, update):
    if update.new_chat_member.is_member and not update.old_chat_member.is_member:
        await app.send_message(update.chat.id, f"🎙 [{update.new_chat_member.user.first_name}](tg://user?id={update.new_chat_member.user.id}) VC join hua")
    elif not update.new_chat_member.is_member and update.old_chat_member.is_member:
        await app.send_message(update.chat.id, f"👋 [{update.old_chat_member.user.first_name}](tg://user?id={update.old_chat_member.user.id}) VC leave kiya")


# Auto mute if non-admin shares screen (mock logic - API limitations)
@app.on_chat_member_updated()
async def auto_mute_screen_share(_, update):
    # NOTE: Telegram API abhi directly "screen share start" ka flag nahi deta Pyrogram me
    # Ye pseudo-code hai agar future me API support aaye
    if hasattr(update.new_chat_member, "is_screen_sharing") and update.new_chat_member.is_screen_sharing:
        if not await is_admin(update.chat.id, update.new_chat_member.user.id):
            await app.mute_chat_member(update.chat.id, update.new_chat_member.user.id)
            await app.send_message(update.chat.id, f"🚫 [{update.new_chat_member.user.first_name}](tg://user?id={update.new_chat_member.user.id}) screen share par mute ho gaya")

