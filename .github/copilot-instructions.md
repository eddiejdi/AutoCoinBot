# Copilot Instructions — AutoCoinBot

> KuCoin trading bot com Streamlit UI e PostgreSQL.

## ⚠️ Regras Críticas

### 1. Estrutura Modular
**TODO código vive em `autocoinbot/`** — arquivos na raiz são shims de compatibilidade.
```python
# ✅ SEMPRE edite autocoinbot/*.py  |  ❌ NUNCA edite shims da raiz
```

### 2. Streamlit: Evitar Freeze
```python
# ❌ FREEZE: st.session_state["key"] = x; st.widget(..., value=x, key="key")
# ✅ CORRETO: st.widget(..., key="key")  # sem value=
```

### 3. CLI Sincronizado
Alterar flags CLI? → Atualizar **ambos**: `autocoinbot/bot_core.py` (argparse) e `autocoinbot/bot_controller.py` (builder)

### 4. Logging
```python
# ❌ print()  →  ✅ DatabaseLogger(db, bot_id).info("msg")
```

### 5. URLs Dinâmicas (Prod vs Local)
```python
is_prod = bool(os.environ.get("FLY_APP_NAME"))
url = "/api/logs" if is_prod else "http://127.0.0.1:8765/api/logs"
```

## 🏗️ Arquitetura

```
UI (autocoinbot/ui.py) → BotController (subprocess) → bot_core.py → PostgreSQL
                                                    ↓
                         terminal_component.py (HTTP API :8765) ← nginx proxy em prod
```

**Arquivos-chave:**
| Arquivo | Responsabilidade |
|---------|-----------------|
| `ui.py` | Interface Streamlit |
| `bot_controller.py` | Spawner de subprocessos |
| `bot_core.py` | Lógica de trading (argparse) |
| `database.py` | Schema PostgreSQL (psycopg) |
| `terminal_component.py` | API HTTP :8765 |

## 🚀 Comandos

```bash
source venv/bin/activate && pip install -r requirements.txt
python -m streamlit run autocoinbot/streamlit_app.py --server.port=8501 --server.headless=true
python -u autocoinbot/bot_core.py --bot-id test1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --dry
./run_tests.sh  # unitários  |  RUN_SELENIUM=1 ./run_tests.sh  # E2E
```

## 📋 Checklist PRs

- [ ] CLI alterado? → Sincronizar bot_core.py + bot_controller.py
- [ ] UI alterado? → Testar session_state (evitar freeze)
- [ ] Adicionou print()? → Usar DatabaseLogger
- [ ] Validar sintaxe: `python -m py_compile <file>.py`

## 🔗 Referências

- [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md) — Manual completo com troubleshooting
- API HTTP: `/api/logs`, `/api/trades`, `/api/bot`, `/monitor`, `/report`
- Secrets (`.env`): `DATABASE_URL`, `API_KEY`, `API_SECRET`, `API_PASSPHRASE`

## 📊 Schema DB

| Tabela | Colunas-chave |
|--------|---------------|
| `bot_sessions` | id, pid, symbol, status, entry_price, dry_run |
| `bot_logs` | bot_id, timestamp (float!), level, message (JSON) |
| `trades` | symbol, side, price, profit, dry_run, order_id |
| `learning_stats` | symbol, param_name, param_value, mean_reward |
