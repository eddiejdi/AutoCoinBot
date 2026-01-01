"""Configuração de pytest para garantir que o diretório do projeto
esteja sempre presente em sys.path durante os testes.
"""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
root_str = str(ROOT)

if root_str not in sys.path:
    sys.path.insert(0, root_str)


# ---------------------------------------------------------------------------
# Selenium fixtures for UI tests
# ---------------------------------------------------------------------------
_SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    _SELENIUM_AVAILABLE = True
except ImportError:
    pass


def _create_chrome_driver():
    """Create a headless Chrome WebDriver."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--incognito")
    try:
        svc = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=svc, options=opts)
    except Exception:
        return webdriver.Chrome(options=opts)


@pytest.fixture(scope="function")
def driver():
    """Fixture for Selenium WebDriver (function scope)."""
    if not _SELENIUM_AVAILABLE:
        pytest.skip("Selenium not available")
    if os.environ.get("RUN_SELENIUM", "0") == "0":
        pytest.skip("Selenium UI tests disabled (set RUN_SELENIUM=1 to enable)")
    d = _create_chrome_driver()
    yield d
    d.quit()


@pytest.fixture(scope="function")
def d():
    """Alias fixture for Selenium WebDriver (used by test_ui_full.py)."""
    if not _SELENIUM_AVAILABLE:
        pytest.skip("Selenium not available")
    if os.environ.get("RUN_SELENIUM", "0") == "0":
        pytest.skip("Selenium UI tests disabled (set RUN_SELENIUM=1 to enable)")
    driver = _create_chrome_driver()
    yield driver
    driver.quit()
