"""Monitor Page Object - Real-time bot monitoring (HTML page)."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class MonitorPage(BasePage):
    """Real-time monitor page (monitor_window.html)."""
    
    # Headers
    HEADER = (By.XPATH, "//*[contains(text(), 'Monitor') or contains(text(), 'Log')]")
    BOT_ID_DISPLAY = (By.XPATH, "//*[contains(text(), 'Bot:') or contains(@id, 'bot')]")
    
    # Log display
    LOG_CONTAINER = (By.XPATH, "//*[@id='logs' or @id='log' or @id='log-container' or @class='terminal' or contains(@class, 'log') or contains(@class, 'content')]")
    LOG_ENTRIES = (By.XPATH, "//*[contains(@class, 'log-entry') or contains(@class, 'log-line') or contains(@class, 'line')]")
    
    # Status indicators
    STATUS_RUNNING = (By.XPATH, "//*[contains(text(), 'Running') or contains(text(), 'Rodando')]")
    STATUS_STOPPED = (By.XPATH, "//*[contains(text(), 'Stopped') or contains(text(), 'Parado')]")
    
    # Actions
    HOME_BUTTON = (By.XPATH, "//button[contains(text(), 'Home') or contains(@id, 'home')]")
    REFRESH_BUTTON = (By.XPATH, "//button[contains(text(), 'Refresh') or contains(@id, 'refresh')]")
    AUTO_SCROLL_TOGGLE = (By.XPATH, "//input[@type='checkbox' and contains(@id, 'auto-scroll')]")
    
    # Filters
    LEVEL_FILTER = (By.XPATH, "//select[contains(@id, 'level') or contains(@aria-label, 'Level')]")
    SEARCH_INPUT = (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Search')]")
    
    def __init__(self, driver, base_url, bot_id: str = ""):
        url = f"{base_url}/monitor"
        if bot_id:
            url += f"?bot={bot_id}"
        super().__init__(driver, url)
        
    def has_header(self) -> bool:
        """Check if monitor header is present."""
        return self.is_element_present(*self.HEADER)
        
    def has_bot_id(self) -> bool:
        """Check if bot ID is displayed."""
        return self.is_element_present(*self.BOT_ID_DISPLAY)
        
    def has_log_container(self) -> bool:
        """Check if log container exists."""
        return self.is_element_present(*self.LOG_CONTAINER)
        
    def count_log_entries(self) -> int:
        """Count log entries."""
        return len(self.find_elements(*self.LOG_ENTRIES))
        
    def get_log_texts(self) -> list:
        """Get all log entry texts."""
        return self.get_text_elements(*self.LOG_ENTRIES)
        
    def is_running(self) -> bool:
        """Check if status shows 'Running'."""
        return self.is_element_present(*self.STATUS_RUNNING)
        
    def is_stopped(self) -> bool:
        """Check if status shows 'Stopped'."""
        return self.is_element_present(*self.STATUS_STOPPED)
        
    def click_home(self) -> bool:
        """Click Home button."""
        button = self.find_element(*self.HOME_BUTTON)
        if button:
            return self.click_element(button)
        return False
        
    def click_refresh(self) -> bool:
        """Click Refresh button."""
        button = self.find_element(*self.REFRESH_BUTTON)
        if button:
            return self.click_element(button)
        return False
