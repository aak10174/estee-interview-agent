"""Turn one raw transcript into one structured markdown note in the vault."""
import datetime
import hashlib
import json
import re
import sys

from claude import ask_json
from config import CLIENT_NAME, INTERVIEWS_DIR, NOTES_DIR

SYSTEM = (
    "You are a rigorous qualitative researcher analysing consumer interviews for "
    + CLIENT_NAME
    + ", a prestige beauty group trying to understand younger consumers. "
    "You never invent evidence. Every claim you make must be traceable to something "
    "the interviewee actually said. If the transcript does not cover a field, return "
    "an empty list or the string 'not discussed' rather than guessing."
)

SCHEMA_BRIEF = """
Return JSON with exactly these keys:

{
  "participant": {
    "alias": "short label, e.g. P03 or the name used in the transcript",
    "age_band": "e.g. 18-24, or 'not discussed'",
    "location": "city or 'not discussed'",
    "spend_level": "budget | mid | prestige | mixed | not discussed"
  },
  "summary": "3-4 sentences on who this person is as a beauty consumer",
  "brand_perception": [
    {"brand": "", "sentiment": "positive|negative|mixed|neutral",
     "why": "", "quote": "verbatim quote"}
  ],
  "unmet_needs": [{"need": "", "evidence": "verbatim quote"}],
  "discovery_channels": [
    {"channel": "e.g. TikTok, Xiaohongshu, Sephora, friend, Douyin livestream",
     "role": "discover|research|purchase|all",
     "evidence": "verbatim quote"}
  ],
  "purchase_drivers": [{"driver": "", "evidence": "verbatim quote"}],
  "purchase_barriers": [{"barrier": "", "evidence": "verbatim quote"}],
  "price_sensitivity": {"level": "low|medium|high|not discussed",
                        "evidence": "verbatim quote"},
  "product_preferences": [{"preference": "", "evidence": "verbatim quote"}],
  "competitor_mentions": [{"brand": "", "why_chosen": "", "quote": ""}],
  "notable_quotes": ["verbatim quotes worth putting in a deck"],
  "tensions": ["things this person said that contradict each other or contradict
                conventional wisdom"],
  "decision_signals": {
    "gen_z_attraction": "what this interview implies about attracting Gen Z, or 'no signal'",
    "channel_investment": "what it implies about where to invest, or 'no signal'",
    "portfolio_direction": "what it implies about products/sub-brands, or 'no signal'"
  }
}
"""


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "interview"


def transcript_files():
    return sorted(
        p
        for p in INTERVIEWS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in (".txt", ".md")
    )


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def note_path(path):
    return NOTES_DIR / (slugify(path.stem) + ".md")


def is_current(path):
    """True when a vault note already exists for this exact transcript content."""
    note = note_path(path)
    if not note.exists():
        return False
    return ("source_hash: " + fingerprint(path)) in note.read_text(encoding="utf-8")


def render_note(path, data):
    p = data.get("participant", {})
    today = datetime.date.today().isoformat()
    out = [
        "---",
        "type: interview-note",
        "source_file: " + path.name,
        "source_hash: " + fingerprint(path),
        "analysed: " + today,
        "alias: " + str(p.get("alias", path.stem)),
        "age_band: " + str(p.get("age_band", "not discussed")),
        "location: " + str(p.get("location", "not discussed")),
        "spend_level: " + str(p.get("spend_level", "not discussed")),
        "---",
        "",
        "# " + str(p.get("alias", path.stem)),
        "",
        "## Summary",
        str(data.get("summary", "")),
        "",
    ]

    def quote_list(title, items, fields):
        out.append("## " + title)
        if not items:
            out.append("_Not discussed._")
            out.append("")
            return
        for item in items:
            if isinstance(item, str):
                out.append("- " + item)
                continue
            head = " — ".join(str(item.get(f, "")) for f in fields if item.get(f))
            out.append("- **" + head + "**")
            ev = item.get("evidence") or item.get("quote")
            if ev:
                out.append("  > " + str(ev).replace("\n", " "))
        out.append("")

    quote_list("Brand perception", data.get("brand_perception"), ["brand", "sentiment", "why"])
    quote_list("Unmet needs", data.get("unmet_needs"), ["need"])
    quote_list("Discovery & purchase channels", data.get("discovery_channels"), ["channel", "role"])
    quote_list("Purchase drivers", data.get("purchase_drivers"), ["driver"])
    quote_list("Purchase barriers", data.get("purchase_barriers"), ["barrier"])
    quote_list("Product preferences", data.get("product_preferences"), ["preference"])
    quote_list("Competitors chosen instead", data.get("competitor_mentions"), ["brand", "why_chosen"])

    ps = data.get("price_sensitivity") or {}
    out += ["## Price sensitivity", "**" + str(ps.get("level", "not discussed")) + "**"]
    if ps.get("evidence"):
        out.append("> " + str(ps["evidence"]).replace("\n", " "))
    out.append("")

    quote_list("Tensions & contradictions", data.get("tensions"), [])
    quote_list("Notable quotes", data.get("notable_quotes"), [])

    ds = data.get("decision_signals") or {}
    out += [
        "## Decision signals",
        "- **Attracting Gen Z:** " + str(ds.get("gen_z_attraction", "no signal")),
        "- **Channel investment:** " + str(ds.get("channel_investment", "no signal")),
        "- **Portfolio direction:** " + str(ds.get("portfolio_direction", "no signal")),
        "",
        "<!-- raw extraction -->",
        "```json",
        json.dumps(data, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(out)


def analyse(path):
    transcript = path.read_text(encoding="utf-8", errors="replace")
    prompt = (
        "Analyse this consumer interview transcript.\n\n"
        + SCHEMA_BRIEF
        + "\n\nTRANSCRIPT (file: "
        + path.name
        + "):\n\"\"\"\n"
        + transcript
        + "\n\"\"\""
    )
    data = ask_json(prompt, system=SYSTEM)
    note = note_path(path)
    note.write_text(render_note(path, data), encoding="utf-8")
    return note


def run(force=False):
    """Analyse every transcript that has no up-to-date note. Returns new notes."""
    written = []
    for path in transcript_files():
        if not force and is_current(path):
            continue
        print("Analysing " + path.name + " ...")
        written.append(analyse(path))
    return written


if __name__ == "__main__":
    notes = run(force="--force" in sys.argv)
    print("Wrote %d note(s)." % len(notes))
    for n in notes:
        print("  " + str(n))
