# Copilot Instructions — AutoCoinBot

> **🎯 Projeto:** Bot de trading KuCoin com Streamlit UI e PostgreSQL  
> **📚 Documentação completa:** [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md)

## ⚠️ REGRAS CRÍTICAS

### 1. Estrutura Modular (2026-01)
**TODO código vive em `autocoinbot/`** — arquivos na raiz são apenas shims:
```python
# Raiz: bot_core.py, ui.py, etc (NÃO EDITAR)
"""Shim for moved module: bot_core."""
from autocoinbot.bot_core import *
```
**✅ SEMPRE edite `autocoinbot/*.py`** | ❌ NUNCA edite shims da raiz

### 2. UI Não Travar (Streamlit)
```python
# ❌ CAUSA FREEZE: session_state + value no mesmo widget
st.session_state["key"] = valor
st.number_input(..., value=valor, key="key")

# ✅ CORRETO: apenas session_state OU value
st.number_input(..., key="key")  # sem value=
```

### 3. CLI Sincronizado
**Alterar flags?** → Atualizar AMBOS:
- `autocoinbot/bot_core.py` (argparse)
- `autocoinbot/bot_controller.py` (builder do comando)

### 4. Logging via Banco
```python
# ❌ print("debug")
# ✅ DatabaseLogger(db_manager, bot_id).info("debug")
```

### 5. URLs Dinâmicas (Prod vs Local)
```python
is_production = bool(os.environ.get("FLY_APP_NAME"))
url = "/api/logs" if is_production else "http://127.0.0.1:8765/api/logs"
```

## 🏗️ Arquitetura (3 camadas)

```
Streamlit UI (autocoinbot/ui.py)
    ↓ spawn subprocess
Bot Controller (autocoinbot/bot_controller.py)
    ↓ execute trading logic  
Bot Core (autocoinbot/bot_core.py + bot.py)
    ↓ persist
PostgreSQL (autocoinbot/database.py)
```

**Arquivos-chave:**
- `autocoinbot/ui.py` — Interface + guardas multi-tab
- `autocoinbot/bot_controller.py` — Spawner de subprocessos
- `autocoinbot/bot_core.py` — Lógica de trading
- `autocoinbot/database.py` — Schema (bot_sessions, bot_logs, trades)
- `autocoinbot/terminal_component.py` — API HTTP :8765

## 🚀 Comandos Rápidos

```bash
# Setup
source venv/bin/activate && pip install -r requirements.txt

# Rodar app
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true

# Dry-run bot
python -u bot_core.py --bot-id test1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.1 --dry

# Testes
./run_tests.sh                    # unitários
RUN_SELENIUM=1 ./run_tests.sh     # E2E
python -m py_compile <file>.py    # sintaxe
```

## 📋 Checklist PRs

- [ ] CLI alterado? → Sincronizar bot_core.py + bot_controller.py
- [ ] Schema alterado? → Atualizar database.py + callers
- [ ] UI alterado? → Testar session_state (não travar)
- [ ] Adicionou print()? → Substituir por DatabaseLogger
- [ ] Commit → Adicionar lição aprendida no fim deste arquivo

## 🔗 Referências

- [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md) — Manual completo
- [agents.json](agents.json) — Multi-agente (dev-senior, scraper, os-cleaner)
- API HTTP: `/api/logs`, `/api/trades`, `/api/bot`, `/monitor`, `/report`
- Secrets: `DATABASE_URL`, `API_KEY`, `API_SECRET`, `API_PASSPHRASE`
---

## 📚 Seções Detalhadas (Referência)

### Arquitetura Completa (fluxo de dados)

```
streamlit_app.py → autocoinbot/ui.py → autocoinbot/bot_controller.py → subprocess(autocoinbot/bot_core.py)
                              ↓                                 ↓
                        bot_sessions (DB)               bot_logs/trades (DB)
                                                              ↑
                          autocoinbot/terminal_component.py ←──┘ (HTTP API :8765)
```

**Deploy (Fly.io):**
```
Internet → nginx(:8080) → Streamlit(:8501) [rotas /]
                       → API HTTP(:8765)   [rotas /api, /monitor, /report]
```

### Padrões Avançados

#### Bandit Learning (epsilon-greedy)
```python
# Escolher parâmetro (25% exploração, 75% exploitation)
db.choose_bandit_param(symbol, "take_profit_trailing_pct", 
                       candidates=[0.2, 0.5, 1.0], epsilon=0.25)

# Atualizar reward (profit_pct positivo = recompensa, negativo = penalização)
db.update_bandit_reward(symbol, param_name, param_value, reward=profit_pct)

# Stop-loss gera penalização extra (profit * 1.5)
db.get_best_learned_param(symbol, "take_profit_trailing_pct")
```

#### Targets com Custos de Trading
`autocoinbot/bot.py` ajusta targets para compensar taxas (~0.25%):
```python
# Target 2% → preço precisa subir 2.25% para lucro líquido de 2%
self._total_trading_cost_pct = self._buy_fee_pct + self._sell_fee_pct + self._slippage_pct
```

#### Eternal Mode
Flag `--eternal` faz o bot reiniciar automaticamente após targets:
```python
# Após completar targets, registra ciclo em eternal_runs e reinicia
db.add_eternal_run(bot_id, run_number, symbol, entry_price, total_targets)
db.complete_eternal_run(run_id, exit_price, profit_pct, profit_usdt, targets_hit)
```

#### Selenium com Webdriver Manager
```python
from selenium_helper import get_chrome_driver
driver = get_chrome_driver(headless=True)
```

### Schema DB (tabelas principais)

| Tabela | Colunas-chave |
|--------|---------------|
| `bot_sessions` | id, pid, symbol, status, entry_price, dry_run |
| `bot_logs` | bot_id, timestamp, level, message |
| `trades` | symbol, side, price, size, profit, dry_run, order_id |
| `learning_stats` | symbol, param_name, param_value, mean_reward, n |
| `eternal_runs` | bot_id, run_number, entry_price, exit_price, profit_pct, status |

### 🔍 Metodologia de correção de bugs

**SEMPRE pesquisar histórico Git antes de implementar:**

```bash
# Buscar commits que alteraram arquivo específico
git log --oneline -20 -- ui.py

# Ver TODAS as alterações de um padrão no histórico
git log --all -p -- ui.py | grep -A5 -B5 "report_url"

# Buscar em todo o projeto por padrão
git log --all -p | grep -B10 "window.location.hostname"

# Ver estado de um arquivo em commit específico
git show abc1234:ui.py | head -100
```

**Por quê?** O projeto pode já ter resolvido o problema antes.

### URLs dinâmicas para produção vs local
```python
# Detectar ambiente
is_production = bool(os.environ.get("FLY_APP_NAME"))

# URLs condicionais
if is_production:
    base_url = ""  # URLs relativas
    home_url = "/?view=dashboard"
else:
    base_url = f"http://127.0.0.1:{api_port}"
    home_url = f"http://127.0.0.1:{st_port}/?view=dashboard"
```

### API HTTP (autocoinbot/terminal_component.py)
- Logs: `/api/logs?bot=<id>&limit=n`
- Trades: `/api/trades?bot=<id>&only_real=1&group=1`
- Sessão bot: `/api/bot?bot=<id>`
- Equity: `/api/equity/history`
- Start/Stop bots: `POST /api/start`, `POST /api/stop`
- Monitor/Report: `/monitor`, `/report`

### Secrets (`.env` ou `st.secrets`)
`API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `KUCOIN_BASE`, `DATABASE_URL`

---

## 📝 Lições Aprendidas (Histórico)

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
O banco PostgreSQL armazena timestamp como `DOUBLE PRECISION` (Unix timestamp). Converter antes de exibir:

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

`.env` ou `st.secrets`: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `KUCOIN_BASE`, `DATABASE_URL` (PostgreSQL)

## 📝 Lições Aprendidas (Histórico)
### 2026-01: Reestruturação modular (autocoinbot/)
- Problema: Código principal estava na raiz do projeto, dificultando importações e organização.
- Causa: Crescimento orgânico do projeto sem estrutura modular desde o início.
- Solução: Todo código movido para módulo `autocoinbot/`; arquivos na raiz são shims (`from autocoinbot.X import *`) para compatibilidade retroativa.
- Arquivos: Todos os arquivos principais agora em `autocoinbot/` (ui.py, bot_core.py, bot_controller.py, database.py, api.py, terminal_component.py, bot.py, etc.)
- **Regra crítica**: SEMPRE edite em `autocoinbot/`, NUNCA nos shims da raiz.
### 2026-01-03: Quickstart para agentes IA
- Problema: As instruções estavam extensas e diluídas, dificultando onboarding rápido de agentes.
- Causa: Documento cresceu com muitos detalhes operacionais e históricos.
- Solução: Adicionada seção "AI Agent Quickstart (2026-01-03)" no topo com arquitetura, limites de serviço, regras críticas e comandos essenciais; mantido conteúdo detalhado abaixo.
- Arquivos: [autocoinbot/ui.py](autocoinbot/ui.py), [autocoinbot/bot_controller.py](autocoinbot/bot_controller.py), [autocoinbot/bot_core.py](autocoinbot/bot_core.py), [autocoinbot/bot.py](autocoinbot/bot.py), [autocoinbot/database.py](autocoinbot/database.py), [autocoinbot/terminal_component.py](autocoinbot/terminal_component.py), [autocoinbot/api.py](autocoinbot/api.py)

### 2026-01-02: URLs dinâmicas para Fly.io

### 2026-01-02: Campo "Último Evento"

### 2026-01-02: Selenium em container

### 2026-01-02: Scripts de debug não devem ter prefixo test_

### 2026-01-02: st.link_button não abre em nova aba
```python

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
O banco PostgreSQL armazena timestamp como `DOUBLE PRECISION` (Unix timestamp). Converter antes de exibir:

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

`.env` ou `st.secrets`: `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `KUCOIN_BASE`, `DATABASE_URL` (PostgreSQL)

## 📝 Lições Aprendidas (Histórico)
### 2026-01: Reestruturação modular (autocoinbot/)
- Problema: Código principal estava na raiz do projeto, dificultando importações e organização.
- Causa: Crescimento orgânico do projeto sem estrutura modular desde o início.
- Solução: Todo código movido para módulo `autocoinbot/`; arquivos na raiz são shims (`from autocoinbot.X import *`) para compatibilidade retroativa.
- Arquivos: Todos os arquivos principais agora em `autocoinbot/` (ui.py, bot_core.py, bot_controller.py, database.py, api.py, terminal_component.py, bot.py, etc.)
- **Regra crítica**: SEMPRE edite em `autocoinbot/`, NUNCA nos shims da raiz.
### 2026-01-03: Quickstart para agentes IA
- Problema: As instruções estavam extensas e diluídas, dificultando onboarding rápido de agentes.
- Causa: Documento cresceu com muitos detalhes operacionais e históricos.
- Solução: Adicionada seção “AI Agent Quickstart (2026-01-03)” no topo com arquitetura, limites de serviço, regras críticas e comandos essenciais; mantido conteúdo detalhado abaixo.
- Arquivos: [autocoinbot/ui.py](autocoinbot/ui.py), [autocoinbot/bot_controller.py](autocoinbot/bot_controller.py), [autocoinbot/bot_core.py](autocoinbot/bot_core.py), [autocoinbot/bot.py](autocoinbot/bot.py), [autocoinbot/database.py](autocoinbot/database.py), [autocoinbot/terminal_component.py](autocoinbot/terminal_component.py), [autocoinbot/api.py](autocoinbot/api.py)

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
- Problema: nginx em produção precisa rotear `/api/*`, `/monitor`, `/report` para API HTTP (:8765)
- Solução: Configurar nginx.conf com proxy_pass

### 2026-01-02: Botão Home no monitor voltava para URL errada
```javascript
// ❌ ERRADO - porta hardcoded não funciona com nginx
home = `${u.protocol}//${u.hostname}:8501${homeRaw}`;

// ✅ CORRETO - usa a origem atual (funciona em qualquer porta)
const origin = window.location.origin;
home = `${origin}${homeRaw}`;
```
### 2026-01-04: Botão LOG/RELATÓRIO retorna 404 (HTML files + Docker cleanup)
- **Problema**: User clicou botão LOG no dashboard e recebeu erro 404
- **Causas**:
  1. **Container Docker obsoleto** (`deploy-streamlit-1`) bloqueava porta 8765 (API HTTP)
  2. **Arquivos HTML ausentes**: `monitor_window.html` e `report_window.html` estavam em raiz, não em `autocoinbot/`
  3. **Session state cache**: URLs armazenadas em cache com porto inválido (8766)
- **Soluções**:
  ```bash
  # 1. Remover container docker obsoleto
  docker stop deploy-streamlit-1
  docker rm deploy-streamlit-1
  
  # 2. Copiar HTML files para autocoinbot/
  cp monitor_window.html report_window.html autocoinbot/
  
  # 3. Reiniciar Streamlit
  nohup python -m streamlit run streamlit_app.py --server.port=8506
  ```
- **Validação**:
  ```bash
  ✅ curl http://127.0.0.1:8765/monitor  → 200 OK
  ✅ curl http://127.0.0.1:8765/report   → 200 OK
  ✅ Botão LOG funciona (clica e abre página)
  ```
- **Lição**: HTML files para rotas HTTP devem estar em `autocoinbot/` (não raiz), pois `terminal_component.py` as busca lá. Sempre limpar containers Docker antigos que podem bloquear portas essenciais.
- **Arquivos**: [autocoinbot/monitor_window.html](autocoinbot/monitor_window.html), [autocoinbot/report_window.html](autocoinbot/report_window.html), [terminal_component.py#L560](autocoinbot/terminal_component.py#L560-L590)

### 2026-01-04: URLs hardcoded em ui.py (botões não funcionam em produção)
- **Problema**: Botões LOG/RELATÓRIO funcionam local mas não em produção (Fly.io)
- **Causa**: URLs hardcoded com `http://127.0.0.1:{api_port}` não funcionam em produção (navegador tenta localhost do cliente, não do servidor)
- **Solução**: URLs dinâmicas baseadas em ambiente
  ```python
  # Detectar produção
  is_production = bool(os.environ.get("FLY_APP_NAME"))
  
  if is_production:
      base = ""  # URLs relativas (nginx faz proxy)
      home_url = "/?view=dashboard"
  else:
      base = f"http://127.0.0.1:{int(api_port)}"
      home_url = f"http://127.0.0.1:{st_port}/?view=dashboard"
  
  log_url = f"{base}/monitor?bot={bot_id}"
  ```
- **Arquitetura produção**: Internet → Fly.io → nginx(:8080) → [Streamlit(:8501) | API(:8765)]
- **Validação produção**:
  ```bash
  fly deploy --app autocoinbot
  curl -I https://autocoinbot.fly.dev/monitor  # → 200 OK
  ```
- **Lição**: Sempre usar URLs relativas em produção quando há proxy reverso (nginx). Detectar ambiente via variáveis como `FLY_APP_NAME`, `APP_ENV`, etc.
- **Arquivos**: [autocoinbot/ui.py#L5320](autocoinbot/ui.py#L5320-L5340), [FIX_PRODUCAO_URLS_DINAMICAS.md](FIX_PRODUCAO_URLS_DINAMICAS.md)
