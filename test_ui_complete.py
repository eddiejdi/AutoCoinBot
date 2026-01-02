#!/usr/bin/env python3
"""
Teste completo da UI - valida elementos em todas as telas.
Economiza tokens: um arquivo único, execução sequencial.
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

URL = os.environ.get('LOCAL_URL', 'http://localhost:8501')
RESULTS = {"passed": [], "failed": [], "warnings": []}

def setup_driver():
    opts = Options()
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--incognito')
    if os.environ.get('HEADLESS', '1') == '1':
        opts.add_argument('--headless=new')
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    except:
        driver = webdriver.Chrome(options=opts)
    driver.set_window_size(1920, 1080)
    return driver

def log_result(name, passed, msg=""):
    if passed:
        RESULTS["passed"].append(name)
        print(f"✅ {name}")
    else:
        RESULTS["failed"].append(f"{name}: {msg}")
        print(f"❌ {name}: {msg}")

def check_eternal_loading(driver, timeout=20):
    """
    Verifica se a página está em loading eterno.
    
    Returns:
        dict: {'is_stuck': bool, 'wait_time': float, 'details': str}
    """
    loading_selectors = [
        "[data-testid='stStatusWidget']",
        "[data-testid='stStatusWidgetRunningIcon']",
        ".stSpinner",
        "[data-testid='stSpinner']",
    ]
    
    loaded_selectors = [
        "[data-testid='stApp']",
        "button",
        "input",
        ".stButton",
    ]
    
    start_time = time.time()
    was_loading = False
    
    while (time.time() - start_time) < timeout:
        is_loading = False
        
        # Verifica indicadores de loading
        for selector in loading_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        is_loading = True
                        was_loading = True
                        break
            except:
                pass
            if is_loading:
                break
        
        # Se não está carregando, verifica conteúdo
        if not is_loading:
            for selector in loaded_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        if el.is_displayed():
                            return {
                                'is_stuck': False,
                                'wait_time': time.time() - start_time,
                                'details': 'Página carregada'
                            }
                except:
                    pass
        
        time.sleep(0.5)
    
    return {
        'is_stuck': True,
        'wait_time': time.time() - start_time,
        'details': f'Loading eterno detectado após {timeout}s'
    }

def wait_page_load(driver, timeout=15):
    time.sleep(2)
    
    # Verifica loading eterno primeiro
    load_status = check_eternal_loading(driver, timeout=timeout)
    if load_status['is_stuck']:
        log_result("Loading Check", False, load_status['details'])
        return False
    
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # Aguarda Streamlit renderizar
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "button"))
        )
        time.sleep(1)
        return True
    except:
        return False

def do_login(driver):
    """Tenta login se necessário."""
    try:
        user = driver.find_element(By.XPATH, "//input[@type='text']")
        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        user.clear(); user.send_keys('admin')
        pwd.clear(); pwd.send_keys('senha123')
        for btn in driver.find_elements(By.TAG_NAME, 'button'):
            if 'Entrar' in (btn.text or ''):
                btn.click()
                time.sleep(3)
                return True
    except:
        pass
    return False

def test_dashboard(driver):
    """Testa elementos da tela principal (dashboard)."""
    driver.get(URL)
    wait_page_load(driver)
    do_login(driver)
    wait_page_load(driver)
    
    # Salva HTML para debug
    with open("debug_dashboard.html", "w") as f:
        f.write(driver.page_source)
    
    tests = [
        ("Header/Logo", "//h1|//h2|//pre"),
        ("Sidebar", "//section[@data-testid='stSidebar']|//aside"),
        ("Algum Botão", "//button"),
        ("Botão START", "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'start')]"),
        ("Botão KILL", "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'kill')]"),
        ("Texto Bot", "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'bot')]"),
        ("Texto Status", "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'status')]"),
        ("Input field", "//input"),
    ]
    
    for name, xpath in tests:
        try:
            els = driver.find_elements(By.XPATH, xpath)
            found = len(els) > 0
            log_result(f"Dashboard: {name}", found, f"{len(els)} encontrados" if found else "não encontrado")
        except Exception as e:
            log_result(f"Dashboard: {name}", False, str(e)[:50])
    
    driver.save_screenshot("test_dashboard.png")
    return True

def test_view_monitor(driver):
    """Testa a view monitor."""
    driver.get(f"{URL}/?view=monitor")
    wait_page_load(driver)
    do_login(driver)
    wait_page_load(driver)
    
    tests = [
        ("Título Monitor", "//*[contains(text(),'Monitor') or contains(text(),'Logs')]"),
        ("Área de conteúdo", "//div[contains(@class,'block-container')]"),
    ]
    
    for name, xpath in tests:
        try:
            el = driver.find_element(By.XPATH, xpath)
            log_result(f"Monitor: {name}", el.is_displayed())
        except:
            log_result(f"Monitor: {name}", False, "não encontrado")
    
    driver.save_screenshot("test_monitor.png")
    return True

def test_view_report(driver):
    """Testa a view report."""
    driver.get(f"{URL}/?view=report")
    wait_page_load(driver)
    do_login(driver)
    wait_page_load(driver)
    
    tests = [
        ("Conteúdo Report", "//iframe|//*[contains(text(),'Relatório') or contains(text(),'Trade')]"),
        ("Área de conteúdo", "//div[contains(@class,'block-container')]"),
    ]
    
    for name, xpath in tests:
        try:
            el = driver.find_element(By.XPATH, xpath)
            log_result(f"Report: {name}", el.is_displayed())
        except:
            log_result(f"Report: {name}", False, "não encontrado")
    
    driver.save_screenshot("test_report.png")
    return True

def test_sidebar_inputs(driver):
    """Testa preenchimento de inputs na sidebar."""
    driver.get(URL)
    wait_page_load(driver)
    do_login(driver)
    wait_page_load(driver)
    
    # Tenta preencher inputs numéricos
    filled = 0
    try:
        inputs = driver.find_elements(By.XPATH, "//input[@type='number' or @type='text']")
        mock = ["BTC-USDT", "30000", "0.1", "5", "20"]
        for i, inp in enumerate(inputs[:5]):
            try:
                if inp.is_displayed() and inp.is_enabled():
                    inp.clear()
                    inp.send_keys(mock[i] if i < len(mock) else "100")
                    filled += 1
            except:
                continue
    except:
        pass
    
    log_result("Sidebar: Preenchimento inputs", filled > 0, f"{filled} preenchidos")
    driver.save_screenshot("test_sidebar_inputs.png")
    return filled > 0

def test_buttons_clickable(driver):
    """Verifica se botões principais são clicáveis (sem executar ações destrutivas)."""
    driver.get(URL)
    wait_page_load(driver)
    do_login(driver)
    wait_page_load(driver)
    
    safe_buttons = ["DRY-RUN", "Tema", "Atualizar", "Refresh"]
    avoid = ["KILL", "REAL", "Stop", "Parar"]
    
    clickable = 0
    for btn in driver.find_elements(By.TAG_NAME, 'button'):
        try:
            txt = btn.text or ''
            if not txt or any(a in txt for a in avoid):
                continue
            if btn.is_displayed() and btn.is_enabled():
                clickable += 1
        except:
            continue
    
    log_result("Botões: Clicáveis encontrados", clickable > 0, f"{clickable} botões")
    return clickable > 0

def test_theme_selector(driver):
    """Testa seletor de tema se existir."""
    driver.get(URL)
    wait_page_load(driver)
    do_login(driver)
    wait_page_load(driver)
    
    try:
        # Procura expander de tema
        exp = driver.find_elements(By.XPATH, "//*[contains(text(),'Tema')]")
        if exp:
            log_result("Tema: Seletor encontrado", True)
            try:
                exp[0].click()
                time.sleep(1)
                driver.save_screenshot("test_theme.png")
            except:
                pass
        else:
            log_result("Tema: Seletor encontrado", False, "não visível")
    except:
        log_result("Tema: Seletor encontrado", False, "erro")
    
    return True

def run_all_tests():
    """Executa todos os testes."""
    print("=" * 50)
    print("TESTE COMPLETO DA UI - AutoCoinBot")
    print("=" * 50)
    
    driver = None
    try:
        driver = setup_driver()
        
        test_dashboard(driver)
        test_sidebar_inputs(driver)
        test_buttons_clickable(driver)
        test_theme_selector(driver)
        test_view_monitor(driver)
        test_view_report(driver)
        
    except Exception as e:
        RESULTS["failed"].append(f"Erro geral: {e}")
        print(f"❌ Erro: {e}")
    finally:
        if driver:
            driver.quit()
    
    # Resumo
    print("\n" + "=" * 50)
    print("RESUMO")
    print("=" * 50)
    print(f"✅ Passou: {len(RESULTS['passed'])}")
    print(f"❌ Falhou: {len(RESULTS['failed'])}")
    
    if RESULTS['failed']:
        print("\nFalhas:")
        for f in RESULTS['failed']:
            print(f"  - {f}")
    
    # Salva relatório
    with open("test_ui_report.txt", "w") as f:
        f.write(f"Passou: {len(RESULTS['passed'])}\n")
        f.write(f"Falhou: {len(RESULTS['failed'])}\n\n")
        f.write("Detalhes:\n")
        for p in RESULTS['passed']:
            f.write(f"✅ {p}\n")
        for fail in RESULTS['failed']:
            f.write(f"❌ {fail}\n")
    
    return len(RESULTS['failed']) == 0

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
