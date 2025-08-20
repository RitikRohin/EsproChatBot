# filename: sticker_ai.py
from __future__ import annotations

import logging
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from EsproChat import app          # your initialized Pyrogram Client
from config import MONGO_URL       # ensure this is set


# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("sticker-ai")


# ---------------- MongoDB ----------------
def init_mongo(url: str) -> Collection:
    """
    Connect to Mongo, ensure indexes, and return the collection handle.
    """
    client = MongoClient(url, serverSelectionTimeoutMS=8000)
    # Trigger a quick server selection to fail fast if not reachable
    client.admin.command("ping")

    db = client["Word"]
    col = db["WordDb"]

    # Unique constraint prevents duplicate (input -> output) pairs
    col.create_index([("word", 1), ("text", 1), ("check", 1)], unique=True)
    # Read perf index for lookup by input sticker
    col.create_index([("word", 1), ("check", 1)])

    log.info("✅ Mongo connected & indexes ensured")
    return col


try:
    chatai = init_mongo(MONGO_URL)
except Exception as e:
    log.error("❌ Failed to init MongoDB: %s", e)
    raise SystemExit(1)


# ---------------- Helpers ----------------
async def _is_self_reply(client: Client, reply_msg: Message) -> bool:
    """
    True if the replied message is from this bot itself (avoid self-learning).
    """
    if not reply_msg.from_user:
        return False
    me = await client.get_me()
    return reply_msg.from_user.id == me.id


def _pick_random_reply(col: Collection, key: str) -> Optional[str]:
    """
    Pick a random stored sticker file_id for input sticker 'key'.
    Returns file_id to send, or None if no mapping exists.
    """
    docs = list(col.aggregate([
        {"$match": {"word": key, "check": "sticker"}},
        {"$sample": {"size": 1}}
    ]))
    if not docs:
        return None
    return docs[0].get("text")


def _store_pair(col: Collection, input_unique: str, reply_file_id: str, reply_unique: str) -> str:
    """
    Persist a learned pair (input_unique -> reply_file_id).
    Returns a short status string for logs.
    """
    try:
        col.insert_one({
            "word": input_unique,          # input sticker (stable unique id)
            "text": reply_file_id,         # reply sticker (file_id used to send)
            "unique": reply_unique,        # reply's file_unique_id (for reference)
            "check": "sticker"
        })
        return "learned"
    except DuplicateKeyError:
        return "duplicate"
    except Exception as e:
        log.error("❌ Insert error: %s", e)
        return "error"


# ---------------- Handler ----------------
@app.on_message(filters.sticker & ~filters.bot)
async def sticker_reply(client: Client, message: Message):
    """
    Sticker Auto-reply & Learning

    Behavior:
    - If the incoming sticker is NOT a reply:
        -> Look up a learned response for that sticker's file_unique_id.
        -> If found, send one random learned sticker reply.
    - If the incoming sticker IS a reply to another sticker (not from the bot):
        -> Learn the mapping (parent.unique_id -> current.file_id).
    """

    # --- Auto-reply path (incoming sticker is not a reply) ---
    if not message.reply_to_message:
        key = message.sticker.file_unique_id
        file_id = _pick_random_reply(chatai, key)

        if file_id:
            try:
                await message.reply_sticker(file_id)
                log.info("✅ Replied to %s with a learned sticker", key)
            except Exception as e:
                log.error("❌ Failed to send sticker reply for %s: %s", key, e)
        else:
            log.info("⚠️ No learned reply found for key: %s", key)
        return

    # --- Learning path (incoming sticker is a reply) ---
    reply_msg = message.reply_to_message

    # Skip if replying to this bot itself
    if await _is_self_reply(client, reply_msg):
        return

    # Only learn sticker -> sticker pairs
    if not (reply_msg.sticker and message.sticker):
        return

    input_unique = reply_msg.sticker.file_unique_id
    reply_file_id = message.sticker.file_id
    reply_unique = message.sticker.file_unique_id

    status = _store_pair(chatai, input_unique, reply_file_id, reply_unique)

    if status == "learned":
        log.info("✅ Learned pair: %s -> %s", input_unique, reply_file_id)
    elif status == "duplicate":
        log.info("⚠️ Duplicate pair skipped: %s -> %s", input_unique, reply_file_id)
    else:
        # Already logged inside _store_pair on error
        pass
