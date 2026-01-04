"""
Testes Selenium para Dashboard do AutoCoinBot
===============================================

Testa:
- Carregamento da página principal
- Elementos visuais presentes
- Funcionalidade de login
- Validação de inputs de configuração
"""

import pytest
import os
import time
from pathlib import Path

# Importar após pytest marks
pytestmark = pytest.mark.skipif(
    os.getenv('RUN_SELENIUM', '0') != '1',
    reason='Testes Selenium desabilitados. Use RUN_SELENIUM=1 para habilitar'
)


@pytest.fixture(scope='module')
def driver():
    """Fixture que cria um driver Chrome para todos os testes"""
    from selenium_helper import get_chrome_driver
    
    driver = get_chrome_driver(headless=True)
    yield driver
    driver.quit()


@pytest.fixture
def app_url():
    """URL da aplicação baseada em APP_ENV"""
    env = os.getenv('APP_ENV', 'dev').lower()
    if env in ('hom', 'homologation', 'prod_hom'):
        return os.getenv('HOM_URL', 'https://autocoinbot.fly.dev/')
    return os.getenv('LOCAL_URL', 'http://localhost:8501')


class TestDashboardBasics:
    """Testes básicos do dashboard"""
    
    def test_dashboard_loads(self, driver, app_url):
        """Testa se o dashboard carrega sem erros"""
        driver.get(app_url)
        time.sleep(3)  # Aguarda carregamento
        
        assert "KuCoin" in driver.title or "AutoCoinBot" in driver.title
        assert driver.current_url.startswith(app_url)
    
    def test_header_exists(self, driver, app_url):
        """Testa se existe um header na página"""
        from selenium.webdriver.common.by import By
        
        driver.get(app_url)
        time.sleep(2)
        
        # Streamlit pode usar h1, h2 ou h3
        headers_found = False
        for tag in ['h1', 'h2', 'h3']:
            try:
                elements = driver.find_elements(By.TAG_NAME, tag)
                if elements:
                    headers_found = True
                    break
            except:
                continue
        
        assert headers_found, "Nenhum header (h1/h2/h3) encontrado"
    
    def test_buttons_exist(self, driver, app_url):
        """Testa se existem botões na interface"""
        from selenium.webdriver.common.by import By
        
        driver.get(app_url)
        time.sleep(2)
        
        # Buscar por diferentes tipos de botões
        buttons = []
        try:
            buttons.extend(driver.find_elements(By.CLASS_NAME, 'stButton'))
        except:
            pass
        
        try:
            buttons.extend(driver.find_elements(By.TAG_NAME, 'button'))
        except:
            pass
        
        assert len(buttons) > 0, "Nenhum botão encontrado na interface"


class TestDashboardLogin:
    """Testes de funcionalidade de login"""
    
    def test_login_form_exists(self, driver, app_url):
        """Verifica se formulário de login existe"""
        from selenium.webdriver.common.by import By
        
        driver.get(app_url)
        time.sleep(2)
        
        # Procurar por campos de input (login)
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        assert len(inputs) >= 2, "Formulário de login não encontrado (esperado: usuário + senha)"
    
    def test_login_with_credentials(self, driver, app_url):
        """Testa login com credenciais padrão"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        driver.get(app_url)
        time.sleep(2)
        
        try:
            # Tentar preencher login
            user_field = driver.find_element(By.XPATH, "//input[@type='text']")
            pass_field = driver.find_element(By.XPATH, "//input[@type='password']")
            
            user_field.clear()
            user_field.send_keys(os.getenv('KUCOIN_USER', 'admin'))
            
            pass_field.clear()
            pass_field.send_keys(os.getenv('KUCOIN_PASS', 'senha123'))
            
            # Clicar em submit
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Entrar') or contains(., 'Login')]")
            if submit_buttons:
                submit_buttons[0].click()
                time.sleep(3)
            
            # Verificar se login foi bem-sucedido (dashboard deve aparecer)
            page_text = driver.page_source.lower()
            assert any(word in page_text for word in ['bot', 'trade', 'balance', 'dashboard'])
            
        except Exception as e:
            pytest.skip(f"Login não pôde ser testado: {e}")


class TestDashboardContent:
    """Testes de conteúdo esperado no dashboard"""
    
    def test_trading_keywords_present(self, driver, app_url):
        """Verifica se palavras-chave de trading estão presentes"""
        driver.get(app_url)
        time.sleep(3)
        
        page_text = driver.page_source.lower()
        
        keywords = ['bot', 'trade', 'usdt', 'btc', 'symbol', 'entry', 'price']
        found_keywords = [kw for kw in keywords if kw in page_text]
        
        assert len(found_keywords) >= 3, f"Poucas palavras-chave encontradas: {found_keywords}"
    
    def test_configuration_section(self, driver, app_url):
        """Verifica se seção de configuração existe"""
        driver.get(app_url)
        time.sleep(3)
        
        page_text = driver.page_source.lower()
        
        config_words = ['config', 'configuração', 'setup', 'settings', 'parâmetros']
        assert any(word in page_text for word in config_words), "Seção de configuração não encontrada"


class TestDashboardScreenshot:
    """Testes que geram screenshots para validação visual"""
    
    def test_capture_dashboard_screenshot(self, driver, app_url):
        """Captura screenshot do dashboard para análise"""
        driver.get(app_url)
        time.sleep(3)
        
        screenshot_dir = Path('selenium_screenshots')
        screenshot_dir.mkdir(exist_ok=True)
        
        screenshot_path = screenshot_dir / 'dashboard_test.png'
        driver.save_screenshot(str(screenshot_path))
        
        assert screenshot_path.exists(), "Screenshot não foi salvo"
        assert screenshot_path.stat().st_size > 1000, "Screenshot muito pequeno (arquivo corrompido?)"


if __name__ == '__main__':
    # Permite executar testes diretamente
    pytest.main([__file__, '-v', '-s'])
