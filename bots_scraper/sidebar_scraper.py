import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent0_scraper import validar_tela

SIDEBAR_URL = "http://localhost:8501/"  # geralmente a sidebar está em todas as telas
ELEMENTOS_SIDEBAR = [
    ("class", "stSidebar"),
    ("tag", "aside"),
    ("tag", "nav"),
    ("tag", "ul"),
    ("tag", "li"),
    ("xpath", "//div[contains(@class,'sidebar') or @role='navigation']"),
]

def main():
    from agent0_scraper import validar_tela as validar_tela_login, ELEMENTOS_ESPERADOS
    validar_tela_login("http://localhost:8501/", ELEMENTOS_ESPERADOS, screenshot_path='login_screenshot.png')
    resultados, screenshot = validar_tela(SIDEBAR_URL, [
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').TAG_NAME, sel) if by == "tag" else
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').CLASS_NAME, sel) if by == "class" else
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').XPATH, sel)
        for by, sel in ELEMENTOS_SIDEBAR
    ], screenshot_path='sidebar_screenshot.png')
    print("Resultados Sidebar:", resultados)

if __name__ == "__main__":
    main()
