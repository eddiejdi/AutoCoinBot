# 🤖 Manual de Treinamento - Agente Dev Sênior

## AutoCoinBot - KuCoin Trading Bot Application

**Versão:** 2.0.0  
**Última atualização:** Janeiro 2026  
**Responsável:** Equipe AutoCoinBot

---

## 📋 Índice

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
4. [Fluxos Principais](#fluxos-principais)
5. [Padrões e Convenções](#padrões-e-convenções)
6. [Testes e Validação](#testes-e-validação)
7. [Troubleshooting](#troubleshooting)
8. [Agentes Especializados](#agentes-especializados)
9. [Checklist de Alterações](#checklist-de-alterações)

---

## 🎯 Visão Geral do Projeto

### Objetivo
AutoCoinBot é uma aplicação de trading automatizado para a exchange KuCoin, com interface Streamlit para gerenciamento de bots, visualização de trades e análise de performance.

### Stack Tecnológico
| Componente | Tecnologia |
|------------|------------|
| Frontend | Streamlit |
| Backend | Python 3.11+ |
| Banco de Dados | PostgreSQL (psycopg) |
| API Trading | KuCoin REST API |
| Testes E2E | Selenium + Chrome |
| Deploy | Docker, Fly.io |

### Arquivos Principais

```
AutoCoinBot/
├── streamlit_app.py      # Entry point da aplicação
├── ui.py                 # Componentes UI e lógica de interface
├── bot_controller.py     # Gerenciamento de subprocessos de bots
├── bot_core.py           # Lógica principal do bot de trading
├── bot.py                # Classe Bot com estratégias
├── database.py           # Schema e helpers do banco de dados
├── api.py                # Integração com KuCoin API
├── terminal_component.py # API HTTP para terminal widget
├── agent0_scraper.py     # Scraper Selenium para validação visual
└── agents/               # Agentes especializados
    └── os_cleaner_agent.py
```

---

## 🏗️ Arquitetura do Sistema

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT APP (ui.py)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │Dashboard │  │ Trading  │  │ Learning │  │ Terminal │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼───────────────┼───────────────┼───────┘
        │             │               │               │
        ▼             ▼               ▼               ▼
┌───────────────────────────────────────────────────────────┐
│                  BOT CONTROLLER                            │
│            (Gerencia subprocessos de bots)                 │
└───────────────────────┬───────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐
   │ Bot #1  │    │ Bot #2  │    │ Bot #N  │
   │bot_core │    │bot_core │    │bot_core │
   └────┬────┘    └────┬────┘    └────┬────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              ┌────────────────┐
              │  DATABASE.PY   │
              │  (PostgreSQL)  │
              └────────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   bot_sessions    bot_logs       trades
```

### Tabelas do Banco de Dados (PostgreSQL)

| Tabela | Descrição |
|--------|-----------|
| `bot_sessions` | Sessões de bots (id, status, PID, config) |
| `bot_logs` | Logs em tempo real dos bots |
| `trades` | Histórico de trades executados |
| `learning_stats` | Estatísticas de aprendizado ML |
| `learning_history` | Histórico de treinamento |

---

## 💻 Ambiente de Desenvolvimento

### Setup Inicial

```bash
# 1. Clonar repositório
git clone https://github.com/eddiejdi/AutoCoinBot.git
cd AutoCoinBot

# 2. Criar e ativar venv
python3 -m venv venv
source venv/bin/activate  # Linux/macOS/WSL
# ou: .\venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais KuCoin
```

### Variáveis de Ambiente

```bash
# .env
APP_ENV=dev                    # dev | hom | prod
LOCAL_URL=http://localhost:8501
HOM_URL=https://autocoinbot-hom.streamlit.app/

# KuCoin API
API_KEY=sua_api_key
API_SECRET=seu_api_secret
API_PASSPHRASE=sua_passphrase

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/autocoinbot
# TRADES_DB é um alias para DATABASE_URL (compatibilidade)
TRADES_DB=postgresql://user:password@localhost:5432/autocoinbot
```

### Executando a Aplicação

```bash
# Terminal 1: Streamlit
python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true

# Terminal 2: Bot (dry-run)
python -u bot_core.py --bot-id test_1 --symbol BTC-USDT --entry 30000 --targets "2:0.3,5:0.4" --interval 5 --size 0.001 --funds 20 --dry
```

---

## 🔄 Fluxos Principais

### 1. Iniciar Bot via UI

```
Usuário preenche form → ui.py valida → BotController.start_bot() 
→ subprocess(bot_core.py) → insert_bot_session() [PostgreSQL] → bot roda em background
```

### 2. Visualizar Logs em Tempo Real

```
UI renderiza terminal → fetch /api/logs?bot=<id> → terminal_component.py 
→ DatabaseManager.get_bot_logs() → JSON response → UI atualiza
```

### 3. Executar Trade

```
Bot detecta sinal → api.py create_order() → KuCoin API → resposta 
→ insert_trade() → atualiza bot_logs → UI reflete
```

---

## 📏 Padrões e Convenções

### Código Python

```python
# ✅ BOM: Use DatabaseLogger para logs
from database import DatabaseLogger
logger = DatabaseLogger(bot_id="meu_bot")
logger.log("Mensagem importante", level="INFO")

# ❌ RUIM: Não use print() em código de produção
print("Debug message")  # Evitar!

# ✅ BOM: Type hints
def calcular_profit(entry: float, exit: float) -> float:
    return ((exit - entry) / entry) * 100

# ✅ BOM: Docstrings
def start_bot(symbol: str, entry: float) -> str:
    """
    Inicia um novo bot de trading.
    
    Args:
        symbol: Par de trading (ex: BTC-USDT)
        entry: Preço de entrada
        
    Returns:
        bot_id: ID único do bot criado
    """
    pass
```

### Estrutura de Arquivos

| Tipo | Local |
|------|-------|
| Documentação | `docs/` |
| Scripts/utilitários | `scripts/` |
| Screenshots/imagens | `docs/reports/images/` |
| Dados/configs | `data/` |
| Relatórios | `docs/reports/` |
| Agentes | `agents/` |
| Testes | `tests/` |

### Commits

```bash
# Formato: <tipo>(<escopo>): <descrição>
git commit -m "feat(bot): adiciona stop-loss dinâmico"
git commit -m "fix(ui): corrige renderização do terminal"
git commit -m "docs(readme): atualiza instruções de setup"
git commit -m "test(selenium): adiciona teste de start bot"
```

---

## 🧪 Testes e Validação

### Verificações Obrigatórias

```bash
# 1. Verificar sintaxe
python -m py_compile arquivo.py

# 2. Rodar testes unitários
pytest tests/

# 3. Rodar testes E2E (requer Chrome + chromedriver)
RUN_SELENIUM=1 ./run_tests.sh

# 4. Validação visual com scraper
python agent0_scraper.py --local --test-all
```

### Testes do Scraper

```bash
# Validar tela inicial
python agent0_scraper.py --local --test-dashboard

# Testar start de bot (dry-run seguro)
python agent0_scraper.py --local --test-bot-start

# Todos os testes
python agent0_scraper.py --local --test-all

# Apenas análise (sem ação)
python agent0_scraper.py --local --analyze
```

### Relatórios de Teste

Após falhas, gerar relatório:
- `relatorio_validacao.md` - Relatório consolidado
- `relatorio_validacao_attempt_N.md` - Tentativas individuais
- `screenshot_*.png` - Capturas de tela

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Bots não aparecem no dashboard
```python
# Verificar:
# 1. database.py → get_active_bots() retornando corretamente
# 2. ui.py → consumindo dados do banco (não apenas memória)
# 3. bot_sessions → status = 'running'

# Diagnóstico:
python scripts/db_inspect.py
# Verificar sessões ativas no PostgreSQL:
psql "$DATABASE_URL" -c "SELECT * FROM bot_sessions WHERE status='running'"
```

#### 2. Erro de conexão no Selenium (WSL)
```bash
# O Chrome no WSL não acessa localhost do Windows
# Solução: Rodar Streamlit no WSL também
wsl -d Ubuntu -e bash -c "cd /home/user/AutoCoinBot && source venv/bin/activate && python -m streamlit run streamlit_app.py"
```

#### 3. Gráficos de aprendizado não aparecem
```bash
# Verificar tabelas no PostgreSQL:
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM learning_stats;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM learning_history;"

# Verificar métodos em DatabaseManager:
# - get_learning_stats()
# - get_learning_history()
# - get_learning_symbols()
```

#### 4. Frontend quebrado após alterações
```bash
# Sempre verificar sintaxe:
python -m py_compile ui.py
python -m py_compile streamlit_app.py

# Verificar erros no navegador:
# F12 → Console → procurar erros JavaScript
```

#### 5. Disco cheio (Windows/WSL)
```bash
# Usar agente de limpeza:
python agents/os_cleaner_agent.py --analyze    # Ver o que pode limpar
python agents/os_cleaner_agent.py --dry-run    # Simular
python agents/os_cleaner_agent.py              # Executar limpeza
```

#### 6. Copilot Chat: “Response contained no choices”
Passos rápidos (em ordem):
- Reduza o prompt (escopo: 1 arquivo/trecho; sem anexos grandes). Veja .github/copilot-prompts.md.
- Developer: Reload Window e reautentique no GitHub (Accounts). Atualize as extensões “GitHub Copilot” e “GitHub Copilot Chat”.
- Copilot Chat: Reset Chat.
- Verifique View → Output → “GitHub Copilot Chat” (401/403 reautenticar; 429 aguardar; 5xx instabilidade).
- Em Dev Container/WSL: Dev Containers: Rebuild and Reopen in Container.

Referências:
- Guia TL;DR e fallback: .github/copilot-instructions.md
- Prompts curtos e resilientes: .github/copilot-prompts.md

---

## 🤖 Agentes Especializados

### OS Cleaner Agent

Agente para limpeza de sistema operacional (Windows/Linux/macOS).

```bash
# Uso básico
python agents/os_cleaner_agent.py --help
python agents/os_cleaner_agent.py --analyze
python agents/os_cleaner_agent.py --target browser temp cache

# Como módulo
from agents import OSCleanerAgent
agent = OSCleanerAgent(dry_run=True)
report = agent.run()
```

**Alvos disponíveis:**

| Windows | Linux/WSL | macOS |
|---------|-----------|-------|
| temp, cache, logs, browser, thumbnails | temp, cache, logs, browser, thumbnails | temp, cache, logs, browser, thumbnails |
| windows_update, prefetch, recycle_bin, delivery_optimization | apt, journal, trash | xcode, trash, ios_backup |

### Scraper Agent (agent0_scraper.py)

Agente de validação visual com Selenium.

```bash
# Validação completa
python agent0_scraper.py --local --test-all

# Apenas análise
python agent0_scraper.py --local --test-dashboard

# Teste de start de bot
python agent0_scraper.py --local --test-bot-start
```

**Funcionalidades:**
- Validação da tela inicial (dashboard)
- Teste de start de bot (dry-run)
- Detecção de elementos (header, inputs, buttons, sections)
- Login automático
- Screenshots e relatórios

---

## ✅ Checklist de Alterações

Antes de fazer commit/PR, verificar:

### Alterações em bot_core.py ou bot_controller.py
- [ ] Atualizar CLI args em ambos os arquivos
- [ ] Testar dry-run: `python bot_core.py --dry ...`
- [ ] Verificar `bot_sessions` no banco

### Alterações em database.py
- [ ] Atualizar todos os callers das funções modificadas
- [ ] Documentar mudanças de schema
- [ ] Rodar `python -m py_compile database.py`

### Alterações em ui.py
- [ ] Verificar sintaxe: `python -m py_compile ui.py`
- [ ] Testar navegação por tabs
- [ ] Validar com scraper: `python agent0_scraper.py --local --test-dashboard`

### Alterações em terminal_component.py
- [ ] Preservar shape do JSON de resposta
- [ ] Manter headers CORS
- [ ] Testar endpoint: `curl http://localhost:8765/api/logs?bot=test`
- [ ] **Segurança/Segredos**
    - [ ] Rodar `pre-commit install` e verificar `ggshield` localmente
    - [ ] Configurar `GITGUARDIAN_API_KEY` no repositório para habilitar scan no CI
    - [ ] Se um segredo vazar, remover do código, rotacionar e (se necessário) reescrever histórico da branch

### Alterações em API/integração KuCoin
- [ ] Testar em dry-run primeiro
- [ ] Verificar rate limits
- [ ] Validar tratamento de erros

---

## 🛡️ Política de Segurança

### Regras Obrigatórias

1. **Nunca commitar credenciais** - Use `.env` ou `st.secrets`
2. **Sempre testar em dry-run** antes de executar trades reais
3. **Validar entradas do usuário** em todos os forms
4. **Logar todas as operações** críticas via DatabaseLogger
5. **Manter backups** do banco de dados antes de migrações

### Rate Limits KuCoin

| Endpoint | Limite |
|----------|--------|
| Spot Trading | 30 req/3s |
| Market Data | 10 req/3s |
| Account Info | 10 req/3s |

---

## 📚 Referências

- [Copilot Instructions](.github/copilot-instructions.md) - Instruções para IA
- [README](README.md) - Documentação geral
- [DEPLOY](DEPLOY.md) - Instruções de deploy
- [AUTH_README](AUTH_README.md) - Sistema de autenticação
- [OS Cleaner README](agents/OS_CLEANER_README.md) - Agente de limpeza

---

## 📞 Contato e Suporte

- **Repositório:** https://github.com/eddiejdi/AutoCoinBot
- **Issues:** Abrir issue no GitHub para bugs/features
- **Mantenedor:** Manter o proprietário informado sobre alterações de comportamento dos agentes

---

## 🔄 Histórico de Atualizações

| Data | Versão | Descrição |
|------|--------|-----------|
| Jan 2026 | 2.0.0 | Reestruturação completa, adição de agentes especializados |
| Dez 2025 | 1.1.0 | Adição de testes Selenium e scraper |
| Nov 2025 | 1.0.0 | Versão inicial |

---

*Este documento deve ser atualizado sempre que houver mudanças significativas na arquitetura, fluxos ou convenções do projeto.*
