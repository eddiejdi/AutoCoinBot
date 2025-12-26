import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent0_scraper import validar_tela

TERMINAL_URL = "http://localhost:8501/terminal"  # ajuste conforme necessário
ELEMENTOS_TERMINAL = [
    ("tag", "h1"),
    ("tag", "h2"),
    ("tag", "h3"),
    ("class", "stAlert"),
    ("class", "stButton"),
    ("tag", "pre"),
    ("tag", "code"),
    ("xpath", "//div[contains(@class,'terminal') or contains(@class,'log') or @role='log']"),
]

def main():
    from agent0_scraper import validar_tela as validar_tela_login, ELEMENTOS_ESPERADOS
    import subprocess
    import time
    # Login
    validar_tela_login("http://localhost:8501/", ELEMENTOS_ESPERADOS, screenshot_path='login_screenshot.png')
    # Start bot dry-run
    bot_proc = subprocess.Popen([
        "python3", "-u", "bot_core.py",
        "--bot-id", "bot_scraper_terminal",
        "--symbol", "BTC-USDT",
        "--entry", "10000",
        "--mode", "mixed",
        "--targets", "2:0.3,5:0.4",
        "--interval", "5",
        "--size", "0.1",
        "--funds", "0",
        "--dry"
    ])
    time.sleep(8)  # Aguarda bot iniciar e tela atualizar
    # Adiciona busca pelo subheader/lista de bots ativos
    from selenium.webdriver.common.by import By
    ELEMENTOS_TERMINAL_EXT = []
    for by, sel in ELEMENTOS_TERMINAL:
        if by == "tag":
            ELEMENTOS_TERMINAL_EXT.append((By.TAG_NAME, sel))
        elif by == "class":
            ELEMENTOS_TERMINAL_EXT.append((By.CLASS_NAME, sel))
        elif by == "xpath":
            ELEMENTOS_TERMINAL_EXT.append((By.XPATH, sel))
        else:
            ELEMENTOS_TERMINAL_EXT.append((by, sel))
    # Adiciona busca pelo subheader/lista de bots ativos
    ELEMENTOS_TERMINAL_EXT.append((By.XPATH, "//*[contains(text(),'Bots Ativos') or contains(text(),'🤖 Bots Ativos')]") )
    resultados, screenshot = validar_tela(TERMINAL_URL, ELEMENTOS_TERMINAL_EXT, screenshot_path='terminal_screenshot.png')
    print("Resultados Terminal após start bot:", resultados)
    bot_proc.terminate()
    bot_proc.wait()

if __name__ == "__main__":
    main()
