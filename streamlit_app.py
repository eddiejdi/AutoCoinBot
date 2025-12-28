


# Captura erros críticos de import/configuração e salva em log
try:
    import streamlit as st
    import os
    import sys
    import traceback
    import hashlib
    import logging
except Exception as exc:
    with open("fatal_error.log", "w") as f:
        import traceback as tb
        f.write("Erro fatal no import do streamlit_app.py:\n")
        f.write("".join(tb.format_exception(type(exc), exc, exc.__traceback__)))
    raise

# Variáveis globais e utilitários
USUARIO_PADRAO = os.getenv("KUCOIN_USER", "admin")
SENHA_HASH_PADRAO = hashlib.sha256(os.getenv("KUCOIN_PASS", "senha123").encode()).hexdigest()
LOGIN_FILE = os.path.join(os.path.dirname(__file__), '.login_status')

def verificar_credenciais(usuario, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    return usuario == USUARIO_PADRAO and senha_hash == SENHA_HASH_PADRAO

def set_logged_in(status):
    if status:
        with open(LOGIN_FILE, 'w') as f:
            f.write('logged_in')
    else:
        if os.path.exists(LOGIN_FILE):
            os.remove(LOGIN_FILE)

def is_logged_in():
    try:
        return os.path.exists(LOGIN_FILE) and open(LOGIN_FILE).read().strip() == 'logged_in'
    except:
        return False

st.set_page_config(page_title="KuCoin PRO", layout="wide")

def _ensure_app_structure():
    """Create required folders and silence noisy streamlit warnings during tests."""
    try:
        # Create common runtime folders
        base = os.path.dirname(__file__)
        for d in ("logs", "pids"):
            try:
                os.makedirs(os.path.join(base, d), exist_ok=True)
            except Exception:
                pass
    except Exception:
        pass
    # Reduce Streamlit/related logger verbosity when running under tests
    try:
        logging.getLogger("streamlit").setLevel(logging.ERROR)
    except Exception:
        pass
    try:
        logging.getLogger("blinker").setLevel(logging.ERROR)
    except Exception:
        pass

# Ensure folders and logging config early
_ensure_app_structure()

def fazer_login():
    st.title("🔐 Login - KuCoin PRO")
    st.markdown("---")
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            if verificar_credenciais(usuario, senha):
                st.session_state["logado"] = True
                set_logged_in(True)
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")

def main():
    try:
        # Persistir login após F5: se .login_status existe, setar session_state['logado']
        try:
            if os.path.exists(LOGIN_FILE):
                st.session_state["logado"] = True
        except Exception:
            pass

        # Mostrar loader/top placeholder como primeiro elemento renderizado
        top_loader = st.empty()
        try:
            top_loader.info("⏳ Carregando...")
        except Exception:
            try:
                top_loader.markdown("⏳ Carregando...")
            except Exception:
                pass

        # Verificar se usuário está logado (exigir login por sessão)
        try:
            logged = bool(st.session_state.get("logado", False))
        except Exception:
            logged = False

        if not logged:
            # Remover loader antes de exibir o formulário de login
            try:
                top_loader.empty()
            except Exception:
                pass
            fazer_login()
