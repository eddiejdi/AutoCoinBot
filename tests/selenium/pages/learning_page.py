"""Learning Page Object - Machine learning statistics and history."""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class LearningPage(BasePage):
    """Learning statistics and bandit algorithm page."""
    
    # Headers - Flexible selector to catch any heading
    HEADER = (By.XPATH, "//h1 | //h2 | //h3 | //*[@data-testid='stHeading']")
    STATS_SECTION = (By.XPATH, "//*[contains(text(), 'Statistics') or contains(text(), 'Estatísticas')]")
    HISTORY_SECTION = (By.XPATH, "//*[contains(text(), 'History') or contains(text(), 'Histórico')]")
    
    # Filters
    SYMBOL_FILTER = (By.XPATH, "//select[contains(@aria-label, 'Symbol') or contains(@aria-label, 'Símbolo')]")
    PARAM_FILTER = (By.XPATH, "//select[contains(@aria-label, 'Parameter') or contains(@aria-label, 'Parâmetro')]")
    
    # Data displays
    LEARNING_CARDS = (By.XPATH, "//*[contains(@class, 'element-container')]")
    PARAMETER_ROWS = (By.XPATH, "//tr[contains(@class, 'row')]")
    REWARD_VALUES = (By.XPATH, "//*[contains(text(), 'reward') or contains(text(), 'recompensa')]")
    
    # Charts
    CHARTS = (By.XPATH, "//*[contains(@class, 'chart') or contains(@class, 'plot')]")
    
    # Actions
    REFRESH_BUTTON = (By.XPATH, "//button[contains(text(), 'Refresh') or contains(text(), 'Atualizar')]")
    RESET_BUTTON = (By.XPATH, "//button[contains(text(), 'Reset') or contains(text(), 'Resetar')]")
    
    def __init__(self, driver, base_url):
        super().__init__(driver, f"{base_url}/?view=learning")
        
    def has_header(self) -> bool:
        """Check if learning header is present."""
        return self.is_element_present(*self.HEADER)
        
    def has_stats_section(self) -> bool:
        """Check if statistics section exists."""
        return self.is_element_present(*self.STATS_SECTION)
        
    def has_history_section(self) -> bool:
        """Check if history section exists."""
        return self.is_element_present(*self.HISTORY_SECTION)
        
    def count_learning_cards(self) -> int:
        """Count learning parameter cards."""
        return len(self.find_elements(*self.LEARNING_CARDS))
        
    def count_parameter_rows(self) -> int:
        """Count parameter rows in table."""
        return len(self.find_elements(*self.PARAMETER_ROWS))
        
    def count_charts(self) -> int:
        """Count displayed charts."""
        return len(self.find_elements(*self.CHARTS))
        
    def get_symbols(self) -> list:
        """Get list of available symbols."""
        elements = self.find_elements(By.XPATH, "//*[contains(text(), '-USDT')]")
        return list(set(el.text for el in elements if '-USDT' in el.text))
        
    def get_parameters(self) -> list:
        """Get list of learning parameters."""
        elements = self.find_elements(By.XPATH, "//*[contains(text(), '_pct') or contains(text(), '_size')]")
        return list(set(el.text for el in elements))
        
    def has_data(self) -> bool:
        """Check if learning data exists."""
        return (self.count_parameter_rows() > 0 or 
                self.count_learning_cards() > 0)
