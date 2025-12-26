import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent0_scraper import validar_tela

DASHBOARD_URL = "http://localhost:8501/dashboard"  # ajuste conforme necessário
ELEMENTOS_DASHBOARD = [
    ("tag", "h1"),
    ("tag", "h2"),
    ("tag", "h3"),
    ("class", "stDataFrame"),
    ("tag", "table"),
    ("xpath", "//div[@role='table']"),
    ("class", "stAlert"),
    ("class", "stSidebar"),
    ("tag", "aside"),
    ("tag", "nav"),
]

def main():
    # Primeiro faz login na tela inicial
    from agent0_scraper import validar_tela as validar_tela_login, ELEMENTOS_ESPERADOS
    validar_tela_login("http://localhost:8501/", ELEMENTOS_ESPERADOS, screenshot_path='login_screenshot.png')
    # Depois navega para a tela desejada
    resultados, screenshot = validar_tela(DASHBOARD_URL, [
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').TAG_NAME, sel) if by == "tag" else
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').CLASS_NAME, sel) if by == "class" else
        (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').XPATH, sel)
        for by, sel in ELEMENTOS_DASHBOARD
    ], screenshot_path='dashboard_screenshot.png')
    print("Resultados Dashboard:", resultados)

if __name__ == "__main__":
    main()
