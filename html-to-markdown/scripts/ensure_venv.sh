#!/usr/bin/env bash
# Creates/refreshes the skill's private venv and installs the Markdown
# conversion dependencies (html2text, beautifulsoup4). Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python3 ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade html2text beautifulsoup4
echo "venv ready: $(dirname "$0")/.venv (html2text + beautifulsoup4)"
