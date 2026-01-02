# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║  🔒 HOMOLOGADO: selenium_helper.py - Configuração Chrome/Chromium             ║
# ║  Data: 2026-01-02 | Sessão: fix-selenium-webdriver-manager                    ║
# ║  NÃO ALTERAR SEM APROVAÇÃO - Funciona em containers sem X11/display           ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
# selenium_helper.py
# Helper para configuração do Selenium com webdriver_manager
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def get_chrome_driver(headless=True, show_browser=False):
    """
    Retorna um driver Chrome configurado corretamente.
    
    Args:
        headless: Se True, roda em modo headless (padrão)
        show_browser: Se True, mostra o navegador (sobrepõe headless)
    
    Returns:
        webdriver.Chrome configurado
    """
    options = Options()
    
    # Configurações para container/CI sem display
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--incognito')
    options.add_argument('--disable-setuid-sandbox')
    
    # Opções para ambiente sem X11/display
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--use-gl=swiftshader')
    options.add_argument('--disable-gl-drawing-for-tests')
    options.add_argument('--disable-3d-apis')
    options.add_argument('--window-size=1920,1080')
    
    # Headless mode
    env_show = os.environ.get('SHOW_BROWSER', '0').lower() in ('1', 'true', 'yes')
    if show_browser or env_show:
        pass  # Não adiciona headless
    elif headless:
        try:
            options.add_argument('--headless=new')
        except Exception:
            options.add_argument('--headless')
    
    # Usar webdriver_manager para gerenciar ChromeDriver automaticamente
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        # Usar ChromeType.CHROMIUM se Chromium estiver instalado
        if os.path.exists('/usr/bin/chromium'):
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        else:
            service = Service(ChromeDriverManager().install())
    except ImportError:
        # Fallback para caminhos padrão
        chrome_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            os.path.expanduser('~/.local/bin/chromedriver'),
        ]
        service = None
        for path in chrome_paths:
            if os.path.exists(path):
                service = Service(path)
                break
        if service is None:
            service = Service()  # Deixa Selenium tentar encontrar
    
    # Detectar binário do Chrome
    chrome_binaries = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
    ]
    for binary in chrome_binaries:
        if os.path.exists(binary):
            options.binary_location = binary
            break
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1920, 1080)
    
    return driver


def wait_for_http(url, timeout=30, interval=0.5):
    """Aguarda até que a URL retorne HTTP 200."""
    import time
    import urllib.request
    
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=2) as resp:
                code = getattr(resp, 'status', None) or getattr(resp, 'getcode', lambda: None)()
                if code and int(code) == 200:
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False

# 🔒 FIM HOMOLOGADO