import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Configurações
APP_URL = "https://autocoinbot-hom.streamlit.app/"
ELEMENTOS_ESPERADOS = [
    (By.TAG_NAME, 'h1'),           # Título principal
    (By.CLASS_NAME, 'stButton'),  # Botões Streamlit
    (By.CLASS_NAME, 'stDataFrame'), # Tabelas
    (By.CLASS_NAME, 'stAlert'),   # Mensagens de alerta
    (By.CLASS_NAME, 'stSidebar'), # Sidebar
]


def validar_tela(url, elementos_esperados, screenshot_path='screenshot.png'):
    options = Options()
    # options.add_argument('--headless')  # Removido para abrir navegador visível
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    driver.get(url)
    time.sleep(5)  # Aguarda renderização

    # Tenta login automático se detectar tela de login customizada do app
    try:
        usuario_input = driver.find_element(By.XPATH, "//input[@type='text' or @autocomplete='username']")
        senha_input = driver.find_element(By.XPATH, "//input[@type='password']")
        usuario_input.clear()
        usuario_input.send_keys('admin')
        senha_input.clear()
        senha_input.send_keys('senha123')
        # Procura botão de submit
        btns = driver.find_elements(By.TAG_NAME, 'button')
        for btn in btns:
            if 'Entrar' in btn.text or 'Login' in btn.text:
                btn.click()
                break
        time.sleep(5)  # Aguarda pós-login
    except Exception as e:
        pass  # Não está na tela de login customizada

    driver.save_screenshot(screenshot_path)
    resultados = {}
    for by, seletor in elementos_esperados:
        try:
            elementos = driver.find_elements(by, seletor)
            resultados[seletor] = len(elementos) > 0
        except NoSuchElementException:
            resultados[seletor] = False
    driver.quit()
    return resultados, screenshot_path


def gerar_relatorio(resultados, screenshot_path, url):
    rel = f"# Validação visual do app: {url}\n\n"
    rel += f"![Screenshot]({screenshot_path})\n\n"
    for seletor, ok in resultados.items():
        rel += f"- Elemento '{seletor}': {'OK' if ok else 'NÃO ENCONTRADO'}\n"
    return rel


if __name__ == "__main__":
    resultados, screenshot = validar_tela(APP_URL, ELEMENTOS_ESPERADOS)
    relatorio = gerar_relatorio(resultados, screenshot, APP_URL)
    with open("relatorio_validacao.md", "w") as f:
        f.write(relatorio)
    print("Validação concluída. Veja relatorio_validacao.md e screenshot.png.")
