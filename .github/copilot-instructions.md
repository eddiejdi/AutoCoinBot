# Copilot Instructions — KuCoin App (AutoCoinBot)

> **🤖 Default Agent: `dev-senior`** — Ver [agents.json](agents.json) para configuração de agentes.  
> **📚 Manual de Treinamento:** [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md)

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
## Copilot Instructions — AutoCoinBot (resumo prático)

Objetivo breve: Streamlit UI controla subprocessos de bots que escrevem logs e trades em `trades.db`. A UI consome um terminal HTTP local para render de logs em tempo real.

- Ambiente & quickstart:
  - Ative venv: `source venv/bin/activate` e `pip install -r requirements.txt`.
  - Inicie a UI: `python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true`.
  - Inicie um bot (dry-run recomendado):
    `python -u bot_core.py --bot-id test_dry_1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.1 --funds 0 --dry`

- Arquitetura (arquivos-chave):
  - [streamlit_app.py](streamlit_app.py): entrada da app + persistência `.login_status`.
  - [ui.py](ui.py): lógica de UI, guardas multi-tab/kill-on-start, e render do terminal.
  - [bot_controller.py](bot_controller.py): compõe o comando do subprocess e grava `bot_sessions`.
  - [bot_core.py](bot_core.py) / [bot.py](bot.py): lógica do bot; usa `DatabaseLogger`/[database.py](database.py).
  - [terminal_component.py](terminal_component.py): API HTTP local (padrão ~8765) que serve os logs para o widget.
  - [database.py](database.py): schema + helpers (tabelas: `bot_sessions`, `bot_logs`, `trades`).

- Convenções importantes (não alterar sem checar):
  - Evite `print()` em código comprometido; use `DatabaseLogger` ou `logging` (vários usos em `bot_core.py`).
  - Se alterar flags/args da CLI do bot, atualize simultaneamente `bot_core.py` e `bot_controller.py` (síncrono: builder vs actor).
  - Se mudar o schema, atualize `database.py` e todos os callers que tocam as colunas modificadas.
  - Preserve o formato JSON e os headers CORS em `terminal_component.py` (a UI depende da shape).
  - Multi-tab/kill-on-start: implementado via `ui.py` + flags no DB (prefira persistência DB a estados em memória).

- Integrações e pontos exteriores:
  - DB SQLite: `trades.db` na raiz (ver `database.py`).
  - Terminal API: `http://localhost:8765/api/logs?bot=<bot_id>` usado pela UI.
  - Segredos: `.env` local ou `st.secrets` para `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `TRADES_DB`.

- Comandos úteis e testes:
  - Ver sintaxe: `python -m py_compile <file>.py`.
  - Testes: `./run_tests.sh` (APP_ENV=dev por padrão) ou `pytest`.
  - Selenium/E2E: requer Chrome + chromedriver; use `RUN_SELENIUM=1 ./run_tests.sh`.
  - Inspeção de DB: `scripts/db_inspect.py`.

- Checklist rápido antes de PRs:
  - Alterou CLI do bot? testar dry-run e validar `bot_sessions`/`bot_logs` no DB.
  - Alterou schema? adicionar migração/nota e atualizar `database.py` callers.
  - Alterou terminal API/UI? validar widget e headers CORS.
  - Evite prints; prefira `DatabaseLogger`.

Referências rápidas: [AGENTE_TREINAMENTO.md](AGENTE_TREINAMENTO.md), [agents.json](agents.json), testes em `tests/`, scripts em `scripts/`.

Se quiser, eu posso expandir seções específicas (ex.: schema das tabelas, exemplos de logs em `bot_logs`, ou o fluxo de `bot_controller.start_bot()`).
  - `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
