#!/usr/bin/env python3
"""Configuration for Selenium tests."""
import os
from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
TESTS_DIR = PROJECT_ROOT / "tests" / "selenium"
SCREENSHOTS_DIR = TESTS_DIR / "screenshots"
REPORTS_DIR = TESTS_DIR / "reports"
PAGES_DIR = TESTS_DIR / "pages"

# Ensure directories exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# URLs
LOCAL_URL = os.environ.get('LOCAL_URL', 'http://localhost:8501')
HOM_URL = os.environ.get('HOM_URL', 'https://autocoinbot.fly.dev')
PROD_URL = os.environ.get('PROD_URL', 'https://autocoinbot.fly.dev')

# Environment
APP_ENV = os.environ.get('APP_ENV', os.environ.get('ENV', 'dev')).lower()

# Determine base URL
if APP_ENV in ('hom', 'homologation'):
    BASE_URL = HOM_URL
elif APP_ENV in ('prod', 'production'):
    BASE_URL = PROD_URL
else:
    BASE_URL = LOCAL_URL

# Browser settings
HEADLESS = os.environ.get('HEADLESS', '1').lower() in ('1', 'true', 'yes')
SHOW_BROWSER = os.environ.get('SHOW_BROWSER', '0').lower() in ('1', 'true', 'yes')

# Timeouts (seconds)
PAGE_LOAD_TIMEOUT = int(os.environ.get('PAGE_LOAD_TIMEOUT', '30'))
ELEMENT_WAIT_TIMEOUT = int(os.environ.get('ELEMENT_WAIT_TIMEOUT', '10'))
HTTP_WAIT_TIMEOUT = int(os.environ.get('HTTP_WAIT_TIMEOUT', '30'))

# Test settings
TAKE_SCREENSHOTS = os.environ.get('TAKE_SCREENSHOTS', '1').lower() in ('1', 'true', 'yes')
SAVE_DOM = os.environ.get('SAVE_DOM', '1').lower() in ('1', 'true', 'yes')
VERBOSE = os.environ.get('VERBOSE', '0').lower() in ('1', 'true', 'yes')

# Authentication (if needed)
AUTH_USER = os.environ.get('AUTH_USER', 'admin')
AUTH_PASS = os.environ.get('AUTH_PASS', 'senha123')

# Report format
REPORT_FORMAT = os.environ.get('REPORT_FORMAT', 'text')  # text, json, html


def get_url(page: str = "") -> str:
    """Get full URL for a page."""
    if page:
        return f"{BASE_URL}/?view={page}"
    return BASE_URL


def get_api_url(endpoint: str) -> str:
    """Get API endpoint URL."""
    return f"{BASE_URL}{endpoint}"


def print_config():
    """Print current configuration."""
    print("🔧 Selenium Test Configuration")
    print("=" * 50)
    print(f"Environment: {APP_ENV}")
    print(f"Base URL: {BASE_URL}")
    print(f"Headless: {HEADLESS}")
    print(f"Show Browser: {SHOW_BROWSER}")
    print(f"Screenshots: {TAKE_SCREENSHOTS}")
    print(f"Save DOM: {SAVE_DOM}")
    print(f"Verbose: {VERBOSE}")
    print(f"Page Load Timeout: {PAGE_LOAD_TIMEOUT}s")
    print(f"Element Wait Timeout: {ELEMENT_WAIT_TIMEOUT}s")
    print("=" * 50)


if __name__ == "__main__":
    print_config()
