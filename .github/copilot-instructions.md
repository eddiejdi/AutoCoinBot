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
