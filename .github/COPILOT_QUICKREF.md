# 🤖 Copilot - Referência Compacta

> **Para IA/Agentes:** Este é o guia mínimo. Para detalhes, ver `.github/copilot-instructions.md`

## 🎯 Arquitetura Resumida

```
streamlit_app.py (entry) → ui.py (interface) → bot_controller.py (spawner)
   ↓
subprocess: bot_core.py → bot.py (trading logic)
   ↓
database.py (PostgreSQL) + api.py (KuCoin)
   ↑
terminal_component.py (HTTP API :8765 para logs/trades)
```

## ⚡ Comandos Críticos

```bash
# Iniciar app
python -m streamlit run streamlit_app.py

# Bot dry-run
python bot_core.py --bot-id test1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --dry

# Validar sintaxe
python -m py_compile <file>.py

# Testes
./run_tests.sh
RUN_SELENIUM=1 ./run_tests.sh
```

## 🔒 Regras Invioláveis

1. **Nunca use `print()`** → Use `DatabaseLogger(db, bot_id).info(msg)`
2. **CLI sync obrigatório** → `bot_core.py` args ↔ `bot_controller.py` flags
3. **UI crítica** → Não alterar `ui.py` sem `python -m py_compile ui.py`
4. **Streamlit widgets** → NUNCA usar `st.session_state[key]` + `value=` juntos
5. **Sempre dry-run** → Testar com `--dry` antes de real

## 📊 Banco (PostgreSQL)

```sql
bot_sessions  -- Sessões ativas (id, pid, status, entry_price, ...)
bot_logs      -- Logs JSON (bot_id, timestamp, level, message)
trades        -- Histórico (symbol, side, price, size, profit, ...)
learning_*    -- ML bandit (stats, history)
```

## 🐛 Debug Rápido

| Erro | Fix |
|------|-----|
| Bots não aparecem | `SELECT * FROM bot_sessions WHERE status='running'` |
| UI não carrega | `python -m py_compile ui.py` + F12 console |
| Selenium falha (WSL) | Rodar Streamlit no WSL também |
| "No choices" Copilot | Reload Window + reautenticar + prompt menor |

## 🔗 Endpoints HTTP (terminal_component.py)

```
GET  /api/logs?bot=<id>&limit=30        # Logs do bot
GET  /api/trades?bot=<id>&only_real=1   # Trades
GET  /api/bot?bot=<id>                  # Info da sessão
POST /api/start                         # Iniciar bot
POST /api/stop                          # Parar bot
GET  /monitor                           # HTML monitor
GET  /report                            # HTML relatório
```

## 📝 Formato de Commit

```bash
git commit -m "feat(bot): adiciona stop-loss dinâmico"
git commit -m "fix(ui): corrige renderização terminal"
git commit -m "docs: atualiza quick reference"
```

## 🧪 Validação

```bash
# Completa
python agent0_scraper.py --local --test-all

# Individual
python agent0_scraper.py --local --test-dashboard
python agent0_scraper.py --local --test-bot-start
```

## 📚 Docs Detalhadas

- **Treinamento completo:** `AGENTE_TREINAMENTO.md`
- **Instruções Copilot:** `.github/copilot-instructions.md`
- **Referência rápida:** `.github/QUICK_REFERENCE.md`

---

**Última atualização:** 04/01/2026
