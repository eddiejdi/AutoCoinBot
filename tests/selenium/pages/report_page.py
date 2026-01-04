"""Report Page Object - Bot performance report (HTML page)."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class ReportPage(BasePage):
    """Bot performance report page (report_window.html)."""
    
    # Headers
    HEADER = (By.XPATH, "//*[contains(text(), 'Report') or contains(text(), 'Relatório')]")
    BOT_ID_DISPLAY = (By.XPATH, "//*[contains(text(), 'Bot:') or contains(@id, 'bot')]")
    
    # Summary cards
    TOTAL_TRADES = (By.XPATH, "//*[contains(text(), 'Total Trades') or contains(@id, 'total-trades')]")
    TOTAL_PROFIT = (By.XPATH, "//*[contains(text(), 'Total Profit') or contains(@id, 'profit')]")
    WIN_RATE = (By.XPATH, "//*[contains(text(), 'Win Rate') or contains(@id, 'win-rate')]")
    AVG_PROFIT = (By.XPATH, "//*[contains(text(), 'Average') or contains(@id, 'avg')]")
    
    # Charts
    PROFIT_CHART = (By.XPATH, "//*[@id='profit-chart' or contains(@class, 'chart')]")
    TRADES_CHART = (By.XPATH, "//*[@id='trades-chart' or contains(@class, 'chart')]")
    
    # Trade table
    TRADE_TABLE = (By.XPATH, "//table")
    TRADE_ROWS = (By.XPATH, "//tr[contains(@class, 'trade')]")
    
    # Actions
    HOME_BUTTON = (By.XPATH, "//button[contains(text(), 'Home') or contains(@id, 'home')]")
    EXPORT_BUTTON = (By.XPATH, "//button[contains(text(), 'Export') or contains(@id, 'export')]")
    REFRESH_BUTTON = (By.XPATH, "//button[contains(text(), 'Refresh') or contains(@id, 'refresh')]")
    
    def __init__(self, driver, base_url, bot_id: str = ""):
        url = f"{base_url}/report"
        if bot_id:
            url += f"?bot={bot_id}"
        super().__init__(driver, url)
        
    def has_header(self) -> bool:
        """Check if report header is present."""
        return self.is_element_present(*self.HEADER)
        
    def has_bot_id(self) -> bool:
        """Check if bot ID is displayed."""
        return self.is_element_present(*self.BOT_ID_DISPLAY)
        
    def has_total_trades(self) -> bool:
        """Check if total trades card exists."""
        return self.is_element_present(*self.TOTAL_TRADES)
        
    def has_total_profit(self) -> bool:
        """Check if total profit card exists."""
        return self.is_element_present(*self.TOTAL_PROFIT)
        
    def has_win_rate(self) -> bool:
        """Check if win rate card exists."""
        return self.is_element_present(*self.WIN_RATE)
        
    def has_profit_chart(self) -> bool:
        """Check if profit chart exists."""
        return self.is_element_present(*self.PROFIT_CHART)
        
    def has_trades_chart(self) -> bool:
        """Check if trades chart exists."""
        return self.is_element_present(*self.TRADES_CHART)
        
    def has_trade_table(self) -> bool:
        """Check if trade table exists."""
        return self.is_element_present(*self.TRADE_TABLE)
        
    def count_trade_rows(self) -> int:
        """Count rows in trade table."""
        return len(self.find_elements(*self.TRADE_ROWS))
        
    def click_home(self) -> bool:
        """Click Home button."""
        button = self.find_element(*self.HOME_BUTTON)
        if button:
            return self.click_element(button)
        return False
