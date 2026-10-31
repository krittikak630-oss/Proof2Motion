#!/bin/sh
cd "$(dirname "$0")/backend" || exit 1
[ -d venv ] || python3 -m venv venv
. venv/bin/activate
pip install -q -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Paste your GEMINI_API_KEY into backend/.env, save, then run ./start.sh again."
  exit 0
fi
echo "Open http://localhost:8000 in your browser"
uvicorn app.main:app --port 8000
