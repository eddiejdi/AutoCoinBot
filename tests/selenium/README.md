# Selenium Test Suite - README

## 📁 Estrutura

```
tests/selenium/
├── pages/                    # Page Object Models
│   ├── base_page.py         # Classe base para todas as páginas
│   ├── dashboard_page.py    # Dashboard (lista de bots ativos)
│   ├── trading_page.py      # Formulário de início de bot
│   ├── learning_page.py     # Estatísticas de aprendizado ML
│   ├── trades_page.py       # Histórico de trades
│   ├── monitor_page.py      # Monitor em tempo real (HTML)
│   └── report_page.py       # Relatório de performance (HTML)
├── screenshots/             # Screenshots de teste (auto-gerado)
├── reports/                 # Relatórios de teste (auto-gerado)
├── config.py               # Configuração centralizada
├── test_all_pages.py       # Suite completa de testes
├── run_tests.sh            # Script Linux/macOS
└── run_tests.bat           # Script Windows
```

## 🚀 Uso Rápido

### Linux/macOS/WSL

```bash
# Local (dev)
cd tests/selenium
./run_tests.sh

# Homologação
APP_ENV=hom ./run_tests.sh

# Com browser visível
HEADLESS=0 ./run_tests.sh

# URL customizada
LOCAL_URL=http://localhost:8506 ./run_tests.sh
```

### Windows (PowerShell)

```powershell
cd tests\selenium
.\run_tests.bat

# Homologação
$env:APP_ENV="hom"; .\run_tests.bat

# Com browser visível
$env:HEADLESS="0"; .\run_tests.bat
```

### Python Direto

```bash
# Suite completa
python test_all_pages.py

# Com configuração
LOCAL_URL=http://localhost:8506 HEADLESS=0 python test_all_pages.py
```

## 🧪 Testes Incluídos

### Dashboard Page (6 testes)
- ✅ Header "Bots Ativos"
- ✅ Mensagem "Nenhum bot ativo" (quando aplicável)
- ✅ Botões LOG (links HTML com target="_blank")
- ✅ Botões RELATÓRIO (links HTML com target="_blank")
- ✅ Coluna "Último Evento"
- ✅ Botões Kill/Stop
- ✅ Checkboxes de seleção
- ✅ Barras de progresso
- ✅ Exibição de profit
- ✅ Estrutura de URLs (relativas vs absolutas)

### Trading Page (7 testes)
- ✅ Formulário completo (Bot ID, Symbol, Entry, Size, Interval)
- ✅ Checkboxes (Dry Run, Eternal Mode)
- ✅ Seção de Targets
- ✅ Botão Start Bot
- ✅ Stop Loss inputs
- ✅ Mensagens de sucesso/erro

### Learning Page (4 testes)
- ✅ Header da página
- ✅ Seção de estatísticas
- ✅ Seção de histórico
- ✅ Cards de parâmetros
- ✅ Gráficos
- ✅ Dados de aprendizado

### Trades Page (6 testes)
- ✅ Header da página
- ✅ Filtros (Symbol, Bot, Date)
- ✅ Toggles (Only Real, Group by Bot)
- ✅ Tabela de trades
- ✅ Ordens BUY/SELL
- ✅ Exibição de profit
- ✅ Resumo (Total Trades, Profit, Win Rate)
- ✅ Gráficos

### Monitor Page (4 testes)
- ✅ Header da página
- ✅ Container de logs
- ✅ Entradas de log
- ✅ Status (Running/Stopped)
- ✅ Botões de ação (Home, Refresh)
- ✅ Auto-scroll toggle

### Report Page (5 testes)
- ✅ Header da página
- ✅ Cards de resumo (Total Trades, Profit, Win Rate)
- ✅ Gráficos (Profit, Trades)
- ✅ Tabela de trades
- ✅ Botões de ação (Home, Export)

**Total: 32+ testes cobrindo todas as telas**

## ⚙️ Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `APP_ENV` | `dev` | Ambiente (dev, hom, prod) |
| `LOCAL_URL` | `http://localhost:8501` | URL local |
| `HOM_URL` | `https://autocoinbot.fly.dev` | URL homologação |
| `HEADLESS` | `1` | Rodar sem interface (0/1) |
| `SHOW_BROWSER` | `0` | Mostrar browser (0/1) |
| `TAKE_SCREENSHOTS` | `1` | Salvar screenshots (0/1) |
| `SAVE_DOM` | `1` | Salvar DOM HTML (0/1) |
| `PAGE_LOAD_TIMEOUT` | `30` | Timeout de carregamento (s) |
| `ELEMENT_WAIT_TIMEOUT` | `10` | Timeout de elemento (s) |
| `VERBOSE` | `0` | Modo verboso (0/1) |

## 📊 Relatórios

### Formato do Relatório

```
═══════════════════════════════════════════════════════════════
🧪 AutoCoinBot - Complete Test Suite Report
URL: http://localhost:8501
Time: 2026-01-04 16:30:00
═══════════════════════════════════════════════════════════════

📊 SUMMARY: 30/32 tests passed (2 failed)

📋 Dashboard Page (8/8 passed):
  ✅ PASS Dashboard Header
  ✅ PASS Log Buttons (2) - Found with target=_blank
  ✅ PASS Report Buttons (2) - Found with target=_blank
  ...

📋 Trading Page (7/7 passed):
  ✅ PASS Trading Form - Bot ID
  ✅ PASS Trading Form - Symbol
  ...

❌ Failed Tests:
  - Monitor Log Entries: Not found
  - Report Profit Chart: Not found

📸 Artifacts:
  Screenshots: tests/selenium/screenshots
  Reports: tests/selenium/reports
```

### Arquivos Gerados

- **Screenshots**: `screenshots/[page]_[timestamp].png`
- **DOM HTML**: `screenshots/[page]_[timestamp].html`
- **Relatório**: `reports/test_report_[timestamp].txt`

## 🔧 Desenvolvimento

### Adicionar Nova Página

1. Criar Page Object em `pages/`:

```python
# pages/my_page.py
from .base_page import BasePage
from selenium.webdriver.common.by import By

class MyPage(BasePage):
    HEADER = (By.XPATH, "//h1[contains(text(), 'My Page')]")
    
    def __init__(self, driver, base_url):
        super().__init__(driver, f"{base_url}/?view=mypage")
        
    def has_header(self) -> bool:
        return self.is_element_present(*self.HEADER)
```

2. Adicionar teste em `test_all_pages.py`:

```python
def test_my_page(self):
    print("\n🔧 Testing My Page...")
    page = MyPage(self.driver, self.base_url)
    page.navigate()
    
    has_header = page.has_header()
    self.results.append(TestResult("My Page Header", has_header))
```

3. Chamar teste no `run_all()`:

```python
def run_all(self):
    self.setup()
    self.test_dashboard()
    self.test_my_page()  # <-- adicionar aqui
    ...
```

### Executar Apenas Um Teste

```python
from tests.selenium.pages.dashboard_page import DashboardPage
from selenium_helper import get_chrome_driver

driver = get_chrome_driver(headless=False)
page = DashboardPage(driver, "http://localhost:8501")
page.navigate()

# Testar elemento específico
print(f"Header exists: {page.has_header()}")
print(f"Log buttons: {page.count_log_links()}")

driver.quit()
```

## 🐛 Troubleshooting

### Chrome/ChromeDriver não encontrado

```bash
# Instalar Chrome (Debian/Ubuntu)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

# Instalar ChromeDriver (automático via webdriver-manager)
pip install webdriver-manager
```

### Erro "Chrome instance exited" (WSL/Container)

```bash
# Instalar Xvfb (display virtual)
sudo apt-get install -y xvfb

# Rodar com Xvfb
xvfb-run python test_all_pages.py
```

### Timeout ao carregar página

```bash
# Aumentar timeouts
PAGE_LOAD_TIMEOUT=60 ELEMENT_WAIT_TIMEOUT=20 python test_all_pages.py
```

### Screenshots não salvos

```bash
# Verificar permissões
chmod -R 755 screenshots/ reports/

# Forçar screenshots
TAKE_SCREENSHOTS=1 SAVE_DOM=1 python test_all_pages.py
```

## 📚 Referências

- [Selenium Python Docs](https://selenium-python.readthedocs.io/)
- [Page Object Pattern](https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/)
- [AutoCoinBot Copilot Instructions](../../.github/copilot-instructions.md)
- [AutoCoinBot Training Manual](../../AGENTE_TREINAMENTO.md)

---

**Versão**: 1.0.0  
**Data**: 2026-01-04  
**Autor**: AutoCoinBot Team
