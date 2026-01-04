#!/bin/bash
# Quick Start - Selenium Tests

# 🚀 EXECUÇÃO RÁPIDA
# ==================

# 1. Local (desenvolvimento)
./run_selenium_tests.sh

# 2. Homologação
./run_selenium_tests.sh hom

# 3. Com browser visível
./run_selenium_tests.sh show

# 4. Porta customizada
LOCAL_URL=http://localhost:8506 ./run_selenium_tests.sh


# 📁 ESTRUTURA
# ============

# tests/selenium/
#   ├── pages/              # Page Objects (7 arquivos)
#   ├── screenshots/        # Capturas automáticas
#   ├── reports/            # Relatórios de teste
#   ├── test_all_pages.py   # Suite completa (36 testes)
#   ├── config.py           # Configuração
#   ├── run_tests.sh        # Script Linux/macOS
#   ├── run_tests.bat       # Script Windows
#   └── README.md           # Documentação completa


# 🧪 TESTES INCLUÍDOS
# ===================

# Dashboard (10 testes)
#   - Header, Bots list, LOG/RELATÓRIO buttons, Último Evento, etc.

# Trading Form (7 testes)
#   - Inputs (Bot ID, Symbol, Entry, Size), Checkboxes, Start button

# Learning (4 testes)
#   - Header, Stats, History, Charts

# Trades (6 testes)
#   - Table, Filters, Toggles, Summary

# Monitor (4 testes)
#   - HTML page, Logs, Actions

# Report (5 testes)
#   - HTML page, Summary cards, Charts, Table


# 📊 RELATÓRIOS
# ============

# Após executar, veja:
#   - Screenshots: tests/selenium/screenshots/
#   - Relatórios: tests/selenium/reports/
#   - Console: output detalhado


# ⚙️ VARIÁVEIS
# ============

export APP_ENV=dev              # dev, hom, prod
export LOCAL_URL=localhost:8501 # URL local
export HEADLESS=1               # 1=sem UI, 0=com browser
export TAKE_SCREENSHOTS=1       # Salvar screenshots
export SAVE_DOM=1               # Salvar HTML


# 🔧 TROUBLESHOOTING
# ==================

# Chrome não encontrado:
#   sudo apt install google-chrome-stable

# Erro em container/WSL:
#   sudo apt install xvfb
#   xvfb-run ./run_selenium_tests.sh

# Timeout:
#   PAGE_LOAD_TIMEOUT=60 ./run_selenium_tests.sh


# 📚 DOCUMENTAÇÃO COMPLETA
# ========================

# Ver: tests/selenium/README.md
# Ou: SELENIUM_EXPANSION_2026-01-04.md
