"""Minimal Telegram HTTP client — no heavyweight bot framework needed."""
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, require

API = "https://api.telegram.org/bot%s/%s"


def call(method, **params):
    require("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    r = requests.post(API % (TELEGRAM_BOT_TOKEN, method), json=params, timeout=70)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("ok"):
        raise RuntimeError("Telegram error: %s" % payload)
    return payload["result"]


def send(text, chat_id=None):
    """Send a message, splitting at Telegram's 4096-character limit."""
    chat = chat_id or TELEGRAM_CHAT_ID
    require("TELEGRAM_CHAT_ID", chat)
    for i in range(0, len(text), 3900):
        call("sendMessage", chat_id=chat, text=text[i : i + 3900])


def get_updates(offset=None, timeout=50):
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    return call("getUpdates", **params)


if __name__ == "__main__":
    # `python src/telegram.py` prints the chat id of whoever messaged the bot last.
    updates = get_updates(timeout=0)
    if not updates:
        print("No messages yet. Open Telegram, find your bot, and send it 'hi'.")
    for u in updates:
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat", {})
        print("chat_id=%s  name=%s" % (chat.get("id"), chat.get("first_name") or chat.get("title")))
