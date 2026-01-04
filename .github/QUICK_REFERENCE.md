# 🚀 Referência Rápida - AutoCoinBot

**Versão:** 2.0.0 | **Atualizado:** Jan 2026

## Stack
Python 3.11+ | Streamlit | PostgreSQL | KuCoin API | Selenium

## Arquivos-Chave
- `streamlit_app.py` - Entry point
- `ui.py` - Interface e lógica UI
- `bot_controller.py` - Gerencia subprocessos
- `bot_core.py` - Lógica do bot
- `bot.py` - Classe Bot + estratégias
- `database.py` - PostgreSQL (psycopg)
- `api.py` - KuCoin API
- `terminal_component.py` - API HTTP para terminal

## Comandos Essenciais

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Executar
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true

# Bot dry-run
python -u bot_core.py --bot-id test1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.001 --dry

# Testes
python -m py_compile <arquivo>.py  # Sintaxe
pytest tests/                       # Unitários
RUN_SELENIUM=1 ./run_tests.sh      # E2E
```

## Padrões Críticos

### 1. CLI Sincronizado (bot_core.py + bot_controller.py)
```python
# Se alterar flags em bot_core.py, atualizar bot_controller.py
parser.add_argument("--eternal", action="store_true")  # bot_core.py
if eternal_mode: cmd.append("--eternal")               # bot_controller.py
```

### 2. Logging (NUNCA use print())
```python
from database import DatabaseLogger
logger = DatabaseLogger(db_manager, bot_id)
logger.info("mensagem")  # Grava em bot_logs (PostgreSQL)
```

### 3. Database Schema (PostgreSQL)
- `bot_sessions` - Sessões (id, status, PID, config)
- `bot_logs` - Logs em tempo real
- `trades` - Histórico de trades
- `learning_stats` - ML stats
- `learning_history` - ML histórico

### 4. Widgets Streamlit (CRÍTICO - evita travamento)
```python
# ❌ ERRADO - causa travamento
st.session_state["var"] = val
st.number_input(..., value=val, key="var")

# ✅ CORRETO - session_state OU value, nunca ambos
st.session_state["var"] = val
st.number_input(..., key="var")  # SEM value=
```

## Troubleshooting Rápido

### Copilot: "Response contained no choices"
1. **Prompt pequeno** - Max 1 arquivo/trecho, sem anexos grandes
2. **Reload Window** - Developer: Reload Window
3. **Reautenticar** - View → Command Palette → "Sign Out" → "Sign In"
4. **Reset Chat** - Botão no topo do chat
5. **Verificar Output** - View → Output → "GitHub Copilot Chat"

### Bots não aparecem
```bash
psql "$DATABASE_URL" -c "SELECT * FROM bot_sessions WHERE status='running'"
python scripts/db_inspect.py
```

### Selenium no WSL
```bash
# Streamlit deve rodar no WSL também
wsl -d Ubuntu -e bash -c "cd ~/AutoCoinBot && source venv/bin/activate && streamlit run streamlit_app.py"
```

## Checklist PRÉ-COMMIT

- [ ] `python -m py_compile <arquivo>.py`
- [ ] Se alterou `bot_core.py` ou `bot_controller.py` → sync CLI args
- [ ] Se alterou `database.py` → atualizar callers
- [ ] Se alterou `ui.py` → testar navegação por tabs
- [ ] `git commit -m "feat(escopo): descrição"`

## Variáveis de Ambiente (.env)
```bash
APP_ENV=dev
DATABASE_URL=postgresql://user:pass@host:5432/autocoinbot
API_KEY=...
API_SECRET=...
API_PASSPHRASE=...
```

## Testes Selenium
```bash
python agent0_scraper.py --local --test-all       # Todos
python agent0_scraper.py --local --test-dashboard # Dashboard
python agent0_scraper.py --local --test-bot-start # Start bot
```

## URLs Produção vs Local
```python
is_production = bool(os.environ.get("FLY_APP_NAME"))
base_url = "" if is_production else f"http://127.0.0.1:{port}"
```

## Docs Completas
- `.github/copilot-instructions.md` - Instruções detalhadas
- `AGENTE_TREINAMENTO.md` - Manual completo
- `README.md` - Documentação geral
