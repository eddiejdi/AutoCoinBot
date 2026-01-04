"""Base Page Object - Common functionality for all pages."""
import time
from typing import Optional, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    """Base class for all page objects."""
    
    def __init__(self, driver: WebDriver, url: str):
        self.driver = driver
        self.url = url
        self.wait = WebDriverWait(driver, 10)
        
    def navigate(self):
        """Navigate to the page URL."""
        self.driver.get(self.url)
        time.sleep(2)  # Wait for initial render
        
    def find_element(self, by: By, value: str) -> Optional[WebElement]:
        """Find a single element, return None if not found."""
        try:
            return self.driver.find_element(by, value)
        except:
            return None
            
    def find_elements(self, by: By, value: str) -> List[WebElement]:
        """Find multiple elements, return empty list if not found."""
        try:
            return self.driver.find_elements(by, value)
        except:
            return []
            
    def wait_for_element(self, by: By, value: str, timeout: int = 10) -> Optional[WebElement]:
        """Wait for element to be present."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except:
            return None
            
    def wait_for_clickable(self, by: By, value: str, timeout: int = 10) -> Optional[WebElement]:
        """Wait for element to be clickable."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except:
            return None
            
    def click_element(self, element: WebElement) -> bool:
        """Click an element safely."""
        try:
            element.click()
            time.sleep(1)
            return True
        except:
            return False
            
    def get_text_elements(self, by: By, value: str) -> List[str]:
        """Get text from all matching elements."""
        elements = self.find_elements(by, value)
        return [el.text for el in elements if el.text]
        
    def is_element_present(self, by: By, value: str) -> bool:
        """Check if element is present."""
        return self.find_element(by, value) is not None
        
    def take_screenshot(self, filename: str):
        """Save screenshot."""
        self.driver.save_screenshot(filename)
        
    def get_page_source(self) -> str:
        """Get current page HTML."""
        return self.driver.page_source
        
    def execute_script(self, script: str):
        """Execute JavaScript."""
        return self.driver.execute_script(script)
        
    def get_dom_html(self) -> str:
        """Get client-side DOM via JavaScript."""
        try:
            return self.driver.execute_script('return document.documentElement.outerHTML')
        except:
            return ""
