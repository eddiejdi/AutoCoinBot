import os
import pytest


pytestmark = pytest.mark.skipif(os.getenv('RUN_SCRAPER_TESTS', '0') != '1', reason='Selenium UI tests disabled by default')


def test_agent0_scraper_runs():
    import agent0_scraper as scraper

    results, screenshot = scraper.validar_tela(scraper.APP_URL, scraper.ELEMENTOS_ESPERADOS, screenshot_path='screenshot_test.png')
    assert isinstance(results, dict)
    # At minimum, scraper should report whether login was attempted
    assert 'login_preenchido' in results
    # Header normalization should exist
    assert 'h1' in results and isinstance(results['h1'], bool)
