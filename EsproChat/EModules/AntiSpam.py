from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ChatPrivileges
)
from EsproChat import app

# --- Configuration ---
OWNER_ID = 7666870729

# --- Temporary in-memory storage ---
user_power_selection = {}  # Selected permissions for each user
awaiting_title = {}         # Admin title for each user

# --- Permissions list with display emojis ---
POWER_BUTTONS = [
    ("🧹 Delete", "can_delete_messages"),
    ("📌 Pin", "can_pin_messages"),
    ("🔗 Invite", "can_invite_users"),
    ("🔒 Restrict", "can_restrict_members"),
    ("🧑‍💼 Promote", "can_promote_members"),
    ("🎥 Video", "can_manage_video_chats"),
    ("⚙️ Manage Chat", "can_manage_chat"),
    ("📝 Change Info", "can_change_info"),   # NEW
    ("🕵️ Anonymous", "is_anonymous")        # NEW
]


# --- Helper: Build default privileges dict ---
def get_privileges(**kwargs):
    base = dict(
        can_manage_chat=False,
        can_delete_messages=False,
        can_restrict_members=False,
        can_invite_users=False,
        can_pin_messages=False,
        can_promote_members=False,
        can_manage_video_chats=False,
        can_change_info=False,  # NEW
        is_anonymous=False      # NEW
    )
    base.update(kwargs)
    return ChatPrivileges(**base)


# --- Helper: Build keyboard for permission selection ---
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


# --- /admin command ---
@app.on_message(filters.command("admin") & filters.group)
async def handle_admin(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        member = await message.chat.get_member(message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.reply("🚫 Only group admins or the owner can use this.")

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

    # Fetch current permissions
    try:
        member = await message.chat.get_member(target.id)
        current_perms = {k for k, v in member.privileges.__dict__.items() if v}
    except Exception:
        current_perms = set()

    user_power_selection[target.id] = current_perms
    awaiting_title[f"title:{target.id}"] = tag

    await message.reply(
        f"🔘 Choose permissions for [{target.first_name}](tg://user?id={target.id}):",
        reply_markup=build_keyboard(target.id),
        disable_web_page_preview=True
    )


# --- Toggle permission buttons ---
@app.on_callback_query(filters.regex(r"toggle:(.*?):(\d+)"))
async def toggle_power(client: Client, query: CallbackQuery):
    power, uid = query.data.split(":")[1:]
    uid = int(uid)

    if query.from_user.id != OWNER_ID:
        member = await client.get_chat_member(query.message.chat.id, query.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await query.answer("❌ Only admins or owner", show_alert=True)

    selected = user_power_selection.setdefault(uid, set())
    if power in selected:
        selected.remove(power)
    else:
        selected.add(power)

    await query.edit_message_reply_markup(reply_markup=build_keyboard(uid))


# --- Apply permissions button ---
@app.on_callback_query(filters.regex(r"apply:(\d+)"))
async def apply_inline_powers(client: Client, query: CallbackQuery):
    uid = int(query.data.split(":")[1])

    if query.from_user.id != OWNER_ID:
        member = await client.get_chat_member(query.message.chat.id, query.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await query.answer("❌ Only admins or owner", show_alert=True)

    powers = user_power_selection.get(uid, set())
    tag = awaiting_title.pop(f"title:{uid}", "Admin")

    privileges = get_privileges(**{p: True for p in powers})

    try:
        await client.promote_chat_member(query.message.chat.id, uid, privileges=privileges)
        await client.set_administrator_title(query.message.chat.id, uid, tag)
        powers_list = ", ".join(powers) if powers else "No special powers"
        await query.edit_message_text(
            f"✅ Promoted [User](tg://user?id={uid}) with title **{tag}** and powers: `{powers_list}`"
        )
        user_power_selection.pop(uid, None)
    except Exception as e:
        await query.edit_message_text(f"❌ Failed to promote:\n`{e}`")


# --- /disadmin command ---
@app.on_message(filters.command("disadmin") & filters.group)
async def disadmin_user(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        member = await message.chat.get_member(message.chat.id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.reply("❌ Only group admins or the owner can use this.")

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
            privileges=get_privileges()
        )
        await message.reply(f"✅ [{target.first_name}](tg://user?id={target.id}) is no longer an admin.")
    except Exception as e:
        await message.reply(f"❌ Error demoting user:\n`{e}`")    perms = {
        "can_manage_chat": False,
        "can_delete_messages": False,
        "can_restrict_members": False,
        "can_invite_users": False,
        "can_pin_messages": False,
        "can_promote_members": False,
        "can_manage_video_chats": False,
        "can_change_info": False,
        "is_anonymous": False
    }

    for power in powers:
        perms[power] = True

    privileges = ChatPrivileges(**perms)

    try:
        await client.promote_chat_member(query.message.chat.id, uid, privileges=privileges)
        await client.set_administrator_title(query.message.chat.id, uid, tag)
        await query.edit_message_text(
            f"✅ [{tag}](tg://user?id={uid}) is now admin."
        )
        user_power_selection.pop(uid, None)
    except Exception as e:
        await query.edit_message_text(f"❌ Failed to promote:\n`{e}`")

# /disadmin command
@app.on_message(filters.command("disadmin") & filters.group)
async def disadmin_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ Only group admins or the owner can use this.")

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
                can_change_info=False,
                is_anonymous=False
            )
        )
        await message.reply(f"✅ [{target.first_name}](tg://user?id={target.id}) is no longer an admin.")
    except Exception as e:
        await message.reply(f"❌ Error demoting user:\n`{e}`")    else:
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
                is_anonymous=False
            )
        )
        await message.reply(f"✅ [{target.first_name}](tg://user?id={target.id}) is no longer an admin.")
    except Exception as e:
        await message.reply(f"❌ Error demoting user:\n`{e}`")
