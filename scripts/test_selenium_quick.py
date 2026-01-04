#!/usr/bin/env python3
"""Quick Selenium test to verify ChromeDriver is working."""
import sys
sys.path.insert(0, '/home/eddie/AutoCoinBot')

from selenium_helper import get_chrome_driver

def main():
    print("Iniciando teste rápido do Selenium...")
    driver = None
    try:
        driver = get_chrome_driver(headless=True)
        print(f"✅ Driver criado com sucesso!")
        print(f"   Browser: {driver.capabilities.get('browserName', 'N/A')}")
        print(f"   Versão: {driver.capabilities.get('browserVersion', 'N/A')}")
        
        # Testar navegação
        driver.get("https://www.google.com")
        print(f"   Título da página: {driver.title}")
        
        print("✅ Teste Selenium concluído com sucesso!")
        return 0
    except Exception as e:
        print(f"❌ Erro no teste Selenium: {e}")
        return 1
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    sys.exit(main())
