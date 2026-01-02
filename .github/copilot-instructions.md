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

## 🔍 Metodologia de correção de bugs

### SEMPRE pesquisar histórico Git antes de implementar
Antes de construir uma solução do zero, **procure uma versão funcional no histórico Git**:

```bash
# 1. Buscar commits que alteraram arquivo específico
git log --oneline -20 -- ui.py

# 2. Ver TODAS as alterações de um padrão no histórico
git log --all -p -- ui.py | grep -A5 -B5 "report_url"

# 3. Buscar em todo o projeto por padrão (atual + histórico)
git log --all -p | grep -B10 "window.location.hostname"

# 4. Ver estado de um arquivo em commit específico
git show abc1234:ui.py | head -100

# 5. Comparar versão atual com versão funcional
git diff abc1234 HEAD -- ui.py
```

**Por quê?** O projeto pode já ter resolvido o problema antes, ou ter padrões funcionais em outros arquivos que podem ser reutilizados.

### 7. URLs dinâmicas para produção vs local
Em produção (Fly.io), usar URLs relativas. Detectar via `FLY_APP_NAME`:
```python
# ui.py - padrão para URLs de iframe/links
is_production = bool(os.environ.get("FLY_APP_NAME"))
if is_production:
    base_url = ""  # URLs relativas
    home_url = "/?view=dashboard"
else:
    base_url = f"http://127.0.0.1:{api_port}"
    home_url = f"http://127.0.0.1:{st_port}/?view=dashboard"
```

## Checklist antes de PRs

- [ ] Alterou CLI? → sincronizar `bot_core.py` ↔ `bot_controller.py`
- [ ] Alterou schema? → atualizar `database.py` e todos os callers
- [ ] Alterou API HTTP? → preservar JSON shape e headers CORS
- [ ] Adicionou prints? → substituir por `DatabaseLogger`
- [ ] Alterou UI? → `python -m py_compile ui.py` e testar navegação

## ⚠️ Workflow Git obrigatório (conflitos e CI)

### Antes de criar PR
```bash
# 1. Sempre sincronizar com main antes de push
git fetch origin main
git merge origin/main

# 2. Se houver conflitos, resolver manualmente:
git status  # ver arquivos com conflito (UU)
# Editar arquivos, remover marcadores <<<<< ===== >>>>>
git add <arquivo>
git commit -m "merge: resolve conflicts with main"

# 3. Verificar sintaxe dos arquivos modificados
python -m py_compile <arquivo>.py
```

### Após criar PR - SEMPRE verificar CI
1. Acessar link do PR no GitHub
2. Verificar aba "Checks" ou "Actions"
3. Se CI falhar:
   ```bash
   # Ver logs do erro no GitHub Actions
   # Corrigir localmente
   git add . && git commit -m "fix: corrigir erro do CI"
   git push
   ```
4. Repetir até CI passar ✅

### Erros comuns de CI e soluções
| Erro | Solução |
|------|---------|
| `ModuleNotFoundError` | Adicionar ao `requirements.txt` |
| `SyntaxError` | `python -m py_compile <file>.py` |
| `Merge conflict` | `git fetch origin main && git merge origin/main` |
| `pytest failed` | Rodar `./run_tests.sh` localmente |
| `ChromeDriver version` | Usar `selenium_helper.py` com webdriver_manager |

### Comandos úteis para debug de CI
```bash
# Simular CI localmente
pip install -r requirements.txt
python -m py_compile *.py
./run_tests.sh

# Ver diferenças com main
git diff origin/main --stat

# Ver commits pendentes
git log origin/main..HEAD --oneline
```

## Secrets

`.env` ou `st.secrets`: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `KUCOIN_BASE`, `TRADES_DB`
