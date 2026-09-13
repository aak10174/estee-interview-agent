.PHONY: setup run bot chatid synth clean

setup:          ## create venv and install dependencies
	python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
	@test -f .env || cp .env.example .env
	@echo "Done. Now edit .env and fill in your keys."

run:            ## full pipeline: analyse -> synthesise -> Telegram digest
	.venv/bin/python src/pipeline.py

synth:          ## re-run only the cross-interview synthesis
	.venv/bin/python src/synthesize.py

bot:            ## start the Telegram bot (Ctrl+C to stop)
	.venv/bin/python src/bot.py

chatid:         ## print the chat id of whoever last messaged the bot
	.venv/bin/python src/telegram.py

clean:          ## delete generated vault notes (transcripts are untouched)
	rm -f vault/interviews/*.md vault/synthesis/*.md
