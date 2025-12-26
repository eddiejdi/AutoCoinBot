import time
import os
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

driver.set_window_size(1920, 1080)
driver.get(URL)
time.sleep(5)

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


    # Verificar se há bots ativos na tela

    # Critério ajustado: verifica header e mensagem de ausência
    bots_ativos_header = None
    nenhum_bot_ativo_msg = None
    try:
        bots_ativos_header = driver.find_element(By.XPATH, "//*[contains(text(), 'Bots Ativos')]").text
    except Exception:
        pass
    try:
        nenhum_bot_ativo_msg = driver.find_element(By.XPATH, "//*[contains(text(), 'Nenhum bot ativo')]").text
    except Exception:
        pass

    with open('selenium_output.txt', 'a', encoding='utf-8') as f:
        f.write(f"\n--- Rodada em {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(f"Header Bots Ativos: {bots_ativos_header}\n")
        f.write(f"Mensagem Nenhum bot ativo: {nenhum_bot_ativo_msg}\n")

    if bots_ativos_header and not nenhum_bot_ativo_msg:
        print("[OK] Bots ativos detectados na tela do dashboard.")
    elif nenhum_bot_ativo_msg:
        print("[ERRO] Nenhum bot ativo detectado na tela do dashboard! Mensagem: " + nenhum_bot_ativo_msg)
    else:
        print("[ERRO] Não foi possível determinar o status dos bots ativos na tela do dashboard.")

    # Scroll para baixo
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(1)

    driver.save_screenshot('screenshot_dashboard.png')
    time.sleep(2)
finally:
    driver.quit()
print('Dashboard Selenium test completed.')
