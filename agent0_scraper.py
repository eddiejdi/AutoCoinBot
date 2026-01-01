import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

import argparse
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

# Load .env if present
ENV_PATH = Path(__file__).resolve().parent / '.env'
if load_dotenv:
    # load .env from repo root first, then module dir
    try:
        load_dotenv(dotenv_path=Path.cwd() / '.env')
    except Exception:
        pass
    try:
        load_dotenv(dotenv_path=ENV_PATH)
    except Exception:
        pass

# Fallback to .streamlit/secrets.toml if variables not set
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

if tomllib:
    secrets_path = Path(__file__).resolve().parent / '.streamlit' / 'secrets.toml'
    if secrets_path.exists():
        try:
            with open(secrets_path, 'rb') as f:
                data = tomllib.load(f)
            if 'secrets' in data:
                for key, value in data['secrets'].items():
                    if key not in os.environ:
                        os.environ[key] = str(value)
        except Exception:
            pass

# Allow overriding via environment: APP_ENV=dev|hom and HOM_URL
# Configurações
LOCAL_URL = os.environ.get('LOCAL_URL', "http://localhost:8501")
REMOTE_URL = os.environ.get('HOM_URL', "https://autocoinbot-hom.streamlit.app/")
# APP_ENV: 'dev' uses LOCAL_URL, 'hom' uses REMOTE_URL, default 'dev'
APP_ENV = os.environ.get('APP_ENV', os.environ.get('ENV', 'dev')).lower()
if APP_ENV == 'hom' or APP_ENV == 'homologation' or APP_ENV == 'prod_hom':
    APP_URL = REMOTE_URL
else:
    APP_URL = LOCAL_URL  # default
ELEMENTOS_ESPERADOS = [
    # Prefer any common header tag (h1/h2/h3) — Streamlit may render as h2
    (By.TAG_NAME, 'h1'),
    (By.TAG_NAME, 'h2'),
    (By.TAG_NAME, 'h3'),
    (By.CLASS_NAME, 'stButton'),  # Botões Streamlit
    # Dataframes: Streamlit often renders them as a container or plain <table>
    (By.CLASS_NAME, 'stDataFrame'), # Tabelas (preferred)
    (By.TAG_NAME, 'table'),         # Fallback to any table element
    (By.CLASS_NAME, 'stAlert'),   # Mensagens de alerta
    # Sidebar can be rendered as an <aside> in some Streamlit versions
    (By.CLASS_NAME, 'stSidebar'), # Sidebar
    (By.TAG_NAME, 'aside'),
]

# Additional loose content checks (case-insensitive substrings expected somewhere on page)
ELEMENTOS_TEXTO = [
    'balance', 'saldo', 'trade', 'trades', 'bot', 'ativo', 'entradas', 'entry', 'profit', 'loss', 'btc', 'usdt'
]

# Elementos esperados na tela inicial (dashboard)
DASHBOARD_ELEMENTS = {
    'header': ['autocoin', 'dashboard', 'kucoin', 'bot'],
    'inputs': ['symbol', 'entry', 'target', 'interval', 'size', 'funds', 'símbolo', 'entrada', 'alvo'],
    'buttons': ['start', 'iniciar', 'simular', 'dry', 'executar', 'parar', 'stop'],
    'sections': ['configuração', 'configuration', 'bots', 'ativos', 'active', 'histórico', 'history'],
}

# Campos de input para configurar um bot
BOT_CONFIG_FIELDS = [
    {'name': 'symbol', 'type': 'text', 'test_value': 'BTC-USDT'},
    {'name': 'entry', 'type': 'number', 'test_value': '30000'},
    {'name': 'targets', 'type': 'text', 'test_value': '2:0.3,5:0.4,10:0.3'},
    {'name': 'interval', 'type': 'number', 'test_value': '5'},
    {'name': 'size', 'type': 'number', 'test_value': '0.001'},
    {'name': 'funds', 'type': 'number', 'test_value': '20'},
]


def _create_driver(headless=False):
    """Cria e configura o driver do Chrome."""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--incognito')
    
    driver = None
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        try:
            driver = webdriver.Chrome(options=options)
        except Exception:
            driver = webdriver.Chrome()
    driver.set_window_size(1920, 1080)
    return driver


def _check_eternal_loading(driver, timeout=30):
    """
    Verifica se a página está em loading eterno (spinner infinito do Streamlit).
    
    Detecta:
    - Spinner de "Running..." do Streamlit
    - Status widget indicando execução
    - Tela travada sem conteúdo interativo
    
    Args:
        driver: WebDriver instance
        timeout: Tempo máximo para aguardar o loading parar (segundos)
        
    Returns:
        dict: {
            'is_loading': bool - Se ainda está carregando
            'is_stuck': bool - Se está travado (loading eterno)
            'wait_time': float - Tempo que aguardou
            'details': str - Detalhes do estado
        }
    """
    result = {
        'is_loading': False,
        'is_stuck': False,
        'wait_time': 0,
        'details': ''
    }
    
    # Seletores que indicam loading no Streamlit
    loading_selectors = [
        "[data-testid='stStatusWidget']",  # Widget de status
        "[data-testid='stStatusWidgetRunningIcon']",  # Ícone "Running..."
        "[data-testid='stAppRunningIcon']",  # App running icon
        ".stSpinner",  # Spinner class
        "[data-testid='stSpinner']",  # Spinner testid
        ".stProgress",  # Progress bar
    ]
    
    # Seletores que indicam que a página carregou
    loaded_selectors = [
        "[data-testid='stApp']",  # App container
        "[data-testid='stSidebar']",  # Sidebar
        "button",  # Qualquer botão
        "input",  # Qualquer input
        ".stButton",  # Botão Streamlit
    ]
    
    start_time = time.time()
    check_interval = 0.5  # Intervalo de verificação
    was_loading = False
    
    while (time.time() - start_time) < timeout:
        is_loading_now = False
        
        # Verifica indicadores de loading
        for selector in loading_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        is_loading_now = True
                        was_loading = True
                        break
            except Exception:
                pass
            if is_loading_now:
                break
        
        # Se não está mais carregando, verifica se tem conteúdo
        if not is_loading_now:
            content_found = False
            for selector in loaded_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        if el.is_displayed():
                            content_found = True
                            break
                except Exception:
                    pass
                if content_found:
                    break
            
            if content_found:
                result['wait_time'] = time.time() - start_time
                result['details'] = 'Página carregada com sucesso'
                return result
        
        result['is_loading'] = is_loading_now
        time.sleep(check_interval)
    
    # Timeout atingido
    result['wait_time'] = time.time() - start_time
    result['is_stuck'] = True
    
    if was_loading:
        result['details'] = f'Loading eterno detectado - spinner ativo por mais de {timeout}s'
    else:
        result['details'] = f'Página não carregou conteúdo após {timeout}s'
    
    return result


def _wait_page_ready(driver, timeout=30, min_wait=3):
    """
    Aguarda a página estar pronta (não mais em loading).
    
    Args:
        driver: WebDriver instance
        timeout: Tempo máximo de espera
        min_wait: Tempo mínimo para aguardar antes de verificar
        
    Returns:
        dict: Resultado da verificação de loading
    """
    # Aguarda tempo mínimo para Streamlit iniciar
    time.sleep(min_wait)
    
    # Verifica loading
    load_status = _check_eternal_loading(driver, timeout=timeout - min_wait)
    
    if load_status['is_stuck']:
        print(f"   ⚠️ ALERTA: {load_status['details']}")
        # Tenta refresh como fallback
        try:
            driver.refresh()
            time.sleep(5)
            load_status_retry = _check_eternal_loading(driver, timeout=15)
            if not load_status_retry['is_stuck']:
                print("   ✓ Página carregou após refresh")
                return load_status_retry
        except Exception:
            pass
    
    return load_status


def validar_tela_inicial(url, screenshot_path='screenshot_dashboard.png'):
    """
    Valida a tela inicial (dashboard) do aplicativo.
    Verifica a presença de elementos essenciais como:
    - Header/título do app
    - Campos de configuração do bot
    - Botões de ação (start, stop, etc.)
    - Seções principais (configuração, bots ativos, histórico)
    
    Returns:
        dict: Resultado da validação com detalhes de cada elemento verificado
    """
    print("🔍 Iniciando validação da tela inicial...")
    
    driver = _create_driver()
    resultados = {
        'url': url,
        'success': False,
        'dashboard_loaded': False,
        'header_found': False,
        'inputs_found': [],
        'buttons_found': [],
        'sections_found': [],
        'loading_status': None,
        'is_stuck_loading': False,
        'errors': []
    }
    
    try:
        driver.get(url)
        print(f"   ✓ Página carregada: {url}")
        
        # NOVA VERIFICAÇÃO: Detecta loading eterno
        print("   ⏳ Verificando estado de carregamento...")
        load_status = _wait_page_ready(driver, timeout=30, min_wait=3)
        resultados['loading_status'] = load_status
        resultados['is_stuck_loading'] = load_status['is_stuck']
        
        if load_status['is_stuck']:
            resultados['errors'].append(f"Loading eterno: {load_status['details']}")
            print(f"   ❌ {load_status['details']}")
            driver.save_screenshot(screenshot_path.replace('.png', '_stuck.png'))
            resultados['screenshot_stuck'] = screenshot_path.replace('.png', '_stuck.png')
        else:
            print(f"   ✓ Página pronta em {load_status['wait_time']:.1f}s")
        
        # Tenta fazer login se necessário
        print("   🔐 Tentando login automático...")
        try:
            login_ok = _try_auto_login(driver, max_attempts=3)
            if login_ok:
                # Re-verifica loading após login
                load_status_post = _wait_page_ready(driver, timeout=20, min_wait=2)
                if load_status_post['is_stuck']:
                    resultados['errors'].append(f"Loading pós-login: {load_status_post['details']}")
        except Exception as e:
            resultados['errors'].append(f"Login: {str(e)}")
        
        # Captura o texto da página
        page_text = ''
        try:
            page_text = driver.find_element(By.TAG_NAME, 'body').text or ''
        except Exception:
            page_text = driver.page_source or ''
        page_text_lower = page_text.lower()
        
        # Salva o HTML para debug
        try:
            with open('debug_dashboard.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
        except Exception:
            pass
        
        # Verifica header/título
        for keyword in DASHBOARD_ELEMENTS['header']:
            if keyword.lower() in page_text_lower:
                resultados['header_found'] = True
                print(f"   ✓ Header encontrado: '{keyword}'")
                break
        
        # Verifica inputs
        try:
            inputs = driver.find_elements(By.XPATH, "//input[@type='text' or @type='number']")
            labels = driver.find_elements(By.TAG_NAME, 'label')
            label_texts = [l.text.lower() for l in labels if l.text]
            
            for keyword in DASHBOARD_ELEMENTS['inputs']:
                for label_text in label_texts:
                    if keyword.lower() in label_text:
                        resultados['inputs_found'].append(keyword)
                        break
                # Também verifica em placeholders dos inputs
                for inp in inputs:
                    try:
                        placeholder = inp.get_attribute('placeholder') or ''
                        aria_label = inp.get_attribute('aria-label') or ''
                        if keyword.lower() in placeholder.lower() or keyword.lower() in aria_label.lower():
                            if keyword not in resultados['inputs_found']:
                                resultados['inputs_found'].append(keyword)
                    except Exception:
                        pass
        except Exception as e:
            resultados['errors'].append(f"Inputs: {str(e)}")
        
        # Verifica botões
        try:
            buttons = driver.find_elements(By.XPATH, "//button|//div[@role='button']")
            for btn in buttons:
                try:
                    btn_text = (btn.text or btn.get_attribute('value') or '').lower()
                    for keyword in DASHBOARD_ELEMENTS['buttons']:
                        if keyword.lower() in btn_text:
                            if keyword not in resultados['buttons_found']:
                                resultados['buttons_found'].append(keyword)
                except Exception:
                    pass
        except Exception as e:
            resultados['errors'].append(f"Buttons: {str(e)}")
        
        # Verifica seções
        for keyword in DASHBOARD_ELEMENTS['sections']:
            if keyword.lower() in page_text_lower:
                resultados['sections_found'].append(keyword)
        
        # Determina se o dashboard carregou corretamente
        resultados['dashboard_loaded'] = (
            resultados['header_found'] or
            len(resultados['inputs_found']) >= 2 or
            len(resultados['buttons_found']) >= 1
        )
        
        resultados['success'] = resultados['dashboard_loaded']
        
        # Captura screenshot
        driver.save_screenshot(screenshot_path)
        resultados['screenshot'] = screenshot_path
        
        print(f"✅ Tela inicial validada: {'SUCESSO' if resultados['success'] else 'FALHA'}")
        print(f"   - Header encontrado: {resultados['header_found']}")
        print(f"   - Inputs encontrados: {resultados['inputs_found']}")
        print(f"   - Botões encontrados: {resultados['buttons_found']}")
        print(f"   - Seções encontradas: {resultados['sections_found']}")
        
    except Exception as e:
        resultados['errors'].append(f"Geral: {str(e)}")
        print(f"❌ Erro na validação da tela inicial: {e}")
    finally:
        driver.quit()
    
    return resultados


def testar_start_bot(url, dry_run=True, screenshot_path='screenshot_bot_start.png'):
    """
    Testa o fluxo de start de um bot via interface web (Selenium).
    
    1. Acessa a URL e faz login se necessário
    2. Preenche os campos de configuração do bot
    3. Marca a opção de dry-run (simulação)
    4. Clica no botão de iniciar
    5. Verifica se o bot foi iniciado (mensagem de sucesso ou bot na lista)
    
    Args:
        url: URL do aplicativo
        dry_run: Se True, marca a opção de simulação (dry-run)
        screenshot_path: Caminho para salvar screenshot
        
    Returns:
        dict: Resultado do teste com detalhes
    """
    print(f"🚀 Iniciando teste de start de bot (dry_run={dry_run})...")
    
    driver = _create_driver()
    resultados = {
        'url': url,
        'dry_run': dry_run,
        'success': False,
        'fields_filled': [],
        'start_button_clicked': False,
        'bot_started': False,
        'bot_id': None,
        'errors': [],
        'messages': []
    }
    
    try:
        driver.get(url)
        print(f"   ✓ Página carregada: {url}")
        
        # NOVA VERIFICAÇÃO: Detecta loading eterno
        print("   ⏳ Verificando estado de carregamento...")
        load_status = _wait_page_ready(driver, timeout=30, min_wait=3)
        resultados['loading_status'] = load_status
        resultados['is_stuck_loading'] = load_status.get('is_stuck', False)
        
        if load_status['is_stuck']:
            resultados['errors'].append(f"Loading eterno: {load_status['details']}")
            print(f"   ❌ {load_status['details']}")
            driver.save_screenshot(screenshot_path.replace('.png', '_stuck.png'))
            # Continua mesmo assim para tentar coletar mais informações
        else:
            print(f"   ✓ Página pronta em {load_status['wait_time']:.1f}s")
        
        # Tenta fazer login se necessário
        print("   🔐 Tentando login automático...")
        try:
            login_ok = _try_auto_login(driver, max_attempts=3)
            if login_ok:
                # Re-verifica loading após login
                load_status_post = _wait_page_ready(driver, timeout=20, min_wait=2)
                if load_status_post['is_stuck']:
                    resultados['errors'].append(f"Loading pós-login: {load_status_post['details']}")
        except Exception as e:
            resultados['errors'].append(f"Login: {str(e)}")
        
        # Preenche os campos de configuração do bot
        print("   📝 Preenchendo campos de configuração...")
        wait = WebDriverWait(driver, 10)
        
        for field in BOT_CONFIG_FIELDS:
            try:
                # Tenta encontrar o input por diferentes seletores
                input_elem = None
                selectors = [
                    f"//input[contains(@aria-label, '{field['name']}')]",
                    f"//input[contains(@placeholder, '{field['name']}')]",
                    f"//label[contains(text(), '{field['name']}')]/following::input[1]",
                    f"//div[contains(text(), '{field['name']}')]/following::input[1]",
                ]
                
                for sel in selectors:
                    try:
                        elems = driver.find_elements(By.XPATH, sel)
                        if elems:
                            input_elem = elems[0]
                            break
                    except Exception:
                        continue
                
                if input_elem and input_elem.is_displayed():
                    input_elem.clear()
                    input_elem.send_keys(field['test_value'])
                    resultados['fields_filled'].append(field['name'])
                    print(f"   ✓ Campo '{field['name']}' preenchido com '{field['test_value']}'")
            except Exception as e:
                resultados['errors'].append(f"Campo {field['name']}: {str(e)}")
        
        # Marca a opção de dry-run se necessário
        if dry_run:
            try:
                dry_checkboxes = driver.find_elements(By.XPATH, 
                    "//input[@type='checkbox']|//div[contains(@class, 'stCheckbox')]//input")
                for cb in dry_checkboxes:
                    try:
                        parent_text = cb.find_element(By.XPATH, './..').text.lower()
                        if any(kw in parent_text for kw in ['dry', 'simul', 'test']):
                            if not cb.is_selected():
                                cb.click()
                            resultados['messages'].append("Checkbox dry-run marcado")
                            break
                    except Exception:
                        pass
            except Exception as e:
                resultados['errors'].append(f"Dry-run checkbox: {str(e)}")
        
        time.sleep(1)
        
        # Encontra e clica no botão de start
        start_keywords = ['start', 'iniciar', 'executar', 'run', 'simular']
        avoid_keywords = ['stop', 'parar', 'kill', 'cancel']
        
        try:
            buttons = driver.find_elements(By.TAG_NAME, 'button')
            start_button = None
            
            for btn in buttons:
                try:
                    btn_text = (btn.text or '').lower()
                    if any(kw in btn_text for kw in start_keywords):
                        if not any(bad in btn_text for bad in avoid_keywords):
                            if btn.is_displayed() and btn.is_enabled():
                                start_button = btn
                                break
                except Exception:
                    continue
            
            if start_button:
                # Captura screenshot antes de clicar
                driver.save_screenshot(screenshot_path.replace('.png', '_before.png'))
                
                start_button.click()
                resultados['start_button_clicked'] = True
                print(f"   ✓ Botão de start clicado: '{start_button.text}'")
                
                time.sleep(4)  # Aguarda processamento
                
                # Verifica se o bot foi iniciado
                page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
                
                success_indicators = [
                    'bot iniciado', 'bot started', 'sucesso', 'success',
                    'running', 'rodando', 'ativo', 'active', 'bot_'
                ]
                
                for indicator in success_indicators:
                    if indicator in page_text:
                        resultados['bot_started'] = True
                        resultados['messages'].append(f"Indicador encontrado: '{indicator}'")
                        break
                
                # Tenta capturar o ID do bot se possível
                import re
                bot_id_match = re.search(r'bot_[a-f0-9]{8}', page_text)
                if bot_id_match:
                    resultados['bot_id'] = bot_id_match.group()
                    resultados['bot_started'] = True
                    print(f"   ✓ Bot ID encontrado: {resultados['bot_id']}")
            else:
                resultados['errors'].append("Botão de start não encontrado")
                print("   ✗ Botão de start não encontrado")
                
        except Exception as e:
            resultados['errors'].append(f"Start button: {str(e)}")
        
        # Captura screenshot final
        driver.save_screenshot(screenshot_path)
        resultados['screenshot'] = screenshot_path
        
        # Determina sucesso geral
        resultados['success'] = (
            resultados['start_button_clicked'] and
            (resultados['bot_started'] or len(resultados['fields_filled']) >= 3)
        )
        
        print(f"✅ Teste de start de bot: {'SUCESSO' if resultados['success'] else 'FALHA'}")
        print(f"   - Campos preenchidos: {len(resultados['fields_filled'])}")
        print(f"   - Botão clicado: {resultados['start_button_clicked']}")
        print(f"   - Bot iniciado: {resultados['bot_started']}")
        
    except Exception as e:
        resultados['errors'].append(f"Geral: {str(e)}")
        print(f"❌ Erro no teste de start de bot: {e}")
    finally:
        driver.quit()
    
    return resultados


def _try_auto_login(driver, max_attempts=3):
    """Tenta fazer login automático no aplicativo.
    
    Args:
        driver: WebDriver do Selenium
        max_attempts: Número máximo de tentativas de login
        
    Returns:
        bool: True se o login foi bem sucedido
    """
    for attempt in range(max_attempts):
        try:
            wait = WebDriverWait(driver, 8)
            
            # Verifica se já está logado (procura elementos do dashboard)
            try:
                page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
                dashboard_indicators = ['dashboard', 'bot', 'configuração', 'start', 'iniciar', 'balance', 'saldo']
                if any(indicator in page_text for indicator in dashboard_indicators):
                    print(f"   ✓ Já logado (indicadores do dashboard encontrados)")
                    return True
            except Exception:
                pass
            
            # Procura campos de login
            user_selectors = [
                "//input[@type='text']",
                "//input[@type='email']",
                "//input[@autocomplete='username']",
                "//input[@aria-label='Usuário']",
                "//input[contains(@placeholder, 'usu')]",
                "//input[contains(@placeholder, 'user')]",
            ]
            pass_selectors = [
                "//input[@type='password']",
                "//input[@aria-label='Senha']",
                "//input[contains(@placeholder, 'senha')]",
                "//input[contains(@placeholder, 'pass')]",
            ]
            
            usuario_input = None
            senha_input = None
            
            # Tenta encontrar campo de usuário
            for sel in user_selectors:
                try:
                    elems = driver.find_elements(By.XPATH, sel)
                    for elem in elems:
                        if elem.is_displayed():
                            usuario_input = elem
                            break
                    if usuario_input:
                        break
                except Exception:
                    continue
            
            # Tenta encontrar campo de senha
            for sel in pass_selectors:
                try:
                    elems = driver.find_elements(By.XPATH, sel)
                    for elem in elems:
                        if elem.is_displayed():
                            senha_input = elem
                            break
                    if senha_input:
                        break
                except Exception:
                    continue
            
            if not usuario_input or not senha_input:
                # Talvez não esteja na tela de login
                print(f"   ℹ️ Campos de login não encontrados (tentativa {attempt + 1})")
                time.sleep(2)
                continue
            
            # Preenche as credenciais
            try:
                usuario_input.clear()
                usuario_input.send_keys('admin')
                print(f"   ✓ Usuário preenchido")
            except Exception as e:
                print(f"   ✗ Erro ao preencher usuário: {e}")
            
            try:
                senha_input.clear()
                senha_input.send_keys('senha123')
                print(f"   ✓ Senha preenchida")
            except Exception as e:
                print(f"   ✗ Erro ao preencher senha: {e}")
            
            # Procura e clica no botão de login
            login_buttons = [
                "//button[contains(translate(., 'ENTRAR', 'entrar'), 'entrar')]",
                "//button[contains(translate(., 'LOGIN', 'login'), 'login')]",
                "//button[contains(translate(., 'SIGN', 'sign'), 'sign')]",
                "//input[@type='submit']",
                "//div[@data-testid='stFormSubmitButton']//button",
                "//button[@type='submit']",
                "//form//button",
            ]
            
            clicked = False
            for btn_sel in login_buttons:
                try:
                    btns = driver.find_elements(By.XPATH, btn_sel)
                    for btn in btns:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            clicked = True
                            print(f"   ✓ Botão de login clicado")
                            break
                    if clicked:
                        break
                except Exception:
                    continue
            
            if clicked:
                time.sleep(4)  # Aguarda processamento do login
                
                # Verifica se login foi bem sucedido
                try:
                    page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
                    if any(indicator in page_text for indicator in dashboard_indicators):
                        print(f"   ✓ Login bem sucedido!")
                        return True
                except Exception:
                    pass
            
            time.sleep(2)
            
        except Exception as e:
            print(f"   ✗ Erro na tentativa de login {attempt + 1}: {e}")
            time.sleep(2)
    
    print(f"   ✗ Login automático falhou após {max_attempts} tentativas")
    return False


def gerar_relatorio_completo(resultados_tela, resultados_bot, output_file='relatorio_scraper_completo.md'):
    """Gera um relatório consolidado dos testes."""
    rel = "# Relatório de Validação - AutoCoinBot Scraper\n\n"
    rel += f"**Data:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    rel += "## 1. Validação da Tela Inicial\n\n"
    if resultados_tela:
        rel += f"- **URL:** {resultados_tela.get('url', 'N/A')}\n"
        rel += f"- **Status:** {'✅ SUCESSO' if resultados_tela.get('success') else '❌ FALHA'}\n"
        rel += f"- **Dashboard carregado:** {resultados_tela.get('dashboard_loaded', False)}\n"
        rel += f"- **Header encontrado:** {resultados_tela.get('header_found', False)}\n"
        rel += f"- **Inputs encontrados:** {', '.join(resultados_tela.get('inputs_found', [])) or 'Nenhum'}\n"
        rel += f"- **Botões encontrados:** {', '.join(resultados_tela.get('buttons_found', [])) or 'Nenhum'}\n"
        rel += f"- **Seções encontradas:** {', '.join(resultados_tela.get('sections_found', [])) or 'Nenhum'}\n"
        if resultados_tela.get('errors'):
            rel += f"- **Erros:** {'; '.join(resultados_tela.get('errors', []))}\n"
        if resultados_tela.get('screenshot'):
            rel += f"\n![Screenshot Dashboard]({resultados_tela.get('screenshot')})\n"
    else:
        rel += "- Teste não executado\n"
    
    rel += "\n## 2. Teste de Start de Bot\n\n"
    if resultados_bot:
        rel += f"- **URL:** {resultados_bot.get('url', 'N/A')}\n"
        rel += f"- **Modo:** {'DRY-RUN (Simulação)' if resultados_bot.get('dry_run') else 'REAL'}\n"
        rel += f"- **Status:** {'✅ SUCESSO' if resultados_bot.get('success') else '❌ FALHA'}\n"
        rel += f"- **Campos preenchidos:** {', '.join(resultados_bot.get('fields_filled', [])) or 'Nenhum'}\n"
        rel += f"- **Botão Start clicado:** {resultados_bot.get('start_button_clicked', False)}\n"
        rel += f"- **Bot iniciado:** {resultados_bot.get('bot_started', False)}\n"
        if resultados_bot.get('bot_id'):
            rel += f"- **Bot ID:** {resultados_bot.get('bot_id')}\n"
        if resultados_bot.get('messages'):
            rel += f"- **Mensagens:** {'; '.join(resultados_bot.get('messages', []))}\n"
        if resultados_bot.get('errors'):
            rel += f"- **Erros:** {'; '.join(resultados_bot.get('errors', []))}\n"
        if resultados_bot.get('screenshot'):
            rel += f"\n![Screenshot Bot Start]({resultados_bot.get('screenshot')})\n"
    else:
        rel += "- Teste não executado\n"
    
    rel += "\n## Resumo\n\n"
    tela_ok = resultados_tela.get('success', False) if resultados_tela else False
    bot_ok = resultados_bot.get('success', False) if resultados_bot else False
    rel += f"| Teste | Resultado |\n"
    rel += f"|-------|----------|\n"
    rel += f"| Tela Inicial | {'✅ PASSOU' if tela_ok else '❌ FALHOU'} |\n"
    rel += f"| Start Bot | {'✅ PASSOU' if bot_ok else '❌ FALHOU'} |\n"
    
    with open(output_file, 'w') as f:
        f.write(rel)
    
    print(f"\n📄 Relatório salvo em: {output_file}")
    return rel


def validar_tela(url, elementos_esperados, screenshot_path='screenshot.png', check_buttons=False, button_labels=None):
    options = Options()
    # Decide whether to run visible browser. Default: headless unless SHOW_BROWSER=1
    # Sempre mostrar o navegador (headless desativado)
    show_browser = True
    # Não adiciona argumento headless
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--incognito')  # Abre janela anônima
    # Prefer webdriver_manager if available to auto-download chromedriver
    driver = None
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        try:
            driver = webdriver.Chrome(options=options)
        except Exception:
            # Last resort: try using Selenium Manager (newer selenium) via default constructor
            driver = webdriver.Chrome()
    driver.set_window_size(1920, 1080)
    driver.get(url)
    # wait a bit for Streamlit to render
    time.sleep(6)


    # Tenta login automático dentro do iframe (ou no documento principal)
    login_preenchido = False
    login_error = None
    login_html = None

    def _try_fill_and_submit(context_driver) -> bool:
        """Tenta múltiplos seletores para user/password e clica no botão de submit.
        Usa WebDriverWait para aguardar elementos quando necessário."""
        wait = WebDriverWait(context_driver, 4)
        user_selectors = [
            "//input[@type='text']",
            "//input[@type='text' and (@name or @id or @placeholder)]",
            "//input[@autocomplete='username']",
            "//input[contains(translate(@name,'USER','user'),'user')]",
            "//input[contains(translate(@id,'USER','user'),'user')]",
            "//input[@type='email']",
            "//input[@id='text_input_1']",
            "//input[@name='username']",
            "//input[@aria-label='Usuário']",
        ]
        pass_selectors = [
            "//input[@type='password']",
            "//input[contains(translate(@name,'PASS','pass'),'pass')]",
            "//input[contains(translate(@id,'PASS','pass'),'pass')]",
            "//input[@id='text_input_2']",
            "//input[@aria-label='Senha']",
        ]

        # Encontrar usuário e senha (com espera)
        usuario_input = None
        senha_input = None
        for sel in user_selectors:
            try:
                usuario_input = wait.until(EC.presence_of_element_located((By.XPATH, sel)))
                if usuario_input:
                    break
            except Exception:
                usuario_input = None
                continue

        for sel in pass_selectors:
            try:
                senha_input = wait.until(EC.presence_of_element_located((By.XPATH, sel)))
                if senha_input:
                    break
            except Exception:
                senha_input = None
                continue

        if usuario_input is None or senha_input is None:
            return False

        try:
            usuario_input.clear()
            usuario_input.send_keys('admin')
        except Exception:
            pass
        try:
            senha_input.clear()
            senha_input.send_keys('senha123')
        except Exception:
            pass

        # Tentar clicar em possíveis botões de submit
        try_buttons = [
            "//button[contains(., 'Entrar') or contains(., 'Login') or contains(., 'Sign in') or contains(., 'Submit') ]",
            "//input[@type='submit']",
            "//button",
            "//div[@data-testid='stFormSubmitButton']//button",
        ]
        for tb in try_buttons:
            try:
                elems = context_driver.find_elements(By.XPATH, tb)
                for btn in elems:
                    try:
                        text = btn.text or btn.get_attribute('value') or ''
                    except Exception:
                        text = ''
                    if any(k in text for k in ['Entrar', 'Login', 'Sign', 'Submit']) or tb != "//button":
                        try:
                            try:
                                wait.until(EC.element_to_be_clickable((By.XPATH, tb)))
                            except Exception:
                                pass
                            btn.click()
                            return True
                        except Exception:
                            continue
            except Exception:
                continue
        return False

    def _exercise_ui_flows(context_driver, base_url: str) -> None:
        """Interage com elementos principais da UI após o login.

        Objetivo é exercitar preenchimento de campos e cliques em botões/links
        típicos (start, LOG, REL, monitor, relatório), incluindo telas que
        possam abrir em novas abas/janelas. Mantém o escopo pequeno para não
        interferir demais no uso normal da aplicação.
        """
        # Preencher alguns inputs de texto/número com valores mock
        try:
            inputs = context_driver.find_elements(By.XPATH, "//input[@type='text' or @type='number']")
            mock_values = [
                "BTC-USDT",  # símbolo
                "30000",     # entry
                "0.1",       # size
                "2:0.3,5:0.4",  # targets
                "5",         # interval
                "20",        # funds
            ]
            idx = 0
            for el in inputs:
                try:
                    if not el.is_displayed() or not el.is_enabled():
                        continue
                except Exception:
                    continue
                try:
                    value = mock_values[idx] if idx < len(mock_values) else str(100 + idx)
                    el.clear()
                    el.send_keys(value)
                    idx += 1
                except Exception:
                    continue
        except Exception:
            pass

        # Interagir com selects (combos) simples
        try:
            selects = context_driver.find_elements(By.TAG_NAME, "select")
            for sel in selects:
                try:
                    if not sel.is_displayed() or not sel.is_enabled():
                        continue
                except Exception:
                    continue
                try:
                    options = sel.find_elements(By.TAG_NAME, "option")
                except Exception:
                    continue
                for opt in options[1:2] or options[:1]:
                    try:
                        opt.click()
                    except Exception:
                        continue
                    break
        except Exception:
            pass

        # Clicar em alguns botões/links "seguros" para navegar entre telas
        safe_keywords = [
            'iniciar', 'start', 'simular', 'dry', 'executar', 'testar',
            'log', 'rel', 'monitor', 'relatório'
        ]
        avoid_keywords = ['kill', 'sair', 'logout', 'excluir', 'delete']

        max_clicks = 5
        clicks_done = 0

        try:
            try:
                main_handle = context_driver.current_window_handle
            except Exception:
                main_handle = None

            candidates = []
            try:
                candidates.extend(context_driver.find_elements(By.TAG_NAME, 'button'))
            except Exception:
                pass
            try:
                # Filtrar links com href válido (não data:, javascript:, #, vazio)
                links = context_driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    try:
                        href = link.get_attribute('href') or ''
                        # Ignorar links com URLs inválidas
                        if href.startswith('data:') or href.startswith('javascript:') or href == '#' or not href:
                            continue
                        candidates.append(link)
                    except Exception:
                        continue
            except Exception:
                pass

            for el in candidates:
                if clicks_done >= max_clicks:
                    break
                try:
                    if not el.is_displayed() or not el.is_enabled():
                        continue
                except Exception:
                    continue

                try:
                    text = (el.text or el.get_attribute('value') or '').strip()
                except Exception:
                    text = ''
                lowered = text.lower()
                if not lowered:
                    continue
                if any(bad in lowered for bad in avoid_keywords):
                    continue
                if not any(key in lowered for key in safe_keywords):
                    continue

                # Tenta clicar e, se abrir nova janela/aba, faz uma validação leve
                try:
                    try:
                        before_handles = set(context_driver.window_handles)
                    except Exception:
                        before_handles = set()

                    el.click()
                    time.sleep(2)

                    # Verificar se navegou para URL inválida e voltar se necessário
                    try:
                        current_url = context_driver.current_url or ''
                        if current_url.startswith('data:') or current_url.startswith('javascript:') or current_url == 'about:blank':
                            if base_url:
                                context_driver.get(base_url)
                                time.sleep(1)
                            continue
                    except Exception:
                        pass

                    try:
                        after_handles = set(context_driver.window_handles)
                    except Exception:
                        after_handles = set()

                    new_handles = [h for h in after_handles if h not in before_handles]

                    for h in new_handles:
                        try:
                            context_driver.switch_to.window(h)
                            time.sleep(2)
                            # Verificar se a nova janela tem URL válida
                            try:
                                child_url = context_driver.current_url or ''
                                if child_url.startswith('data:') or child_url.startswith('javascript:') or child_url == 'about:blank':
                                    # Fechar janela inválida imediatamente
                                    context_driver.close()
                                    if main_handle:
                                        context_driver.switch_to.window(main_handle)
                                    continue
                            except Exception:
                                pass
                            # Scroll leve para forçar renderização e captura de screenshot auxiliar
                            try:
                                context_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                time.sleep(0.5)
                            except Exception:
                                pass
                            try:
                                context_driver.save_screenshot(f"screenshot_child_{abs(hash(h)) & 0xffff:x}.png")
                            except Exception:
                                pass
                        finally:
                            try:
                                if main_handle and h != main_handle:
                                    context_driver.close()
                            except Exception:
                                pass
                            if main_handle:
                                try:
                                    context_driver.switch_to.window(main_handle)
                                except Exception:
                                    pass

                    # Se não abriu nova janela, volta para a URL base (se fornecida)
                    if not new_handles and base_url:
                        try:
                            context_driver.get(base_url)
                            time.sleep(1)
                        except Exception:
                            pass

                    clicks_done += 1
                except Exception:
                    continue
        except Exception:
            # Erros nessa parte não devem quebrar a validação principal
            pass

    # Primeiro tente dentro de um iframe (se houver)
    try:
        iframe = None
        try:
            iframe = driver.find_element(By.TAG_NAME, "iframe")
        except Exception:
            iframe = None

        if iframe:
            try:
                driver.switch_to.frame(iframe)
                time.sleep(1)
                if _try_fill_and_submit(driver):
                    login_preenchido = True
                driver.switch_to.default_content()
            except Exception as e:
                login_error = str(e)
                try:
                    login_html = driver.page_source
                except Exception:
                    login_html = None
        else:
            # Tentar no contexto principal
            try:
                if _try_fill_and_submit(driver):
                    login_preenchido = True
            except Exception as e:
                login_error = str(e)
                try:
                    login_html = driver.page_source
                except Exception:
                    login_html = None

        # Aguarda pós-login se tentou
        if login_preenchido:
            time.sleep(5)
    except Exception as e:
        login_error = str(e)
        try:
            login_html = driver.page_source
        except Exception:
            login_html = None

    # Após tentar login, exercita alguns fluxos principais da UI (mock)
    try:
        _exercise_ui_flows(driver, url)
    except Exception:
        pass


    driver.save_screenshot(screenshot_path)
    resultados = {}
    for by, seletor in elementos_esperados:
        try:
            elementos = driver.find_elements(by, seletor)
            resultados[seletor] = len(elementos) > 0
        except NoSuchElementException:
            resultados[seletor] = False
    # Additional loose text checks: look for key words anywhere in visible text
    page_text = ''
    try:
        page_text = driver.find_element(By.TAG_NAME, 'body').text or ''
    except Exception:
        page_text = driver.page_source or ''
    page_text_lower = page_text.lower()
    for token in ELEMENTOS_TEXTO:
        resultados[f'text_contains:{token}'] = token.lower() in page_text_lower
    # Check for at least one numeric metric on the page (e.g., 1234.56)
    import re
    nums = re.findall(r"\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?", page_text)
    resultados['numeric_found'] = len(nums) > 0

    # Button checks: collect visible/clickable buttons and verify expected labels
    try:
        # Determine expected labels from parameter or env var
        if button_labels:
            expected_labels = [b.strip().lower() for b in button_labels.split(',') if b.strip()]
        else:
            env_labels = os.environ.get('BUTTON_LABELS', '')
            if env_labels:
                expected_labels = [b.strip().lower() for b in env_labels.split(',') if b.strip()]
            else:
                expected_labels = [
                    'start', 'stop', 'iniciar', 'parar', 'run', 'executar', 'start bot', 'stop bot'
                ]

        btn_elements = []
        try:
            btn_elements = driver.find_elements(By.XPATH, "//button|//input[@type='button']|//input[@type='submit']|//div[@role='button']|//a[@role='button']")
        except Exception:
            btn_elements = []

        textos = []
        clickable_found = False
        for b in btn_elements:
            try:
                t = (b.text or b.get_attribute('value') or '').strip()
            except Exception:
                t = ''
            textos.append(t)
            is_disabled = False
            try:
                disabled_attr = b.get_attribute('disabled')
                if disabled_attr:
                    is_disabled = True
            except Exception:
                is_disabled = False
            # Só clica se não for botão 'Deploy' ou vazio
            if not is_disabled and t and t.lower() not in ['deploy']:
                try:
                    if b.is_displayed() and b.is_enabled():
                        clickable_found = True
                        # Tenta clicar no botão e captura erros de navegação
                        try:
                            b.click()
                            time.sleep(2)  # Aguarda possível navegação
                        except Exception as click_err:
                            with open('erro_clique_botao.txt', 'a') as f:
                                f.write(f"Erro ao clicar no botão '{t}': {click_err}\n")
                        try:
                            driver.get(url)
                            time.sleep(2)
                        except Exception:
                            pass
                except Exception:
                    clickable_found = True

        resultados['buttons_count'] = len(btn_elements)
        # store up to 10 button texts for debugging
        resultados['button_texts'] = textos[:10]
        resultados['clickable_button_found'] = clickable_found
        # expected label checks
        for lbl in expected_labels:
            key = f'button_label:{lbl}'
            found_lbl = any(lbl in (t or '').lower() for t in textos)
            resultados[key] = found_lbl
    except Exception:
        resultados['buttons_check_error'] = True
    driver.quit()
    # Adiciona ao relatório se login foi tentado e detalhes de erro
    resultados['login_preenchido'] = login_preenchido
    # Normalize/aggregate certain checks for robustness
    try:
        header_found = any(resultados.get(t, False) for t in ('h1', 'h2', 'h3'))
        resultados['h1'] = header_found
    except Exception:
        pass
    try:
        df_found = resultados.get('stDataFrame') or resultados.get('table')
        resultados['stDataFrame'] = bool(df_found)
    except Exception:
        pass
    try:
        sidebar_found = resultados.get('stSidebar') or resultados.get('aside')
        resultados['stSidebar'] = bool(sidebar_found)
    except Exception:
        pass
    if login_error:
        with open('login_error.txt', 'w') as f:
            f.write(f"Erro: {login_error}\n\n")
            if login_html:
                f.write("HTML da página:\n")
                f.write(login_html)
    return resultados, screenshot_path


def gerar_relatorio(resultados, screenshot_path, url):
    rel = f"# Validação visual do app: {url}\n\n"
    rel += f"![Screenshot]({screenshot_path})\n\n"
    for seletor, ok in resultados.items():
        rel += f"- Elemento '{seletor}': {'OK' if ok else 'NÃO ENCONTRADO'}\n"
    return rel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Valida tela do KuCoin Bot")
    parser.add_argument('--remote', action='store_true', help='Valida endpoint remoto')
    parser.add_argument('--local', action='store_true', help='Valida endpoint local')
    parser.add_argument('--url', type=str, default=None, help='URL explícita para validar (substitui --remote/--local)')
    parser.add_argument('--retries', type=int, default=3, help='Número de tentativas automáticas')
    parser.add_argument('--wait', type=int, default=3, help='Segundos entre tentativas')
    parser.add_argument('--check-buttons', action='store_true', help='Valida presença e rótulos de botões na tela')
    parser.add_argument('--button-labels', type=str, default=None, help='Lista separada por vírgula de rótulos esperados para botões')
    parser.add_argument('--test-dashboard', action='store_true', help='Executa validação da tela inicial (dashboard)')
    parser.add_argument('--test-bot-start', action='store_true', help='Executa teste de start de bot (dry-run)')
    parser.add_argument('--test-bot-real', action='store_true', help='Executa teste de start de bot (modo REAL - cuidado!)')
    parser.add_argument('--test-all', action='store_true', help='Executa todos os testes (dashboard + bot start dry-run)')
    args = parser.parse_args()

    # CLI precedence: explicit --url > --remote > --local > default APP_URL
    if args.url:
        url = args.url
    elif args.remote:
        url = REMOTE_URL
    elif args.local:
        url = LOCAL_URL
    else:
        url = APP_URL

    # Executa novos testes se solicitado
    if args.test_dashboard or args.test_bot_start or args.test_bot_real or args.test_all:
        print("=" * 60)
        print("🧪 AutoCoinBot Scraper - Testes Avançados")
        print("=" * 60)
        print(f"URL: {url}")
        print()
        
        resultados_tela = None
        resultados_bot = None
        
        # Teste de tela inicial
        if args.test_dashboard or args.test_all:
            print("\n" + "=" * 40)
            print("📺 TESTE 1: Validação da Tela Inicial")
            print("=" * 40)
            resultados_tela = validar_tela_inicial(url)
        
        # Teste de start de bot (dry-run)
        if args.test_bot_start or args.test_all:
            print("\n" + "=" * 40)
            print("🤖 TESTE 2: Start de Bot (DRY-RUN)")
            print("=" * 40)
            resultados_bot = testar_start_bot(url, dry_run=True)
        
        # Teste de start de bot (modo real - com confirmação)
        if args.test_bot_real:
            print("\n" + "=" * 40)
            print("⚠️  TESTE 3: Start de Bot (MODO REAL)")
            print("=" * 40)
            print("🚨 ATENÇÃO: Este teste pode executar trades REAIS!")
            
            auto_confirm = os.environ.get('AUTO_CONFIRM_REAL_TEST', '').lower() == 'true'
            if not auto_confirm:
                import sys
                if sys.stdin.isatty():
                    try:
                        resposta = input("Digite 'SIM' para confirmar ou Enter para pular: ").strip()
                        if resposta.upper() != 'SIM':
                            print("⏭️  Teste real pulado pelo usuário")
                        else:
                            resultados_bot = testar_start_bot(url, dry_run=False)
                    except EOFError:
                        print("⏭️  Ambiente não-interativo - pulando teste real")
                else:
                    print("⏭️  Ambiente não-interativo - pulando teste real")
            else:
                resultados_bot = testar_start_bot(url, dry_run=False)
        
        # Gera relatório consolidado
        if resultados_tela or resultados_bot:
            gerar_relatorio_completo(resultados_tela, resultados_bot)
        
        # Resumo final
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        if resultados_tela:
            status_tela = "✅ PASSOU" if resultados_tela.get('success') else "❌ FALHOU"
            print(f"  Tela Inicial: {status_tela}")
        
        if resultados_bot:
            status_bot = "✅ PASSOU" if resultados_bot.get('success') else "❌ FALHOU"
            modo = "DRY-RUN" if resultados_bot.get('dry_run') else "REAL"
            print(f"  Start Bot ({modo}): {status_bot}")
        
        print("\n🎯 Testes concluídos!")
        print("=" * 60)
    else:
        # Comportamento original do scraper
        expected_selectors = [s for (_, s) in ELEMENTOS_ESPERADOS]

        final_results = None
        for attempt in range(1, args.retries + 1):
            print(f"[attempt {attempt}/{args.retries}] Validando {url} ...")
            resultados, screenshot = validar_tela(url, ELEMENTOS_ESPERADOS, screenshot_path='screenshot.png', check_buttons=args.check_buttons or os.environ.get('CHECK_BUTTONS','0') in ('1','true','yes'), button_labels=args.button_labels)
            relatorio = gerar_relatorio(resultados, screenshot, url)
            fname = f"relatorio_validacao_attempt_{attempt}.md"
            with open(fname, "w") as f:
                f.write(relatorio)
            print(f"Relatório salvo: {fname}")

            # Decide se passou: todos os expected selectors True
            passed = True
            for sel in expected_selectors:
                if not resultados.get(sel, False):
                    passed = False
                    break

            if passed:
                print(f"Sucesso na tentativa {attempt}. Saindo.")
                final_results = (resultados, screenshot)
                break
            else:
                print(f"Falha na tentativa {attempt}. Retrying in {args.wait}s...")
                time.sleep(args.wait)

        if final_results is None:
            # write final aggregated report
            with open("relatorio_validacao.md", "w") as f:
                f.write(relatorio)
            print("Validação finalizada com falhas. Veja relatorios de tentativa.")
        else:
            resultados, screenshot = final_results
            with open("relatorio_validacao.md", "w") as f:
                f.write(gerar_relatorio(resultados, screenshot, url))
            print("Validação concluída com sucesso. Veja relatorio_validacao.md e screenshot.png.")
