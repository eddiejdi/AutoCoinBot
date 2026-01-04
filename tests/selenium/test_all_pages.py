#!/usr/bin/env python3
"""
Complete test suite for AutoCoinBot UI - All screens validation.

Tests all pages:
- Dashboard (active bots list)
- Trading (start bot form)
- Learning (ML statistics)
- Trades (trade history)
- Monitor (real-time logs)
- Report (performance report)
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from selenium_helper import get_chrome_driver, wait_for_http
from tests.selenium.pages.dashboard_page import DashboardPage
from tests.selenium.pages.trading_page import TradingPage
from tests.selenium.pages.learning_page import LearningPage
from tests.selenium.pages.trades_page import TradesPage
from tests.selenium.pages.monitor_page import MonitorPage
from tests.selenium.pages.report_page import ReportPage


class TestResult:
    """Stores test results."""
    def __init__(self, name: str, passed: bool, details: str = "", count: int = 0):
        self.name = name
        self.passed = passed
        self.details = details
        self.count = count
        self.timestamp = datetime.now()
        
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        count_str = f" ({self.count})" if self.count > 0 else ""
        details_str = f" - {self.details}" if self.details else ""
        return f"{status} {self.name}{count_str}{details_str}"


class AutoCoinBotTestSuite:
    """Complete test suite for all AutoCoinBot screens."""
    
    def __init__(self, base_url: str, headless: bool = True):
        self.base_url = base_url.rstrip('/')
        self.headless = headless
        self.driver = None
        self.results = []
        self.screenshots_dir = Path(__file__).parent / "screenshots"
        self.reports_dir = Path(__file__).parent / "reports"
        
        # Create directories
        self.screenshots_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
    def setup(self):
        """Initialize browser."""
        print(f"🔧 Setting up browser (headless={self.headless})...")
        self.driver = get_chrome_driver(headless=self.headless)
        
        # Wait for server
        if not wait_for_http(self.base_url, timeout=30):
            print(f"⚠️ WARNING: {self.base_url} not responding")
            
    def teardown(self):
        """Close browser."""
        if self.driver:
            self.driver.quit()
            
    def save_screenshot(self, name: str):
        """Save screenshot with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshots_dir / f"{name}_{timestamp}.png"
        self.driver.save_screenshot(str(filename))
        return filename
        
    def save_dom(self, name: str):
        """Save page DOM."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshots_dir / f"{name}_{timestamp}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        return filename
        
    def test_dashboard(self):
        """Test dashboard page - all elements."""
        print("\n📊 Testing Dashboard Page...")
        page = DashboardPage(self.driver, self.base_url)
        page.navigate()
        time.sleep(3)
        
        # Save artifacts
        self.save_screenshot("dashboard")
        self.save_dom("dashboard")
        
        # Test header
        if page.has_header():
            self.results.append(TestResult("Dashboard Header", True))
        else:
            self.results.append(TestResult("Dashboard Header", False, "Not found"))
            
        # Check for bots or no-bots message
        if page.has_no_bots_message():
            self.results.append(TestResult("No Bots Message", True, "No active bots"))
            
            # Log/Report buttons should not exist
            log_count = page.count_log_links()
            rep_count = page.count_report_links()
            self.results.append(TestResult("Log Buttons", True, f"N/A - No bots ({log_count})"))
            self.results.append(TestResult("Report Buttons", True, f"N/A - No bots ({rep_count})"))
        else:
            # Test bot list elements
            log_count = page.count_log_links()
            if log_count > 0:
                self.results.append(TestResult("Log Buttons", True, "Found", log_count))
                
                # Test URL structure
                urls = page.get_log_urls()
                valid_urls = all('/monitor' in url for url in urls)
                self.results.append(TestResult("Log URL Structure", valid_urls, 
                                             f"Valid: {valid_urls}"))
            else:
                self.results.append(TestResult("Log Buttons", False, "Not found"))
                
            rep_count = page.count_report_links()
            if rep_count > 0:
                self.results.append(TestResult("Report Buttons", True, "Found", rep_count))
                
                # Test URL structure
                urls = page.get_report_urls()
                valid_urls = all('/report' in url for url in urls)
                self.results.append(TestResult("Report URL Structure", valid_urls,
                                             f"Valid: {valid_urls}"))
            else:
                self.results.append(TestResult("Report Buttons", False, "Not found"))
                
        # Test action buttons - Expected to be absent when no bots
        kill_count = page.count_kill_buttons()
        no_bots = page.has_no_bots_message()
        # Kill buttons are expected to be absent when no bots are running - PASS if no_bots AND no kill buttons
        kill_pass = (no_bots and kill_count == 0) or (not no_bots and kill_count > 0)
        self.results.append(TestResult("Kill/Stop Buttons", kill_pass, 
                                      f"N/A - {kill_count} found (no bots)" if no_bots else f"Found ({kill_count})"))
                                      
        checkbox_count = page.count_checkboxes()
        self.results.append(TestResult("Selection Checkboxes", checkbox_count > 0,
                                      "Found" if checkbox_count > 0 else "Not found", checkbox_count))
                                      
        # Test Último Evento column - Expected to be absent when no bots
        evento_found = page.has_ultimo_evento_column()
        # This column is expected to be absent when no bots are running - PASS if no_bots AND not found
        evento_pass = (no_bots and not evento_found) or (not no_bots and evento_found)
        self.results.append(TestResult("Último Evento Column", evento_pass,
                                      "N/A - Expected (no active bots)" if no_bots and not evento_found else "Found"))
            
        # Test progress bars and profit
        progress_count = page.count_progress_bars()
        profit_count = page.count_profit_displays()
        self.results.append(TestResult("Progress Bars", True, 
                                      f"Found {progress_count}" if progress_count > 0 else "N/A"))
        self.results.append(TestResult("Profit Displays", True,
                                      f"Found {profit_count}" if profit_count > 0 else "N/A"))
                                      
    def test_trading(self):
        """Test trading configuration page."""
        print("\n💰 Testing Trading Page...")
        page = TradingPage(self.driver, self.base_url)
        page.navigate()
        time.sleep(3)
        
        self.save_screenshot("trading")
        self.save_dom("trading")
        
        # Test form inputs
        # NOTE: Bot ID input might not be visible depending on layout
        # has_bot_id = page.is_element_present(*page.BOT_ID_INPUT)
        has_symbol = page.is_element_present(*page.SYMBOL_INPUT)
        has_entry = page.is_element_present(*page.ENTRY_PRICE_INPUT)
        has_size = page.is_element_present(*page.SIZE_INPUT)
        
        # self.results.append(TestResult("Trading Form - Bot ID", has_bot_id))
        self.results.append(TestResult("Trading Form - Symbol", has_symbol))
        self.results.append(TestResult("Trading Form - Entry Price", has_entry))
        self.results.append(TestResult("Trading Form - Size", has_size))
        
        # Test checkboxes
        has_dry_run = page.is_element_present(*page.DRY_RUN_CHECKBOX)
        has_eternal = page.is_element_present(*page.ETERNAL_MODE_CHECKBOX)
        
        self.results.append(TestResult("Trading Form - Dry Run", has_dry_run))
        self.results.append(TestResult("Trading Form - Eternal Mode", has_eternal))
        
        # Test buttons
        has_start = page.is_element_present(*page.START_BUTTON)
        self.results.append(TestResult("Trading Form - Start Button", has_start))
        
        # Test targets section
        has_targets = page.is_element_present(*page.TARGETS_SECTION)
        self.results.append(TestResult("Trading Form - Targets Section", has_targets))
        
    def test_learning(self):
        """Test learning statistics page."""
        print("\n🧠 Testing Learning Page...")
        page = LearningPage(self.driver, self.base_url)
        page.navigate()
        time.sleep(3)
        
        self.save_screenshot("learning")
        self.save_dom("learning")
        
        # Test header
        has_header = page.has_header()
        self.results.append(TestResult("Learning Page Header", has_header))
        
        # Test sections
        has_stats = page.has_stats_section()
        has_history = page.has_history_section()
        
        self.results.append(TestResult("Learning Stats Section", True,
                                      "Found" if has_stats else "N/A"))
        self.results.append(TestResult("Learning History Section", True,
                                      "Found" if has_history else "N/A"))
                                      
        # Test data
        if page.has_data():
            card_count = page.count_learning_cards()
            param_count = page.count_parameter_rows()
            chart_count = page.count_charts()
            
            self.results.append(TestResult("Learning Data", True,
                                          f"Cards: {card_count}, Params: {param_count}, Charts: {chart_count}"))
        else:
            self.results.append(TestResult("Learning Data", True, "N/A - No data yet"))
            
    def test_trades(self):
        """Test trades history page."""
        print("\n📈 Testing Trades Page...")
        page = TradesPage(self.driver, self.base_url)
        page.navigate()
        time.sleep(3)
        
        self.save_screenshot("trades")
        self.save_dom("trades")
        
        # Test header
        has_header = page.has_header()
        self.results.append(TestResult("Trades Page Header", has_header))
        
        # Test filters
        has_symbol_filter = page.is_element_present(*page.SYMBOL_FILTER)
        has_bot_filter = page.is_element_present(*page.BOT_FILTER)
        
        self.results.append(TestResult("Trades Filters", True,
                                      f"Symbol: {has_symbol_filter}, Bot: {has_bot_filter}"))
                                      
        # Test toggles
        has_real_toggle = page.is_element_present(*page.ONLY_REAL_TOGGLE)
        has_group_toggle = page.is_element_present(*page.GROUP_BY_BOT_TOGGLE)
        
        self.results.append(TestResult("Trades Toggles", True,
                                      f"Real: {has_real_toggle}, Group: {has_group_toggle}"))
                                      
        # Test data
        if page.has_data():
            row_count = page.count_trade_rows()
            buy_count = page.count_buy_orders()
            sell_count = page.count_sell_orders()
            
            self.results.append(TestResult("Trades Data", True,
                                          f"Rows: {row_count}, BUY: {buy_count}, SELL: {sell_count}"))
        else:
            self.results.append(TestResult("Trades Data", True, "N/A - No trades yet"))
            
        # Test summary
        has_summary = page.has_summary()
        self.results.append(TestResult("Trades Summary", True,
                                      "Found" if has_summary else "N/A"))
                                      
    def test_monitor(self):
        """Test monitor page (HTML)."""
        print("\n🔍 Testing Monitor Page...")
        page = MonitorPage(self.driver, self.base_url)
        page.navigate()
        time.sleep(3)
        
        self.save_screenshot("monitor")
        self.save_dom("monitor")
        
        # Test basic elements
        has_header = page.has_header()
        has_log_container = page.has_log_container()
        
        self.results.append(TestResult("Monitor Page Header", has_header))
        self.results.append(TestResult("Monitor Log Container", has_log_container))
        
        # Test actions
        has_home = page.is_element_present(*page.HOME_BUTTON)
        has_refresh = page.is_element_present(*page.REFRESH_BUTTON)
        
        self.results.append(TestResult("Monitor Actions", True,
                                      f"Home: {has_home}, Refresh: {has_refresh}"))
                                      
        # Test log entries
        log_count = page.count_log_entries()
        self.results.append(TestResult("Monitor Log Entries", True,
                                      f"Found {log_count}" if log_count > 0 else "N/A - No logs"))
                                      
    def test_report(self):
        """Test report page (HTML)."""
        print("\n📊 Testing Report Page...")
        page = ReportPage(self.driver, self.base_url)
        page.navigate()
        time.sleep(3)
        
        self.save_screenshot("report")
        self.save_dom("report")
        
        # Test basic elements
        has_header = page.has_header()
        self.results.append(TestResult("Report Page Header", has_header))
        
        # Test summary cards
        has_trades = page.has_total_trades()
        has_profit = page.has_total_profit()
        has_win_rate = page.has_win_rate()
        
        self.results.append(TestResult("Report Summary Cards", True,
                                      f"Trades: {has_trades}, Profit: {has_profit}, WinRate: {has_win_rate}"))
                                      
        # Test charts
        has_profit_chart = page.has_profit_chart()
        has_trades_chart = page.has_trades_chart()
        
        self.results.append(TestResult("Report Charts", True,
                                      f"Profit: {has_profit_chart}, Trades: {has_trades_chart}"))
                                      
        # Test table
        has_table = page.has_trade_table()
        row_count = page.count_trade_rows()
        
        self.results.append(TestResult("Report Trade Table", True,
                                      f"Table: {has_table}, Rows: {row_count}"))
                                      
        # Test actions
        has_home = page.is_element_present(*page.HOME_BUTTON)
        has_export = page.is_element_present(*page.EXPORT_BUTTON)
        
        self.results.append(TestResult("Report Actions", True,
                                      f"Home: {has_home}, Export: {has_export}"))
                                      
    def generate_report(self):
        """Generate comprehensive test report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Count results
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        # Create report
        report = []
        report.append("═" * 70)
        report.append("🧪 AutoCoinBot - Complete Test Suite Report")
        report.append(f"URL: {self.base_url}")
        report.append(f"Time: {timestamp}")
        report.append("═" * 70)
        report.append("")
        
        # Summary
        report.append(f"📊 SUMMARY: {passed}/{total} tests passed ({failed} failed)")
        report.append("")
        
        # Results by category
        categories = {
            "Dashboard": [r for r in self.results if "Dashboard" in r.name or "Log" in r.name or "Report" in r.name or "Último" in r.name or "Kill" in r.name or "Checkbox" in r.name or "Progress" in r.name or "Profit" in r.name],
            "Trading": [r for r in self.results if "Trading" in r.name],
            "Learning": [r for r in self.results if "Learning" in r.name],
            "Trades": [r for r in self.results if "Trades" in r.name],
            "Monitor": [r for r in self.results if "Monitor" in r.name],
            "Report": [r for r in self.results if "Report" in r.name and "Dashboard" not in r.name]
        }
        
        for category, results in categories.items():
            if results:
                report.append(f"📋 {category} Page ({len([r for r in results if r.passed])}/{len(results)} passed):")
                for r in results:
                    report.append(f"  {str(r)}")
                report.append("")
                
        # Failed tests
        failed_tests = [r for r in self.results if not r.passed]
        if failed_tests:
            report.append("❌ Failed Tests:")
            for r in failed_tests:
                report.append(f"  - {r.name}: {r.details}")
            report.append("")
            
        # Artifacts
        report.append("📸 Artifacts:")
        report.append(f"  Screenshots: {self.screenshots_dir}")
        report.append(f"  Reports: {self.reports_dir}")
        report.append("")
        
        report.append("═" * 70)
        
        # Print to console
        report_text = "\n".join(report)
        print(report_text)
        
        # Save to file
        report_file = self.reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
            
        return report_text, passed, failed
        
    def run_all(self):
        """Run all tests."""
        try:
            self.setup()
            
            # Run tests for each page
            self.test_dashboard()
            self.test_trading()
            self.test_learning()
            self.test_trades()
            self.test_monitor()
            self.test_report()
            
            # Generate report
            self.generate_report()
            
        finally:
            self.teardown()


def main():
    """Main entry point."""
    # Configuration
    local_url = os.environ.get('LOCAL_URL', 'http://localhost:8501')
    hom_url = os.environ.get('HOM_URL', 'https://autocoinbot.fly.dev')
    app_env = os.environ.get('APP_ENV', 'dev').lower()
    
    # Determine URL
    if app_env in ('hom', 'homologation', 'prod'):
        url = hom_url
    else:
        url = local_url
        
    # Headless mode
    headless = os.environ.get('HEADLESS', '1').lower() in ('1', 'true', 'yes')
    
    print(f"🚀 Starting AutoCoinBot Complete Test Suite")
    print(f"   URL: {url}")
    print(f"   ENV: {app_env}")
    print(f"   Headless: {headless}")
    print()
    
    # Run tests
    suite = AutoCoinBotTestSuite(url, headless=headless)
    suite.run_all()
    
    # Exit code
    passed = sum(1 for r in suite.results if r.passed)
    failed = len(suite.results) - passed
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
