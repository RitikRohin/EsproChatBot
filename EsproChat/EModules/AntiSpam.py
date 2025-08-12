from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ChatPrivileges
)
from EsproChat import app

OWNER_ID = 7666870729
user_power_selection = {}  # Temporary permission storage
awaiting_title = {}        # Temporary title storage

# Powers with display emojis
POWER_BUTTONS = [
    ("🧹 Delete", "can_delete_messages"),
    ("📌 Pin", "can_pin_messages"),
    ("🔗 Invite", "can_invite_users"),
    ("🔒 Restrict", "can_restrict_members"),
    ("🧑‍💼 Promote", "can_promote_members"),
    ("🎥 Video", "can_manage_video_chats"),
    ("⚙️ Manage Chat", "can_manage_chat"),
    ("✏️ Change Info", "can_change_info")  # NEW permission
]

# Build keyboard for selecting permissions
def build_keyboard(uid):
    selected = user_power_selection.get(uid, set())
    buttons, row = [], []
    for emoji, power in POWER_BUTTONS:
        mark = "✅" if power in selected else "☐"
        row.append(InlineKeyboardButton(f"{mark} {emoji}", callback_data=f"toggle:{power}:{uid}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("✅ Apply Permissions", callback_data=f"apply:{uid}")])
    return InlineKeyboardMarkup(buttons)

# Check if user can promote
async def can_promote(chat, user_id):
    if user_id == OWNER_ID:
        return True
    member = await chat.get_member(user_id)
    return bool(member.privileges and member.privileges.can_promote_members)

# /admin command
@app.on_message(filters.command("admin") & filters.group)
async def handle_admin(client: Client, message: Message):
    if not await can_promote(message.chat, message.from_user.id):
        return await message.reply("🚫 Only admins with promote rights or the owner can use this.")

    args = message.text.split()[1:]

    if message.reply_to_message:
        target = message.reply_to_message.from_user
        tag = args[0] if args else "Admin"
    elif args:
        try:
            target = await client.get_users(args[0] if args[0].startswith("@") else int(args[0]))
            tag = args[1] if len(args) > 1 else "Admin"
        except Exception as e:
            return await message.reply(f"❌ Failed to find user:\n`{e}`")
    else:
        return await message.reply("🧠 Usage:\n• Reply with `/admin Boss`\n• or `/admin @user Boss`")

    user_power_selection[target.id] = set()
    awaiting_title[f"title:{target.id}"] = tag

    await message.reply(
        f"🔘 Choose permissions for [{target.first_name}](tg://user?id={target.id}):",
        reply_markup=build_keyboard(target.id),
        disable_web_page_preview=True
    )

# Toggle buttons
@app.on_callback_query(filters.regex("toggle:(.*?):(\\d+)"))
async def toggle_power(client: Client, query: CallbackQuery):
    power, uid = query.data.split(":")[1:]
    uid = int(uid)

    if not await can_promote(query.message.chat, query.from_user.id):
        return await query.answer("❌ Only admins with promote rights or the owner can use this.", show_alert=True)

    selected = user_power_selection.setdefault(uid, set())
    if power in selected:
        selected.remove(power)
    else:
        selected.add(power)

    await query.edit_message_reply_markup(reply_markup=build_keyboard(uid))

# Apply button
@app.on_callback_query(filters.regex("apply:(\\d+)"))
async def apply_inline_powers(client: Client, query: CallbackQuery):
    uid = int(query.data.split(":")[1])

    if not await can_promote(query.message.chat, query.from_user.id):
        return await query.answer("❌ Only admins with promote rights or the owner can use this.", show_alert=True)

    powers = user_power_selection.get(uid, set())
    tag = awaiting_title.pop(f"title:{uid}", "Admin")

    perms = {
        "can_manage_chat": False,
        "can_delete_messages": False,
        "can_restrict_members": False,
        "can_invite_users": False,
        "can_pin_messages": False,
        "can_promote_members": False,
        "can_manage_video_chats": False,
        "can_change_info": False,  # NEW
        "is_anonymous": False
    }

    for power in powers:
        perms[power] = True

    privileges = ChatPrivileges(**perms)

    try:
        await client.promote_chat_member(query.message.chat.id, uid, privileges=privileges)
        await client.set_administrator_title(query.message.chat.id, uid, tag)
        await query.edit_message_text(
            f"✅ Promoted [User](tg://user?id={uid}) with title **{tag}** "
        )
        user_power_selection.pop(uid, None)
    except Exception as e:
        await query.edit_message_text(f"❌ Failed to promote:\n`{e}`")

# /disadmin command
@app.on_message(filters.command("disadmin") & filters.group)
async def disadmin_user(client: Client, message: Message):
    if not await can_promote(message.chat, message.from_user.id):
        return await message.reply("❌ Only admins with promote rights or the owner can use this.")

    args = message.text.split()[1:]

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif args:
        try:
            target = await client.get_users(args[0] if args[0].startswith("@") else int(args[0]))
        except Exception as e:
            return await message.reply(f"❌ Failed to find user:\n`{e}`")
    else:
        return await message.reply("🧠 Usage:\n• Reply with `/disadmin`\n• or `/disadmin @username`")

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            privileges=ChatPrivileges(
                can_manage_chat=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_video_chats=False,
                can_change_info=False,  # NEW
                is_anonymous=False
            )
        )
        await message.reply(f"✅ [{target.first_name}](tg://user?id={target.id}) is no longer an admin.")
    except Exception as e:
        await message.reply(f"❌ Error demoting user:\n`{e}`")
