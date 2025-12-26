import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent0_scraper import validar_tela

REPORTS_URL = "http://localhost:8501/reports"  # ajuste conforme necessário
ELEMENTOS_REPORTS = [
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
    resultados, screenshot = validar_tela(REPORTS_URL, [
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').TAG_NAME, sel) if by == "tag" else
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').CLASS_NAME, sel) if by == "class" else
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').XPATH, sel)
        for by, sel in ELEMENTOS_REPORTS
    ], screenshot_path='reports_screenshot.png')
    print("Resultados Reports:", resultados)

if __name__ == "__main__":
    main()
