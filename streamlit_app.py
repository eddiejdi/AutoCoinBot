import os
import sys
import traceback
import streamlit as st
import hashlib
import logging

# Add current directory to sys.path to ensure imports work
sys.path.insert(0, os.path.dirname(__file__))

# auth_config.py - Configurações de autenticação (inlined to avoid import issues)
USUARIO_PADRAO = os.getenv("KUCOIN_USER", "admin")
SENHA_HASH_PADRAO = hashlib.sha256(os.getenv("KUCOIN_PASS", "senha123").encode()).hexdigest()

def verificar_credenciais(usuario, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    return usuario == USUARIO_PADRAO and senha_hash == SENHA_HASH_PADRAO

# Persistência de login
LOGIN_FILE = os.path.join(os.path.dirname(__file__), '.login_status')

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

# from auth_config import verificar_credenciais


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
        return

    # Garantir que session_state tenha logado
    st.session_state["logado"] = True

    # Usuário logado - renderizar aplicação principal
    ui_mod = None
    here = os.path.dirname(__file__)
    try:
        import ui as ui_mod
    except Exception:
        # If importing the package fails, create a small package shim named
        # `kucoin_app` that points to the current directory so `from .xxx`
        # relative imports inside `ui.py` work even when files are copied
        # directly into the container root (i.e. no enclosing kucoin_app/ dir).
        try:
            import types
            import importlib.util

            pkg_name = "kucoin_app"
            pkg = types.ModuleType(pkg_name)
            pkg.__path__ = [here]
            sys.modules[pkg_name] = pkg

            ui_path = os.path.join(here, "ui.py")
            spec = importlib.util.spec_from_file_location(f"{pkg_name}.ui", ui_path)
            ui_mod = importlib.util.module_from_spec(spec)
            ui_mod.__package__ = pkg_name
            sys.modules[f"{pkg_name}.ui"] = ui_mod
            spec.loader.exec_module(ui_mod)
        except Exception as e:
            st.error("Erro ao importar módulos (fallback)")
            st.error(str(e))
            st.code(traceback.format_exc())
            raise SystemExit(1)

    # All UI (top bar, dashboard, monitor, report) is rendered by ui.py.
    if hasattr(ui_mod, "render_bot_control"):
        try:
            ui_mod.render_bot_control()
        finally:
            # Garantir que o loader seja removido após a UI carregar
            try:
                top_loader.empty()
            except Exception:
                pass
    else:
        st.error("render_bot_control não encontrado em ui.py")

if __name__ == "__main__":
    main()