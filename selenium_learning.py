import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium_helper import get_chrome_driver, wait_for_http

# Config
LOCAL_URL = os.environ.get('LOCAL_URL', 'http://localhost:8501')
REMOTE_URL = os.environ.get('HOM_URL', 'https://autocoinbot.fly.dev/')
APP_ENV = os.environ.get('APP_ENV', os.environ.get('ENV', 'dev')).lower()
if APP_ENV in ('hom', 'homologation', 'prod_hom'):
    URL = REMOTE_URL + "?report=1"
else:
    URL = LOCAL_URL + "?report=1"

driver = get_chrome_driver(headless=False)
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

    # Interagir com tabs de aprendizado se existirem
    tabs = driver.find_elements(By.CLASS_NAME, 'stTabs')
    for tab in tabs:
        try:
            tab_buttons = tab.find_elements(By.TAG_NAME, 'button')
            for tbtn in tab_buttons:
                if 'Aprendizado' in (tbtn.text or '') and tbtn.is_displayed() and tbtn.is_enabled():
                    tbtn.click()
                    time.sleep(1)
        except Exception:
            continue
    for tab in tabs:
        try:
            tab_buttons = tab.find_elements(By.TAG_NAME, 'button')
            for tbtn in tab_buttons:
                if 'Aprendizado' in (tbtn.text or '') and tbtn.is_displayed() and tbtn.is_enabled():
                    tbtn.click()
                    time.sleep(1)
        except Exception:
            continue

    # Interagir com selects, inputs, etc.
    selects = driver.find_elements(By.TAG_NAME, 'select')
    for sel in selects:
        try:
            if sel.is_displayed() and sel.is_enabled():
                for option in sel.find_elements(By.TAG_NAME, 'option'):
                    option.click()
                    time.sleep(0.5)
        except Exception:
            continue

    # Scroll para baixo
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(1)


    driver.save_screenshot('screenshot_learning.png')
    time.sleep(2)
finally:
    driver.quit()
print('Learning Selenium test completed.')
