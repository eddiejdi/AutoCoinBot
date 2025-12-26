import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent0_scraper import validar_tela

TRADES_URL = "http://localhost:8501/trades"  # ajuste conforme necessário
ELEMENTOS_TRADES = [
    ("tag", "h1"),
    ("tag", "h2"),
    ("tag", "h3"),
    ("class", "stDataFrame"),
    ("tag", "table"),
    ("xpath", "//div[@role='table']"),
    ("class", "stAlert"),
    ("class", "stButton"),
    ("xpath", "//button|//input[@type='button']|//input[@type='submit']"),
]

def main():
    from agent0_scraper import validar_tela as validar_tela_login, ELEMENTOS_ESPERADOS
    validar_tela_login("http://localhost:8501/", ELEMENTOS_ESPERADOS, screenshot_path='login_screenshot.png')
    resultados, screenshot = validar_tela(TRADES_URL, [
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').TAG_NAME, sel) if by == "tag" else
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').CLASS_NAME, sel) if by == "class" else
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').XPATH, sel)
        for by, sel in ELEMENTOS_TRADES
    ], screenshot_path='trades_screenshot.png')
    print("Resultados Trades:", resultados)

if __name__ == "__main__":
    main()
