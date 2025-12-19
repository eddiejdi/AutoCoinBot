import streamlit as st, sys, os, importlib, traceback
st.set_page_config(page_title='KuCoin PRO (final)', layout='wide')
here = os.path.abspath(os.path.dirname(__file__))
parent = os.path.dirname(here)

if parent not in sys.path: sys.path.insert(0,parent)
try:
    from kucoin_app import ui as ui_mod, api, bot_core
except Exception as e:
    st.title('Erro ao importar módulos')
    st.error(str(e))
    st.code(traceback.format_exc())
    raise SystemExit(1)
st.title('KuCoin PRO — Final Package')
st.sidebar.title('Controls')
if hasattr(ui_mod, 'render_bot_control'):
    ui_mod.render_bot_control()
else:
    st.error('render_bot_control não encontrado em ui.py')

