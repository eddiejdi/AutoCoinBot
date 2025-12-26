# Copilot Instructions for KuCoin App (AutoCoinBot)

This file gives targeted, discoverable guidance for AI code contributors working on this repo.

## Big picture
- Purpose: a Streamlit-based dashboard that manages trading bot subprocesses, stores logs/trades in SQLite (`trades.db`), and exposes a tiny local HTTP API for live terminal views.
- Components & boundaries:
	- `streamlit_app.py` — app entry + login gating (persists login to `.login_status`).
	- `ui.py` — single place that renders the UI, coordinates bot lifecycle, and contains server-side coordination (kill-on-start, multi-tab guards).
	- `bot_controller.py` — starts/stops bots as subprocesses (invokes `bot_core.py` via `sys.executable`).
	- `bot_core.py` / `bot.py` — subprocess bot logic (command-line args: `--bot-id`, `--symbol`, `--entry`, `--targets`, `--size`, `--dry`, etc.).
	- `terminal_component.py` — renders terminal HTML, starts local HTTP API (`start_api_server`) or static file server for logs (default port 8765 if available).
	- `database.py` — SQLite manager; key methods: `insert_bot_session`, `get_active_bots`, `add_bot_log`, `get_bot_logs`, `insert_trade`.
	- `api.py` — integration with KuCoin; uses environment or Streamlit secrets via `_get_secret()`.

## Concrete developer workflows
- Start UI (dev): `python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true`
- Restart helper: `./control_app.sh restart` (project script used in docs/workflows).
- Quick checks: `python -m py_compile <file>.py` to validate syntax as preferred by this repo.
- Run unit/ux tests: repo contains tests (`test_bot_start.py`, `test_interface.py`) — run with your test runner (e.g. `pytest`).
- Inspect logs: `logs/` folder and `logs/kucoin_api.log` (API logs). Terminal widget polls `http://localhost:8765/api/logs?bot=<bot_id>` by default.

## Project-specific conventions & patterns
- No ad-hoc print/debug statements in committed code; use the DB logger or proper logging. See `bot_core.DatabaseLogger` which writes logs into SQLite via `DatabaseManager`.
- Login is persisted to a file: `.login_status` (used by `streamlit_app.py` / `ui.py`).
- Bot processes are intentionally launched as subprocesses from `bot_controller.BotController.start_bot()` using `sys.executable` and `bot_core.py`; prefer editing `bot_core.py` contract when changing CLI args.
- Streamlit multi-tab behavior is managed explicitly (see `_get_kill_on_start_guard()` and `_KILL_ON_START_GUARD_RESOURCE` in `ui.py`). Coordinate cross-session state changes through DB or st.cache_resource.
- Local API/terminal: `terminal_component.start_api_server()` starts a CORS-enabled HTTP server that reads logs from `DatabaseManager.get_bot_logs()`; the UI expects JSON arrays of log objects.
- Secrets: API credentials are read via environment variables or `st.secrets` (see `api._get_secret()`); prefer `.env` for local dev.

## Integration points & config
- DB file: `trades.db` at repository root (managed by `database.py`). Schema and indexes are created via `DatabaseManager.init_database()`.
- Default local API port: `8765` (auto-finds free port near that); code accepts other ports via helper calls.
- Bot CLI example (constructed in `BotController.start_bot`):
	- sys.executable -u bot_core.py --bot-id <id> --symbol BTC-USDT --entry 30000 --targets "2:0.3,5:0.4" --interval 5 --size 0.1 --funds 0 --dry

## Safe editing guidance for AI agents
- When changing process lifecycle behavior, update both `bot_controller.py` and the CLI parsing in `bot_core.py`.
- If adding DB fields, update `database.py` schema and the places that `insert_bot_session` / `get_active_bots` are used (e.g., `ui._kill_active_bot_sessions_on_start`).
- When modifying the terminal UI or API, keep CORS headers in `terminal_component.APIHandler.end_headers()` and preserve the JSON format returned by `get_bot_logs()`.
- Preserve the project's no-debug-prints rule; use `DatabaseLogger` or `logging` instead.

## Useful files & entrypoints (examples)
- UI entry: [streamlit_app.py](streamlit_app.py#L1)
- Main UI: [ui.py](ui.py#L1)
- Terminal & local API: [terminal_component.py](terminal_component.py#L1)
- Bot runner: [bot_core.py](bot_core.py#L1)
- Controller that spawns bots: [bot_controller.py](bot_controller.py#L1)
- DB manager: [database.py](database.py#L1)
- KuCoin integration: [api.py](api.py#L1)
- Quick start scripts: [QUICK_START.sh](QUICK_START.sh#L1), [start_streamlit.sh](start_streamlit.sh#L1), [control_app.sh](control_app.sh#L1)
 - DB helpers: [scripts/db_inspect.py](scripts/db_inspect.py#L1) (CLI inspector; make it executable with `chmod +x scripts/db_inspect.py`)

---

If anything here is unclear or you want more examples (e.g., exact DB table columns used by a specific UI panel), tell me which area to expand and I'll iterate.

## Env vars & secrets
- The code reads configuration from environment variables, a `.env` file (if present), or Streamlit `st.secrets`. Common keys used:
	- `API_KEYv1` / `API_KEY`
	- `API_SECRETv1` / `API_SECRET`
	- `API_PASSPHRASEv1` / `API_PASSPHRASE`
	- `API_KEY_VERSION` (defaults to `1`)
	- `KUCOIN_BASE` (default `https://api.kucoin.com`)
	- `TRADES_DB` (path to `trades.db`, default `trades.db`)
	- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
	- `WEBHOOK_HOST`, `WEBHOOK_PORT`, `WEBHOOK_DRYRUN`

- Example `.env` file (place at repo root):

```
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
API_PASSPHRASE=your_passphrase_here
API_KEY_VERSION=1
KUCOIN_BASE=https://api.kucoin.com
TRADES_DB=trades.db
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
WEBHOOK_PORT=5000
```

- Example `secrets.toml` for Streamlit (`.streamlit/secrets.toml`):

```
[kucoin]
API_KEY = "your_api_key_here"
API_SECRET = "your_api_secret_here"
API_PASSPHRASE = "your_passphrase_here"
API_KEY_VERSION = "1"

[app]
TRADES_DB = "trades.db"
```

Notes:
- `api._get_secret()` tries env vars first, then `st.secrets` (flat or nested). Use whichever fits your deployment.
- For local development prefer `.env` and `python-dotenv`; CI or Streamlit sharing use `secrets.toml` or environment variables.

## Start / Stop (developer & deploy)

- Start the app (development):

```
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true
```

- Start using helper script (sets up env/venv if present):

```
./start_streamlit.sh
```

- Stop the app (quick):

```
pkill -f streamlit_app.py || pkill -f streamlit
rm -f .login_status
```

- Stop gracefully via project helper (if available):

```
./control_app.sh stop
./control_app.sh restart
```

- Notes about process lifecycle and bots:
	- Bots are started as subprocesses by `bot_controller.BotController.start_bot()`; their commands include `bot_core.py` and a generated `--bot-id`.
	- On UI startup, `ui._kill_active_bot_sessions_on_start()` will attempt to stop leftover bot sessions recorded in the DB; this is a deliberate safety behavior to avoid orphaned bots.
	- To kill bot processes manually: `pkill -f bot_core.py` (use with care) or inspect `ps -eo pid,args | grep bot_core.py` and `DatabaseManager.get_active_bots()` for tracked sessions.
	- Bot PIDs are recorded in the DB (`bot_sessions.pid`) and the `pids/` directory may contain `streamlit.pid` for service management.

- Service / production hints:
	- Systemd unit example: `deploy/streamlit.service.template` (use it to create a systemd service for Streamlit).
	- Docker / compose: `deploy/docker-compose.yml` — start/stop with `docker-compose up -d` / `docker-compose down`.

- Running under the project virtualenv (recommended):

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true
```

---

If you want, I can append exact DB schema snippets for `bot_sessions`, `trades`, and `bot_logs` to this file for quick reference.

## DB schema (quick reference)
Below are the primary table schemas created by `DatabaseManager.init_database()` in `database.py`.

- `trades` (simplified):

```sql
CREATE TABLE IF NOT EXISTS trades (
	id TEXT PRIMARY KEY,
	timestamp REAL NOT NULL,
	symbol TEXT NOT NULL,
	side TEXT NOT NULL,
	price REAL NOT NULL,
	size REAL,
	funds REAL,
	profit REAL,
	commission REAL,
	order_id TEXT,
	bot_id TEXT,
	strategy TEXT,
	dry_run INTEGER DEFAULT 1,
	metadata TEXT,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

- `bot_sessions` (simplified):

```sql
CREATE TABLE IF NOT EXISTS bot_sessions (
	id TEXT PRIMARY KEY,
	pid INTEGER,
	symbol TEXT NOT NULL,
	mode TEXT NOT NULL,
	entry_price REAL NOT NULL,
	targets TEXT,
	trailing_stop_pct REAL,
	stop_loss_pct REAL,
	size REAL,
	funds REAL,
	start_ts REAL NOT NULL,
	end_ts REAL,
	status TEXT DEFAULT 'running',
	executed_parts TEXT,
	remaining_fraction REAL,
	total_profit REAL,
	dry_run INTEGER DEFAULT 1,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

- `bot_logs` (simplified):

```sql
CREATE TABLE IF NOT EXISTS bot_logs (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	bot_id TEXT NOT NULL,
	timestamp REAL NOT NULL,
	level TEXT NOT NULL,
	message TEXT NOT NULL,
	data TEXT,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

These snippets are kept in sync with `database.py`; if you change columns, update both the schema and any code that reads/writes these tables.

## Scrapers & validation
- The repo includes a set of small "scrapers" and validators used during CI/dev validation:
	- `agent0_scraper.py` — Selenium-based visual validation of the Streamlit UI (needs Chrome/Chromedriver). Used by `run_dry_validate.py`.
	- `wallet_releases_rss.py` — RSS/Atom fetcher used by the dashboard; safe to run in CI (uses `feedparser`).
	- `public_flow_intel.py` — public market-flow calculation (calls public KuCoin endpoints).
- Validation runner: `run_dry_validate.py` — starts dry-run bots, runs `agent0_scraper` to capture screenshots and writes `relatorio_bot_<bot_id>.md` and `screenshot_<bot_id>.png`.
- When running scrapers in CI or headless servers:
	- `agent0_scraper.py` requires a browser and chromedriver; prefer running it locally or in containers with Chrome installed.
	- `wallet_releases_rss.py` and `public_flow_intel.py` can be executed in the virtualenv and are safe for automated checks.

## Common SQL queries
Use these snippets when debugging or writing small scripts that inspect the DB.

- Recent logs for a bot (JSON `data` column may contain extra fields):

```sql
SELECT timestamp, level, message, data
FROM bot_logs
WHERE bot_id = ?
ORDER BY timestamp DESC
LIMIT ?;
```

- List active bot sessions (running):

```sql
SELECT id, pid, symbol, mode, entry_price, start_ts
FROM bot_sessions
WHERE status = 'running'
ORDER BY start_ts DESC;
```

- Recent trades for a bot (used by charts):

```sql
SELECT timestamp, profit, bot_id
FROM trades
WHERE bot_id = ?
ORDER BY timestamp DESC
LIMIT ?;
```

- Find trades by order id (dedupe / investigation):

```sql
SELECT * FROM trades WHERE order_id = ?;
```

- Equity snapshots (most recent):

```sql
SELECT timestamp, balance_usdt, btc_price, average_cost
FROM equity_snapshots
ORDER BY timestamp DESC
LIMIT 50;
```
