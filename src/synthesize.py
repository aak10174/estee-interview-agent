"""Read every interview note and produce the cross-interview synthesis.

This is the step that finds intersections: what several people said
independently, where they disagree, and which of the three candidate
decisions the evidence can actually support.
"""
import datetime

from claude import ask
from config import CLIENT_NAME, NOTES_DIR, SYNTHESIS_DIR, SYNTHESIS_MODEL

SYSTEM = (
    "You are a senior strategy consultant briefing "
    + CLIENT_NAME
    + " on qualitative consumer research. You are blunt about weak evidence. "
    "You distinguish between a pattern seen across many interviews and one loud "
    "opinion from a single person, and you always say how many participants back "
    "a claim. You never invent quotes."
)

PROMPT = """Below are structured notes from {n} consumer interviews.

Write a synthesis in markdown with these sections, in this order:

## Executive summary
Five bullets. What does this set of interviews actually tell {client}?

## Intersections
Themes at least two participants raised independently. For each: a heading, how
many participants (e.g. "4 of {n}"), which aliases, what they said, and one or two
verbatim quotes. Order by how many participants back them.

## Tensions and disagreements
Where participants contradict each other, or contradict what the brand assumes.
Name both sides.

## Outliers worth watching
Single-participant signals that are strategically interesting even though only
one person said them. Label them clearly as n=1.

## The three candidate decisions
Assess each of these on the evidence, and say plainly which one this research
can support and which it cannot:
1. How to attract Gen Z
2. Which channel to invest in
3. Product / portfolio direction
For each, state: what the evidence says, how strong it is, and what is missing.

## Recommendation
The single direction you would put in front of {client} leadership, with the
three strongest pieces of evidence behind it, and the one risk that would
change your mind.

## Evidence gaps
What to ask in the next round of interviews.

Rules: cite participant aliases inline like (P02, P05). Never state a number of
participants you have not counted. If the evidence is thin, say so rather than
padding the section.

INTERVIEW NOTES
===============
{notes}
"""


def load_notes():
    return sorted(p for p in NOTES_DIR.glob("*.md"))


def run():
    notes = load_notes()
    if not notes:
        raise SystemExit("No interview notes in the vault yet. Run analyze.py first.")

    blob = "\n\n---\n\n".join(
        "### FILE: " + p.name + "\n" + p.read_text(encoding="utf-8").split("<!-- raw extraction -->")[0]
        for p in notes
    )
    body = ask(
        PROMPT.format(n=len(notes), client=CLIENT_NAME, notes=blob),
        system=SYSTEM,
        model=SYNTHESIS_MODEL,
        max_tokens=16000,
    )

    today = datetime.date.today().isoformat()
    header = "\n".join(
        [
            "---",
            "type: synthesis",
            "generated: " + today,
            "interviews: %d" % len(notes),
            "sources: " + ", ".join(p.stem for p in notes),
            "---",
            "",
            "# Cross-interview synthesis — %s (%d interviews)" % (CLIENT_NAME, len(notes)),
            "",
        ]
    )
    text = header + body + "\n"

    latest = SYNTHESIS_DIR / "latest.md"
    latest.write_text(text, encoding="utf-8")
    (SYNTHESIS_DIR / ("synthesis-" + today + ".md")).write_text(text, encoding="utf-8")
    return latest


if __name__ == "__main__":
    print("Wrote " + str(run()))
