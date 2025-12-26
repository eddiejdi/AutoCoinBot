import time
import os
import urllib.request
import urllib.error
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Config
LOCAL_URL = os.environ.get('LOCAL_URL', 'http://localhost:8501')
REMOTE_URL = os.environ.get('HOM_URL', 'https://autocoinbot-hom.streamlit.app/')
APP_ENV = os.environ.get('APP_ENV', os.environ.get('ENV', 'dev')).lower()
if APP_ENV in ('hom', 'homologation', 'prod_hom'):
    URL = REMOTE_URL
else:
    URL = LOCAL_URL

options = Options()
show_browser = os.environ.get('SHOW_BROWSER', '1').lower() in ('1', 'true', 'yes')
if not show_browser:
    try:
        options.add_argument('--headless=new')  # Não usar headless para manter janela visível
    except Exception:
        options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--incognito')

service = Service('/usr/bin/chromedriver')
options.binary_location = '/usr/bin/chromium-browser' if os.path.exists('/usr/bin/chromium-browser') else '/usr/bin/chromium'
driver = webdriver.Chrome(service=service, options=options)


def wait_for_http(url, timeout=30, interval=0.5):
    deadline = time.time() + timeout
    last_exc = None
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=2) as resp:
                code = getattr(resp, 'status', None) or getattr(resp, 'getcode', lambda: None)()
                if code and int(code) == 200:
                    return True
        except Exception as e:
            last_exc = e
        time.sleep(interval)
    return False


driver.set_window_size(1920, 1080)

# Wait until the server responds HTTP 200 to avoid connection/refused race
if not wait_for_http(URL, timeout=30, interval=0.5):
    print(f"[WARN] {URL} did not respond with HTTP 200 within timeout; continuing and letting Selenium handle errors.")

driver.get(URL)
time.sleep(3)

# Immediately capture server-rendered HTML and a JS DOM snapshot so we always
# have diagnostics even if client render is incomplete.
try:
    # server-side HTML (page_source)
    with open('selenium_dom_initial.html', 'w', encoding='utf-8') as fh:
        fh.write(driver.page_source or '')
except Exception:
    pass
try:
    # client-side DOM via JS (may include hydrated React content)
    try:
        html_js = driver.execute_script('return document.documentElement.outerHTML')
    except Exception:
        html_js = None
    if html_js:
        with open('selenium_dom_js_initial.html', 'w', encoding='utf-8') as fh:
            fh.write(html_js)
except Exception:
    pass

# Wait for client-side render: look for either the header, a legacy 'ID:' text
# or any Streamlit-generated button class for LOG (st-key-log_). This avoids
# validating against a partially rendered page.
def wait_for_client_render(driver, timeout=30, interval=0.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            # 1) header
            headers = driver.find_elements(By.XPATH, "//*[contains(text(), 'Bots Ativos') or contains(text(), '🤖 Bots Ativos')]")
            if headers:
                return True
            # 2) legacy ID text lines
            id_lines = driver.find_elements(By.XPATH, "//*[contains(text(), 'ID:')]")
            if id_lines:
                return True
            # 3) st-key log buttons
            log_els = driver.find_elements(By.CSS_SELECTOR, '[class*="st-key-log_"]')
            if log_els:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


# Block until client-side render is detectable (or timeout)
if not wait_for_client_render(driver, timeout=30, interval=0.5):
    print('[WARN] Client-side render not detected within timeout; proceeding to diagnostics.')

    # Wait until element counts stabilize (helps ensure last elements finished rendering)
def wait_for_stable_elements(driver, selectors, timeout=45, stable_time=1.0, interval=0.5):
    deadline = time.time() + timeout
    last_count = None
    stable_since = None
    while time.time() < deadline:
        total = 0
        for sel in selectors:
            try:
                if sel.strip().startswith("//"):
                    elems = driver.find_elements(By.XPATH, sel)
                else:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                total += len(elems)
            except Exception:
                pass
        if last_count is None or total != last_count:
            last_count = total
            stable_since = time.time()
        else:
            # count unchanged
            if stable_since is not None and (time.time() - stable_since) >= stable_time:
                return True
        time.sleep(interval)
    return False

monitor_selectors = ['[class*="st-key-log_"]', '[class*="st-key-sel_kill_"]', "//*[contains(text(), 'ID:')]"]
if not wait_for_stable_elements(driver, monitor_selectors, timeout=45, stable_time=1.0, interval=0.5):
    print('[WARN] Element counts did not stabilize within timeout; proceeding anyway.')

# Interagir com elementos principais do dashboard
try:

    # Login automático se necessário
    try:
        user_input = driver.find_element(By.XPATH, "//input[@type='text']")
        pass_input = driver.find_element(By.XPATH, "//input[@type='password']")
        user_input.send_keys('admin')
        pass_input.send_keys('senha123')
        # Clicar no botão com texto 'Entrar' (visível e habilitado)
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for btn in buttons:
            if 'Entrar' in (btn.text or '') and btn.is_displayed() and btn.is_enabled():
                btn.click()
                time.sleep(1)
                break
        # Esperar sumir o campo de senha (login bem-sucedido)
        WebDriverWait(driver, 10).until_not(
            lambda d: d.find_element(By.XPATH, "//input[@type='password']").is_displayed()
        )
    except Exception:
        pass


        # Esperar pelo header ou pela mensagem de 'Nenhum bot ativo'
        bots_ativos_header = None
        nenhum_bot_ativo_msg = None
        try:
            wait = WebDriverWait(driver, 15)
            # Aguarda elemento que contenha o texto 'Bots Ativos' (pode ter emoji)
            header_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Bots Ativos') or contains(text(), '🤖 Bots Ativos') or contains(text(), '🤖 Bots Ativos') ]")))
            bots_ativos_header = header_el.text if header_el is not None else None
        except Exception:
            bots_ativos_header = None

        try:
            wait = WebDriverWait(driver, 2)
            msg_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Nenhum bot ativo') or contains(text(), 'Nenhuma sessão de bot encontrada') ]")))
            nenhum_bot_ativo_msg = msg_el.text if msg_el is not None else None
        except Exception:
            nenhum_bot_ativo_msg = None

        with open('selenium_output.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n--- Rodada em {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(f"Header Bots Ativos: {bots_ativos_header}\n")
            f.write(f"Mensagem Nenhum bot ativo: {nenhum_bot_ativo_msg}\n")

        if bots_ativos_header and not nenhum_bot_ativo_msg:
            print("[OK] Bots ativos detectados na tela do dashboard.")
            # Procurar por controles usando classes geradas por Streamlit relacionadas a keys
            try:
                kill_btns = driver.find_elements(By.CSS_SELECTOR, 'button[class*=\"st-key-kill_selected\"]')
                if kill_btns:
                    print(f"[OK] Botão Kill -9 detectado via classe st-key-kill_selected ({len(kill_btns)})")
                else:
                    # fallback: procurar botão com texto 'Kill -9' ou '🛑 Kill'
                    alt = driver.find_elements(By.XPATH, "//button[contains(text(), 'Kill') or contains(text(), '🛑')]")
                    if alt:
                        print(f"[OK] Botão Kill detectado por texto ({len(alt)})")
                    else:
                        print("[ERRO] Botão Kill não encontrado (classe st-key ou texto).")
            except Exception:
                print("[ERRO] Falha ao procurar botão Kill -9.")

            # Checkboxes (seleção por key 'sel_kill_')
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, '[class*=\"st-key-sel_kill_\"]')
                if checkboxes:
                    print(f"[OK] {len(checkboxes)} elemento(s) relacionados a 'sel_kill_' detectado(s) (classe st-key).")
                else:
                    # tentar inputs do tipo checkbox
                    inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type=checkbox]')
                    if inputs:
                        print(f"[AVISO] {len(inputs)} checkbox(es) genéricos detectado(s) (input[type=checkbox]).")
                    else:
                        print("[ERRO] Nenhum checkbox de seleção detectado.")
            except Exception:
                print("[ERRO] Falha ao procurar checkboxes de seleção.")

            # Links / botões LOG / REP (classes st-key-log_, st-key-rep_)
            try:
                log_buttons = driver.find_elements(By.CSS_SELECTOR, '[class*=\"st-key-log_\"]')
                rep_buttons = driver.find_elements(By.CSS_SELECTOR, '[class*=\"st-key-rep_\"]')
                found = 0
                if log_buttons:
                    print(f"[OK] {len(log_buttons)} botão(ões) LOG detectado(s) (st-key-log_).")
                    found += len(log_buttons)
                if rep_buttons:
                    print(f"[OK] {len(rep_buttons)} botão(ões) REL detectado(s) (st-key-rep_).")
                    found += len(rep_buttons)
                if not found:
                    # fallback: procurar links com 'LOG' ou 'REL.'
                    links = driver.find_elements(By.XPATH, "//a[contains(text(), 'LOG') or contains(text(), 'REL') or contains(text(), 'REL.')]")
                    if links:
                        print(f"[AVISO] {len(links)} link(s) de LOG/REL detectado(s) por texto.")
                    else:
                        print("[ERRO] Nenhum botão/link de LOG/REL detectado.")
            except Exception:
                print("[ERRO] Falha ao procurar botões LOG/REL.")

        elif nenhum_bot_ativo_msg:
            print("[ERRO] Nenhum bot ativo detectado na tela do dashboard! Mensagem: " + nenhum_bot_ativo_msg)
        else:
            print("[ERRO] Não foi possível determinar o status dos bots ativos na tela do dashboard.")
            # Em caso de falha, salvar snapshot do DOM para inspeção
            try:
                html = driver.page_source
                with open('selenium_dom_fail.html', 'w', encoding='utf-8') as fh:
                    fh.write(html)
                print('[INFO] Salvado selenium_dom_fail.html para inspeção.')
            except Exception:
                pass

        # Scroll para baixo e salvar screenshot
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(1)
        except Exception:
            pass

        try:
            driver.save_screenshot('screenshot_dashboard.png')
        except Exception:
            pass
        # Always save the final DOM for inspection (helps diagnose missing buttons)
        try:
            html_src = driver.page_source
            with open('selenium_dom_last.html', 'w', encoding='utf-8') as fh:
                fh.write(html_src)
        except Exception:
            pass
        time.sleep(1)
finally:
    driver.quit()
print('Dashboard Selenium test completed.')
