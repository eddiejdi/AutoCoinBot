# Copilot Instructions — AutoCoinBot (versão compacta)

> **📚 Base de conhecimento completa**: [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md)
> **🤖 Manual de treinamento**: [../AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md)

---

## 🎯 Objetivo

Streamlit UI controla subprocessos de bots de trading KuCoin. Logs/trades em PostgreSQL. Terminal HTTP local para UI em tempo real.

---

## 🏗️ Arquitetura (TL;DR)

```
streamlit_app.py → ui.py → bot_controller.py → subprocess(bot_core.py)
                              ↓                        ↓
                        bot_sessions (DB)        bot_logs/trades (DB)
                                                       ↑
                              terminal_component.py ←──┘ (HTTP :8765)
```

**Produção (Fly.io)**:
```
nginx (:8080) → Streamlit (:8501) [/]
             → API HTTP (:8765)   [/api/*, /monitor, /report]
```

---

## ⚡ Comandos Essenciais

```bash
# Setup
source venv/bin/activate && pip install -r requirements.txt

# Rodar UI
python -m streamlit run streamlit_app.py --server.port=8501

# Bot dry-run
python -u bot_core.py --bot-id test --symbol BTC-USDT --entry 90000 --targets "2:0.3" --interval 5 --size 0.001 --funds 0 --dry

# Testes
python -m py_compile arquivo.py  # Sintaxe
./run_tests.sh                   # Pytest
RUN_SELENIUM=1 ./run_tests.sh    # E2E
```

---

## 🚫 Regras Críticas

1. **Nunca `print()`** → Use `DatabaseLogger`
2. **CLI sync**: `bot_core.py` args ↔ `bot_controller.py` cmd builder
3. **Widgets**: `session_state` OU `value=`, nunca ambos
4. **URLs**: Relativas em prod (`FLY_APP_NAME`), absolutas em dev
5. **Blocos homologados**: Ver [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md)

---

## 🔧 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| Loading eterno | Verificar conflito `session_state` + `value=` |
| Bot não aparece | `cleanup_dead_bots.py` ou verificar PID |
| Erro 401 KuCoin | Timestamp sync automático via `_sync_time_offset()` |
| Selenium WSL | Rodar Streamlit dentro do WSL |

---

## 📋 Checklist PR

- [ ] `python -m py_compile` nos arquivos alterados
- [ ] CLI alterado? Sincronizar `bot_core.py` ↔ `bot_controller.py`
- [ ] Schema alterado? Atualizar callers
- [ ] UI alterada? Testar navegação + themes
- [ ] Não mexeu em blocos homologados

---

## 📚 Referências Completas

- **Base de Conhecimento**: [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md)
- **Manual Treinamento**: [../AGENTE_TREINAMENTO.md](../AGENTE_TREINAMENTO.md)
- **Agentes**: [agents.json](agents.json)
