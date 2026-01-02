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
REMOTE_URL = os.environ.get('HOM_URL', 'https://autocoinbot.fly.dev/')
APP_ENV = os.environ.get('APP_ENV', os.environ.get('ENV', 'dev')).lower()
if APP_ENV in ('hom', 'homologation', 'prod_hom'):
    URL = REMOTE_URL + "?report=1"
else:
    URL = LOCAL_URL + "?report=1"

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--incognito')

options.add_argument('--headless=new')  # Não usar headless para manter janela visível
service = Service('/usr/bin/chromedriver')
options.binary_location = '/usr/bin/chromium-browser' if os.path.exists('/usr/bin/chromium-browser') else '/usr/bin/chromium'
driver = webdriver.Chrome(service=service, options=options)

driver.set_window_size(1920, 1080)
driver.get(URL)
time.sleep(5)

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
        WebDriverWait(driver, 10).until_not(
            lambda d: d.find_element(By.XPATH, "//input[@type='password']").is_displayed()
        )
    except Exception:
        pass

    # Não clicar em outros botões genéricos após login

    # Interagir com tabelas
    tables = driver.find_elements(By.TAG_NAME, 'table')
    for table in tables:
        try:
            rows = table.find_elements(By.TAG_NAME, 'tr')
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                for cell in cells:
                    _ = cell.text
        except Exception:
            continue

    # Scroll para baixo
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(1)

    driver.save_screenshot('screenshot_report.png')
    time.sleep(2)
finally:
    driver.quit()
print('Report Selenium test completed.')
