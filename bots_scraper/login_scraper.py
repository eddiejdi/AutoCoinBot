import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent0_scraper import validar_tela

LOGIN_URL = "http://localhost:8501/"  # ajuste se necessário
ELEMENTOS_LOGIN = [
    ("xpath", "//input[@type='text' or @type='email' or contains(@placeholder,'usu') or contains(@aria-label,'Usu')]"),
    ("xpath", "//input[@type='password' or contains(@placeholder,'sen') or contains(@aria-label,'Senha') or contains(@id,'pass') or contains(@name,'pass') ]"),
    ("xpath", "//button[contains(translate(.,'LOGIN','login'),'login') or contains(translate(.,'ENTRAR','entrar'),'entrar') or contains(.,'Sign in') or contains(.,'Submit') or contains(.,'Acessar')]")
]

def main():
    resultados, screenshot = validar_tela(LOGIN_URL, [
        (by, sel) if by != "xpath" else (getattr(__import__('selenium.webdriver.common.by', fromlist=['By']), 'By').XPATH, sel)
        for by, sel in ELEMENTOS_LOGIN
    ], screenshot_path='login_screenshot.png')
    print("Resultados Login:", resultados)

if __name__ == "__main__":
    main()
