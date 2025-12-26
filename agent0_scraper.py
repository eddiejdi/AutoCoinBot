import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import argparse
# Configurações
LOCAL_URL = "http://localhost:8501"
REMOTE_URL = "https://autocoinbot-hom.streamlit.app/"
APP_URL = LOCAL_URL  # Padrão: localhost
ELEMENTOS_ESPERADOS = [
    # Prefer any common header tag (h1/h2/h3) — Streamlit may render as h2
    (By.TAG_NAME, 'h1'),
    (By.TAG_NAME, 'h2'),
    (By.TAG_NAME, 'h3'),
    (By.CLASS_NAME, 'stButton'),  # Botões Streamlit
    # Dataframes: Streamlit often renders them as a container or plain <table>
    (By.CLASS_NAME, 'stDataFrame'), # Tabelas (preferred)
    (By.TAG_NAME, 'table'),         # Fallback to any table element
    (By.CLASS_NAME, 'stAlert'),   # Mensagens de alerta
    # Sidebar can be rendered as an <aside> in some Streamlit versions
    (By.CLASS_NAME, 'stSidebar'), # Sidebar
    (By.TAG_NAME, 'aside'),
]


def validar_tela(url, elementos_esperados, screenshot_path='screenshot.png'):
    options = Options()
    # options.add_argument('--headless')  # Removido para abrir navegador visível
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--incognito')  # Abre janela anônima
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    driver.get(url)
    time.sleep(5)  # Aguarda renderização

    # Tenta login automático dentro do iframe (ou no documento principal)
    login_preenchido = False
    login_error = None
    login_html = None

    def _try_fill_and_submit(context_driver) -> bool:
        """Tenta múltiplos seletores para user/password e clica no botão de submit.
        Usa WebDriverWait para aguardar elementos quando necessário."""
        wait = WebDriverWait(context_driver, 4)
        user_selectors = [
            "//input[@type='text']",
            "//input[@type='text' and (@name or @id or @placeholder)]",
            "//input[@autocomplete='username']",
            "//input[contains(translate(@name,'USER','user'),'user')]",
            "//input[contains(translate(@id,'USER','user'),'user')]",
            "//input[@type='email']",
            "//input[@id='text_input_1']",
            "//input[@name='username']",
            "//input[@aria-label='Usuário']",
        ]
        pass_selectors = [
            "//input[@type='password']",
            "//input[contains(translate(@name,'PASS','pass'),'pass')]",
            "//input[contains(translate(@id,'PASS','pass'),'pass')]",
            "//input[@id='text_input_2']",
            "//input[@aria-label='Senha']",
        ]

        # Encontrar usuário e senha (com espera)
        usuario_input = None
        senha_input = None
        for sel in user_selectors:
            try:
                usuario_input = wait.until(EC.presence_of_element_located((By.XPATH, sel)))
                if usuario_input:
                    break
            except Exception:
                usuario_input = None
                continue

        for sel in pass_selectors:
            try:
                senha_input = wait.until(EC.presence_of_element_located((By.XPATH, sel)))
                if senha_input:
                    break
            except Exception:
                senha_input = None
                continue

        if usuario_input is None or senha_input is None:
            return False

        try:
            usuario_input.clear()
            usuario_input.send_keys('admin')
        except Exception:
            pass
        try:
            senha_input.clear()
            senha_input.send_keys('senha123')
        except Exception:
            pass

        # Tentar clicar em possíveis botões de submit
        try_buttons = [
            "//button[contains(., 'Entrar') or contains(., 'Login') or contains(., 'Sign in') or contains(., 'Submit') ]",
            "//input[@type='submit']",
            "//button",
            "//div[@data-testid='stFormSubmitButton']//button",
        ]
        for tb in try_buttons:
            try:
                elems = context_driver.find_elements(By.XPATH, tb)
                for btn in elems:
                    try:
                        text = btn.text or btn.get_attribute('value') or ''
                    except Exception:
                        text = ''
                    if any(k in text for k in ['Entrar', 'Login', 'Sign', 'Submit']) or tb != "//button":
                        try:
                            try:
                                wait.until(EC.element_to_be_clickable((By.XPATH, tb)))
                            except Exception:
                                pass
                            btn.click()
                            return True
                        except Exception:
                            continue
            except Exception:
                continue
        return False

    # Primeiro tente dentro de um iframe (se houver)
    try:
        iframe = None
        try:
            iframe = driver.find_element(By.TAG_NAME, "iframe")
        except Exception:
            iframe = None

        if iframe:
            try:
                driver.switch_to.frame(iframe)
                time.sleep(1)
                if _try_fill_and_submit(driver):
                    login_preenchido = True
                driver.switch_to.default_content()
            except Exception as e:
                login_error = str(e)
                try:
                    login_html = driver.page_source
                except Exception:
                    login_html = None
        else:
            # Tentar no contexto principal
            try:
                if _try_fill_and_submit(driver):
                    login_preenchido = True
            except Exception as e:
                login_error = str(e)
                try:
                    login_html = driver.page_source
                except Exception:
                    login_html = None

        # Aguarda pós-login se tentou
        if login_preenchido:
            time.sleep(5)
    except Exception as e:
        login_error = str(e)
        try:
            login_html = driver.page_source
        except Exception:
            login_html = None


    driver.save_screenshot(screenshot_path)
    resultados = {}
    for by, seletor in elementos_esperados:
        try:
            elementos = driver.find_elements(by, seletor)
            resultados[seletor] = len(elementos) > 0
        except NoSuchElementException:
            resultados[seletor] = False
    driver.quit()
    # Adiciona ao relatório se login foi tentado e detalhes de erro
    resultados['login_preenchido'] = login_preenchido
    # Normalize/aggregate certain checks for robustness
    try:
        header_found = any(resultados.get(t, False) for t in ('h1', 'h2', 'h3'))
        resultados['h1'] = header_found
    except Exception:
        pass
    try:
        df_found = resultados.get('stDataFrame') or resultados.get('table')
        resultados['stDataFrame'] = bool(df_found)
    except Exception:
        pass
    try:
        sidebar_found = resultados.get('stSidebar') or resultados.get('aside')
        resultados['stSidebar'] = bool(sidebar_found)
    except Exception:
        pass
    if login_error:
        with open('login_error.txt', 'w') as f:
            f.write(f"Erro: {login_error}\n\n")
            if login_html:
                f.write("HTML da página:\n")
                f.write(login_html)
    return resultados, screenshot_path


def gerar_relatorio(resultados, screenshot_path, url):
    rel = f"# Validação visual do app: {url}\n\n"
    rel += f"![Screenshot]({screenshot_path})\n\n"
    for seletor, ok in resultados.items():
        rel += f"- Elemento '{seletor}': {'OK' if ok else 'NÃO ENCONTRADO'}\n"
    return rel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Valida tela do KuCoin Bot")
    parser.add_argument('--remote', action='store_true', help='Valida endpoint remoto')
    parser.add_argument('--local', action='store_true', help='Valida endpoint local')
    parser.add_argument('--retries', type=int, default=3, help='Número de tentativas automáticas')
    parser.add_argument('--wait', type=int, default=3, help='Segundos entre tentativas')
    args = parser.parse_args()

    if args.remote:
        url = REMOTE_URL
    else:
        url = LOCAL_URL

    expected_selectors = [s for (_, s) in ELEMENTOS_ESPERADOS]

    final_results = None
    for attempt in range(1, args.retries + 1):
        print(f"[attempt {attempt}/{args.retries}] Validando {url} ...")
        resultados, screenshot = validar_tela(url, ELEMENTOS_ESPERADOS)
        relatorio = gerar_relatorio(resultados, screenshot, url)
        fname = f"relatorio_validacao_attempt_{attempt}.md"
        with open(fname, "w") as f:
            f.write(relatorio)
        print(f"Relatório salvo: {fname}")

        # Decide se passou: todos os expected selectors True
        passed = True
        for sel in expected_selectors:
            if not resultados.get(sel, False):
                passed = False
                break

        if passed:
            print(f"Sucesso na tentativa {attempt}. Saindo.")
            final_results = (resultados, screenshot)
            break
        else:
            print(f"Falha na tentativa {attempt}. Retrying in {args.wait}s...")
            time.sleep(args.wait)

    if final_results is None:
        # write final aggregated report
        with open("relatorio_validacao.md", "w") as f:
            f.write(relatorio)
        print("Validação finalizada com falhas. Veja relatorios de tentativa.")
    else:
        resultados, screenshot = final_results
        with open("relatorio_validacao.md", "w") as f:
            f.write(gerar_relatorio(resultados, screenshot, url))
        print("Validação concluída com sucesso. Veja relatorio_validacao.md e screenshot.png.")
