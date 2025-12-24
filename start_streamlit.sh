#!/usr/bin/env bash
set -euo pipefail

# Enable shell debug if requested: set SHELL_DEBUG=1 in environment to enable
if [ "${SHELL_DEBUG:-0}" != "0" ]; then
  set -x
fi

# start_streamlit.sh
# Usage:
#   ./start_streamlit.sh [PORT]
#   ./start_streamlit.sh --foreground [PORT]
#
# Behavior:
# - Default: kills existing Streamlit processes, activates .venv_app/venv, and
#   starts Streamlit in background (writes /tmp/streamlit_<PORT>.pid).
# - With `--foreground`: runs Streamlit in foreground (useful for systemd or
#   container runtimes). In foreground mode the script does not pkill processes
#   and does not daemonize.

MODE_FOREGROUND=false
DOCKER_MODE=false

if [ "${1:-}" = "--foreground" ]; then
  MODE_FOREGROUND=true
  shift || true
fi

if [ "${1:-}" = "--docker" ]; then
  DOCKER_MODE=true
  shift || true
fi

PORT="${1:-${PORT:-8501}}"

# Streamlit log level (env override). Default to `debug` to increase verbosity
# when starting via this script. Set `LOG_LEVEL=info` or `LOG_LEVEL=warning`
# to reduce verbosity.
LOG_LEVEL="${LOG_LEVEL:-debug}"

export STREAMLIT_LOG_LEVEL="${LOG_LEVEL}"
export PYTHONFAULTHANDLER=1

activate_venv() {
  if [ -f .venv_app/bin/activate ]; then
    # shellcheck disable=SC1091
    . .venv_app/bin/activate
  elif [ -f venv/bin/activate ]; then
    # shellcheck disable=SC1091
    . venv/bin/activate
  fi
}

COMPOSE_FILE="${COMPOSE_FILE:-deploy/docker-compose.yml}"

docker_available() {
  command -v docker >/dev/null 2>&1
}

docker_compose_up() {
  echo "[start_streamlit] bringing Docker Compose (${COMPOSE_FILE}) down and up..."
  docker compose -f "${COMPOSE_FILE}" down --remove-orphans || true
  if [ "$MODE_FOREGROUND" = true ]; then
    docker compose -f "${COMPOSE_FILE}" up --build
  else
    docker compose -f "${COMPOSE_FILE}" up -d --build
  fi
}

if [ "$DOCKER_MODE" = true ]; then
  if ! docker_available; then
    echo "[start_streamlit] docker is not available in PATH; cannot start Docker Compose." >&2
    exit 2
  fi
  docker_compose_up
  exit 0
fi

if [ "$MODE_FOREGROUND" = false ]; then
  echo "[start_streamlit] stopping any existing streamlit processes..."
  pkill -f "streamlit" || true
  pkill -f "streamlit_app.py" || true
  sleep 1
fi

echo "[start_streamlit] activating virtualenv (if present)"
activate_venv || true

if [ "$MODE_FOREGROUND" = true ]; then
  echo "[start_streamlit] running in foreground on port ${PORT} (LOG_LEVEL=${LOG_LEVEL})"
  exec env STREAMLIT_LOG_LEVEL="${LOG_LEVEL}" PYTHONFAULTHANDLER=1 \
    python3 -m streamlit run streamlit_app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true --logger.level ${LOG_LEVEL}
else
  LOGFILE="/tmp/streamlit_${PORT}.log"
  PIDFILE="/tmp/streamlit_${PORT}.pid"

  echo "[start_streamlit] starting Streamlit on port ${PORT} (logs -> ${LOGFILE})"
  nohup setsid bash -c "export STREAMLIT_LOG_LEVEL=${LOG_LEVEL} PYTHONFAULTHANDLER=1; exec python3 -m streamlit run streamlit_app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true --logger.level ${LOG_LEVEL}" >"${LOGFILE}" 2>&1 &
  echo $! > "${PIDFILE}"
  echo "[start_streamlit] started with pid $(cat ${PIDFILE})"
fi
