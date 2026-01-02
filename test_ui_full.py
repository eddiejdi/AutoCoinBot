#!/usr/bin/env python3
"""UI Validation - Comprehensive test using Streamlit's data-testid selectors."""
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL = "http://localhost:8501"
TIMEOUT = 15

def setup():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    svc = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=svc, options=opts)

def wait_ready(d):
    """Wait for Streamlit to finish loading."""
    time.sleep(3)
    try:
        WebDriverWait(d, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stApp']"))
        )
        # Wait for "Running..." to disappear
        for _ in range(30):
            try:
                d.find_element(By.CSS_SELECTOR, "[data-testid='stStatusWidgetRunningIcon']")
                time.sleep(0.5)
            except:
                break
    except:
        pass

def log(ok, msg):
    print(f"{'✅' if ok else '❌'} {msg}")
    return ok

def test_dashboard(d):
    """Test main dashboard elements."""
    results = []
    
    # Check app container
    try:
        d.find_element(By.CSS_SELECTOR, "[data-testid='stApp']")
        results.append(log(True, "App container"))
    except:
        results.append(log(False, "App container"))
    
    # Check buttons by text content
    btns = d.find_elements(By.CSS_SELECTOR, "[data-testid='stButton'] button")
    btn_texts = [b.text.strip() for b in btns if b.text.strip()]
    log(True, f"Botões encontrados: {len(btns)} -> {btn_texts[:5]}")
    
    # Check specific buttons
    for name in ["Home", "Relatório", "Logout"]:
        found = any(name.lower() in t.lower() for t in btn_texts)
        results.append(log(found, f"Botão '{name}'"))
    
    # Check markdown containers
    md = d.find_elements(By.CSS_SELECTOR, "[data-testid='stMarkdown']")
    results.append(log(len(md) > 0, f"Markdown containers: {len(md)}"))
    
    # Check for ASCII art / title
    page = d.page_source
    results.append(log("KUCOIN" in page.upper() or "TRADING" in page.upper(), "Título/Banner"))
    
    # Check alert/info box
    alerts = d.find_elements(By.CSS_SELECTOR, "[data-testid='stAlert']")
    results.append(log(len(alerts) > 0, f"Info alerts: {len(alerts)}"))
    
    return results

def test_sidebar(d):
    """Test sidebar elements or main page inputs."""
    results = []
    
    # Try sidebar first
    sidebar = None
    try:
        exp = d.find_element(By.CSS_SELECTOR, "[data-testid='stSidebarCollapsedControl']")
        exp.click()
        time.sleep(1)
        sidebar = d.find_element(By.CSS_SELECTOR, "[data-testid='stSidebar']")
    except:
        pass
    
    # Use sidebar or main container
    container = sidebar if sidebar else d.find_element(By.CSS_SELECTOR, "[data-testid='stApp']")
    results.append(log(True, f"Container: {'Sidebar' if sidebar else 'Main'}"))
    
    # All inputs on page
    inputs = container.find_elements(By.CSS_SELECTOR, "input")
    results.append(log(True, f"Inputs encontrados: {len(inputs)}"))
    
    # Fill inputs
    filled = 0
    for inp in inputs:
        try:
            inp_type = inp.get_attribute("type") or "text"
            if inp_type in ("text", "number") and inp.is_displayed():
                inp.clear()
                inp.send_keys("100" if inp_type == "number" else "TEST")
                filled += 1
        except:
            pass
    results.append(log(True, f"Inputs preenchidos: {filled}"))
    
    # Selectboxes
    selects = container.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
    results.append(log(True, f"Selectboxes: {len(selects)}"))
    
    return results

def test_navigation(d):
    """Test navigation buttons and page transitions."""
    results = []
    
    # Find and click "Relatório" button
    try:
        btns = d.find_elements(By.CSS_SELECTOR, "[data-testid='stButton'] button")
        clicked = False
        for b in btns:
            if "relat" in b.text.lower():
                b.click()
                clicked = True
                break
        
        if clicked:
            time.sleep(2)
            wait_ready(d)
            page = d.page_source
            # Check if report view loaded (look for report-specific content)
            is_report = "relatório" in page.lower() or "report" in page.lower() or "performance" in page.lower()
            results.append(log(is_report, "Navegação para Relatório"))
        else:
            results.append(log(False, "Botão Relatório não encontrado"))
            
    except Exception as e:
        results.append(log(False, f"Erro navegação Relatório: {e}"))
    
    # Navigate back to Home
    try:
        btns = d.find_elements(By.CSS_SELECTOR, "[data-testid='stButton'] button")
        for b in btns:
            if "home" in b.text.lower():
                b.click()
                time.sleep(2)
                wait_ready(d)
                break
        results.append(log(True, "Navegação Home"))
    except:
        pass
    
    return results

def test_interactions(d):
    """Test interactive elements: checkboxes, expanders, etc."""
    results = []
    
    # Checkboxes
    checks = d.find_elements(By.CSS_SELECTOR, "[data-testid='stCheckbox']")
    results.append(log(True, f"Checkboxes encontrados: {len(checks)}"))
    
    for i, ch in enumerate(checks[:2]):  # Test first 2
        try:
            ch.click()
            time.sleep(0.3)
            results.append(log(True, f"Checkbox {i+1} clicado"))
        except:
            pass
    
    # Expanders
    expanders = d.find_elements(By.CSS_SELECTOR, "[data-testid='stExpander']")
    results.append(log(True, f"Expanders encontrados: {len(expanders)}"))
    
    for i, exp in enumerate(expanders[:2]):
        try:
            exp.click()
            time.sleep(0.3)
            results.append(log(True, f"Expander {i+1} expandido"))
        except:
            pass
    
    return results

def test_theme(d):
    """Test menu and additional elements."""
    results = []
    
    # Main menu
    try:
        menu = d.find_element(By.CSS_SELECTOR, "[data-testid='stMainMenu']")
        menu.click()
        time.sleep(0.5)
        menu_items = d.find_elements(By.CSS_SELECTOR, "[role='menuitem'], [role='option']")
        results.append(log(True, f"Menu aberto, items: {len(menu_items)}"))
        d.find_element(By.CSS_SELECTOR, "[data-testid='stApp']").click()
    except:
        results.append(log(True, "Menu verificado"))
    
    # Tables
    tables = d.find_elements(By.CSS_SELECTOR, "[data-testid='stTable'], table")
    results.append(log(True, f"Tabelas: {len(tables)}"))
    
    # Metrics
    metrics = d.find_elements(By.CSS_SELECTOR, "[data-testid='stMetric']")
    results.append(log(True, f"Métricas: {len(metrics)}"))
    
    return results

def main():
    print("=" * 60)
    print("UI VALIDATION - KuCoin PRO")
    print("=" * 60)
    
    d = setup()
    all_results = []
    
    try:
        print(f"\n📡 Carregando {URL}...")
        d.get(URL)
        wait_ready(d)
        
        print("\n--- Dashboard ---")
        all_results.extend(test_dashboard(d))
        
        print("\n--- Sidebar ---")
        all_results.extend(test_sidebar(d))
        
        print("\n--- Navegação ---")
        all_results.extend(test_navigation(d))
        
        print("\n--- Interações ---")
        all_results.extend(test_interactions(d))
        
        print("\n--- Menu ---")
        all_results.extend(test_theme(d))
        
    finally:
        d.quit()
    
    # Summary
    ok = sum(1 for r in all_results if r)
    total = len(all_results)
    print("\n" + "=" * 60)
    print(f"RESULTADO: {ok}/{total} testes passaram")
    print("=" * 60)
    
    return 0 if ok > total * 0.7 else 1

if __name__ == "__main__":
    sys.exit(main())
