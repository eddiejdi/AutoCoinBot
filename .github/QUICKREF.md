# AutoCoinBot - Referência Rápida

## 🎯 Arquitetura (1 minuto)

```
streamlit_app.py → ui.py → bot_controller.py → subprocess(bot_core.py → bot.py)
                                ↓                              ↓
                          bot_sessions (DB)            bot_logs/trades (DB)
```

**Stack:** Streamlit + Python + PostgreSQL + KuCoin API

## ⚡ Comandos Essenciais

```bash
# Setup
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Rodar
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true

# Testar bot (dry-run)
python -u bot_core.py --bot-id test1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.1 --dry

# Testes
./run_tests.sh                    # unitários
RUN_SELENIUM=1 ./run_tests.sh     # E2E
python -m py_compile <file>.py    # sintaxe
```

## 🚨 Regras Críticas

1. **Nunca** use `print()` → sempre `DatabaseLogger` ou logging
2. **Sincronize CLI**: `bot_core.py` ↔ `bot_controller.py` (flags)
3. **Widgets Streamlit**: Use `st.session_state` **OU** `value=`, nunca ambos
4. **URLs**: Relativas em prod, `127.0.0.1` local (detectar com `FLY_APP_NAME`)
5. **Não altere** blocos marcados "🔒 HOMOLOGADO" em ui.py

## 📁 Arquivos Core

| Arquivo | Função |
|---------|--------|
| `streamlit_app.py` | Entry point + auth |
| `ui.py` | Interface (🔒 cuidado!) |
| `bot_controller.py` | Spawn subprocessos |
| `bot_core.py` | CLI do bot |
| `bot.py` | Estratégias de trading |
| `database.py` | Schema PostgreSQL |
| `api.py` | KuCoin REST API |
| `terminal_component.py` | HTTP API local :8765 |

## 🔧 Troubleshooting Rápido

### Bot não aparece no dashboard
```bash
# Verificar DB
psql "$DATABASE_URL" -c "SELECT * FROM bot_sessions WHERE status='running'"
python scripts/db_inspect.py
```

### Selenium no WSL não acessa localhost Windows
```bash
# Rodar Streamlit no WSL também
wsl -d Ubuntu -e bash -c "cd ~/AutoCoinBot && source venv/bin/activate && python -m streamlit run streamlit_app.py"
```

### Gráficos de aprendizado vazios
```bash
# Verificar tabelas
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM learning_stats;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM learning_history;"
```

### Frontend quebrado
```bash
python -m py_compile ui.py
python -m py_compile streamlit_app.py
# F12 no browser → Console
```

### Copilot "Response contained no choices"
1. **Reduza o prompt** (1 arquivo, sem anexos grandes)
2. **Reload Window** + reautenticar GitHub
3. **Reset Chat** no Copilot
4. Ver Output → "GitHub Copilot Chat" (401/403=auth, 429=aguardar, 5xx=instabilidade)
5. Dev Container: `Rebuild and Reopen in Container`

## 📊 Database (PostgreSQL)

**Tabelas principais:**
- `bot_sessions` - Sessões (id, status, PID, config)
- `bot_logs` - Logs em tempo real
- `trades` - Histórico de trades
- `learning_stats` - ML bandit learning
- `learning_history` - Histórico de rewards

## 🌐 API HTTP Local (:8765)

**Endpoints:**
- `GET /api/logs?bot=<id>&limit=30`
- `GET /api/trades?bot=<id>&only_real=1`
- `GET /api/bot?bot=<id>`
- `GET /api/equity/history`
- `POST /api/start` (body: config)
- `POST /api/stop` (body: {bot_id})

**HTML:**
- `/monitor` - Terminal live
- `/report` - Relatório de trades

## ✅ Checklist Alterações

### bot_core.py ou bot_controller.py
- [ ] Sincronizar flags CLI em ambos
- [ ] Testar dry-run
- [ ] Verificar `bot_sessions` no DB

### database.py
- [ ] Atualizar todos os callers
- [ ] Documentar mudanças de schema
- [ ] `python -m py_compile database.py`

### ui.py
- [ ] `python -m py_compile ui.py`
- [ ] Testar navegação por tabs
- [ ] Validar com scraper

### API/KuCoin
- [ ] Testar em dry-run primeiro
- [ ] Verificar rate limits (30 req/3s)
- [ ] Validar tratamento de erros

## 🔐 Segurança

1. Nunca commitar credenciais (use `.env` ou `st.secrets`)
2. Sempre testar em dry-run antes de trades reais
3. Validar entradas do usuário
4. Logar operações críticas via DatabaseLogger
5. Backup DB antes de migrações

## 📚 Docs Completos

- [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md) - Manual completo
- [.github/copilot-instructions.md](copilot-instructions.md) - Instruções IA
- [README.md](../README.md) - Visão geral
- [DEPLOY.md](../DEPLOY.md) - Deploy

---
**Versão:** 2.0.0 | **Data:** Jan 2026
