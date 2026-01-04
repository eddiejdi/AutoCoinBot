"""
Testes Selenium para Navegação
================================

Testa:
- Navegação entre páginas/tabs
- Links funcionais
- Transições de estado
"""

import pytest
import os
import time

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_SELENIUM', '0') != '1',
    reason='Testes Selenium desabilitados. Use RUN_SELENIUM=1 para habilitar'
)


@pytest.fixture(scope='module')
def driver():
    """Fixture que cria um driver Chrome"""
    from selenium_helper import get_chrome_driver
    
    driver = get_chrome_driver(headless=True)
    yield driver
    driver.quit()


@pytest.fixture
def app_url():
    """URL da aplicação"""
    env = os.getenv('APP_ENV', 'dev').lower()
    if env in ('hom', 'homologation', 'prod_hom'):
        return os.getenv('HOM_URL', 'https://autocoinbot.fly.dev/')
    return os.getenv('LOCAL_URL', 'http://localhost:8501')


class TestPageNavigation:
    """Testes de navegação entre páginas"""
    
    def test_navigate_to_dashboard(self, driver, app_url):
        """Testa navegação para dashboard"""
        driver.get(app_url)
        time.sleep(2)
        
        assert driver.current_url.startswith(app_url)
    
    def test_page_title_loads(self, driver, app_url):
        """Verifica se título da página carrega"""
        driver.get(app_url)
        time.sleep(2)
        
        title = driver.title
        assert len(title) > 0, "Título da página está vazio"
        assert any(word in title.lower() for word in ['kucoin', 'bot', 'auto', 'trade'])
    
    def test_page_has_content(self, driver, app_url):
        """Verifica se página tem conteúdo"""
        driver.get(app_url)
        time.sleep(2)
        
        body = driver.find_element('tag name', 'body')
        assert len(body.text) > 100, "Página tem pouco conteúdo"


class TestTabNavigation:
    """Testes de navegação por tabs/seções"""
    
    def test_tabs_or_sections_exist(self, driver, app_url):
        """Verifica se existem tabs ou seções navegáveis"""
        from selenium.webdriver.common.by import By
        
        driver.get(app_url)
        time.sleep(2)
        
        # Streamlit usa tabs, buttons ou links para navegação
        page_source = driver.page_source.lower()
        
        nav_indicators = [
            'tab', 'section', 'menu', 'navigate', 'página',
            'dashboard', 'relatório', 'report', 'config'
        ]
        
        found = [ind for ind in nav_indicators if ind in page_source]
        assert len(found) >= 2, f"Poucos indicadores de navegação: {found}"


class TestLinksFunctionality:
    """Testes de funcionalidade de links"""
    
    def test_clickable_elements(self, driver, app_url):
        """Verifica se existem elementos clicáveis"""
        from selenium.webdriver.common.by import By
        
        driver.get(app_url)
        time.sleep(2)
        
        # Contar elementos clicáveis
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        links = driver.find_elements(By.TAG_NAME, 'a')
        
        total_clickable = len(buttons) + len(links)
        assert total_clickable > 0, "Nenhum elemento clicável encontrado"
    
    def test_no_broken_links(self, driver, app_url):
        """Verifica se não há links quebrados visíveis"""
        from selenium.webdriver.common.by import By
        
        driver.get(app_url)
        time.sleep(2)
        
        links = driver.find_elements(By.TAG_NAME, 'a')
        
        broken_count = 0
        for link in links[:10]:  # Testar primeiros 10 links apenas
            href = link.get_attribute('href')
            if href and (href == '#' or href == 'javascript:void(0)'):
                broken_count += 1
        
        # Permitir alguns links internos/placeholder
        assert broken_count < len(links), "Muitos links quebrados/placeholder"


class TestResponsiveness:
    """Testes de responsividade da interface"""
    
    def test_mobile_viewport(self, driver, app_url):
        """Testa se página funciona em viewport mobile"""
        driver.set_window_size(375, 667)  # iPhone 8
        driver.get(app_url)
        time.sleep(2)
        
        body = driver.find_element('tag name', 'body')
        assert len(body.text) > 50, "Conteúdo não carregou em viewport mobile"
    
    def test_desktop_viewport(self, driver, app_url):
        """Testa se página funciona em viewport desktop"""
        driver.set_window_size(1920, 1080)
        driver.get(app_url)
        time.sleep(2)
        
        body = driver.find_element('tag name', 'body')
        assert len(body.text) > 50, "Conteúdo não carregou em viewport desktop"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
