# Estée Lauder Interview Intelligence

An agent that reads consumer interview transcripts, files structured notes into a
markdown knowledge vault, finds the intersections across interviews, and answers
questions about them over Telegram.

It exists to support one decision: **which direction should Estée Lauder take to
grow sales with younger consumers?** The analysis deliberately keeps three
candidate answers open — attract Gen Z, invest in a channel, change the portfolio —
and reports which one the interviews actually have evidence for.

## How it works

```
interviews/*.md                raw transcripts you drop in
      |
      v  analyze.py            one Claude call per interview
vault/interviews/*.md          structured notes: themes, quotes, needs, channels
      |
      v  synthesize.py         one call across the whole vault
vault/synthesis/latest.md      intersections, tensions, recommendation
      |
      +--> pipeline.py         digest pushed to Telegram
      +--> bot.py              ask the vault questions from your phone
```

Nothing is thrown away and nothing is hidden: every claim in the synthesis is
traceable to a note, and every note keeps the verbatim quotes it was built from.

## Setup (10 minutes)

```bash
make setup          # creates .venv, installs deps, copies .env.example -> .env
```

Then fill in `.env`:

**1. Anthropic API key** — console.anthropic.com → API keys → Create key.
Add ~$5 of credit. A 20-interview study costs a few dollars.

**2. Telegram bot token** — in Telegram, message **@BotFather**:
- send `/newbot`
- give it a name (e.g. `Estee Insights`) and a username ending in `bot`
- BotFather replies with a token like `123456:ABC...` → paste into `.env`

**3. Telegram chat id** — open your new bot in Telegram, send it `hi`, then:
```bash
make chatid         # prints your chat_id -> paste into .env
```

## What it costs

Roughly **$4–10 for an entire 12-interview study**, including a few hundred bot
questions. Check before you spend:

```bash
make cost            # counts tokens (free) and prices the next run
```

Each job runs on the model that job needs, set per-task in `.env`:

| Job | Default | Why | Per unit |
|---|---|---|---|
| Extraction | `claude-sonnet-5` | mechanical: read one transcript, fill a schema | ~$0.03 / interview |
| Synthesis | `claude-opus-5` | the reasoning step — this is the one worth paying for | ~$0.21 / run |
| Digest | `claude-haiku-4-5` | a 200-word rewrite of text that already exists | ~$0.006 / day |
| Bot answers | `claude-sonnet-5` | ~$0.06 cold, **~$0.009 cached** | per question |

Three things keep the bill down without touching quality:

1. **Nothing is re-analysed.** Each note stores a hash of its transcript; a run
   with no new transcripts costs nothing at all and exits.
2. **The vault is cached for the bot.** It sits in a cached system prompt, so the
   second and later questions in a session re-read it at a tenth of the price.
   Every call prints its own token usage, so a cache miss is visible immediately.
3. **The digest uses Haiku.** It is rewriting the synthesis, not producing it.

Want it cheaper still? Set `ANTHROPIC_MODEL=claude-haiku-4-5` for extraction
(halves it) and `ANTHROPIC_SYNTHESIS_MODEL=claude-sonnet-5`. Compare the output
before you keep it — synthesis is where the model quality actually shows.

## Daily use

```bash
make run            # analyse new transcripts, re-synthesise, send digest
make bot            # start the Q&A bot; leave the terminal open
```

Drop new transcripts into `interviews/` as `.txt` or `.md`. `make run` only
processes files that are new or have changed, so it is safe to run repeatedly.

Ask the bot things like:
- *What do people say about price?*
- *Which channels came up most often?*
- *Where do participants disagree?*
- `/synthesis` — the current recommendation
- `/status` — how many interviews are in the vault

## Running it on a schedule

**Option A — your laptop (no extra accounts).** Runs daily at 07:00 when the
laptop is awake:
```bash
crontab -e
# add this line, with the real path:
0 7 * * * /Users/you/path/to/estee-agent/run.sh
```
Output goes to `.state/pipeline.log`.

**Option B — GitHub Actions (runs even when the laptop is closed).**
`.github/workflows/pipeline.yml` is ready. Add three repo secrets under
Settings → Secrets and variables → Actions: `ANTHROPIC_API_KEY`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. It commits new vault notes back to the
repo each night. Note: the *bot* still needs a laptop; only the pipeline moves
to the cloud.

## Handing this over

The repo carries no secrets — `.env` is gitignored, only `.env.example` ships.
To transfer ownership:

```bash
gh auth login                       # log in as your friend's GitHub account
gh repo create estee-agent --public --source=. --push
gh auth switch                      # back to your own account afterwards
```

He then runs `git clone <url>`, `make setup`, and puts **his own** API key and
bot token in `.env`. Nothing else changes. If you would rather keep it under your
account, use `gh repo create` as yourself and add him as a collaborator
(Settings → Collaborators), or transfer it later under Settings → Transfer
ownership.

## Layout

| path | what it is |
|---|---|
| `interviews/` | raw transcripts (your input) |
| `vault/` | generated notes and synthesis (the knowledge vault) |
| `src/analyze.py` | one transcript → one structured note |
| `src/synthesize.py` | whole vault → intersections + recommendation |
| `src/vault.py` | question answering over the vault |
| `src/bot.py` | Telegram bot loop |
| `src/pipeline.py` | the full flow, used by the scheduler |
| `src/claude.py` | the only place the model is called |

## A caveat worth keeping

The agent reports patterns in what people *said*. Interviews over-represent
whoever agreed to be interviewed, and people are unreliable narrators of their own
spending. Treat the synthesis as a sharpened set of hypotheses for Estée Lauder to
test, not as a measurement of the market.
