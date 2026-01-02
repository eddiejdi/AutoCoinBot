# Copilot Instructions — AutoCoinBot

Streamlit UI que gerencia subprocessos de trading bots. Logs e trades são persistidos em SQLite (`trades.db`). UI consome API HTTP local (porta 8765) para logs em tempo real.

## Arquitetura (fluxo de dados)

```
streamlit_app.py → ui.py → bot_controller.py → subprocess(bot_core.py)
                              ↓                        ↓
                        bot_sessions (DB)        bot_logs/trades (DB)
                                                       ↑
                              terminal_component.py ←──┘ (HTTP API :8765)
```

**Arquivos-chave:**
- `bot_controller.py` — monta comando CLI e grava `bot_sessions`
- `bot_core.py` / `bot.py` (`EnhancedTradeBot`) — lógica de trading, modos: `sell`, `buy`, `mixed`, `flow`
- `database.py` — schema SQLite: `bot_sessions`, `bot_logs`, `trades`, `learning_stats`, `eternal_runs`
- `terminal_component.py` — API HTTP (`/api/logs`, `/api/trades`, `/monitor`, `/report`)
- `ui_components/` — módulos: `utils.py`, `theme.py`, `navigation.py`, `gauges.py`, `terminal.py`, `dashboard.py`

## Comandos essenciais

```bash
# Ativar venv (obrigatório)
source venv/bin/activate

# Streamlit
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true

# Bot dry-run (recomendado para testes)
python -u bot_core.py --bot-id test_1 --symbol BTC-USDT --entry 90000 --targets "2:0.3,5:0.5" --interval 5 --size 0.001 --funds 0 --dry

# Bot eternal mode (reinicia após cada target)
python -u bot_core.py --bot-id eternal_1 --symbol BTC-USDT --entry 90000 --targets "2:1" --eternal --dry

# Testes
./run_tests.sh                    # pytest (exclui Selenium)
RUN_SELENIUM=1 ./run_tests.sh     # inclui testes visuais
python -m py_compile <file>.py    # verificar sintaxe

# Docker
docker-compose up -d              # subir containers (streamlit + api)
docker-compose logs -f            # ver logs
docker-compose down               # parar
```

## Padrões críticos do projeto

### 1. CLI do bot sincronizado
Se alterar flags em `bot_core.py` (argparse), **atualizar também** `bot_controller.py` (builder do comando):
```python
# bot_core.py: --eternal flag
parser.add_argument("--eternal", action="store_true")
# bot_controller.py: deve adicionar ao cmd[]
if eternal_mode:
    cmd.append("--eternal")
```

### 2. ⚠️ UI NÃO TRAVAR (ui.py + sidebar_controller.py)
**CRÍTICO**: Alterações em `ui.py` podem causar "loading eterno". Regras:
```python
# ❌ ERRADO - causa warning e possível travamento
st.session_state["target_profit_pct"] = 2.0  # em ui.py
st.number_input(..., value=2.0, key="target_profit_pct")  # em sidebar_controller.py

# ✅ CORRETO - session_state OU value, nunca ambos
st.session_state["target_profit_pct"] = 2.0  # em ui.py
st.number_input(..., key="target_profit_pct")  # SEM value= no widget
```
**Antes de alterar ui.py**: `git checkout main -- ui.py` para restaurar versão estável.

### 3. Logging via DatabaseLogger (não use `print()`)
```python
# bot_core.py
from database import DatabaseManager
logger = DatabaseLogger(db_manager, bot_id)
logger.info("mensagem")  # grava em bot_logs
```

### 4. Targets com custos de trading
`bot.py` ajusta targets para compensar taxas (~0.25%):
```python
self._total_trading_cost_pct = self._buy_fee_pct + self._sell_fee_pct + self._slippage_pct
# Target 2% → preço precisa subir 2.25% para lucro líquido de 2%
```

### 4. Bandit learning para parâmetros
`database.py` implementa epsilon-greedy para auto-tuning com recompensa/penalização:
```python
# Escolher parâmetro (25% exploração, 75% greedy)
db.choose_bandit_param(symbol, "take_profit_trailing_pct", candidates=[0.2, 0.5, 1.0], epsilon=0.25)

# Atualizar reward após SELL (profit_pct positivo = recompensa, negativo = penalização)
db.update_bandit_reward(symbol, param_name, param_value, reward=profit_pct)

# Stop-loss gera penalização extra (profit * 1.5) para evitar configurações ruins
# Consultar melhor parâmetro aprendido
db.get_best_learned_param(symbol, "take_profit_trailing_pct")  # retorna {value, mean_reward, n}
db.get_learning_summary(symbol)  # resumo geral com positive/negative rewards
```

### 5. Selenium com webdriver_manager
Use `selenium_helper.py` para configuração automática:
```python
from selenium_helper import get_chrome_driver
driver = get_chrome_driver(headless=True)
```

### 6. Eternal Mode (reinício automático)
Flag `--eternal` faz o bot reiniciar automaticamente após atingir todos os targets:
```python
# bot_core.py detecta flag
if args.eternal:
    # Após completar targets, registra ciclo em eternal_runs e reinicia
    db.add_eternal_run(bot_id, run_number, symbol, entry_price, total_targets)
    # ... executa ciclo ...
    db.complete_eternal_run(run_id, exit_price, profit_pct, profit_usdt, targets_hit)
    # Loop infinito: bot não para até SIGTERM
```

## Schema DB (tabelas principais)

| Tabela | Colunas-chave |
|--------|---------------|
| `bot_sessions` | id, pid, symbol, status, entry_price, dry_run |
| `bot_logs` | bot_id, timestamp, level, message |
| `trades` | symbol, side, price, size, profit, dry_run, order_id |
| `learning_stats` | symbol, param_name, param_value, mean_reward, n |
| `eternal_runs` | bot_id, run_number, entry_price, exit_price, profit_pct, status |

## Checklist antes de PRs

- [ ] Alterou CLI? → sincronizar `bot_core.py` ↔ `bot_controller.py`
- [ ] Alterou schema? → atualizar `database.py` e todos os callers
- [ ] Alterou API HTTP? → preservar JSON shape e headers CORS
- [ ] Adicionou prints? → substituir por `DatabaseLogger`
- [ ] Alterou UI? → `python -m py_compile ui.py` e testar navegação

## Secrets

`.env` ou `st.secrets`: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `KUCOIN_BASE`, `TRADES_DB`

## 📝 Lições Aprendidas

### 2026-01-02: Scripts de debug não devem ter prefixo test_
- **Problema**: pytest coletava arquivos `test_imports.py`, `test_validation_debug.py` que são scripts de debug, não testes
- **Causa**: Arquivos com prefixo `test_` são coletados automaticamente pelo pytest
- **Solução**: Renomear para `debug_*.py`: `debug_imports.py`, `debug_validation.py`, `debug_loading_check.py`
- **Arquivos**: Scripts de debug na raiz do projeto
- **Regra**: Nunca criar arquivos de debug com prefixo `test_`, usar `debug_` ou `check_`
