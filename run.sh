#!/usr/bin/env bash
# Wrapper for cron/launchd: cron has a bare environment, so use absolute paths.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p .state
exec .venv/bin/python src/pipeline.py >> .state/pipeline.log 2>&1
