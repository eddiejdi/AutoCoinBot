#!/usr/bin/env bash
set -euo pipefail
# Start helper for Linux / WSL
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

# Copy example env if missing
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Created .env from .env.example (edit with real secrets)"
fi

# Setup venv
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Start Streamlit in background and save pid
nohup python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true > streamlit.log 2>&1 &
echo $! > streamlit.pid
echo "Streamlit started (pid=$(cat streamlit.pid)). Logs: streamlit.log"

echo "To follow logs: tail -f streamlit.log"
