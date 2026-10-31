#!/usr/bin/env bash
# Run on your Cloudways server over SSH:  bash deploy/cloudways_setup.sh
# Installs dependencies, then (re)starts Proof2Motion on port 8000.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

python3 -m venv venv
. venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  sed -i 's/^# ENVIRONMENT=.*/ENVIRONMENT=production/; s/^# TRUST_PROXY=.*/TRUST_PROXY=true/' .env
  echo "Created backend/.env. Add your GEMINI_API_KEY (nano backend/.env), then run this script again."
  exit 1
fi

if [ -f "$ROOT/proof2motion.pid" ] && kill -0 "$(cat "$ROOT/proof2motion.pid")" 2>/dev/null; then
  kill "$(cat "$ROOT/proof2motion.pid")"; sleep 1
fi
nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers \
  > "$ROOT/proof2motion.log" 2>&1 &
echo $! > "$ROOT/proof2motion.pid"
sleep 2
curl -fsS http://127.0.0.1:8000/api/health && echo && echo "Running. Logs: $ROOT/proof2motion.log"
