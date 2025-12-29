#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

# Ensure running inside WSL on Windows hosts
if grep -qi microsoft /proc/version 2>/dev/null; then
  echo "[check] running inside WSL"
else
  echo "[warn] not running inside WSL (or /proc/version not accessible)"
fi

# Verify venv activation or at least that python3 points to project venv
if [ -n "${VIRTUAL_ENV:-}" ]; then
  echo "[check] venv active: ${VIRTUAL_ENV}"
else
  PY=$(command -v python3 || true)
  if [ -z "$PY" ]; then
    echo "[error] python3 not found in PATH. Activate venv first." >&2
    exit 2
  fi
  case "$PY" in
    "$ROOT"/venv/*|"$ROOT"/.venv_app/*)
      echo "[check] python3 resolved inside project venv: $PY"
      ;;
    *)
      echo "[warn] venv not active and python3 is $PY. It's recommended to activate the venv: source venv/bin/activate" >&2
      ;;
  esac
fi

echo "[stop] stopping existing processes"
pkill -f streamlit || true
pkill -f start_terminal_api.py || true
sleep 1

echo "[prepare] ensure trades.db"
touch trades.db

echo "[start] starting terminal API (no-docker)"
PYTHONPATH="$ROOT" nohup python3 ./scripts/start_terminal_api.py --port 8765 > logs/terminal_api_start.out 2>&1 &
echo $! > logs/terminal_api.pid || true
sleep 1

echo "[start] starting streamlit (no-docker)"
bash ./start_streamlit.sh --no-docker 8501 > logs/streamlit_8501.log 2>&1 &
echo $! > logs/streamlit.pid || true
sleep 6

echo
echo "--- listeners ---"
ss -ltnp | egrep ':8501|:8765' || true

echo
echo "--- processes (filtered) ---"
ps aux | egrep 'streamlit|start_terminal_api.py|terminal_component' || true

echo
echo "--- logs listing ---"
ls -la logs || true

echo
for f in logs/api_port.txt logs/terminal_component_debug.log logs/terminal_api_start.out logs/terminal_api.log logs/streamlit_8501.log logs/streamlit.pid logs/terminal_api.pid; do
  if [ -f "$f" ]; then
    echo "=== $f ==="
    sed -n '1,400p' "$f" || true
    echo
  else
    echo "MISSING: $f"
    echo
  fi
done

echo '[done]'
