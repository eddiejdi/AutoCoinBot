#!/usr/bin/env bash
set -euo pipefail

# Wrapper central para iniciar/parar serviços (Streamlit, terminal API)
# Uso:
#   ./scripts/run_service.sh streamlit start [--no-docker] [PORT]
#   ./scripts/run_service.sh streamlit stop
#   ./scripts/run_service.sh api start [--no-docker] [PORT]
#   ./scripts/run_service.sh api stop

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/deploy/docker-compose.yml}"
LOGDIR="${LOGDIR:-$ROOT_DIR/logs}"
mkdir -p "$LOGDIR"

cmd="$1" || true
action="$2" || true

shift 2 || true

NO_DOCKER=false
for a in "$@"; do
  if [ "$a" = "--no-docker" ]; then
    NO_DOCKER=true
  fi
done

docker_available() { command -v docker >/dev/null 2>&1; }

docker_up() {
  echo "[run_service] docker compose up..."
  docker compose -f "${COMPOSE_FILE}" down --remove-orphans || true
  docker compose -f "${COMPOSE_FILE}" up -d --build
}

docker_down() {
  echo "[run_service] docker compose down..."
  docker compose -f "${COMPOSE_FILE}" down --remove-orphans || true
}

case "${cmd}" in
  streamlit)
    case "${action}" in
      start)
        PORT="${1:-8501}"
        if [ "$NO_DOCKER" = true ]; then
          echo "[run_service] starting streamlit locally on port ${PORT}"
          bash "$ROOT_DIR/start_streamlit.sh" --foreground "${PORT}"
        else
          if ! docker_available; then
            echo "docker not available; falling back to local start" >&2
            bash "$ROOT_DIR/start_streamlit.sh" --foreground "${PORT}"
          else
            docker_up
          fi
        fi
        ;;
      stop)
        echo "[run_service] stopping streamlit"
        if [ "$NO_DOCKER" = true ]; then
          pkill -f "streamlit" || true
        else
          docker_down
        fi
        ;;
      *) echo "Usage: $0 streamlit (start|stop) [--no-docker] [PORT]"; exit 2;;
    esac
    ;;
  api)
    case "${action}" in
      start)
        PORT="${1:-8765}"
        if [ "$NO_DOCKER" = true ]; then
          echo "[run_service] starting terminal API locally on port ${PORT}"
          PYTHONPATH="$ROOT_DIR" bash -lc "python3 $ROOT_DIR/scripts/start_terminal_api.py --port ${PORT} > $LOGDIR/terminal_api_start.out 2>&1 & echo \$! > $LOGDIR/terminal_api.pid"
        else
          if ! docker_available; then
            echo "docker not available; falling back to local start" >&2
            PYTHONPATH="$ROOT_DIR" bash -lc "python3 $ROOT_DIR/scripts/start_terminal_api.py --port ${PORT} > $LOGDIR/terminal_api_start.out 2>&1 & echo \$! > $LOGDIR/terminal_api.pid"
          else
            echo "[run_service] starting API via Docker Compose"
            docker_up
          fi
        fi
        ;;
      stop)
        echo "[run_service] stopping terminal API"
        pkill -f "terminal_component" || true
        ;;
      *) echo "Usage: $0 api (start|stop) [--no-docker] [PORT]"; exit 2;;
    esac
    ;;
  *)
    echo "Usage: $0 (streamlit|api) (start|stop) [--no-docker] [PORT]"
    exit 2
    ;;
esac
