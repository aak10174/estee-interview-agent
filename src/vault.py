"""Loads the vault and answers questions about it."""
from claude import ask
from config import CLIENT_NAME, NOTES_DIR, SYNTHESIS_DIR

SYSTEM = (
    "You answer questions about a set of consumer interviews conducted for "
    + CLIENT_NAME
    + ". Answer only from the notes provided. If the notes do not cover the "
    "question, say so plainly instead of speculating. Cite participant aliases "
    "like (P02). Keep answers under 250 words unless asked for more — they are "
    "read on a phone."
)


def load_context():
    parts = []
    latest = SYNTHESIS_DIR / "latest.md"
    if latest.exists():
        parts.append("=== CURRENT SYNTHESIS ===\n" + latest.read_text())
    for p in sorted(NOTES_DIR.glob("*.md")):
        parts.append(
            "=== NOTE: " + p.name + " ===\n"
            + p.read_text().split("<!-- raw extraction -->")[0]
        )
    return "\n\n".join(parts)


def answer(question):
    context = load_context()
    if not context.strip():
        return "The vault is empty. Add transcripts to interviews/ and run the pipeline."
    return ask(
        "VAULT\n=====\n" + context + "\n\nQUESTION: " + question,
        system=SYSTEM,
        max_tokens=2000,
    )


def stats():
    n = len(list(NOTES_DIR.glob("*.md")))
    syn = SYNTHESIS_DIR / "latest.md"
    when = "never"
    if syn.exists():
        for line in syn.read_text().splitlines()[:8]:
            if line.startswith("generated: "):
                when = line.split(": ", 1)[1]
    return "Vault: %d interview note(s). Synthesis last generated: %s." % (n, when)
