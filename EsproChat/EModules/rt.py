from pyrogram import Client, filters
from g4f import ChatCompletion


@app.on_message(filters.text)
def g4f_fast_chat(client, message):
    if message.from_user and message.from_user.is_bot:
        return

    user_msg = message.text

    try:
        # Typing indicator
        client.send_chat_action(message.chat.id, "typing")

        # AI response (short & fast)
        response = ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"Reply short, cute, friendly, g4f style, unique: {user_msg}"
            }],
            max_tokens=30
        )

        bot_reply = response['choices'][0]['message']['content']

    except Exception:
        bot_reply = "Oops! 😅 Thoda problem ho gaya."

    message.reply_text(bot_reply)

