"""Price the next pipeline run before spending anything.

Counting tokens is a free API call, so this tells you what `make run` will cost
without running it. Rates are $ per million tokens, from Anthropic's price list.
"""
import analyze
import synthesize
from claude import client
from config import DIGEST_MODEL, MODEL, NOTES_DIR, SYNTHESIS_MODEL

RATES = {
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

# Typical output sizes, measured from real runs of this pipeline.
OUT_NOTE = 1800
OUT_SYNTH = 4000
OUT_DIGEST = 300


def count(model, text):
    r = client().messages.count_tokens(
        model=model, messages=[{"role": "user", "content": text}]
    )
    return r.input_tokens


def price(model, tin, tout):
    rate_in, rate_out = RATES.get(model, (5.0, 25.0))
    return tin / 1e6 * rate_in + tout / 1e6 * rate_out


def main():
    pending = [p for p in analyze.transcript_files() if not analyze.is_current(p)]
    rows = []
    total = 0.0

    for path in pending:
        tin = count(MODEL, analyze.SCHEMA_BRIEF + path.read_text(errors="replace"))
        cost = price(MODEL, tin, OUT_NOTE)
        total += cost
        rows.append(("analyse %s" % path.name, MODEL, tin, cost))

    notes = list(NOTES_DIR.glob("*.md"))
    if pending or notes:
        blob = "\n".join(p.read_text() for p in notes)
        tin = count(SYNTHESIS_MODEL, synthesize.PROMPT + blob)
        cost = price(SYNTHESIS_MODEL, tin, OUT_SYNTH)
        total += cost
        rows.append(("synthesise %d note(s)" % len(notes), SYNTHESIS_MODEL, tin, cost))
        total += price(DIGEST_MODEL, OUT_SYNTH, OUT_DIGEST)
        rows.append(("digest", DIGEST_MODEL, OUT_SYNTH,
                     price(DIGEST_MODEL, OUT_SYNTH, OUT_DIGEST)))

    if not rows:
        print("Nothing to do — every transcript already has a current note.")
        return

    print("\n%-34s %-18s %9s %9s" % ("STEP", "MODEL", "TOKENS IN", "COST"))
    print("-" * 74)
    for label, model, tin, cost in rows:
        print("%-34s %-18s %9s   $%.3f" % (label, model, "{:,}".format(tin), cost))
    print("-" * 74)
    print("%-63s $%.2f" % ("estimated total for the next `make run`", total))
    print("\n(Output sizes are estimates; input counts are exact.)")


if __name__ == "__main__":
    main()
