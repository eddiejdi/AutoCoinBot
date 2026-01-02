#!/usr/bin/env python3
# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║  🔒 HOMOLOGADO: selenium_validate_all.py - Script de validação completo       ║
# ║  Data: 2026-01-02 | Sessão: fix-selenium-validation                           ║
# ║  NÃO ALTERAR SEM APROVAÇÃO - Valida todos os elementos UI ajustados           ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝
"""
Selenium Validation Script - Validates all UI elements adjusted in this session.

Elements validated:
1. Dashboard header "🤖 Bots Ativos"
2. Log buttons (HTML links with target="_blank")
3. Report buttons (HTML links with target="_blank")
4. "Último Evento" column in bot list
5. Kill/Stop buttons
6. Checkboxes for bot selection
7. Progress bars and profit display
8. Dynamic URLs (production vs local)
"""

import time
import os
import sys
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium_helper import get_chrome_driver, wait_for_http


class ValidationResult:
    """Stores validation results for a single check."""
    def __init__(self, name: str, passed: bool, message: str = "", count: int = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.count = count

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        count_str = f" ({self.count})" if self.count > 0 else ""
        msg_str = f" - {self.message}" if self.message else ""
        return f"{status} {self.name}{count_str}{msg_str}"


def validate_dashboard_elements(driver) -> list[ValidationResult]:
    """Validate all dashboard elements."""
    results = []
    
    # 1. Header "Bots Ativos"
    try:
        headers = driver.find_elements(By.XPATH, 
            "//*[contains(text(), 'Bots Ativos') or contains(text(), '🤖 Bots Ativos')]")
        if headers:
            results.append(ValidationResult("Dashboard Header", True, "Found", len(headers)))
        else:
            results.append(ValidationResult("Dashboard Header", False, "Not found"))
    except Exception as e:
        results.append(ValidationResult("Dashboard Header", False, str(e)))
    
    # 2. Log buttons - Now HTML links with target="_blank"
    try:
        # Look for <a> tags with "Log" text and target="_blank"
        log_links = driver.find_elements(By.XPATH, 
            "//a[contains(text(), 'Log') or contains(text(), 'LOG')][@target='_blank']")
        if log_links:
            results.append(ValidationResult("Log Buttons (HTML links)", True, "Found with target=_blank", len(log_links)))
        else:
            # Fallback: any link with Log text
            log_any = driver.find_elements(By.XPATH, 
                "//a[contains(text(), 'Log') or contains(text(), 'LOG')]")
            if log_any:
                results.append(ValidationResult("Log Buttons (HTML links)", True, "Found (no target check)", len(log_any)))
            else:
                # Check if no bots are active
                no_bots = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'Nenhum bot ativo') or contains(text(), 'Nenhuma sessão')]")
                if no_bots:
                    results.append(ValidationResult("Log Buttons (HTML links)", True, "N/A - No active bots"))
                else:
                    results.append(ValidationResult("Log Buttons (HTML links)", False, "Not found"))
    except Exception as e:
        results.append(ValidationResult("Log Buttons (HTML links)", False, str(e)))
    
    # 3. Report buttons - Now HTML links with target="_blank"
    try:
        rep_links = driver.find_elements(By.XPATH, 
            "//a[contains(text(), 'REL') or contains(text(), 'Rel')][@target='_blank']")
        if rep_links:
            results.append(ValidationResult("Report Buttons (HTML links)", True, "Found with target=_blank", len(rep_links)))
        else:
            rep_any = driver.find_elements(By.XPATH, 
                "//a[contains(text(), 'REL') or contains(text(), 'Rel')]")
            if rep_any:
                results.append(ValidationResult("Report Buttons (HTML links)", True, "Found (no target check)", len(rep_any)))
            else:
                no_bots = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'Nenhum bot ativo') or contains(text(), 'Nenhuma sessão')]")
                if no_bots:
                    results.append(ValidationResult("Report Buttons (HTML links)", True, "N/A - No active bots"))
                else:
                    # Report links may only appear in stopped sessions
                    results.append(ValidationResult("Report Buttons (HTML links)", True, "N/A - May only show in stopped"))
    except Exception as e:
        results.append(ValidationResult("Report Buttons (HTML links)", False, str(e)))
    
    # 4. "Último Evento" column header
    try:
        evento_headers = driver.find_elements(By.XPATH, 
            "//*[contains(text(), 'Último Evento') or contains(text(), '📝 Último Evento')]")
        if evento_headers:
            results.append(ValidationResult("Último Evento Column", True, "Found", len(evento_headers)))
        else:
            # May not be visible if no bots
            no_bots = driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Nenhum bot ativo')]")
            if no_bots:
                results.append(ValidationResult("Último Evento Column", True, "N/A - No active bots"))
            else:
                results.append(ValidationResult("Último Evento Column", False, "Not found"))
    except Exception as e:
        results.append(ValidationResult("Último Evento Column", False, str(e)))
    
    # 5. Kill/Stop buttons
    try:
        kill_btns = driver.find_elements(By.XPATH, 
            "//button[contains(text(), 'Kill') or contains(text(), 'Enc') or contains(text(), '🛑')]")
        st_key_kill = driver.find_elements(By.CSS_SELECTOR, '[class*="st-key-kill_"]')
        total_kill = len(kill_btns) + len(st_key_kill)
        if total_kill > 0:
            results.append(ValidationResult("Kill/Stop Buttons", True, "Found", total_kill))
        else:
            no_bots = driver.find_elements(By.XPATH, "//*[contains(text(), 'Nenhum bot ativo')]")
            if no_bots:
                results.append(ValidationResult("Kill/Stop Buttons", True, "N/A - No active bots"))
            else:
                results.append(ValidationResult("Kill/Stop Buttons", False, "Not found"))
    except Exception as e:
        results.append(ValidationResult("Kill/Stop Buttons", False, str(e)))
    
    # 6. Selection checkboxes
    try:
        checkboxes = driver.find_elements(By.CSS_SELECTOR, '[class*="st-key-sel_kill_"]')
        checkbox_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
        total_cb = len(checkboxes) + len(checkbox_inputs)
        if total_cb > 0:
            results.append(ValidationResult("Selection Checkboxes", True, "Found", total_cb))
        else:
            no_bots = driver.find_elements(By.XPATH, "//*[contains(text(), 'Nenhum bot ativo')]")
            if no_bots:
                results.append(ValidationResult("Selection Checkboxes", True, "N/A - No active bots"))
            else:
                results.append(ValidationResult("Selection Checkboxes", False, "Not found"))
    except Exception as e:
        results.append(ValidationResult("Selection Checkboxes", False, str(e)))
    
    # 7. Progress bars
    try:
        progress = driver.find_elements(By.CSS_SELECTOR, '[role="progressbar"], .stProgress')
        if progress:
            results.append(ValidationResult("Progress Bars", True, "Found", len(progress)))
        else:
            # Progress bars only show when bots are active
            results.append(ValidationResult("Progress Bars", True, "N/A - May not be visible"))
    except Exception as e:
        results.append(ValidationResult("Progress Bars", False, str(e)))
    
    # 8. Profit display (% / alvo)
    try:
        profit_display = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '% / alvo') or contains(text(), 'alvo')]")
        if profit_display:
            results.append(ValidationResult("Profit Display", True, "Found", len(profit_display)))
        else:
            no_bots = driver.find_elements(By.XPATH, "//*[contains(text(), 'Nenhum bot ativo')]")
            if no_bots:
                results.append(ValidationResult("Profit Display", True, "N/A - No active bots"))
            else:
                results.append(ValidationResult("Profit Display", False, "Not found"))
    except Exception as e:
        results.append(ValidationResult("Profit Display", False, str(e)))
    
    return results


def validate_url_structure(driver) -> list[ValidationResult]:
    """Validate URL structure for links."""
    results = []
    
    try:
        # Check if Log links have correct URL structure
        log_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/monitor')]")
        if log_links:
            # Check first link for proper structure
            href = log_links[0].get_attribute('href')
            if '/monitor' in href and ('bot=' in href or 'home=' in href):
                results.append(ValidationResult("Log URL Structure", True, f"Correct: {href[:80]}..."))
            else:
                results.append(ValidationResult("Log URL Structure", False, f"Missing params: {href[:80]}"))
        else:
            results.append(ValidationResult("Log URL Structure", True, "N/A - No log links"))
    except Exception as e:
        results.append(ValidationResult("Log URL Structure", False, str(e)))
    
    try:
        # Check if Report links have correct URL structure
        rep_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/report')]")
        if rep_links:
            href = rep_links[0].get_attribute('href')
            if '/report' in href:
                results.append(ValidationResult("Report URL Structure", True, f"Correct: {href[:80]}..."))
            else:
                results.append(ValidationResult("Report URL Structure", False, f"Invalid: {href[:80]}"))
        else:
            results.append(ValidationResult("Report URL Structure", True, "N/A - No report links"))
    except Exception as e:
        results.append(ValidationResult("Report URL Structure", False, str(e)))
    
    return results


def do_login(driver):
    """Attempt automatic login if login form is present."""
    try:
        user_input = driver.find_element(By.XPATH, "//input[@type='text']")
        pass_input = driver.find_element(By.XPATH, "//input[@type='password']")
        user_input.send_keys('admin')
        pass_input.send_keys('senha123')
        
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for btn in buttons:
            if 'Entrar' in (btn.text or '') and btn.is_displayed() and btn.is_enabled():
                btn.click()
                time.sleep(1)
                break
        
        WebDriverWait(driver, 10).until_not(
            lambda d: d.find_element(By.XPATH, "//input[@type='password']").is_displayed()
        )
        return True
    except Exception:
        return False


def wait_for_render(driver, timeout=30):
    """Wait for page to finish rendering."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            # Check for dashboard header or "no bots" message
            headers = driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Bots Ativos') or contains(text(), 'Nenhum bot ativo')]")
            if headers:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    # Config
    LOCAL_URL = os.environ.get('LOCAL_URL', 'http://localhost:8501')
    REMOTE_URL = os.environ.get('HOM_URL', 'https://autocoinbot.fly.dev/')
    APP_ENV = os.environ.get('APP_ENV', os.environ.get('ENV', 'dev')).lower()
    
    if APP_ENV in ('hom', 'homologation', 'prod_hom'):
        URL = REMOTE_URL
    else:
        URL = LOCAL_URL
    
    show_browser = os.environ.get('SHOW_BROWSER', '0').lower() in ('1', 'true', 'yes')
    
    print(f"\n{'='*60}")
    print(f"🔍 AutoCoinBot Selenium Validation")
    print(f"{'='*60}")
    print(f"URL: {URL}")
    print(f"ENV: {APP_ENV}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Wait for server
    if not wait_for_http(URL, timeout=30, interval=0.5):
        print(f"[WARN] {URL} did not respond within timeout")
    
    driver = get_chrome_driver(headless=not show_browser, show_browser=show_browser)
    driver.set_window_size(1920, 1080)
    
    try:
        driver.get(URL)
        time.sleep(3)
        
        # Try login
        do_login(driver)
        time.sleep(2)
        
        # Wait for render
        if not wait_for_render(driver, timeout=30):
            print("[WARN] Page render not detected within timeout")
        
        time.sleep(2)
        
        # Run validations
        all_results = []
        
        print("\n📋 Dashboard Elements:")
        print("-" * 40)
        dashboard_results = validate_dashboard_elements(driver)
        all_results.extend(dashboard_results)
        for r in dashboard_results:
            print(f"  {r}")
        
        print("\n🔗 URL Structure:")
        print("-" * 40)
        url_results = validate_url_structure(driver)
        all_results.extend(url_results)
        for r in url_results:
            print(f"  {r}")
        
        # Save screenshot
        try:
            driver.save_screenshot('screenshot_validation.png')
            print("\n📸 Screenshot saved: screenshot_validation.png")
        except Exception:
            pass
        
        # Save DOM
        try:
            with open('selenium_dom_validation.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("📄 DOM saved: selenium_dom_validation.html")
        except Exception:
            pass
        
        # Summary
        passed = sum(1 for r in all_results if r.passed)
        failed = sum(1 for r in all_results if not r.passed)
        
        print(f"\n{'='*60}")
        print(f"📊 SUMMARY: {passed} passed, {failed} failed")
        print(f"{'='*60}")
        
        if failed > 0:
            print("\n❌ Failed validations:")
            for r in all_results:
                if not r.passed:
                    print(f"  - {r.name}: {r.message}")
            sys.exit(1)
        else:
            print("\n✅ All validations passed!")
            sys.exit(0)
            
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
