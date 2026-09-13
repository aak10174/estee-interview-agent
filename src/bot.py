"""Telegram bot: ask the interview vault questions in plain language.

Run it on a laptop with:  python src/bot.py
It long-polls Telegram, so no webhook or public URL is needed.
"""
import traceback

import telegram
import vault
from config import STATE_DIR

OFFSET_FILE = STATE_DIR / "telegram_offset.txt"

HELP = (
    "I answer questions about the Estee Lauder interview vault.\n\n"
    "Just ask, e.g.:\n"
    "  What do people say about price?\n"
    "  Which channels came up most often?\n"
    "  Where do participants disagree?\n\n"
    "Commands:\n"
    "  /status — how many interviews are in the vault\n"
    "  /synthesis — the current recommendation\n"
    "  /help — this message"
)


def read_offset():
    if OFFSET_FILE.exists():
        return int(OFFSET_FILE.read_text(encoding="utf-8").strip())
    return None


def write_offset(value):
    OFFSET_FILE.write_text(str(value), encoding="utf-8")


def handle(text):
    cmd = text.strip().split()[0].lower() if text.strip() else ""
    if cmd in ("/start", "/help"):
        return HELP
    if cmd == "/status":
        return vault.stats()
    if cmd == "/synthesis":
        from config import SYNTHESIS_DIR

        latest = SYNTHESIS_DIR / "latest.md"
        if not latest.exists():
            return "No synthesis yet. Run: python src/pipeline.py"
        return latest.read_text(encoding="utf-8")
    return vault.answer(text)


def main():
    print("Bot running. Press Ctrl+C to stop.")
    offset = read_offset()
    while True:
        try:
            updates = telegram.get_updates(offset=offset)
        except Exception:
            traceback.print_exc()
            continue
        for u in updates:
            offset = u["update_id"] + 1
            write_offset(offset)
            msg = u.get("message") or {}
            text = msg.get("text")
            chat_id = (msg.get("chat") or {}).get("id")
            if not text or not chat_id:
                continue
            print("<- %s: %s" % (chat_id, text))
            try:
                reply = handle(text)
            except Exception as exc:
                traceback.print_exc()
                reply = "Something broke while answering: %s" % exc
            telegram.send(reply, chat_id=chat_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
