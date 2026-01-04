# 🔒 AutoCoinBot - Base de Conhecimento Compacta

> **Propósito**: Referência rápida para IA. Economiza tokens ao evitar carregar arquivos completos.
> **Última atualização**: 2026-01-03

---

## 🚫 BLOCOS HOMOLOGADOS (NÃO MEXER)

| Arquivo | Função/Bloco | Razão |
|---------|--------------|-------|
| `ui.py` | `render_top_nav_bar()` | Navegação estável, testada |
| `ui.py` | `render_cobol_gauge_static()` | Gauges COBOL funcionando |
| `ui.py` | `render_mario_gauge()` | Tema SMW completo |
| `ui.py` | `inject_global_css()` | CSS responsivo validado |
| `database.py` | Schema completo (todas tabelas) | Migrations complexas |
| `api.py` | `_build_headers()` | Auth KuCoin V1/V2 |
| `api.py` | `_sync_time_offset()` | Sincronização de tempo crítica |
| `terminal_component.py` | `APIHandler` classe inteira | CORS + rotas HTTP funcionais |
| `bot.py` | `EnhancedTradeBot.__init__()` | Inicialização complexa |
| `bot.py` | `_record_trade()` | Registro de trades + learning |

---

## ✅ PADRÕES OBRIGATÓRIOS

### Logging
```python
# ✅ CORRETO
from database import DatabaseManager
logger = DatabaseLogger(db, bot_id)
logger.info("mensagem")

# ❌ ERRADO
print("debug")  # Nunca em produção
```

### Widgets Streamlit
```python
# ✅ CORRETO - usar UM dos dois
st.session_state["key"] = valor  # OU
st.number_input(..., value=valor, key="key")

# ❌ ERRADO - causa "loading eterno"
st.session_state["key"] = valor
st.number_input(..., value=outro_valor, key="key")  # Conflito!
```

### CLI Bot (manter sincronizado)
```
bot_core.py  --flag    ←→    bot_controller.py  cmd.append("--flag")
```

### URLs Produção vs Local
```python
is_production = bool(os.environ.get("FLY_APP_NAME"))
base_url = "" if is_production else f"http://127.0.0.1:{port}"
```

---

## 🗄️ SCHEMA DO BANCO (PostgreSQL)

| Tabela | Colunas Principais | Índices |
|--------|-------------------|---------|
| `bot_sessions` | id, pid, symbol, status, entry_price, dry_run, start_ts, end_ts | status |
| `bot_logs` | id, bot_id, timestamp, level, message | bot_id, timestamp |
| `trades` | id, symbol, side, price, size, profit, dry_run, order_id, bot_id | timestamp, symbol, bot_id |
| `learning_stats` | symbol, param_name, param_value, mean_reward, n | (symbol, param_name, param_value) PK |
| `learning_history` | id, symbol, param_name, param_value, reward, timestamp | symbol+param, timestamp |
| `equity_snapshots` | id, timestamp, balance_usdt, btc_price, average_cost | timestamp |
| `eternal_runs` | id, bot_id, run_number, entry_price, exit_price, profit_pct | bot_id |

---

## 🐛 ERROS CONHECIDOS E SOLUÇÕES

| Sintoma | Causa Raiz | Solução |
|---------|-----------|---------|
| "Loading eterno" na UI | `session_state` + `value=` no mesmo widget | Usar apenas um método |
| Bot não aparece na lista | PID morto, status ainda "running" | `cleanup_dead_bots.py` ou verificar `_pid_alive()` |
| Preço = 0 no bot | `entry` não setado | Fallback automático em `bot_core.py` (busca preço atual) |
| Erro 401 KuCoin | Timestamp dessincronizado | `_sync_time_offset()` já implementado |
| Gráficos learning vazios | Tabelas sem dados | Rodar bots até gerar SELLs |
| Selenium não conecta (WSL) | localhost Windows ≠ WSL | Rodar Streamlit dentro do WSL |
| "below minimum size" | Ordem muito pequena | Usar `_carryover_fraction` (já implementado) |

---

## 🔄 FLUXOS PRINCIPAIS

### Iniciar Bot
```
UI form → BotController.start_bot() → subprocess(bot_core.py) 
→ insert_bot_session(DB) → bot.run() → logs/trades em DB
```

### Terminal Logs (tempo real)
```
UI iframe → fetch /api/logs?bot=X → terminal_component.py 
→ DatabaseManager.get_bot_logs() → JSON
```

### Learning (Bandit)
```
bot.py SELL → profit_pct → update_bandit_reward() 
→ learning_stats atualizado → próximo bot usa choose_bandit_param()
```

---

## 🧪 COMANDOS DE TESTE

```bash
# Sintaxe
python -m py_compile arquivo.py

# Testes unitários
pytest tests/

# Testes E2E
RUN_SELENIUM=1 ./run_tests.sh

# Validação visual
python agent0_scraper.py --local --test-dashboard

# Bot dry-run
python -u bot_core.py --bot-id test --symbol BTC-USDT --entry 90000 --targets "2:0.3" --interval 5 --size 0.001 --funds 0 --dry
```

---

## 📁 ESTRUTURA DE ARQUIVOS CHAVE

```
streamlit_app.py    → Entry point, login
ui.py               → UI completa, temas, gauges
bot_controller.py   → Start/stop subprocessos
bot_core.py         → CLI do bot, DatabaseLogger
bot.py              → EnhancedTradeBot, estratégias
database.py         → Schema, CRUD, learning
api.py              → KuCoin REST API
terminal_component.py → HTTP server para logs
sidebar_controller.py → Inputs da sidebar
```

---

## 🔐 SECRETS NECESSÁRIOS

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `API_KEY` | ✅ | KuCoin API Key |
| `API_SECRET` | ✅ | KuCoin API Secret |
| `API_PASSPHRASE` | ✅ | KuCoin Passphrase |
| `KUCOIN_BASE` | ❌ | Default: `https://api.kucoin.com` |
| `TRADES_DB` | ❌ | Default: `trades.db` |
| `FLY_APP_NAME` | ❌ | Detecta ambiente Fly.io |

---

## ✍️ CHECKLIST PRÉ-COMMIT

- [ ] `python -m py_compile` nos arquivos alterados
- [ ] Se alterou CLI: sincronizar `bot_core.py` ↔ `bot_controller.py`
- [ ] Se alterou schema: atualizar callers em `database.py`
- [ ] Se alterou UI: testar navegação + verificar não quebrou themes
- [ ] Se alterou API: testar em dry-run primeiro
- [ ] Não mexeu em blocos HOMOLOGADOS sem autorização
