# Copilot Instructions — AutoCoinBot

> KuCoin trading bot com Streamlit UI e PostgreSQL (psycopg).  
> **Guia completo:** [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md) | **Histórico:** [Lições Aprendidas](#-lições-aprendidas-2026)

---

## 🎯 Essencial: Arquitetura em 30 segundos

```
USER (Browser) :8501 → Streamlit (streamlit_app.py → ui.py) → BotController
                                                               ↓
                                                   bot_core.py (subprocess PID)
                                                               ↓
                                             PostgreSQL (database.py)
                                             ├─ bot_sessions
                                             ├─ bot_logs (timestamp = FLOAT!)
                                             ├─ trades
                                             └─ learning_stats
                                                        ↑
                                           /api/logs (HTTP :8765)
                                     terminal_component.py
```

| Arquivo | Responsabilidade |
|---------|-----------------|
| `autocoinbot/streamlit_app.py` | Entry point (autenticação básica) |
| `autocoinbot/ui.py` | Interface Streamlit (4+ abas com tabs) |
| `autocoinbot/bot_controller.py` | BotController — spawner de subprocessos |
| `autocoinbot/bot_core.py` | Lógica de trading (argparse, DatabaseLogger) |
| `autocoinbot/bot.py` | Classe EnhancedTradeBot (estratégia, cálculos) |
| `autocoinbot/database.py` | DatabaseManager — PostgreSQL via psycopg |
| `autocoinbot/terminal_component.py` | HTTP API server :8765 (/api/logs) |
| `autocoinbot/api.py` | KuCoin API wrapper (create_order, get_balance, etc) |
| `autocoinbot/market.py` | Market analysis (regime detection 5m) |
| `autocoinbot/bot_registry.py` | In-memory bot registry (compatibilidade) |

**Shims na raiz** (para compatibilidade): `bot_core.py`, `ui.py`, `database.py` etc. apenas importam de `autocoinbot/`.

---

## 🔄 Fluxos Críticos & Padrões

### Bot Lifecycle
1. **Start**: `ui.py` → `BotController.start_bot()` → subprocess `bot_core.py --bot-id ... --symbol ... --entry ... --targets ...`
2. **Register**: `bot_core.py` → `DatabaseManager.insert_bot_session()` [PostgreSQL]
3. **Trade**: `bot_core.py` → `EnhancedTradeBot.run()` → `api.create_order()` [KuCoin]
4. **Log**: `DatabaseLogger.info/error()` → `DatabaseManager.add_bot_log()` [PostgreSQL]
5. **Monitor**: `ui.py` → `GET /api/logs?bot=<id>` → `terminal_component.py` [HTTP]
6. **Stop**: Bot termina quando targets atingidos (ou erro) → `insert_trade()` com resultado

### Log JSON Structure
```python
# DatabaseManager.add_bot_log(bot_id, level, message, data_dict)
# Armazenado em bot_logs.message como JSON string
{
    "event": "order_success",  # ou price_update, order_failed, target_hit, stop_loss
    "price": 50000.5,
    "target": "2:0.3",
    "timestamp": <unix_float>
}
```

### Targets Format
```python
# Entrada do usuário: "2:0.3" → (2 targets, 0.3 = 30% per target)
targets = "2:0.3"
parsed = [(float(x), float(y)) for x, y in [t.split(":") for t in targets.split(",")]]
# [(2.0, 0.3)]  → vender em +2% com 30% do saldo
```

---

### 1️⃣ Estrutura Modular — Edite em `autocoinbot/`, NUNCA na raiz
```python
# ✅ EDITAR:  autocoinbot/bot_core.py, autocoinbot/ui.py, autocoinbot/database.py
# ❌ EVITAR: raiz/bot_core.py (são SHIMS que importam de autocoinbot/)
```
**Por quê?** Código principal vive em `autocoinbot/`. Arquivos na raiz apenas fazem `from autocoinbot.X import *` para compatibilidade.

**Padrão de Shim (exemplo):**
```python
# raiz/bot_core.py
"""Shim for moved module: bot_core."""
from autocoinbot.bot_core import *

if __name__ == "__main__":
    import autocoinbot.bot_core as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
```
Isso permite que código antigo que faz `from bot_core import X` continue funcionando.

### 2️⃣ CLI Args: Sincronizar `bot_core.py` ↔ `bot_controller.py`
Se alterar flags CLI, **atualizar em AMBOS arquivos simultaneamente:**

```python
# autocoinbot/bot_core.py (linhas ~191-204) — argparse
parser.add_argument("--bot-id", required=True)
parser.add_argument("--symbol", required=True)
parser.add_argument("--entry", type=float, required=True)
parser.add_argument("--mode", default="mixed", choices=["sell", "buy", "mixed", "flow"])
parser.add_argument("--targets", required=True)  # "2:0.3"
parser.add_argument("--interval", type=float, default=5.0)
parser.add_argument("--size", type=float, default=0.0)
parser.add_argument("--funds", type=float, default=0.0)
parser.add_argument("--dry", action="store_true", default=False)
parser.add_argument("--reserve-pct", type=float, default=50.0)
parser.add_argument("--target-profit-pct", type=float, default=2.0)
parser.add_argument("--eternal", action="store_true", default=False)
parser.add_argument("--screenshot", action="store_true", default=False)

# autocoinbot/bot_controller.py (linhas ~43-82) — subprocess cmd
cmd = [sys.executable, "-u", str(BOT_CORE),
       "--bot-id", bot_id, "--symbol", symbol, "--entry", str(entry),
       "--mode", mode, "--targets", targets, "--interval", str(interval),
       "--size", str(size), "--funds", str(funds),
       "--reserve-pct", str(reserve_pct), "--target-profit-pct", str(target_profit_pct)]
if dry:
    cmd.append("--dry")
if eternal_mode:
    cmd.append("--eternal")
```
⚠️ **Atenção:** Quando adicionar novo argumento CLI, atualizar método `start_bot()` em `bot_controller.py`.

### 3️⃣ Streamlit: Evitar Freeze com `session_state`
```python
# ❌ FREEZE: st.session_state["key"] = x; st.widget(..., value=x, key="key")
# ✅ CORRETO:
if "key" not in st.session_state:
    st.session_state.key = default_value
st.widget(..., key="key")  # SEM value=
```

### 4️⃣ Timestamps: São FLOAT (Unix timestamp), NÃO string
Database `bot_logs.timestamp` → `DOUBLE PRECISION` (float).
```python
# ❌ ERRADO: ts[:19]  (causa "float object is not subscriptable")
# ✅ CORRETO:
import time
if isinstance(ts, (int, float)):
    ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
```

### 5️⃣ URLs Dinâmicas: Produção vs Local
```python
is_prod = bool(os.environ.get("FLY_APP_NAME"))
if is_prod:
    url = "/api/logs"  # relativa (nginx faz proxy)
else:
    url = "http://127.0.0.1:8765/api/logs"
```
**⚠️ Crítico:** URLs hardcoded com `127.0.0.1:8765` quebram em produção.

### 6️⃣ Logging: Use `DatabaseLogger`, NÃO `print()`
```python
# ❌ print("msg")  → invisível em produção
# ✅ DatabaseLogger (definido em bot_core.py)
from autocoinbot.bot_core import DatabaseLogger
from autocoinbot.database import DatabaseManager
db = DatabaseManager()
logger = DatabaseLogger(db, bot_id="my_bot")
logger.info("Sinal de compra")
logger.error("Erro crítico")
```

### 7️⃣ HTML Files para rotas HTTP → `autocoinbot/`
`terminal_component.py` busca HTML files em seu próprio diretório.
```python
# autocoinbot/terminal_component.py (~560)
html_path = Path(__file__).parent / "monitor_window.html"  # ✅ Em autocoinbot/
```

### 8️⃣ Entry Points Principales
**Aplicação Principal (Streamlit):**
- `autocoinbot/streamlit_app.py` → Login simples (usuário/senha) → importa `ui.py`
- `autocoinbot/ui.py` → Interface Streamlit com 4+ abas (Dashboard, Trading, Learning, Terminal)

**Bot Executável (subprocess):**
- `autocoinbot/bot_core.py` → Pode ser executado como script com `--bot-id`, `--symbol`, `--entry`, etc.
- Define `DatabaseLogger` para logging estruturado em PostgreSQL

---
## 🔌 Integração KuCoin API

### Rate Limiting
```python
# autocoinbot/api.py (linhas ~130-141)
_last_request_time = 0
_min_request_interval = 0.1  # 100ms entre requests

def rate_limit():
    """Rate limiting para evitar throttling da API"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _min_request_interval:
        time.sleep(_min_request_interval - elapsed)
    _last_request_time = time.time()
```
**Padrão:** Toda função que chama API deve chamar `rate_limit()` ANTES da requisição.

### Retry com Backoff Exponencial
```python
# autocoinbot/api.py (linhas ~145-166)
@retry_on_failure(max_retries=3, backoff=2.0)
def create_order(self, order_params: Dict) -> Dict:
    """Cria ordem com retry automático (0.1s, 0.2s, 0.4s)"""
    rate_limit()
    response = self.client.create_order(**order_params)
    return response
```
**Importante:** Usar decorator `@retry_on_failure` para todas operações críticas.

### Endpoints Principais
| Método | Rate Limit | Uso |
|--------|-----------|-----|
| `get_account_info()` | 10 req/3s | Saldo, status da conta |
| `create_order()` | 30 req/3s | Enviar ordem (BUY/SELL) |
| `get_klines()` | 10 req/3s | Candlestick data (análise) |
| `cancel_order()` | 30 req/3s | Cancelar ordem pendente |

---

## 🧠 Learning Module (ML Feedback)

### Estrutura de Dados
```python
# autocoinbot/database.py
learning_stats: (symbol, param_name, param_value, mean_reward, n)
learning_history: (symbol, param_name, param_value, reward, timestamp)
```

### Fluxo de Aprendizado
1. **Coleta**: `bot.py` → executa com parâmetro X → gera resultado (profit/loss)
2. **Registro**: `DatabaseManager.record_learning()` → insere em `learning_history`
3. **Agregação**: Recalcula `mean_reward` e `n` em `learning_stats`
4. **Visualização**: `ui.py` → `get_learning_stats()` → exibe gráfico

### Métodos da DatabaseManager
```python
# autocoinbot/database.py
db.get_learning_symbols() -> List[str]  # ["BTC-USDT", "ETH-USDT", ...]
db.get_learning_stats(symbol, param_name) -> List[Dict]  # stats por parâmetro
db.get_learning_history(symbol, param_name, limit=2000) -> List[Dict]  # histórico completo
db.get_learning_reward_range(symbol, param_name) -> (min, max)
db.record_learning(symbol, param_name, param_value, reward)  # registra novo resultado
```

**Padrão:** Sempre agregar rewards em `learning_stats` para evitar varrição de tabelas gigantes.

---

## 🔐 Autenticação & Segredos

### Sistema de Login (Streamlit)
```python
# autocoinbot/streamlit_app.py (linhas ~15-38)
USUARIO_PADRAO = os.getenv("KUCOIN_USER", "admin")
SENHA_HASH_PADRAO = hashlib.sha256(os.getenv("KUCOIN_PASS", "senha123").encode()).hexdigest()
LOGIN_FILE = os.path.join(os.path.dirname(__file__), '.login_status')

def verificar_credenciais(usuario, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    return usuario == USUARIO_PADRAO and senha_hash == SENHA_HASH_PADRAO
```

### Variáveis de Ambiente Obrigatórias
```bash
# .env (desenvolvimento local)
KUCOIN_USER=admin                    # Usuário Streamlit
KUCOIN_PASS=senha123                 # Senha Streamlit (será hasheada)
API_KEY=xxx                          # KuCoin API Key
API_SECRET=xxx                       # KuCoin API Secret
API_PASSPHRASE=xxx                   # KuCoin API Passphrase
DATABASE_URL=postgresql://...        # PostgreSQL connection string
```

### ⚠️ Segurança
- ❌ **Nunca** commitar `.env` ou credenciais
- ✅ Usar `os.getenv()` para tudo (fallback seguro é essencial)
- ✅ Hash de senhas sempre com SHA256
- ✅ Tokens de API em variáveis de ambiente (Fly.io secrets)

---

## 🤖 Agentes Especializados

### OS Cleaner Agent
```bash
# autocoinbot/agents/os_cleaner_agent.py
python agents/os_cleaner_agent.py --analyze    # Ver o que pode limpar
python agents/os_cleaner_agent.py --dry-run    # Simular limpeza
python agents/os_cleaner_agent.py --target browser temp cache  # Limpar específicos
python agents/os_cleaner_agent.py --aggressive # Limpeza agressiva
```

**Alvos disponíveis (Windows/Linux/macOS):**
- `temp`, `cache`, `logs` - Arquivos temporários
- `browser` - Cache de navegadores
- `windows_update`, `prefetch` - Windows specific
- `apt`, `journal` - Linux specific
- `xcode`, `ios_backup` - macOS specific

**Padrão de Uso:**
```python
from agents.os_cleaner_agent import OSCleanerAgent
agent = OSCleanerAgent(dry_run=True)  # Sempre testar primeiro!
report = agent.run()
print(report.summary)  # Exibe bytes liberados, arquivos removidos, etc
```

### Scraper Agent (Validação Visual)
```bash
# autocoinbot/agent0_scraper.py
python agent0_scraper.py --local --test-dashboard  # Valida UI inicial
python agent0_scraper.py --local --test-bot-start   # Testa start de bot
python agent0_scraper.py --local --test-all         # Validação completa
python agent0_scraper.py --local --analyze          # Apenas análise
```

**Funcionalidades:**
- Login automático via Selenium
- Detecção de elementos (header, inputs, buttons)
- Screenshots automáticas
- Relatórios (`relatorio_validacao*.md`)

---
## � Padrões de Código Importantes

### Imports Multidirecionais (Compatibilidade)
```python
# ✅ Dentro de autocoinbot/
from autocoinbot.database import DatabaseManager
from .bot_registry import BotRegistry

# ✅ A partir da raiz (shims permitem ambos)
from database import DatabaseManager
from bot_registry import BotRegistry

# ✅ Em bot.py (pode estar em autocoinbot/ ou raiz)
try:
    from .market import analyze_market_regime_5m
except Exception:
    from market import analyze_market_regime_5m  # Fallback
```
**Padrão:** Sempre tentar import relativo (`.`) primeiro, depois fallback para import absoluto.

### Tratamento de Modo Simulação (Dry Run)
```python
# autocoinbot/bot.py — EnhancedTradeBot
if self.dry_run:
    # Simulação: não faz requisições reais
    print("[DRY RUN] Would create order:", order_details)
else:
    # Real: envia para KuCoin API
    response = api.create_order(order_details)
```

### Integração com PostgreSQL
```python
# autocoinbot/database.py
class DatabaseManager:
    def __init__(self, db_dsn: str = None):
        self.db_dsn = db_dsn or os.getenv("DATABASE_URL") or os.getenv("TRADES_DB")
        self.conn = psycopg.connect(self.db_dsn, row_factory=dict_row)
    
    def add_bot_log(self, bot_id: str, level: str, message: str, data: Dict):
        """Grava log estruturado em bot_logs"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO bot_logs (bot_id, timestamp, level, message)
            VALUES (%s, %s, %s, %s)
        """, (bot_id, time.time(), level, json.dumps(data)))
```

---

## 🚀 Comandos Essenciais

### Ambientes (Detect Terminal Type First!)
```python
# PowerShell: NUNCA usar && (usar ; ao invés)
# Bash/WSL: usar && ou ;
# Ativar venv: source venv/bin/activate (Bash) | .\venv\Scripts\Activate.ps1 (PowerShell)
```

### Start Streamlit (Bash/WSL)
```bash
cd /home/eddie/AutoCoinBot
source venv/bin/activate
pip install -r requirements.txt  # se necessário
python -m streamlit run autocoinbot/streamlit_app.py --server.port=8501 --server.headless=true
```

### Start Streamlit (PowerShell)
```powershell
cd C:\path\to\AutoCoinBot
.\venv\Scripts\Activate.ps1 ; pip install -r requirements.txt
python -m streamlit run autocoinbot/streamlit_app.py --server.port=8501 --server.headless=true
```

### Bot Dry-Run (ambos shells)
```bash
python -u autocoinbot/bot_core.py \
  --bot-id test1 \
  --symbol BTC-USDT \
  --entry 50000 \
  --targets "2:0.3" \
  --dry
```

### Testes (Bash only)
```bash
./run_tests.sh  # unitários
RUN_SELENIUM=1 ./run_tests.sh  # E2E (requer Chrome + chromedriver)
```

### Validação Sintaxe
```bash
python -m py_compile autocoinbot/bot_core.py autocoinbot/ui.py autocoinbot/database.py
```

---

## 📋 Checklist para PRs

- [ ] Alterou CLI (`--symbol`, `--entry`, `--targets`)? → Sincronizar bot_core.py + bot_controller.py
- [ ] Alterou `ui.py`? → Testar `session_state` para evitar freeze
- [ ] Usou `print()`? → Substituir por `DatabaseLogger`
- [ ] Criou HTML para rota HTTP? → Mover para `autocoinbot/` e registrar em `terminal_component.py`
- [ ] Validar sintaxe: `python -m py_compile <arquivo>.py`
- [ ] Testar com `--dry` antes de submeter

---

## 🌍 Ambiente & Secrets

### `.env` (raiz do projeto)
```bash
APP_ENV=dev  # dev | hom | prod
API_KEY=xxx
API_SECRET=xxx
API_PASSPHRASE=xxx
DATABASE_URL=postgresql://user:password@localhost:5432/autocoinbot
```

### Variáveis Produção (Fly.io)
```bash
fly secrets set API_KEY=xxx API_SECRET=xxx API_PASSPHRASE=xxx DATABASE_URL=xxx
```

---

## 🗄️ Schema PostgreSQL (Principais)

| Tabela | Colunas-chave | Tipo |
|--------|---------------|------|
| `bot_sessions` | id, pid, symbol, status, entry_price, dry_run | — |
| `bot_logs` | bot_id, timestamp (float!), level, message (JSON) | — |
| `trades` | symbol, side, price, profit, dry_run, order_id | — |
| `learning_stats` | symbol, param_name, param_value, mean_reward | — |

**⚠️ Importante:** `bot_logs.timestamp` é float (Unix timestamp), NÃO string.

---

## 🐛 Troubleshooting Rápido

| Problema | Causa | Solução |
|----------|-------|---------|
| Bots não aparecem | `get_active_bots()` vazio | `psql "$DATABASE_URL" -c "SELECT * FROM bot_sessions"` |
| "float object not subscriptable" | Code faz `ts[:19]` | Usar `time.strftime()` ou `datetime.fromtimestamp()` |
| Botão LOG retorna 404 | HTML files na raiz | Mover para `autocoinbot/` |
| URLs quebram em produção | Hardcoded `127.0.0.1:8765` | Usar URLs dinâmicas com detecção de ambiente |
| Streamlit freeze | `session_state` + `value=` conflitam | Remover `value=`, deixar `key=` apenas |
| ChromeDriver não encontrado | Selenium não configurado | Usar `selenium_helper.py` |
| Container Docker bloqueia porta 8765 | Múltiplos containers | `docker stop <container>; docker rm <container>` |

---

## 📊 UI: Campo "Último Evento" (bot dashboard)

Estrutura da coluna que exibe último log em tempo real:

```python
# autocoinbot/ui.py
logs = db.get_bot_logs(bot_id, limit=1)
if logs:
    last_log = logs[0]
    msg = last_log.get('message', '')  # JSON string
    ts = last_log.get('timestamp', '')  # ⚠️ É FLOAT!

# Extrair evento do JSON
import json
try:
    data = json.loads(msg)
    event = data.get('event', '').upper().replace('_', ' ')
    # "order_success" → "ORDER SUCCESS"
except:
    event = msg[:40] + "..." if len(msg) > 40 else msg

# Formatar timestamp
if isinstance(ts, (int, float)):
    ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
```

**Eventos comuns:**
| Evento | Display | Significado |
|--------|---------|-------------|
| `price_update` | PRICE UPDATE | Atualização de preço |
| `order_success` | ORDER SUCCESS | Ordem executada |
| `order_failed` | ORDER FAILED | Falha ao enviar ordem |
| `target_hit` | TARGET HIT | Target atingido |
| `stop_loss` | STOP LOSS | Stop-loss disparado |

---

## 🔗 Referências Adicionais

- **AGENTE_TREINAMENTO.md** — Manual completo (arquitetura, fluxos, troubleshooting)
- **DEPLOY.md** — Deploy em Fly.io
- **AUTH_README.md** — Sistema de autenticação
- **OS_CLEANER_README.md** — Agente de limpeza do SO

---

## 📝 Lições Aprendidas (2026)

### 2026-01: Reestruturação Modular (`autocoinbot/`)
- **Problema:** Código na raiz, importações confusas
- **Solução:** Mover tudo para `autocoinbot/`; shims na raiz para compatibilidade
- **Regra:** SEMPRE editar em `autocoinbot/` (Regra 1️⃣)

### 2026-01-02: URLs Dinâmicas para Fly.io
- **Problema:** URLs hardcoded `http://127.0.0.1:8765` quebram em produção
- **Solução:** Detectar `FLY_APP_NAME` e usar URLs relativas
- **Regra:** `is_prod = bool(os.environ.get("FLY_APP_NAME"))` (Regra 5️⃣)

### 2026-01-04: Botão LOG retorna 404
- **Problema:** HTML files (`monitor_window.html`) na raiz, API busca em `autocoinbot/`
- **Solução:** Mover HTML files para `autocoinbot/`
- **Regra:** HTML para rotas HTTP deve estar em `autocoinbot/` (Regra 7️⃣)
- **Validação:** `curl http://127.0.0.1:8765/monitor` → 200 OK

### 2026-01-04: Sincronizar CLI Args
- **Problema:** Alterações em `bot_core.py` não refletiam em `bot_controller.py`
- **Solução:** Manter ambos sincronizados (mesmos args, mesma ordem)
- **Regra:** Atualizar simultaneamente (Regra 2️⃣)
- **Checklist:** `python -u bot_core.py --help` deve listar todos os args

---

## 👤 Informações Gerais

- **Repositório:** https://github.com/eddiejdi/AutoCoinBot
- **Última atualização:** 5 de janeiro de 2026
- **Maintainer:** Equipe AutoCoinBot
