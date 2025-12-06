from pyrogram import filters, enums
from pyrogram.types import ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from EsproChat import app

last_msg = {}

@app.on_chat_member_updated(filters.group)
async def welcome(_, cmu: ChatMemberUpdated):

    new = cmu.new_chat_member
    old = cmu.old_chat_member

    # Only trigger when new user joins
    if not new or new.status != enums.ChatMemberStatus.MEMBER:
        return

    user = new.user
    chat = cmu.chat

    # delete previous welcome
    if last_msg.get(chat.id):
        try:
            await last_msg[chat.id].delete()
        except:
            pass

    text = f"👋 Welcome {user.mention}!"

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("View", url=f"tg://user?id={user.id}")]
    ])

    msg = await app.send_message(chat.id, text, reply_markup=btn)
    last_msg[chat.id] = msg
