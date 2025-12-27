# Copilot Instructions — KuCoin App (AutoCoinBot)

Quick, actionable notes to help an AI contributor be immediately productive in this repo.

1) Environment & quickstart
- Activate the venv before anything:

```bash
source venv/bin/activate
pip install -r requirements.txt
```
- Start the UI (Streamlit) in one terminal:

```bash
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true
```
- Start a bot (separate terminal) for dry-run or real runs:

```bash
python -u bot_core.py --bot-id test_dry_1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.1 --funds 0 --dry
```

2) Big picture (why and what files)
- `streamlit_app.py`: entry for the dashboard and login gating (.login_status persistence).
- `ui.py`: streamlit UI, controls bot lifecycle and multi-tab/kill-on-start guards.
- `bot_controller.py`: builds subprocess commands and records sessions (writes `bot_sessions` entries).
- `bot_core.py` / `bot.py`: bot logic; uses `DatabaseLogger`/`database.py` to write `bot_logs` and `trades`.
- `terminal_component.py`: local HTTP API (~port 8765) used by the web terminal widget; returns JSON logs.
- `database.py`: single-file schema + access helpers; `trades.db` lives at repository root by default.
- `api.py`: KuCoin integration helpers and secret lookup (`st.secrets` / env fallback).

3) Developer workflows & commands
- Setup: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Syntax check: `python -m py_compile <file>.py`
- Tests: `./run_tests.sh` (defaults to `APP_ENV=dev`) or `pytest` for unit tests. Selenium tests require Chrome + chromedriver and `RUN_SELENIUM=1`.
- DB checks: `scripts/db_inspect.py`.

4) Project-specific conventions (do not change lightly)
- Avoid ad-hoc `print()` in committed code — use `DatabaseLogger` or Python `logging` (see `bot_core.py`).
- If you change bot CLI args: update both `bot_core.py` and `bot_controller.py` so the command builder and the actor stay in sync.
- If you change DB schema: update `database.py` and every caller that reads/writes the modified columns.
- Preserve the JSON shape and CORS headers from `terminal_component.py` if you modify the terminal API (UI depends on it).
- UI multi-tab and kill-on-start behavior is coordinated via `ui.py` and DB state — prefer DB flags over in-memory globals.

5) Integration points & env
- DB file: `trades.db` at repo root (see `database.py`).
- Local terminal API default port: ~8765; UI polls `/api/logs?bot=<bot_id>`.
- Secrets: use `.env` locally or `st.secrets`. Keys commonly referenced: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `API_KEY_VERSION`, `KUCOIN_BASE`, `TRADES_DB`.

6) Safe-change checklist (quick review before PR)
- If changing bot CLI: run a local dry-run bot and verify `bot_sessions` and `bot_logs` entries.
- If changing DB schema: add migration steps and update `database.py` callers.
- If changing terminal API or UI props: verify terminal widget still renders and that CORS/JSON shape unchanged.
- Avoid adding prints; prefer `DatabaseLogger` for runtime data you want surfaced to the UI.

7) Useful file references
- UI entry: [streamlit_app.py](../../streamlit_app.py)
- UI components + lifecycle: [ui.py](../../ui.py)
- Bot execution: [bot_controller.py](../../bot_controller.py) and [bot_core.py](../../bot_core.py)
- DB helpers: [database.py](../../database.py)
- Terminal API: [terminal_component.py](../../terminal_component.py)

If anything here is unclear or you want more detail (DB schemas, specific CLI flags, or testing steps), tell me which area to expand and I'll iterate.


# Copilot Instructions — KuCoin App (AutoCoinBot)

**Always activate the venv before running any command:**

```bash
source venv/bin/activate
```

Use `python3` (or the venv python path) for all scripts:

```bash
python3 agent0_scraper.py --local --check-buttons
```

Install dependencies with:

```bash
pip install -r requirements.txt
```

If `python` is not available, always use `python3`.

Concise, actionable guidance for AI agents contributing to this repo.

## Big Picture & Architecture
- **Purpose:** Streamlit dashboard to manage trading bot subprocesses, store logs/trades in SQLite (`trades.db`), and expose a local HTTP API for live terminal widgets.
- **Major components:**
  - [streamlit_app.py](../../streamlit_app.py): App entry, login gating (persists `.login_status`).
  - [ui.py](../../ui.py): UI rendering, bot lifecycle, server-side coordination (kill-on-start, multi-tab guards, uses `st.cache_resource`).
  - [bot_controller.py](../../bot_controller.py): Spawns/stops bot subprocesses via `sys.executable` calling [bot_core.py](../../bot_core.py).
  - [bot_core.py](../../bot_core.py) / [bot.py](../../bot.py): Bot logic, uses `DatabaseLogger` for `bot_logs`/`trades`.
  - [terminal_component.py](../../terminal_component.py): Starts local HTTP API (default port ~8765) for terminal widget.
  - [database.py](../../database.py): DB schema + helpers (`insert_bot_session`, `get_active_bots`, `add_bot_log`, `get_bot_logs`, `insert_trade`).
  - [api.py](../../api.py): KuCoin integration, reads secrets from env or `st.secrets` via `_get_secret()`.

## Developer Workflows
- **Run Streamlit and bots in separate terminals** for clear logs/debugging:
  1. Terminal 1: `python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true`
  2. Terminal 2: `python -u bot_core.py --bot-id <id> --symbol BTC-USDT --entry 30000 --targets "2:0.3,5:0.4" --interval 5 --size 0.1 --funds 0 --dry`
- **Setup:**
  - `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- **Testing:**
  - Use `pytest` (see [test_bot_start.py](../../test_bot_start.py), [test_interface.py](../../test_interface.py), [test_visual_validation.py](../../test_visual_validation.py)).
  - Always run tests from the project venv. Use `./run_tests.sh` (defaults to `APP_ENV=dev`). Example: `APP_ENV=hom ./run_tests.sh` for homologation.
  - Selenium visual tests: require Chrome + chromedriver. Run with `./run_tests.sh --selenium` or `RUN_SELENIUM=1 ./run_tests.sh`.
- **Syntax check:** `python -m py_compile <file>.py`
- **DB inspection:** `scripts/db_inspect.py` (make executable: `chmod +x scripts/db_inspect.py`)
- **Start/stop helpers:** `./start_streamlit.sh`, `./control_app.sh restart|stop`

## Project Conventions & Patterns
- **No ad-hoc `print()` in committed code** — use `DatabaseLogger`/`logging` (see [bot_core.py](../../bot_core.py)).
- **Bot lifecycle:** `BotController.start_bot()` builds a `sys.executable -u bot_core.py ...` command and records session in `bot_sessions` (PID recorded). If you change CLI args, update both [bot_core.py](../../bot_core.py) and [bot_controller.py](../../bot_controller.py).
- **UI multi-tab:** [ui.py](../../ui.py) implements `_get_kill_on_start_guard()` and a resource to avoid duplicate/conflicting runs. Prefer DB/state updates over in-memory globals.
- **Terminal API:** [terminal_component.py](../../terminal_component.py) returns JSON arrays from `DatabaseManager.get_bot_logs()`. Preserve CORS headers if changing handlers.
- **Login state:** `.login_status` file persists login between runs.

## Integration Points & Environment
- **DB:** `trades.db` at repo root (see [database.py](../../database.py)). If you add columns, update [database.py](../../database.py) and all callers.
- **Local API port:** Default ~8765. UI polls `/api/logs?bot=<bot_id>`.
- **Env/secrets:** Prefer `.env` for local dev or `st.secrets` in Streamlit. Keys: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `API_KEY_VERSION`, `KUCOIN_BASE`, `TRADES_DB`.
- **App environment:** Set `APP_ENV=dev` (uses `LOCAL_URL`) or `APP_ENV=hom` (uses `HOM_URL`). `.env.example` shows usage.

## Editing & Safe-Change Checklist
1. If modifying bot CLI/lifecycle: update both [bot_core.py](../../bot_core.py) and [bot_controller.py](../../bot_controller.py).
2. If changing DB schema: update [database.py](../../database.py) and all code that reads/writes affected columns (search for `bot_sessions`, `trades`, `bot_logs`).
3. If touching terminal API/UI endpoints: preserve JSON shape and CORS headers in [terminal_component.py](../../terminal_component.py).
4. Avoid `print()`; use `DatabaseLogger` or `logging`.

## Examples & Validation
- **Bot command:** `python -u bot_core.py --bot-id <id> --symbol BTC-USDT --entry 30000 --targets "2:0.3,5:0.4" --interval 5 --size 0.1 --funds 0 --dry`
- **Scrapers/headless validation:** [agent0_scraper.py](../../agent0_scraper.py) (Selenium-based, needs Chrome + chromedriver); [run_dry_validate.py](../../run_dry_validate.py) exercises dry-run bots and the scraper.

## Deployment Notes
- For production, prefer systemd (see [deploy/streamlit.service.template](../../deploy/streamlit.service.template)) or Docker Compose ([deploy/docker-compose.yml](../../deploy/docker-compose.yml)).
- When using Docker, mount the project directory for persistent DB storage (default SQLite DB is ephemeral in containers/cloud).
- [start_streamlit.sh](../../start_streamlit.sh) supports `--foreground` for systemd and background mode by default.
- See [deploy/README.md](../../deploy/README.md) for deployment steps.

---
If anything critical is missing or you want DB schemas, specify which table(s) to append.

## Recent Fixes & Notes (Dec 2025)
- **Files changed:** `ui.py`, `wallet_releases_rss.py`, `streamlit_app.py` (local fixes branch: `fix/ui-html-wallet-releases-20251226`).
- **Bug fixes applied:** added missing imports (`time` in `ui.py`, `html` in `wallet_releases_rss.py`), defensive shim for `html` in `ui.py`, fixed an indentation error causing login to loop.
- **LOG button behavior:** restored inline LOG action that sets `st.session_state.selected_bot` and calls `render_terminal_live_api(bot_id)` so logs open in-page for started bots. Alternative UX (open `/monitor` in new tab) was explored but reverted per preference.
- **Runtime notes:** a root-owned Streamlit process may block port `8501`; start Streamlit as the local user or use another port. Example:

```bash
source venv/bin/activate
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true
```

- **E2E validation:** to verify live terminal rendering, run a dry-run bot and then click LOG in the UI:

```bash
# in one terminal: start streamlit (see above)
# in another terminal: start a dry-run bot that writes DB logs
python -u bot_core.py --bot-id test_dry_1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.1 --funds 0 --dry
```

- **PR created:** branch `fix/ui-html-wallet-releases-20251226` pushed and PR opened: https://github.com/eddiejdi/AutoCoinBot/pull/19
- **Testing & checks:** run `python -m py_compile <file>.py` for syntax checks; run `./run_tests.sh` or `pytest` from the venv for tests. Selenium tests require Chrome + chromedriver.
- **When editing:** If you change the bot CLI args or DB schema, update `bot_controller.py`/`bot_core.py` and `database.py` respectively (see Editing & Safe-Change Checklist above).
