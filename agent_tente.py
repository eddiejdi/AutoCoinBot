#!/usr/bin/env python3
"""
Agent Tente - Suporte automatizado via Selenium para AutoCoinBot
- Navega na interface web (http://localhost:8501)
- Tira screenshots
- Loga erros/exceções
- Ajuda a identificar problemas visuais e de fluxo
- Inicia bot, valida e verifica execução
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
import time
import os
import datetime

# Configurações
URL = "http://localhost:8501"
SCREENSHOT_DIR = "selenium_screenshots"
LOG_FILE = "selenium_agent.log"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{now}] {msg}\n")
    try:
        print(f"[LOG] {msg}")
    except (IOError, BrokenPipeError):
        pass  # Ignorar erros de pipe quebrado

def take_screenshot(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    log(f"Screenshot salva: {path}")

def main():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
    except WebDriverException as e:
        log(f"Erro ao iniciar ChromeDriver: {e}")
        return
    
    try:
        # 1. Acessar home
        log(f"Acessando {URL}")
        driver.get(URL)
        
        # Esperar página carregar completamente - verificar se Streamlit renderizou
        log("Aguardando página carregar completamente...")
        max_wait = 45  # Aumentado para 45s
        start_time = time.time()
        page_loaded = False
        
        while time.time() - start_time < max_wait:
            try:
                # Verificar se elemento raiz do Streamlit existe
                st_app = driver.find_elements(By.CLASS_NAME, "stApp")
                if st_app:
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    # Se não tem "Carregando" e tem conteúdo
                    if "Carregando" not in page_text and len(page_text) > 50:
                        page_loaded = True
                        log("✅ Página carregada!")
                        break
                time.sleep(2)
            except Exception as e:
                log(f"⏳ Aguardando... ({int(time.time() - start_time)}s)")
                time.sleep(2)
        
        if not page_loaded:
            log("⚠️ ERRO: Página não carregou no tempo esperado")
            take_screenshot(driver, "erro_timeout_carregamento")
            return
        
        time.sleep(3)
        take_screenshot(driver, "01_home_inicial")
        
        # Verificar estrutura da página (inputs, botões)
        log("Analisando estrutura da página...")
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        log(f"Encontrados {len(all_inputs)} inputs e {len(all_buttons)} botões")
        
        # Listar alguns inputs para debug
        for i, inp in enumerate(all_inputs[:5]):
            try:
                label = inp.get_attribute("aria-label") or inp.get_attribute("placeholder") or inp.get_attribute("id") or "sem label"
                log(f"  Input {i+1}: {label}")
            except:
                pass
        
        # Listar alguns botões para debug
        for i, btn in enumerate(all_buttons[:5]):
            try:
                btn_text = btn.text or btn.get_attribute("aria-label") or "sem texto"
                log(f"  Botão {i+1}: {btn_text}")
            except:
                pass
        
        # Verificar se precisa fazer login (várias formas de detectar)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        needs_login = False
        
        # Detectar página de login por múltiplos sinais
        if "Login" in page_text or "Usuário" in page_text or "Entrar" in page_text:
            needs_login = True
        elif len(all_inputs) <= 2 and any("password" in inp.get_attribute("type") or "" for inp in all_inputs):
            needs_login = True
        elif not ("Symbol" in page_text or "Dashboard" in page_text or "Entry" in page_text):
            needs_login = True
        
        if needs_login:
            log("🔐 Página de login detectada, fazendo login...")
            try:
                # Aguardar formulário carregar
                time.sleep(2)
                
                # Re-buscar inputs após espera
                login_inputs = driver.find_elements(By.TAG_NAME, "input")
                log(f"Inputs encontrados para login: {len(login_inputs)}")
                
                if len(login_inputs) >= 2:
                    # Primeiro input: usuário
                    user_input = login_inputs[0]
                    user_input.clear()
                    user_input.send_keys("admin")
                    log("✅ Usuário preenchido")
                    time.sleep(0.5)
                    
                    # Segundo input: senha
                    pass_input = login_inputs[1]
                    pass_input.clear()
                    pass_input.send_keys("senha123")
                    log("✅ Senha preenchida")
                    time.sleep(0.5)
                else:
                    log(f"❌ Esperava 2+ inputs, encontrou {len(login_inputs)}")
                    raise Exception("Inputs de login não encontrados")
                
                # Clicar em Entrar
                login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
                login_btn.click()
                log("✅ Login enviado!")
                time.sleep(5)
                
                # Aguardar dashboard carregar
                start_time = time.time()
                while time.time() - start_time < 20:
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    if "Symbol" in page_text or "Dashboard" in page_text:
                        log("✅ Dashboard carregado após login!")
                        break
                    time.sleep(2)
                
                take_screenshot(driver, "01b_apos_login")
                
                # Atualizar lista de inputs e botões
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                log(f"Após login: {len(all_inputs)} inputs e {len(all_buttons)} botões")
                
            except Exception as e:
                log(f"❌ Erro no login: {e}")
                take_screenshot(driver, "erro_login")
                return
        
        # 2. Procurar e preencher formulário de bot (abordagem mais genérica)
        log("Procurando campos de configuração do bot...")
        
        # Verificar se encontrou elementos do dashboard
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if "Symbol" not in page_text and "Entry" not in page_text:
            log("❌ Dashboard não carregou - campos esperados não encontrados")
            take_screenshot(driver, "erro_dashboard_nao_carregado")
            return
        
        try:
            # Filtrar apenas inputs interativos (Symbol, Entry, etc)
            interactive_inputs = []
            for inp in all_inputs:
                try:
                    label = inp.get_attribute("aria-label") or ""
                    placeholder = inp.get_attribute("placeholder") or ""
                    # Pular inputs de tema/seleção
                    if "tema" in label.lower() or "theme" in label.lower() or "selected" in label.lower():
                        continue
                    if inp.is_displayed() and inp.is_enabled():
                        interactive_inputs.append(inp)
                except:
                    pass
            
            log(f"ℹ️ Inputs interativos encontrados: {len(interactive_inputs)}")
            
            # Tentar preencher campos interativos usando JavaScript para mais confiabilidade
            if len(interactive_inputs) >= 1:
                try:
                    inp = interactive_inputs[0]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inp)
                    time.sleep(0.5)
                    # Usar JavaScript para definir valor (mais confiável que send_keys)
                    driver.execute_script("arguments[0].value = arguments[1];", inp, "BTC-USDT")
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", inp)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", inp)
                    log("✅ Campo 1 preenchido: BTC-USDT (Symbol)")
                    time.sleep(1)
                except Exception as e:
                    log(f"⚠️ Erro ao preencher campo 1: {e}")
            
            if len(interactive_inputs) >= 2:
                try:
                    inp = interactive_inputs[1]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inp)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].value = arguments[1];", inp, "50000")
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", inp)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", inp)
                    log("✅ Campo 2 preenchido: 50000 (Entry)")
                    time.sleep(1)
                except Exception as e:
                    log(f"⚠️ Erro ao preencher campo 2: {e}")
            
            if len(interactive_inputs) >= 3:
                try:
                    inp = interactive_inputs[2]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inp)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].value = arguments[1];", inp, "2:0.5")
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", inp)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", inp)
                    log("✅ Campo 3 preenchido: 2:0.5 (Targets)")
                    time.sleep(1)
                except Exception as e:
                    log(f"⚠️ Erro ao preencher campo 3: {e}")
            
            take_screenshot(driver, "02_formulario_preenchido")
        except Exception as e:
            log(f"Erro geral ao preencher formulário: {e}")
            take_screenshot(driver, "erro_preenchimento_geral")
        
        # Esperar Streamlit re-renderizar após preencher campos
        log("Aguardando Streamlit re-renderizar...")
        time.sleep(3)
        
        # RE-BUSCAR botões após formulário ser preenchido (evita stale element)
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        log(f"Botões após preencher formulário: {len(all_buttons)}")
        
        # 3. Procurar e clicar no botão START (buscar por texto ou posição)
        log("Procurando botão START...")
        start_btn = None
        
        # Tentar por texto
        for btn in all_buttons:
            btn_text = (btn.text or "").upper()
            if "START" in btn_text or "INICIAR" in btn_text:
                start_btn = btn
                log(f"✅ Botão START encontrado pelo texto: {btn.text}")
                break
        
        # Se não encontrou, pegar o último botão visível (geralmente é o botão principal)
        if not start_btn and all_buttons:
            start_btn = all_buttons[-1]
            log(f"⚠️ Botão START não encontrado por texto, usando último botão: {start_btn.text or 'sem texto'}")
        
        if start_btn:
            take_screenshot(driver, "03_antes_start")
            start_btn.click()
            log("✅ Botão clicado!")
            time.sleep(3)
            
            # 4. Validar página que abriu
            take_screenshot(driver, "04_apos_start")
            page_title = driver.title
            log(f"Página atual após click: {page_title}")
            
            # Verificar se há mensagem de sucesso ou confirmação
            try:
                success_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sucesso') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'iniciado') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'started') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'running')]")
                if success_elements:
                    log(f"✅ Mensagem de sucesso encontrada: {success_elements[0].text}")
                else:
                    log("⚠️ Nenhuma mensagem de sucesso explícita")
            except Exception as e:
                log(f"⚠️ Erro ao buscar mensagem de sucesso: {e}")
            
            time.sleep(2)
            
            # 5. Voltar para a home e recarregar completamente
            log("Voltando para a home...")
            driver.get(URL)
            time.sleep(8)  # Aguardar página recarregar e hidratar bots ativos
            take_screenshot(driver, "05_retorno_home")
            
            # 6. Validar que o bot está executando no frontend
            log("Verificando se o bot aparece como rodando...")
            
            # Primeiro: verificar se existe seção "Bots Ativos"
            page_text = driver.find_element(By.TAG_NAME, "body").text
            log(f"Texto da página (primeiros 500 chars): {page_text[:500]}")
            
            # Procurar por várias variações
            if "Bots Ativos" in page_text:
                log("✅ Encontrou texto 'Bots Ativos'")
            elif "🤖" in page_text:
                log("✅ Encontrou emoji 🤖")
            else:
                log("❌ NÃO encontrou 'Bots Ativos' nem emoji 🤖")
            
            # Buscar seção por diferentes métodos
            bots_section = driver.find_elements(By.XPATH, "//*[contains(text(), 'Bots Ativos')]")
            emoji_section = driver.find_elements(By.XPATH, "//*[contains(text(), '🤖')]")
            
            log(f"Seções encontradas: 'Bots Ativos'={len(bots_section)}, emoji={len(emoji_section)}")
            
            if bots_section or emoji_section or "Bots Ativos" in page_text or "🤖" in page_text:
                log("✅ Seção de bots ativos encontrada!")
                take_screenshot(driver, "06_secao_bots_encontrada")
                
                # Buscar por botões STOP ou LOG (indicam bot rodando)
                stop_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'STOP') or contains(text(), 'Stop')]")
                log_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'LOG') or contains(text(), 'Log')]")
                
                log(f"Botões encontrados: STOP={len(stop_buttons)}, LOG={len(log_buttons)}")
                
                if stop_buttons or log_buttons:
                    log(f"✅ Bot rodando confirmado! STOP buttons: {len(stop_buttons)}, LOG buttons: {len(log_buttons)}")
                    take_screenshot(driver, "07_bot_rodando_confirmado")
                else:
                    log("⚠️ Seção existe mas não há botões STOP/LOG")
                    log("Listando todos os botões visíveis:")
                    all_btns = driver.find_elements(By.TAG_NAME, "button")
                    for i, btn in enumerate(all_btns[:20]):
                        try:
                            txt = btn.text or btn.get_attribute("aria-label") or "sem texto"
                            log(f"  Botão {i+1}: {txt}")
                        except:
                            pass
                    take_screenshot(driver, "07_secao_sem_bots")
            else:
                log("❌ Seção 'Bots Ativos' NÃO encontrada - bot pode não estar rodando")
                take_screenshot(driver, "06_secao_nao_encontrada")
                
                # Debug: mostrar estrutura da página
                log("Debug: Procurando por qualquer referência a 'bot'...")
                bot_refs = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bot')]")
                log(f"Elementos com 'bot': {len(bot_refs)}")
                for i, elem in enumerate(bot_refs[:5]):
                    try:
                        log(f"  Elem {i+1}: {elem.text[:80]}")
                    except:
                        pass
            
            # Primeiro: verificar estrutura de bots ativos
                try:
                    # Buscar todos os botões visíveis novamente
                    current_buttons = driver.find_elements(By.TAG_NAME, "button")
                    log(f"ℹ️ Botões na home após retorno: {len(current_buttons)}")
                    
                    # Listar botões STOP e LOG (indicam bots rodando)
                    stop_buttons = [b for b in current_buttons if 'stop' in (b.text or '').lower()]
                    log_buttons = [b for b in current_buttons if 'log' in (b.text or '').lower()]
                    
                    if stop_buttons:
                        log(f"✅ Botões STOP encontrados: {len(stop_buttons)}")
                    if log_buttons:
                        log(f"✅ Botões LOG encontrados: {len(log_buttons)}")
                    
                    if stop_buttons or log_buttons:
                        take_screenshot(driver, "06_bots_ativos_confirmados")
                        log("✅ Bot(s) ativo(s) confirmado(s) pela presença de botões de controle!")
                    else:
                        log("⚠️ Nenhum botão STOP/LOG encontrado (pode não haver bots ativos)")
                        take_screenshot(driver, "06_sem_bots_ativos")
                    
                except Exception as e:
                    log(f"⚠️ Erro ao verificar botões de controle: {e}")
                
                # Segundo: buscar por nome do bot específico
                try:
                    bot_running = driver.find_element(By.XPATH, "//*[contains(text(), 'test_selenium_bot')]")
                    log(f"✅ Bot 'test_selenium_bot' encontrado no frontend: {bot_running.text}")
                    take_screenshot(driver, "07_bot_especifico_encontrado")
                except NoSuchElementException:
                    log("ℹ️ Bot 'test_selenium_bot' não encontrado pelo nome (pode ter ID diferente)")
                
                # Terceiro: procurar indicadores de status
                try:
                    status_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'running') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'active') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'executando') or contains(text(), 'Eternal')]")
                    if status_elements:
                        log(f"✅ Indicadores de status encontrados: {len(status_elements)}")
                        for i, elem in enumerate(status_elements[:3]):
                            log(f"  Status {i+1}: {elem.text[:50]}")
                        take_screenshot(driver, "08_status_indicators")
                except Exception as e:
                    log(f"⚠️ Erro ao buscar indicadores de status: {e}")
                
                log("✅ Fluxo completo executado!")
        else:
            log("❌ Nenhum botão encontrado para clicar")
            
    except Exception as e:
        log(f"❌ Erro no fluxo principal: {e}")
        take_screenshot(driver, "erro_fluxo_principal")
        
        # Verificar mensagens de erro gerais na tela
        try:
            error_msgs = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'erro') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'error') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'exception')]")
            if error_msgs:
                for i, el in enumerate(error_msgs[:3]):  # Limitar a 3 primeiros
                    log(f"⚠️ Erro visível: {el.text[:100]}")
                    take_screenshot(driver, f"erro_geral_{i}")
            else:
                log("✅ Nenhuma mensagem de erro visível detectada.")
        except Exception as e:
            log(f"Falha ao buscar mensagens de erro: {e}")
            
    except Exception as e:
        log(f"❌ Exceção geral: {e}")
        take_screenshot(driver, "exception")
    finally:
        driver.quit()
        log("Navegação Selenium finalizada.")

if __name__ == "__main__":
    main()
