# Copilot Instructions — AutoCoinBot

Guia conciso para agentes IA (TL;DR)
- Objetivo: Streamlit orquestra bots KuCoin; subprocessos registram tudo em SQLite. A UI lê logs via API HTTP local (porta 8765) para monitor/relatório.
- Arquitetura (fluxo principal): [streamlit_app.py](streamlit_app.py) → [ui.py](ui.py) → [bot_controller.py](bot_controller.py) → subprocesso [bot_core.py](bot_core.py) → lógica em [bot.py](bot.py) e persistência em [database.py](database.py). Logs/relatórios servidos por [terminal_component.py](terminal_component.py) (rotas /api, /monitor, /report).
- Padrões críticos (podem travar/romper):
    - Sincronize flags CLI entre `bot_core.py` (argparse) e `BotController.start_bot()` em [bot_controller.py](bot_controller.py).
    - Em Streamlit, use `st.session_state` OU `value=` nos widgets, nunca ambos; evite travar a UI (regra documentada em [ui.py](ui.py)).
    - Use `DatabaseLogger` em vez de `print()` (logs vão para bot_logs via [database.py](database.py)).
    - URLs dinâmicas: em produção (Fly.io, env FLY_APP_NAME) use URLs relativas; localmente use `http://127.0.0.1:<porta>` (ver detecção em [ui.py](ui.py), [monitor_window.html](monitor_window.html), [report_window.html](report_window.html)).
- Fluxos de trabalho do dev:
    - Ambiente: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`.
    - UI: `python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true`.
    - Bot dry-run: `python -u bot_core.py --bot-id test_1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.1 --funds 0 --dry`.
    - Testes: `./run_tests.sh` (use `RUN_SELENIUM=1` para E2E); validação: `python -m py_compile <file>.py`.
- Integrações/depêndencias:
    - KuCoin REST em [api.py](api.py); checagem de credenciais via `'_has_keys'`. Para UI, prefira `get_price_fast()`/timeouts curtos.
    - Selenium headless por [selenium_helper.py](selenium_helper.py); use Xvfb/pyvirtualdisplay em CI quando necessário.
- Dados e contratos (SQLite):
    - Tabelas principais: bot_sessions, bot_logs (JSON em `message`, `timestamp` float), trades, learning_stats/history, eternal_runs. Métodos em `DatabaseManager` ([database.py](database.py)).
    - "Último Evento" na UI: extraia `event` do JSON de `message`; formate `timestamp` float → string (exemplo em [ui.py](ui.py)).
- Monitor/Relatório:
    - `start_api_server()` em [terminal_component.py](terminal_component.py) inicia a API (8765). UI embute iframes com URLs relativas em produção e `window.location.origin` nos HTMLs.
    - Botões Log/Report abrem em nova aba via HTML custom (não `st.link_button`); blocos 🔒 não modificar.
- Convenções do bot:
    - `EnhancedTradeBot` ([bot.py](bot.py)) compensa taxas nos targets e faz trailing após target; bandit learning via `choose_bandit_param`/`update_bandit_reward` ([database.py](database.py)).
    - Modo `--eternal` registra ciclos em `eternal_runs` e reinicia automaticamente.
- Evite:
    - Alterar blocos "🔒 HOMOLOGADO" sem aprovação.
    - Hardcode de `127.0.0.1` em produção; respeite `FLY_APP_NAME`.
    - `print()` em caminhos críticos; prefira logger/DB.
- Pontos de entrada úteis:
    - Start/stop via API: POST `/api/start` e `/api/stop` em [terminal_component.py](terminal_component.py).
    - UI principal: `render_bot_control()` em [ui.py](ui.py) e navegação por query `view=dashboard|monitor|report`.
    - Mais detalhes: [AGENTE_TREINAMENTO.md](AGENTE_TREINAMENTO.md).

Falha do Copilot Chat (Response contained no choices) — fallback rápido
- Reduza o prompt e remova anexos grandes; tente novamente.
- Reload VS Code: Command Palette → Developer: Reload Window.
- Reautentique: sair/entrar GitHub (Accounts) e atualize “GitHub Copilot” e “GitHub Copilot Chat”.
- Reset Chat: Command Palette → Copilot Chat: Reset Chat.
- Ver logs: View → Output → “GitHub Copilot Chat” (401/403 reautenticar; 429 aguardar; 5xx serviço instável).
- Em Dev Container/WSL: “Dev Containers: Rebuild and Reopen in Container”.

Streamlit UI que gerencia subprocessos de trading bots. Logs e trades são persistidos em SQLite (`trades.db`). UI consome API HTTP local (porta 8765) para logs em tempo real.

## 🔒 BLOCOS HOMOLOGADOS - NÃO ALTERAR

**CRÍTICO**: Blocos marcados com `# 🔒 HOMOLOGADO` são código **validado e funcional**.

### Regras para blocos homologados:
1. **NÃO ALTERAR** sem aprovação explícita do usuário
2. **NÃO REFATORAR** mesmo que pareça "melhorável"
3. **NÃO MOVER** para outros arquivos/módulos
4. **PULAR** durante análise de código (economia de tokens)

### Formato dos marcadores:
```python
# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║  🔒 HOMOLOGADO: <descrição curta>                                             ║
# ║  Data: YYYY-MM-DD | Sessão: <identificador>                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
<código homologado>
# 🔒 FIM HOMOLOGADO
```

### Lista de blocos homologados:
| Arquivo | Linha | Descrição |
|---------|-------|-----------|
| `ui.py` | ~5408 | Botões Log/Report com HTML target="_blank" |
| `ui.py` | ~5398 | Detecção FLY_APP_NAME para URLs dinâmicas |
| `ui.py` | ~5551 | Botões Log/Report em sessões encerradas |
| `selenium_helper.py` | todo | Configuração Chrome/Chromium para containers |
| `selenium_validate_all.py` | todo | Script de validação completo |

### Como adicionar novo bloco homologado:
1. Usuário aprova o código: "homologue este bloco"
2. Adicionar marcadores no código
3. Atualizar tabela acima
4. Commit: `git commit -m "lock: homologar <descrição>"`


## 🧠 REGRA DE APRENDIZADO CONTÍNUO

**OBRIGATÓRIO**: Toda vez que for feito um **commit** ou **checkpoint**, executar a rotina de aprendizado:

1. **Identificar lições aprendidas** na sessão atual:
   - Bugs corrigidos e suas causas raiz
   - Padrões que funcionaram vs não funcionaram
   - Erros de CI/CD e soluções
   - Peculiaridades do ambiente (container, produção, etc)

2. **Atualizar este documento** (`copilot-instructions.md`):
   - Adicionar na seção "📝 Lições Aprendidas" com data
   - Criar nova seção se o tópico for recorrente/importante
   - Incluir código de exemplo quando relevante

3. **Formato da entrada**:
   ```markdown
   ### YYYY-MM-DD: Título curto do problema
   - **Problema**: Descrição do que aconteceu
   - **Causa**: Por que aconteceu
   - **Solução**: Como foi resolvido
   - **Arquivos**: Quais arquivos foram afetados
   ```

4. **Commit junto com as alterações**:
   ```bash
   git add .github/copilot-instructions.md
   git commit -m "docs: atualizar treinamento com lições da sessão"
   ```

**Por quê?** Isso garante que o conhecimento adquirido seja persistido e reutilizado em sessões futuras, evitando repetir os mesmos erros.


## Arquitetura (fluxo de dados)

```
streamlit_app.py → ui.py → bot_controller.py → subprocess(bot_core.py)
                              ↓                        ↓
                        bot_sessions (DB)        bot_logs/trades (DB)
                                                       ↑
                              terminal_component.py ←──┘ (HTTP API :8765)
```

### Arquitetura de Deploy (Produção - Fly.io)

```
Internet → nginx (:8080) → Streamlit (:8501)  [rotas /]
                        → API HTTP (:8765)    [rotas /api, /monitor, /report]
```

**Arquivos de deploy:**

**Arquivos-chave:**

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

## 🖥️ Selenium e Testes Visuais

### Configuração do Chrome para containers
O `selenium_helper.py` configura Chrome/Chromium com opções necessárias para rodar em containers sem display:

```python
from selenium_helper import get_chrome_driver

# Headless por padrão
driver = get_chrome_driver(headless=True)

# Com browser visível (requer DISPLAY ou Xvfb)
driver = get_chrome_driver(show_browser=True)
```

### ⚠️ Problema comum: "Chrome instance exited"
Em containers sem X11/display, Selenium falha com erro `SessionNotCreatedException`. Soluções:

1. **Instalar Xvfb** (recomendado para CI):
```bash
apt-get install -y xvfb
xvfb-run python selenium_dashboard.py
```

2. **Usar pyvirtualdisplay** (Python):
```python
from pyvirtualdisplay import Display
display = Display(visible=0, size=(1920, 1080))
display.start()
# ... usar Selenium ...
display.stop()
```

3. **Validação alternativa sem Selenium**:
```python
import requests

# Testar Streamlit
r = requests.get('http://localhost:8501', timeout=10)
assert r.status_code == 200

# Testar Health
r = requests.get('http://localhost:8501/_stcore/health', timeout=5)
assert 'ok' in r.text.lower()

# Testar Database
from database import DatabaseManager
db = DatabaseManager()
active = db.get_active_bots()  # deve funcionar
```

### Testes Selenium disponíveis
```bash
# Dashboard completo
python selenium_dashboard.py

# Página de learning
python selenium_learning.py

# Relatório
python selenium_report.py

# Lista de trades
python selenium_trades.py
```

## 📊 UI: Campo "Último Evento" na lista de bots

### Estrutura da coluna
A lista de bots ativos exibe o último evento registrado no log:

```python
# ui.py - buscar último log
logs = db_for_logs.get_bot_logs(bot_id, limit=1)
if logs:
    last_log = logs[0]
    msg = last_log.get('message', '')
    ts = last_log.get('timestamp', '')  # ⚠️ É um FLOAT, não string!
```

### ⚠️ Timestamp é float, não string
O banco SQLite armazena timestamp como `float` (Unix timestamp). Converter antes de exibir:

```python
# ❌ ERRADO - causa erro "float object is not subscriptable"
ts_short = ts[:19]

# ✅ CORRETO - converter para datetime
if isinstance(ts, (int, float)):
    from datetime import datetime
    ts = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
ts_short = str(ts)[:19] if ts else ''
```

### Extrair evento do JSON
Os logs são salvos como JSON. Extrair campo `event` se disponível:

```python
import json
msg = log.get('message', '')
try:
    data = json.loads(msg)
    if 'event' in data:
        event_display = data['event'].upper().replace('_', ' ')
        # "order_success" → "ORDER SUCCESS"
except:
    # Fallback: usar mensagem truncada
    event_display = msg[:40] + "..." if len(msg) > 40 else msg
```

### Eventos comuns do bot
| Evento JSON | Display | Significado |
|-------------|---------|-------------|
| `price_update` | PRICE UPDATE | Atualização de preço |
| `order_success` | ORDER SUCCESS | Ordem executada |
| `order_failed` | ORDER FAILED | Ordem falhou |
| `target_hit` | TARGET HIT | Target atingido |
| `stop_loss` | STOP LOSS | Stop-loss disparado |
| `simulated_order` | SIMULATED ORDER | Ordem dry-run |

## 🔄 Padrões de Produção vs Local

### Detecção de ambiente
```python
import os

# Fly.io define automaticamente FLY_APP_NAME
is_production = bool(os.environ.get("FLY_APP_NAME"))

# Ou usar APP_ENV
APP_ENV = os.environ.get('APP_ENV', 'dev').lower()
is_hom = APP_ENV in ('hom', 'homologation', 'prod_hom')
```

### URLs condicionais
```python
# ⚠️ CRÍTICO: URLs hardcoded (127.0.0.1) não funcionam em produção

# ❌ ERRADO - só funciona local
report_url = f"http://127.0.0.1:{api_port}/report"

# ✅ CORRETO - funciona em ambos
is_production = bool(os.environ.get("FLY_APP_NAME"))
if is_production:
    report_url = "/report"  # URL relativa
else:
    report_url = f"http://127.0.0.1:{api_port}/report"
```

### Arquivos HTML com JavaScript
Os arquivos HTML (`report_window.html`, `monitor_window.html`) usam `window.location.origin` para APIs:

```javascript
// ✅ Padrão correto para produção
const apiUrl = new URL('/api/trades', window.location.origin);

// ❌ Evitar hardcoded
const apiUrl = 'http://127.0.0.1:8765/api/trades';  // quebra em produção
```

## Secrets

`.env` ou `st.secrets`: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `KUCOIN_BASE`, `TRADES_DB`

## 📝 Lições Aprendidas (Histórico)

### 2026-01-02: URLs dinâmicas para Fly.io

### 2026-01-02: Campo "Último Evento"

### 2026-01-02: Selenium em container

### 2026-01-02: Scripts de debug não devem ter prefixo test_

### 2026-01-02: st.link_button não abre em nova aba
```python
# ❌ ERRADO - não abre em nova aba
st.link_button("📜 Log", log_url, use_container_width=True)

# ✅ CORRETO - abre em nova aba
st.markdown(f'''
<a href="{log_url}" target="_blank" rel="noopener noreferrer"
   style="display:inline-flex;align-items:center;justify-content:center;
          width:100%;padding:0.25rem 0.75rem;border-radius:0.5rem;
          min-height:2.5rem;text-decoration:none;
          background-color:rgb(19,23,32);color:rgb(250,250,250);
          border:1px solid rgba(250,250,250,0.2);">
    📜 Log
</a>
''', unsafe_allow_html=True)
```
### 2026-01-02: API HTTP não acessível em produção (Fly.io)

### 2026-01-02: Botão Home no monitor voltava para URL errada
```javascript
// ❌ ERRADO - porta hardcoded não funciona com nginx
home = `${u.protocol}//${u.hostname}:8501${homeRaw}`;

// ✅ CORRETO - usa a origem atual (funciona em qualquer porta)
const origin = window.location.origin;
home = `${origin}${homeRaw}`;
```
```
nginx (:8080) → /         → Streamlit (:8501)
             → /api/*    → API HTTP (:8765)
             → /monitor  → API HTTP (:8765)
             → /report   → API HTTP (:8765)
```

```bash
source venv/bin/activate
pip install -r requirements.txt
```

```bash
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true
```

```bash
python -u bot_core.py --bot-id test_dry_1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.1 --funds 0 --dry
```

# Copilot Instructions — AutoCoinBot (resumo prático)
# Copilot Instructions — AutoCoinBot (resumo prático)

> **🤖 Default Agent: `dev-senior`** — Ver [agents.json](agents.json) para configuração de agentes.  
> **📚 Manual de Treinamento:** [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md)

**Objetivo breve:** Streamlit UI controla subprocessos de bots que escrevem logs e trades em `trades.db`. A UI consome um terminal HTTP local para render de logs em tempo real.

---

## 1. Ambiente & Quickstart

### Setup inicial
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS/WSL
pip install -r requirements.txt
```

### Executar a aplicação
```bash
# Terminal 1: Streamlit UI
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true

# Terminal 2: Bot (dry-run recomendado)
python -u bot_core.py --bot-id test_dry_1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.1 --funds 0 --dry
```

---

## 2. Arquitetura (arquivos-chave)

| Arquivo | Descrição |
|---------|-----------|
| [streamlit_app.py](../streamlit_app.py) | Entrada da app + persistência `.login_status` |
| [ui.py](../ui.py) | Lógica de UI, guardas multi-tab/kill-on-start, render do terminal |
| [bot_controller.py](../bot_controller.py) | Compõe o comando do subprocess e grava `bot_sessions` |
| [bot_core.py](../bot_core.py) / [bot.py](../bot.py) | Lógica do bot; usa `DatabaseLogger`/`database.py` |
| [terminal_component.py](../terminal_component.py) | API HTTP local (~8765) que serve logs para o widget |
| [database.py](../database.py) | Schema + helpers (tabelas: `bot_sessions`, `bot_logs`, `trades`) |
| [api.py](../api.py) | Integração com KuCoin API e lookup de secrets |

### Tabelas principais do banco de dados
- **`bot_sessions`**: sessões de bots (id, status, PID, config)
- **`bot_logs`**: logs em tempo real dos bots
- **`trades`**: histórico de trades executados
- **`learning_stats`**: estatísticas de aprendizado ML
- **`learning_history`**: histórico de treinamento

---

## 3. Convenções importantes (não alterar sem checar)

- **Evite `print()`** em código comprometido; use `DatabaseLogger` ou `logging` (ver `bot_core.py`)
- **CLI do bot**: se alterar flags/args, atualizar **simultaneamente** `bot_core.py` e `bot_controller.py` (builder vs actor devem estar sincronizados)
- **Schema do DB**: se mudar, atualizar `database.py` e **todos** os callers que tocam as colunas modificadas
- **Terminal API**: preservar formato JSON e headers CORS em `terminal_component.py` (UI depende da shape)
- **Multi-tab/kill-on-start**: implementado via `ui.py` + flags no DB (prefira persistência DB a estados em memória)

---

## 4. Integrações e pontos exteriores

| Componente | Detalhe |
|------------|---------|
| **DB SQLite** | `trades.db` na raiz do repo (ver `database.py`) |
| **Terminal API** | `http://localhost:8765/api/logs?bot=<bot_id>` usado pela UI |
| **Secrets** | `.env` local ou `st.secrets` para `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `API_KEY_VERSION`, `KUCOIN_BASE`, `TRADES_DB` |

---

## 5. Comandos úteis e testes

```bash
# Verificar sintaxe
python -m py_compile <file>.py

# Testes unitários
pytest tests/

# Testes completos (APP_ENV=dev por padrão)
./run_tests.sh

# Testes Selenium/E2E (requer Chrome + chromedriver)
RUN_SELENIUM=1 ./run_tests.sh

# Inspeção do banco de dados
python scripts/db_inspect.py
```

---

## 6. Checklist rápido antes de PRs

- [ ] **Alterou CLI do bot?** → testar dry-run e validar `bot_sessions`/`bot_logs` no DB
- [ ] **Alterou schema?** → adicionar migração/nota e atualizar `database.py` callers
- [ ] **Alterou terminal API/UI?** → validar widget e headers CORS
- [ ] **Adicionou prints?** → substituir por `DatabaseLogger`
- [ ] **Alterou UI?** → rodar `python -m py_compile ui.py` e testar navegação por tabs

---

## 7. Referências rápidas

- [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md) — Manual completo de treinamento
- [agents.json](agents.json) — Configuração de agentes especializados
- [tests/](../tests/) — Testes unitários e E2E
- [scripts/](../scripts/) — Scripts de manutenção e inspeção

---

**Nota:** Este documento contém as instruções essenciais para agentes Copilot. Para documentação detalhada, consulte [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md).
 
