"""Dashboard Page Object - Main dashboard with active bots."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class DashboardPage(BasePage):
    """Dashboard page with active bots list."""
    
    # Locators
    HEADER = (By.XPATH, "//h1 | //h2 | //h3 | //*[@data-testid='stHeading'] | //*[contains(text(), 'Bots')]")
    NO_BOTS_MSG = (By.XPATH, "//*[contains(text(), 'Nenhum bot') or contains(text(), 'nenhum bot')] | //*[contains(text(), 'no active')]")
    
    # Bot list elements
    LOG_LINKS = (By.XPATH, "//a[contains(text(), 'Log') or contains(text(), 'LOG')]")
    REPORT_LINKS = (By.XPATH, "//a[contains(text(), 'REL') or contains(text(), 'Rel')]")
    KILL_BUTTONS = (By.XPATH, "//button[contains(text(), 'Kill') or contains(text(), 'Stop')]")
    CHECKBOXES = (By.XPATH, "//input[@type='checkbox']")
    
    # Bot details
    ULTIMO_EVENTO_COLUMN = (By.XPATH, "//*[contains(text(), 'Último Evento') or contains(text(), 'ÚLTIMO EVENTO')]")
    PROGRESS_BARS = (By.XPATH, "//*[contains(@class, 'stProgress')]")
    PROFIT_DISPLAYS = (By.XPATH, "//*[contains(text(), '%') or contains(text(), 'USDT')]")
    
    # Actions
    START_BOT_BUTTON = (By.XPATH, "//button[contains(text(), 'Start Bot') or contains(text(), 'Iniciar Bot')]")
    BULK_KILL_BUTTON = (By.XPATH, "//button[contains(text(), 'Kill Selecionados')]")
    
    def __init__(self, driver, base_url):
        super().__init__(driver, f"{base_url}/?view=dashboard")
        
    def has_header(self) -> bool:
        """Check if dashboard header is present."""
        return self.is_element_present(*self.HEADER)
        
    def has_no_bots_message(self) -> bool:
        """Check if 'no bots' message is shown."""
        return self.is_element_present(*self.NO_BOTS_MSG)
        
    def count_log_links(self) -> int:
        """Count LOG button links."""
        return len(self.find_elements(*self.LOG_LINKS))
        
    def count_report_links(self) -> int:
        """Count RELATÓRIO button links."""
        return len(self.find_elements(*self.REPORT_LINKS))
        
    def count_kill_buttons(self) -> int:
        """Count Kill/Stop buttons."""
        return len(self.find_elements(*self.KILL_BUTTONS))
        
    def count_checkboxes(self) -> int:
        """Count selection checkboxes."""
        return len(self.find_elements(*self.CHECKBOXES))
        
    def has_ultimo_evento_column(self) -> bool:
        """Check if 'Último Evento' column exists."""
        return self.is_element_present(*self.ULTIMO_EVENTO_COLUMN)
        
    def count_progress_bars(self) -> int:
        """Count progress bars."""
        return len(self.find_elements(*self.PROGRESS_BARS))
        
    def count_profit_displays(self) -> int:
        """Count profit displays."""
        return len(self.find_elements(*self.PROFIT_DISPLAYS))
        
    def get_log_urls(self) -> list:
        """Extract all LOG button URLs."""
        links = self.find_elements(*self.LOG_LINKS)
        return [link.get_attribute('href') for link in links]
        
    def get_report_urls(self) -> list:
        """Extract all RELATÓRIO button URLs."""
        links = self.find_elements(*self.REPORT_LINKS)
        return [link.get_attribute('href') for link in links]
        
    def click_first_log_link(self) -> bool:
        """Click first LOG link."""
        links = self.find_elements(*self.LOG_LINKS)
        if links:
            return self.click_element(links[0])
        return False
        
    def click_first_report_link(self) -> bool:
        """Click first RELATÓRIO link."""
        links = self.find_elements(*self.REPORT_LINKS)
        if links:
            return self.click_element(links[0])
        return False
        
    def get_bot_ids(self) -> list:
        """Extract bot IDs from the dashboard."""
        # Look for bot_id patterns in text
        elements = self.find_elements(By.XPATH, "//*[contains(text(), 'bot_')]")
        return [el.text for el in elements]
        
    def get_bot_symbols(self) -> list:
        """Extract trading symbols (BTC-USDT, ETH-USDT, etc.)."""
        elements = self.find_elements(By.XPATH, "//*[contains(text(), '-USDT')]")
        return [el.text for el in elements]
