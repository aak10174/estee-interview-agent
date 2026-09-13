"""Central configuration. Everything secret comes from .env, never from code."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

INTERVIEWS_DIR = ROOT / "interviews"
VAULT_DIR = ROOT / "vault"
NOTES_DIR = VAULT_DIR / "interviews"
SYNTHESIS_DIR = VAULT_DIR / "synthesis"
STATE_DIR = ROOT / ".state"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# One model per job. Extraction is mechanical (cheap model is fine); synthesis is
# the reasoning step worth paying for; the digest is a 200-word rewrite.
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
SYNTHESIS_MODEL = os.getenv("ANTHROPIC_SYNTHESIS_MODEL", "claude-opus-5")
DIGEST_MODEL = os.getenv("ANTHROPIC_DIGEST_MODEL", "claude-haiku-4-5")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

CLIENT_NAME = "Estee Lauder"

for d in (INTERVIEWS_DIR, NOTES_DIR, SYNTHESIS_DIR, STATE_DIR):
    d.mkdir(parents=True, exist_ok=True)


def require(var_name, value):
    if not value:
        raise SystemExit(
            "Missing %s. Copy .env.example to .env and fill it in." % var_name
        )
    return value
