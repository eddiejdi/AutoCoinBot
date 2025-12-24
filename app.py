import os
import sys
import traceback
import streamlit as st

from auth_config import verificar_credenciais


st.set_page_config(page_title="KuCoin PRO", layout="wide")

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
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")

def main():
    # Verificar se usuário está logado
    if "logado" not in st.session_state or not st.session_state["logado"]:
        fazer_login()
        return

    # Usuário logado - renderizar aplicação principal
    ui_mod = None
    try:
        from kucoin_app import ui as ui_mod
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
        ui_mod.render_bot_control()
    else:
        st.error("render_bot_control não encontrado em ui.py")

if __name__ == "__main__":
    main()

