"""The whole flow, start to finish.

  1. analyse any transcript that does not yet have an up-to-date vault note
  2. regenerate the cross-interview synthesis if anything changed
  3. send a short digest to Telegram

Run by hand (`python src/pipeline.py`) or on a schedule (see .github/workflows
and README). Safe to run repeatedly: unchanged transcripts are skipped.
"""
import sys

import analyze
import synthesize
import telegram
from claude import ask
from config import DIGEST_MODEL, SYNTHESIS_DIR, TELEGRAM_CHAT_ID

DIGEST_PROMPT = (
    "Here is the latest cross-interview synthesis. Write a Telegram digest of at "
    "most 200 words in plain text (no markdown symbols, no headers): what changed, "
    "the single strongest intersection, and the current recommendation in one "
    "sentence. Write it so someone reads it on a phone at breakfast.\n\n"
)


def main(force=False, notify=True):
    new_notes = analyze.run(force=force)
    if not new_notes:
        print("No new or changed transcripts.")
        if not force:
            return
    print("Synthesising across the whole vault ...")
    synthesize.run()

    if not notify:
        return
    if not TELEGRAM_CHAT_ID:
        print("TELEGRAM_CHAT_ID not set — skipping digest.")
        return
    text = (SYNTHESIS_DIR / "latest.md").read_text(encoding="utf-8")
    digest = ask(DIGEST_PROMPT + text, model=DIGEST_MODEL, max_tokens=800)
    header = "Interview vault updated: %d new note(s).\n\n" % len(new_notes)
    telegram.send(header + digest)
    print("Digest sent.")


if __name__ == "__main__":
    main(force="--force" in sys.argv, notify="--no-telegram" not in sys.argv)
