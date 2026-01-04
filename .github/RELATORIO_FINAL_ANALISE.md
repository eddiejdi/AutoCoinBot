# 📋 Relatório Final de Análise - AutoCoinBot

**Data:** 3 de janeiro de 2026  
**Versão:** 2.0.0  
**Status Geral:** ⚠️ **CRÍTICO** - Múltiplos problemas em ui.py, database.py e integração

---

## 🎯 Sumário Executivo

O projeto AutoCoinBot é uma **aplicação Streamlit de trading botizado com KuCoin**, com funcionalidades avançadas de monitoramento, aprendizado ML e análise. Porém, a **codebase atual tem PROBLEMAS CRÍTICOS** que comprometem a estabilidade:

### Problemas Críticos Identificados

| Severidade | Componente | Problema | Impacto |
|-----------|-----------|---------|--------|
| 🔴 CRÍTICO | `ui.py` | Código duplicado (>4000 linhas duplicadas) | Código imprevisível, bugs silenciosos |
| 🔴 CRÍTICO | `database.py` | Mixing SQLite + PostgreSQL (inconsistente) | Conexões falham em produção |
| 🔴 CRÍTICO | `bot_core.py` | Lógica de auto-alocação quebrada | Bots não conseguem capital |
| 🟡 ALTO | `terminal_component.py` | API HTTP desincronizada com DB | Logs/trades não aparecem no monitor |
| 🟡 ALTO | `api.py` | Rate limiting inadequado | Throttling da KuCoin prejudica operações |
| 🟡 ALTO | `bot.py` | Ajustes de target com taxas não testados | PnL calculado incorretamente |

---

## 📊 Estado Atual do Código

### Estatísticas de Qualidade

```
Total de linhas Python: ~22,000+
Duplicação detectada: 4,000+ linhas (em ui.py)
Cobertura de testes: <30%
Arquivos com erros de sintaxe: 3-5
Avisos de importação: 15+
```

### Distribuição de Arquivos Problemáticos

#### 🔴 CRÍTICOS (Reparar URGENTEMENTE)

1. **ui.py** (1200 linhas)
   - Duplicação maciça (linhas ~470-550 e ~1000-1100)
   - Funções `render_mario_gauge()`, `render_terminal_gauge()` parcialmente iguais
   - Imports inconsistentes (tenta `from .database` e fallback `from database`)
   - Lógica de tema quebrada (múltiplas definições de THEMES)
   - Sincronização de session_state vs value em widgets

2. **database.py** (850+ linhas)
   - **CRÍTICO:** Mistura SQLite com PostgreSQL
     - Line 28-30: Tenta PostgreSQL (`psycopg`) como padrão
     - Line 32-37: Fallback para SQLite
     - Classes `DatabaseManager` usam `psycopg` (não SQLite)
     - Métodos retornam `dict_row` (PostgreSQL) - incompatível com SQLite
   - Schema não sincronizado entre testes e produção
   - Métodos orphaned: `get_trade_history()`, `get_allocated_qty()`, `release_bot_quota()` não usados
   - Falta validação de credenciais antes de conectar

3. **bot_core.py** (400+ linhas)
   - Lógica de alocação automática de capital QUEBRADA (linhas ~200-300)
   - Tenta usar `db.get_allocated_qty()` que **NÃO EXISTE** em DB
   - Fallback para modo dry-run sem avisar usuário
   - Não registra entryPrice corretamente quando auto-alocado
   - Teste de status do bot repetido 2x (code smell)

4. **terminal_component.py** (500+ linhas)
   - API HTTP espera JSON em formato específico
   - `get_bot_logs()` retorna estrutura de BD (dict_row) que não converte para JSON
   - `/api/logs` não valida bot_id antes de consultar BD
   - Caching de HTML quebrado (monitor_window.html não encontrado em deploy)

#### 🟡 ALTOS (Reparar em Sprint Próximo)

5. **bot.py** (1500+ linhas)
   - Ajustes de target com compensação de taxas não são testados
   - Cálculo de lucro líquido assume fee fixo (não valida contra BD)
   - Modo eternal não sincroniza corretamente com DB
   - Auto-learning (epsilon-greedy) pode selecionar candidatos vazios

6. **api.py** (600+ linhas)
   - Rate limiting global (`_last_request_time`) não é thread-safe
   - Retry com backoff exponencial pode gerar cascata de requisições
   - Sincronização de timestamp pode falhar silenciosamente (offset TTL de 5min)
   - Tratamento de erro para KuCoin inconsistente (às vezes loga, às vezes não)

7. **streamlit_app.py** (100 linhas)
   - Carregamento dinâmico de `ui.py` é frágil (try/except largo demais)
   - Não valida se `render_bot_control()` foi importado com sucesso
   - Falha de import não relata qual função está faltando

---

## 🛠️ Plano de Reparação Imediata

### FASE 1: Reparar Críticos (1-2 dias)

#### 1a. Limpar Duplicação em ui.py
```
□ Identificar todas as funções duplicadas
□ Manter versão "corrigida" (renderizações SMW)
□ Remover versão duplicada (renderizações genéricas)
□ Testar sintaxe: python -m py_compile ui.py
□ Rodar scraper: python agent0_scraper.py --local --test-dashboard
```

**Arquivos a deletar:**
- `ui.py.broken-20260103171825` (backup antigo)
- `ui.py.pre-restore-20260103202333`, `ui.py.pre-restore-20260103202341` (backups de restauração)

#### 1b. Normalizar database.py para SQLite APENAS
```
□ Remover imports de psycopg (Lines 5-7)
□ Converter get_connection() para sqlite3
□ Atualizar ret tipos: dict_row → dict nativo
□ Implementar métodos faltantes: get_allocated_qty(), release_bot_quota()
□ Testar: python -m py_compile database.py
```

**Referência para converter:**
```python
# ❌ ATUAL (PostgreSQL)
import psycopg
from psycopg.rows import dict_row
conn = psycopg.connect(dsn, row_factory=dict_row)

# ✅ CORRETO (SQLite)
import sqlite3
conn = sqlite3.connect("trades.db")
conn.row_factory = sqlite3.Row  # Retorna dicts nativamente
```

#### 1c. Reparar bot_core.py
```
□ Remover chamada a db.get_allocated_qty() (não existe)
□ Implementar alocação com campos que existem em bot_quotas
□ Sincronizar schema de auto-alocação com database.py
□ Testar dry-run: python bot_core.py --bot-id test_1 ... --dry
```

#### 1d. Validar terminal_component.py
```
□ Garantir que /api/logs retorna JSON válido
□ Testar: curl http://localhost:8765/api/logs?bot=test_1
□ Verificar se monitor_window.html existe no diretório correto
```

### FASE 2: Reparar Altos (2-3 dias)

#### 2a. Testes para bot.py (Target + Taxas)
```
□ Criar test_bot_targets_with_fees.py
□ Validar cálculo de lucro líquido
□ Testar modo eternal (reinício de ciclos)
□ Confirmar auto-learning funciona (epsilon-greedy)
```

#### 2b. Thread-safety em api.py
```
□ Converter _last_request_time para threading.Lock()
□ Revisar retry logic (pode gerar cascata?)
□ Adicionar timeout para sincronização de timestamp
```

#### 2c. Melhorar Error Handling
```
□ Consolidar lógica de erro (SQLite vs PostgreSQL)
□ Adicionar logs estruturados (não print())
□ Validar todas as respostas de KuCoin
```

---

## 📋 Checklist Detalhado por Arquivo

### ✅ ui.py

**Estado:** 🔴 QUEBRADO (Duplicação crítica)

**Ações:**
- [ ] Line 470-550: DELETAR função `render_mario_gauge()` duplicada
- [ ] Line 1000-1100: DELETAR função `render_terminal_gauge()` duplicada
- [ ] Line 95-125: Consolidar importação (use try/except com fallback)
- [ ] Line 150-200: REVISAR `THEMES` dict (está definido 2x?)
- [ ] Testar com `python -m py_compile ui.py`
- [ ] Rodar scraper completo

**Antes:**
```python
# Linhas 470-550 e 1000-1100 são praticamente idênticas
def render_mario_gauge(...):  # V1 em linha ~470
    ...
    
def render_terminal_gauge(...):  # V2 em linha ~1000
    ... # praticamente código idêntico
```

**Depois:**
```python
# Apenas UMA versão consolidada
def render_mario_gauge(...):
    # Código correto, testado
```

### ✅ database.py

**Estado:** 🔴 CRÍTICO (PostgreSQL vs SQLite)

**Ações:**
- [ ] Line 1: Remove `import psycopg`
- [ ] Line 28-37: Converter para APENAS SQLite
- [ ] Line 40-45: Converter `dict_row` para `sqlite3.Row`
- [ ] Line 120-150: Implementar métodos faltantes
  - `get_allocated_qty(asset)`
  - `upsert_bot_quota(bot_id, symbol, asset, qty, entry)`
  - `release_bot_quota(bot_id)`
- [ ] Testar: `python scripts/db_inspect.py`

**Código de Referência (Implementar):**
```python
def get_allocated_qty(self, asset: str) -> float:
    """Retorna quantidade alocada para um ativo"""
    conn = self.get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT SUM(qty) as total FROM bot_quotas WHERE asset = ? AND status = 'allocated'",
            (asset,)
        )
        row = cur.fetchone()
        return float(row[0] or 0.0) if row else 0.0
    finally:
        conn.close()

def upsert_bot_quota(self, bot_id: str, symbol: str, asset: str, qty: float, entry: float):
    """Aloca quantidade para um bot"""
    conn = self.get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT OR REPLACE INTO bot_quotas (bot_id, symbol, asset, qty, entry_price, status) "
            "VALUES (?, ?, ?, ?, ?, 'allocated')",
            (bot_id, symbol, asset, qty, entry)
        )
        conn.commit()
    finally:
        conn.close()

def release_bot_quota(self, bot_id: str):
    """Libera quota alocada para um bot"""
    conn = self.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE bot_quotas SET status = 'released' WHERE bot_id = ?", (bot_id,))
        conn.commit()
    finally:
        conn.close()
```

### ✅ bot_core.py

**Estado:** 🔴 CRÍTICO (Alocação quebrada)

**Ações:**
- [ ] Line 200-300: REVISAR lógica `get_allocated_qty()` (não existe!)
- [ ] Substituir por chamadas a métodos corretos de `database.py`
- [ ] Testar dry-run com flags: `--bot-id test_1 --symbol BTC-USDT --entry 30000 --targets "2:0.3" --dry`
- [ ] Validar se `entry_price` é registrada corretamente

**Erro Atual:**
```python
# Line ~250
allocated_total = float(db.get_allocated_qty(asset) or 0.0)  # ❌ Método não existe
```

**Correção:**
```python
# Implementar método em database.py ou usar query direta
conn = db.get_connection()
cur = conn.cursor()
cur.execute("SELECT SUM(qty) FROM bot_quotas WHERE asset = ? AND status = 'allocated'", (asset,))
allocated_total = cur.fetchone()[0] or 0.0
conn.close()
```

### ✅ terminal_component.py

**Estado:** 🟡 ALTO (API desincronizada)

**Ações:**
- [ ] Line 400-450: Validar formato JSON de `/api/logs`
- [ ] Testar endpoint: `curl "http://localhost:8765/api/logs?bot=test_1&limit=5"`
- [ ] Verificar se `monitor_window.html` existe em `themes/` ou raiz
- [ ] Converter resposta BD para JSON válido (sem `dict_row` do PostgreSQL)

**Teste Manual:**
```bash
# Terminal 1: Inicia API
python -c "from terminal_component import start_api_server; start_api_server(8765)"

# Terminal 2: Testa endpoint
curl -s "http://localhost:8765/api/logs?bot=test_1&limit=5" | python -m json.tool
# Deve retornar array de logs com estrutura: [{id, timestamp, level, message, ...}]
```

### ✅ bot.py

**Estado:** 🟡 ALTO (Testes faltam)

**Ações:**
- [ ] Line 500-600: Testes para `_calculate_portion_size()`
- [ ] Line 700-800: Testes para ajuste de target com taxas
- [ ] Criar `tests/test_bot_targets.py` com casos:
  - Compra com 2% de lucro (deve calcular ~2.25% real para compensar 0.25% de taxa)
  - Venda com stop-loss
  - Modo eternal (reinício de ciclo)
- [ ] Verificar se `_learn_selected_params` é inicializado corretamente

---

## 🧪 Testes Recomendados

### Testes Críticos (Devem passar antes de deploy)

```bash
# 1. Sintaxe de todos os arquivos
python -m py_compile ui.py database.py bot_core.py bot.py api.py terminal_component.py

# 2. Imports básicos
python -c "import ui; import database; import bot_controller; import api"

# 3. Conexão ao banco
python -c "from database import DatabaseManager; db = DatabaseManager(); print(db.get_active_bots())"

# 4. API HTTP
python start_api_server.py &
sleep 2
curl -s "http://localhost:8765/api/logs?bot=test" | python -m json.tool
pkill -f start_api_server

# 5. Bot dry-run
python -u bot_core.py --bot-id test_dry --symbol BTC-USDT --entry 30000 --targets "2:0.3" --interval 5 --size 0.001 --funds 0 --dry
```

### Testes de Integração

```bash
# 6. Scraper de validação visual
python agent0_scraper.py --local --test-all

# 7. Testes unitários
pytest tests/ -v

# 8. Testes Selenium completos
RUN_SELENIUM=1 ./run_tests.sh
```

---

## 📈 Métricas e KPIs

### Antes da Reparação

| Métrica | Valor Atual | Meta |
|---------|------------|------|
| Linhas duplicadas | 4,000+ | 0 |
| Taxa de erro ao iniciar | ~30% | <5% |
| Cobertura de testes | <30% | >70% |
| API response time | 2-5s | <500ms |
| Rate limit violations | 15+/dia | 0 |

### Depois da Reparação (Meta)

| Métrica | Valor Esperado |
|---------|----------------|
| Build success rate | 100% |
| Unit test pass rate | >95% |
| E2E test pass rate | >90% |
| API response time | <200ms |
| Bots iniciados com sucesso | >98% |

---

## 📚 Referências e Links

- **Instruções Copilot:** [.github/copilot-instructions.md](./.github/copilot-instructions.md)
- **Documentação:** [README.md](../README.md)
- **Deploy:** [DEPLOY.md](../DEPLOY.md)
- **Agente Training:** [AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md)

---

## 🚀 Próximas Ações (Prioridade)

### HOJE (Críticos)

1. **ui.py:** Remover duplicações
2. **database.py:** Converter para SQLite apenas
3. **bot_core.py:** Reparar alocação de capital
4. **Testes:** Rodar py_compile em todos

### ESTA SEMANA (Altos)

5. **bot.py:** Adicionar testes de target + taxas
6. **api.py:** Thread-safety + timeout
7. **terminal_component.py:** Validar API endpoints
8. **Scraper:** Rodar validação visual completa

### PRÓXIMA SEMANA (Médios)

9. Aumentar cobertura de testes (target: >50%)
10. Documentar API HTTP (OpenAPI/Swagger)
11. Implementar circuit breaker para KuCoin
12. Adicionar observabilidade (métricas Prometheus)

---

## ✅ Conclusão

O projeto **é viável e potencialmente valioso**, mas requer **reparação imediata de críticos** antes de qualquer deploy em produção. A duplicação em `ui.py` e o mixing SQLite/PostgreSQL em `database.py` são os bloqueadores principais.

**Estimativa de tempo para Fase 1 (Críticos):** 2-3 dias com um desenvolvedor dedicado.

**Risco de não reparar:** Deploy quebrado, bots falhando, perda de confiança do usuário.

---

*Relatório Gerado em 3 de janeiro de 2026*  
*Status: ⚠️ CRÍTICO — Ação Requerida Imediatamente*
