"""Trades Page Object - Trade history and statistics."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class TradesPage(BasePage):
    """Trade history page."""
    
    # Headers - Flexible selector
    HEADER = (By.XPATH, "//h1 | //h2 | //h3 | //*[@data-testid='stHeading']")
    
    # Filters
    SYMBOL_FILTER = (By.XPATH, "//select[contains(@aria-label, 'Symbol')]")
    BOT_FILTER = (By.XPATH, "//select[contains(@aria-label, 'Bot')]")
    DATE_FROM = (By.XPATH, "//input[@type='date' and contains(@aria-label, 'From')]")
    DATE_TO = (By.XPATH, "//input[@type='date' and contains(@aria-label, 'To')]")
    
    # Toggle switches
    ONLY_REAL_TOGGLE = (By.XPATH, "//input[@type='checkbox' and contains(@aria-label, 'Real')]")
    GROUP_BY_BOT_TOGGLE = (By.XPATH, "//input[@type='checkbox' and contains(@aria-label, 'Group')]")
    
    # Table
    TRADE_ROWS = (By.XPATH, "//tr[contains(@class, 'row')]")
    BUY_ORDERS = (By.XPATH, "//*[contains(text(), 'BUY') or contains(text(), 'Compra')]")
    SELL_ORDERS = (By.XPATH, "//*[contains(text(), 'SELL') or contains(text(), 'Venda')]")
    
    # Profit displays
    POSITIVE_PROFIT = (By.XPATH, "//*[contains(@style, 'green') or contains(text(), '+')]")
    NEGATIVE_PROFIT = (By.XPATH, "//*[contains(@style, 'red') or contains(text(), '-')]")
    
    # Summary
    TOTAL_TRADES = (By.XPATH, "//*[contains(text(), 'Total') and contains(text(), 'trades')]")
    TOTAL_PROFIT = (By.XPATH, "//*[contains(text(), 'Profit') or contains(text(), 'Lucro')]")
    WIN_RATE = (By.XPATH, "//*[contains(text(), 'Win Rate') or contains(text(), 'Taxa')]")
    
    # Charts
    PROFIT_CHART = (By.XPATH, "//*[contains(@class, 'chart')]")
    
    # Actions
    EXPORT_BUTTON = (By.XPATH, "//button[contains(text(), 'Export') or contains(text(), 'Exportar')]")
    REFRESH_BUTTON = (By.XPATH, "//button[contains(text(), 'Refresh') or contains(text(), 'Atualizar')]")
    
    def __init__(self, driver, base_url):
        super().__init__(driver, f"{base_url}/?view=trades")
        
    def has_header(self) -> bool:
        """Check if trades header is present."""
        return self.is_element_present(*self.HEADER)
        
    def count_trade_rows(self) -> int:
        """Count trade rows in table."""
        return len(self.find_elements(*self.TRADE_ROWS))
        
    def count_buy_orders(self) -> int:
        """Count BUY orders."""
        return len(self.find_elements(*self.BUY_ORDERS))
        
    def count_sell_orders(self) -> int:
        """Count SELL orders."""
        return len(self.find_elements(*self.SELL_ORDERS))
        
    def count_positive_profits(self) -> int:
        """Count trades with positive profit."""
        return len(self.find_elements(*self.POSITIVE_PROFIT))
        
    def count_negative_profits(self) -> int:
        """Count trades with negative profit."""
        return len(self.find_elements(*self.NEGATIVE_PROFIT))
        
    def has_summary(self) -> bool:
        """Check if summary section exists."""
        return (self.is_element_present(*self.TOTAL_TRADES) or
                self.is_element_present(*self.TOTAL_PROFIT))
        
    def has_chart(self) -> bool:
        """Check if profit chart exists."""
        return self.is_element_present(*self.PROFIT_CHART)
        
    def toggle_only_real(self, enabled: bool = True):
        """Toggle 'Only Real' filter."""
        checkbox = self.find_element(*self.ONLY_REAL_TOGGLE)
        if checkbox and checkbox.is_selected() != enabled:
            self.click_element(checkbox)
            
    def toggle_group_by_bot(self, enabled: bool = True):
        """Toggle 'Group by Bot' filter."""
        checkbox = self.find_element(*self.GROUP_BY_BOT_TOGGLE)
        if checkbox and checkbox.is_selected() != enabled:
            self.click_element(checkbox)
            
    def has_data(self) -> bool:
        """Check if trade data exists."""
        return self.count_trade_rows() > 0
