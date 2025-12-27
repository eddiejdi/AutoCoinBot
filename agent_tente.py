#!/usr/bin/env python3
"""
Agent Tente - Suporte automatizado via Selenium para AutoCoinBot
- Navega na interface web (http://localhost:8501)
- Tira screenshots
- Loga erros/exceções
- Ajuda a identificar problemas visuais e de fluxo
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
import os
import datetime

# Configurações
URL = "http://localhost:8501"
SCREENSHOT_DIR = "selenium_screenshots"
LOG_FILE = "selenium_agent.log"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{now}] {msg}\n")
    print(f"[LOG] {msg}")

def take_screenshot(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    log(f"Screenshot salva: {path}")

def main():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except WebDriverException as e:
        log(f"Erro ao iniciar ChromeDriver: {e}")
        return
    try:
        log(f"Acessando {URL}")
        driver.get(URL)
        time.sleep(3)
        take_screenshot(driver, "home")
        # Exemplo: tentar encontrar botão START
        try:
            start_btn = driver.find_element(By.XPATH, "//*[contains(text(),'START') or contains(text(),'Start')]")
            start_btn.location_once_scrolled_into_view
            take_screenshot(driver, "start_btn_visible")
            log("Botão START encontrado na tela.")
        except NoSuchElementException:
            log("Botão START não encontrado!")
        # Exemplo: verificar mensagens de erro na tela
        try:
            error_msgs = driver.find_elements(By.XPATH, "//*[contains(text(),'erro') or contains(text(),'Error') or contains(text(),'Exception')]")
            if error_msgs:
                for i, el in enumerate(error_msgs):
                    log(f"Erro visível: {el.text}")
                    take_screenshot(driver, f"erro_{i}")
            else:
                log("Nenhuma mensagem de erro visível detectada.")
        except Exception as e:
            log(f"Falha ao buscar mensagens de erro: {e}")
        # Adicione mais interações conforme necessário
    except Exception as e:
        log(f"Exceção geral: {e}")
        take_screenshot(driver, "exception")
    finally:
        driver.quit()
        log("Navegação Selenium finalizada.")

if __name__ == "__main__":
    main()
