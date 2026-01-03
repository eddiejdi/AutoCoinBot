import os
import sys
import hashlib
import logging

try:
    import streamlit as st
except Exception as exc:
    with open("fatal_error.log", "w") as f:
        import traceback as tb
        f.write("Erro fatal no import do streamlit_app.py:\n")
        f.write("".join(tb.format_exception(type(exc), exc, exc.__traceback__)))
    raise

# Basic configuration
USUARIO_PADRAO = os.getenv("KUCOIN_USER", "admin")
SENHA_HASH_PADRAO = hashlib.sha256(os.getenv("KUCOIN_PASS", "senha123").encode()).hexdigest()
LOGIN_FILE = os.path.join(os.path.dirname(__file__), '.login_status')


def verificar_credenciais(usuario, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    return usuario == USUARIO_PADRAO and senha_hash == SENHA_HASH_PADRAO


def set_logged_in(status: bool):
    if status:
        with open(LOGIN_FILE, 'w') as f:
            f.write('logged_in')
    else:
        if os.path.exists(LOGIN_FILE):
            os.remove(LOGIN_FILE)


def is_logged_in() -> bool:
    try:
        return os.path.exists(LOGIN_FILE) and open(LOGIN_FILE).read().strip() == 'logged_in'
    except Exception:
        return False


st.set_page_config(page_title="KuCoin PRO", layout="wide")


def _ensure_app_structure():
    try:
        base = os.path.dirname(__file__)
        for d in ("logs", "pids"):
            try:
                os.makedirs(os.path.join(base, d), exist_ok=True)
            except Exception:
                pass
    except Exception:
        pass

    try:
        logging.getLogger("streamlit").setLevel(logging.ERROR)
    except Exception:
        pass


_ensure_app_structure()


def fazer_login():
    st.title("🔐 Login - KuCoin PRO")
    st.markdown("---")

    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

                st.error("Usuário ou senha incorretos!")


def main():
    try:
        try:
            if os.path.exists(LOGIN_FILE):
                st.session_state.setdefault("logado", True)
        except Exception:
            pass

        # Verificar se usuário está logado (exigir login por sessão)
        try:
            logged = bool(st.session_state.get("logado", False))
        except Exception:
            logged = False

        if not logged:
            fazer_login()
            return

<<<<<<< HEAD
        # Mostrar loader enquanto importa UI
        with st.spinner("⏳ Carregando dashboard..."):
            # Usuário logado - importar UI
            ui_mod = None
            here = os.path.dirname(__file__)
=======
        # Usuário já está logado: remove o indicador de carregamento
        # antes de renderizar a UI principal, para evitar a impressão de
        # "carregamento infinito" caso a UI chame st.stop()/st.rerun.
        try:
            top_loader.empty()
            pass

        # Usuário logado - importar UI
        ui_mod = None
        here = os.path.dirname(__file__)
        try:
            import ui as ui_mod
        except Exception:
>>>>>>> d82f869 (Checkpoint from VS Code for coding agent session)
            try:
                import ui as ui_mod
            except Exception:
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
                    st.error(f"❌ Erro ao carregar módulos: {e}")
                    return

<<<<<<< HEAD
        if ui_mod and hasattr(ui_mod, "render_bot_control"):
            try:
                ui_mod.render_bot_control()
            except Exception as e:
                st.error(f"❌ Erro ao renderizar interface: {e}")
=======
        if hasattr(ui_mod, "render_bot_control"):
            # A UI pode chamar st.stop()/st.rerun; o loader já foi
            # limpo acima para não ficar preso na tela.
            ui_mod.render_bot_control()
>>>>>>> d82f869 (Checkpoint from VS Code for coding agent session)
        else:
            st.error("render_bot_control não encontrado em ui.py")

    except Exception as exc:
        st.error(f"❌ Erro global: {exc}")
        import traceback
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
