"""Trading Page Object - Bot start/configuration form."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class TradingPage(BasePage):
    """Trading configuration page for starting new bots."""
    
    # Form inputs - Using aria-label for robustness (IDs can shift)
    BOT_ID_INPUT = (By.XPATH, "//div[contains(@class, 'st-key-bot_id') or contains(@class, 'st-key-bot-id')]//input[@type='text'] | //div[contains(@class, 'st-key-bot_id')]//input | //input[@aria-label='Bot ID']")
    SYMBOL_INPUT = (By.XPATH, "//div[contains(@class, 'st-key-symbol')]//input[@type='text']")  
    ENTRY_PRICE_INPUT = (By.XPATH, "//div[contains(@class, 'st-key-entry')]//input[@type='number']")
    MODE_SELECT = (By.XPATH, "//div[contains(@class, 'st-key-mode')]//input[@role='combobox']")
    TARGETS_INPUT = (By.XPATH, "//div[contains(@class, 'st-key-targets')]//input[@type='text']")
    INTERVAL_INPUT = (By.XPATH, "//div[contains(@class, 'st-key-interval')]//input[@type='number']")
    SIZE_INPUT = (By.XPATH, "//div[contains(@class, 'st-key-size')]//input[@type='number']")
    FUNDS_INPUT = (By.XPATH, "//div[contains(@class, 'st-key-funds')]//input[@type='number']")
    TARGET_INPUTS = (By.XPATH, "//input[@aria-label*='Target']")
    
    # Advanced settings
    RESERVE_PCT_INPUT = (By.XPATH, "//input[@aria-label*='Reserve']")
    TARGET_PROFIT_INPUT = (By.XPATH, "//input[@aria-label*='Profit']")
    
    # Mode toggles (checkboxes) - Using st-key- selectors
    DRY_RUN_CHECKBOX = (By.XPATH, "//div[contains(@class, 'st-key-eternal_mode')]//input[@type='checkbox']")
    ETERNAL_MODE_CHECKBOX = (By.XPATH, "//div[contains(@class, 'st-key-eternal_mode')]//input[@type='checkbox']")
    
    # Targets section  
    TARGETS_SECTION = (By.XPATH, "//div[contains(@class, 'st-key-targets')]")
    ADD_TARGET_BUTTON = (By.XPATH, "//button[contains(text(), 'Add') or contains(text(), 'Adicionar')]")
    
    # Actions - Using st-key- selectors for buttons
    START_BUTTON = (By.XPATH, "//div[contains(@class, 'st-key-start_dry')]//button")
    CLEAR_BUTTON = (By.XPATH, "//button[contains(text(), 'Clear') or contains(text(), 'Limpar')]")
    
    # Validation messages
    SUCCESS_MSG = (By.XPATH, "//*[contains(@class, 'success') or contains(text(), 'sucesso') or contains(@class, 'positive')]")
    ERROR_MSG = (By.XPATH, "//*[contains(@class, 'error') or contains(text(), 'erro') or contains(@class, 'negative')]")
    
    def __init__(self, driver, base_url):
        super().__init__(driver, f"{base_url}/?view=trading")
        
    def fill_bot_id(self, bot_id: str):
        """Fill bot ID field."""
        elem = self.find_element(*self.BOT_ID_INPUT)
        if elem:
            elem.clear()
            elem.send_keys(bot_id)
            
    def fill_symbol(self, symbol: str):
        """Fill trading symbol."""
        elem = self.find_element(*self.SYMBOL_INPUT)
        if elem:
            elem.clear()
            elem.send_keys(symbol)
            
    def fill_entry_price(self, price: float):
        """Fill entry price."""
        elem = self.find_element(*self.ENTRY_PRICE_INPUT)
        if elem:
            elem.clear()
            elem.send_keys(str(price))
            
    def fill_size(self, size: float):
        """Fill position size."""
        elem = self.find_element(*self.SIZE_INPUT)
        if elem:
            elem.clear()
            elem.send_keys(str(size))
            
    def toggle_dry_run(self, enabled: bool = True):
        """Toggle dry run mode."""
        checkbox = self.find_element(*self.DRY_RUN_CHECKBOX)
        if checkbox and checkbox.is_selected() != enabled:
            self.click_element(checkbox)
            
    def toggle_eternal_mode(self, enabled: bool = True):
        """Toggle eternal mode."""
        checkbox = self.find_element(*self.ETERNAL_MODE_CHECKBOX)
        if checkbox and checkbox.is_selected() != enabled:
            self.click_element(checkbox)
            
    def click_start(self) -> bool:
        """Click Start Bot button."""
        button = self.wait_for_clickable(*self.START_BUTTON)
        if button:
            return self.click_element(button)
        return False
        
    def has_success_message(self) -> bool:
        """Check if success message is displayed."""
        return self.is_element_present(*self.SUCCESS_MSG)
        
    def has_error_message(self) -> bool:
        """Check if error message is displayed."""
        return self.is_element_present(*self.ERROR_MSG)
        
    def count_target_inputs(self) -> int:
        """Count target input fields."""
        return len(self.find_elements(*self.TARGET_INPUTS))
        
    def add_target(self) -> bool:
        """Click Add Target button."""
        button = self.find_element(*self.ADD_TARGET_BUTTON)
        if button:
            return self.click_element(button)
        return False
