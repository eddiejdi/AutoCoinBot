# Copilot Instructions for KuCoin App (AutoCoinBot)

This file gives targeted, discoverable guidance for AI code contributors working on this repo.

## Big picture
- Purpose: a Streamlit-based dashboard that manages trading bot subprocesses, stores logs/trades in SQLite (`trades.db`), and exposes a tiny local HTTP API for live terminal views.
- Components & boundaries:
	- `streamlit_app.py` — app entry + login gating (persists login to `.login_status`).
	- `ui.py` — single place that renders the UI, coordinates bot lifecycle, and contains server-side coordination (kill-on-start, multi-tab guards).
	# Copilot Instructions — KuCoin App (AutoCoinBot)

	Short, focused guidance for AI contributors to be productive in this repo.

	Purpose
	- Streamlit dashboard that manages long-running trading bot subprocesses, stores logs/trades in SQLite (`trades.db`), and exposes a tiny local HTTP API for terminal widgets.

	Architecture (core components)
	- `streamlit_app.py`: app entry + login gate (persists `.login_status`).
	- `ui.py`: UI renderer + server-side coordination (kill-on-start, multi-tab guards, uses `st.cache_resource`).
	- `bot_controller.py`: spawns/stops bot subprocesses via `sys.executable` calling `bot_core.py`.
	- `bot_core.py` / `bot.py`: bot subprocess logic and `DatabaseLogger` used for writing `bot_logs` and `trades`.
	- `terminal_component.py`: starts small local HTTP API (default near port 8765) used by the terminal widget.
	- `database.py`: DB schema + helpers (`insert_bot_session`, `get_active_bots`, `add_bot_log`, `get_bot_logs`, `insert_trade`).
	- `api.py`: KuCoin integration; reads secrets from env or `st.secrets` via `_get_secret()`.

	- Sempre rode o Streamlit e o bot em terminais separados para facilitar debug e visualização:
		1. **Terminal 1:** `python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true`
		2. **Terminal 2:** Inicie o bot manualmente (exemplo):
			 `python -u bot_core.py --bot-id <id> --symbol BTC-USDT --entry 30000 --targets "2:0.3,5:0.4" --interval 5 --size 0.1 --funds 0 --dry`
		Isso garante que logs, status e problemas de sincronização fiquem visíveis e isolados.
	- Setup venv and deps:
		- `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`.
	- Tests: `pytest` (repo includes `test_bot_start.py`, `test_interface.py`, `test_visual_validation.py`).
	  - Always run tests from the project virtualenv. Use `run_tests.sh` to create/activate the venv, install deps and run `pytest` (defaults to `APP_ENV=dev`).
	  - Example: `./run_tests.sh` or `APP_ENV=hom ./run_tests.sh` for homologation-targeted tests.
	  - Selenium visual tests: require Chrome + chromedriver on `PATH`. Run with `./run_tests.sh --selenium` or `RUN_SELENIUM=1 ./run_tests.sh`.
	- Syntax check: `python -m py_compile <file>.py`.
	- DB inspection helper: `scripts/db_inspect.py` (make executable: `chmod +x scripts/db_inspect.py`).
	- Start/stop helpers: `./start_streamlit.sh`, `./control_app.sh restart|stop`.

	Project conventions & gotchas
	- No ad-hoc `print()` in committed code — use `DatabaseLogger`/`logging` (see `bot_core.py`).
	- Bot lifecycle: `BotController.start_bot()` constructs a `sys.executable -u bot_core.py ...` command and records the session in `bot_sessions` (PID recorded). Changes to CLI args must be reflected in both places.
	- UI multi-tab behavior: `ui.py` implements `_get_kill_on_start_guard()` and a resource to avoid duplicate/conflicting runs; prefer DB/state updates over in-memory globals.
	- Terminal API: `terminal_component.start_api_server()` returns JSON arrays from `DatabaseManager.get_bot_logs()`; keep CORS headers intact when changing handlers.
	- Login state: `.login_status` file is used to persist login between runs.

	Integration points & environment
	- DB: `trades.db` at repo root by default (`database.py` controls schema). If you add columns, update `database.py` and callers.
	- Local API port: default near `8765` — UI polls `/api/logs?bot=<bot_id>`.
	- Env / secrets: prefer `.env` for local dev or `st.secrets` in Streamlit. Keys: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `API_KEY_VERSION`, `KUCOIN_BASE`, `TRADES_DB`.
	 - Env / secrets: prefer `.env` for local dev or `st.secrets` in Streamlit. Keys: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `API_KEY_VERSION`, `KUCOIN_BASE`, `TRADES_DB`.
	 - New: control which app to validate via environment: set `APP_ENV=dev` (uses `LOCAL_URL`) or `APP_ENV=hom` (uses `HOM_URL`). You can also set `HOM_URL` or `LOCAL_URL` directly in `.env` or environment.
	 - A sample file `.env.example` is included showing `APP_ENV`, `LOCAL_URL`, and `HOM_URL`.

	Editing & safe-change checklist for AI agents
	1. If modifying bot CLI or lifecycle: update `bot_core.py` arg parsing and `bot_controller.py` command construction.
	2. If changing DB schema: update `database.py` and any code that reads/writes affected columns (search for `bot_sessions`, `trades`, `bot_logs`).
	3. If touching terminal API or UI endpoints: preserve JSON shape and CORS headers used by the `terminal_component` widget.
	4. Avoid introducing `print()`s; use `DatabaseLogger` or `logging` for diagnostics.

	Key files (quick links)
	- [streamlit_app.py](streamlit_app.py#L1)
	- [ui.py](ui.py#L1)
	- [bot_controller.py](bot_controller.py#L1)
	- [bot_core.py](bot_core.py#L1)
	- [terminal_component.py](terminal_component.py#L1)
	- [database.py](database.py#L1)
	- [api.py](api.py#L1)
	- [scripts/db_inspect.py](scripts/db_inspect.py#L1)

	Short examples
	- Example bot command (constructed in `BotController.start_bot`):
		- `python -u bot_core.py --bot-id <id> --symbol BTC-USDT --entry 30000 --targets "2:0.3,5:0.4" --interval 5 --size 0.1 --funds 0 --dry`

	Scrapers & headless validation
	- `agent0_scraper.py` is a Selenium-based visual check (requires Chrome + chromedriver); `run_dry_validate.py` exercises dry-run bots and the scraper.

	# Deployment notes

	- For production or persistent use, prefer running as a systemd service (see deploy/streamlit.service.template) or via Docker Compose (see deploy/docker-compose.yml).
	- When using Docker, the project directory is mounted into the container; adjust volumes for persistent DB storage (the default SQLite DB is ephemeral in containers/cloud).
	- The helper script `start_streamlit.sh` supports `--foreground` for systemd and background mode by default.
	- See deploy/README.md for step-by-step deployment instructions.
	If anything critical is missing or you want the DB schemas, tell me which table(s) to append and I'll add concise schemas and example queries.
