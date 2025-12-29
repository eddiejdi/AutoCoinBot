import html
# dashboard.py
import time
import logging
import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
from pathlib import Path
import os
import sys

# Ensure current directory is in sys.path for imports
sys.path.insert(0, os.path.dirname(__file__))

from bot_controller import BotController
from bot_session import BotSession
from database import DatabaseManager
from sidebar_controller import SidebarController
from ui import inject_global_css, get_current_theme, render_theme_selector, render_cobol_gauge_static, render_eternal_runs_history

try:
    from terminal_component import render_terminal as render_terminal
    HAS_TERMINAL = True
except Exception:
    HAS_TERMINAL = False


ROOT = Path(__file__).resolve().parent


def render_dashboard():
    """
    Main dashboard rendering function - extracted from ui.py for better organization
    """
    # =====================================================
    # SESSION STATE
    # =====================================================
    if "controller" not in st.session_state:
        st.session_state.controller = BotController()

    if "bot_id" not in st.session_state:
        st.session_state.bot_id = None

    if "terminal_theme" not in st.session_state:
        st.session_state.terminal_theme = "COBOL Verde"

    if "eternal_mode" not in st.session_state:
        st.session_state.eternal_mode = False

    controller = st.session_state.controller

    # =====================================================
    # PAGE CONFIG & TEMA GLOBAL
    # =====================================================
    st.set_page_config(page_title="KuCoin Trading Bot", layout="wide")

    # Injetar CSS do tema terminal
    inject_global_css()

    # Header estilo terminal
    theme = get_current_theme()
    st.markdown(f'''
    <div style="text-align: center; padding: 10px; margin-bottom: 20px;">
        <pre style="color: {theme["border"]}; font-size: 10px; line-height: 1.2;">
╔══════════════════════════════════════════════════════════════════════════════╗
║  ██╗  ██╗██╗   ██╗ ██████╗ ██████╗ ██╗███╗   ██╗    ██████╗ ██████╗  ██████╗ ║
║  ██║ ██╔╝██║   ██║██╔════╝██╔═══██╗██║████╗  ██║    ██╔══██╗██╔══██╗██╔═══██╗║
║  █████╔╝ ██║   ██║██║     ██║   ██║██║██╔██╗ ██║    ██████╔╝██████╔╝██║   ██║║
║  ██╔═██╗ ██║   ██║██║     ██║   ██║██║██║╚██╗██║    ██╔═══╝ ██╔══██╗██║   ██║║
║  ██║  ██╗╚██████╔╝╚██████╗╚██████╔╝██║██║ ╚████║    ██║     ██║  ██║╚██████╔╝║
║  ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ║
║                      T R A D I N G   T E R M I N A L                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
        </pre>
    </div>
    ''', unsafe_allow_html=True)

    # =====================================================
    # QUERY STRING (?bot=...)
    # =====================================================
    q = st.query_params
    # query params may be returned as list or single string depending on Streamlit version
    def _qs_get(key, default=None):
        v = q.get(key, None)
        if v is None:
            return default
        # if it's a list, take first element; otherwise return as-is
        try:
            if isinstance(v, (list, tuple)):
                return v[0]
        except Exception:
            pass
        return v

    query_bot = _qs_get("bot", None)
    if query_bot:
        st.session_state.bot_id = query_bot

    # Se a página for aberta com ?start=1 e parâmetros, iniciar o bot aqui
    q = st.query_params
    start_param = _qs_get("start", None)
    if start_param:
        try:
            s_symbol = _qs_get("symbol", "BTC-USDT")
            s_entry = float(_qs_get("entry", "88000"))
            s_mode = _qs_get("mode", "sell")
            s_targets = _qs_get("targets", "2:0.3,5:0.4")
            s_interval = float(_qs_get("interval", "5"))
            s_size_raw = _qs_get("size", "")
            s_size = None if s_size_raw in ("", "0", "0.0", "None") else float(s_size_raw)
            s_funds_raw = _qs_get("funds", "")
            s_funds = None if s_funds_raw in ("", "0", "0.0", "None") else float(s_funds_raw)
            s_dry = _qs_get("dry", "0").lower() in ("1", "true", "yes")

            bot_id_started = st.session_state.controller.start_bot(
                s_symbol, s_entry, s_mode, s_targets,
                s_interval, s_size, s_funds, s_dry,
            )

            st.session_state.bot_id = bot_id_started
            time.sleep(0.5)  # Deixa bot subprocess começar a gravar logs
            # substitui a query para exibir ?bot=... evitando reinícios
            st.query_params = {"bot": [bot_id_started]}
            st.session_state["_started_from_qs"] = True
            st.rerun()
        except Exception as e:
            st.error(f"Erro iniciando bot via query: {e}")

    bot_id = st.session_state.bot_id
    if bot_id:
        # Tentar obter PID do registry
        try:
            registry_info = controller.registry.get_bot_info(bot_id)
            pid_info = ""
            if registry_info and "pid" in registry_info:
                pid_info = f" | PID: {registry_info['pid']}"
            st.success(f"🤖 Bot ativo: {bot_id}{pid_info}")
        except Exception:
            st.success(f"🤖 Bot ativo: {bot_id}")

    # =====================================================
    # SIDEBAR (sempre visível)
    # =====================================================
    # Usar SidebarController para renderizar sidebar completo com saldos, status e controles
    sidebar_controller = SidebarController()
    start_real, start_dry, kill_bot = sidebar_controller.render()

    # Adicionar seletor de tema no sidebar
    render_theme_selector(key_suffix="_dashboard")

    # =====================================================
    # TRATAMENTO DOS BOTÕES
    # =====================================================
    if start_real or start_dry:
        try:
            # Obter parâmetros do session_state
            symbol = st.session_state.get("symbol", "BTC-USDT")
            entry = st.session_state.get("entry", 0.0)
            mode = st.session_state.get("mode", "sell")
            targets = st.session_state.get("targets", "1:0.3,3:0.5,5:0.2")
            interval = st.session_state.get("interval", 5.0)
            size = st.session_state.get("size", 0.0006)
            funds = st.session_state.get("funds", 20.0)
            reserve_pct = st.session_state.get("reserve_pct", 50.0)
            eternal_mode = st.session_state.get("eternal_mode", False)

            # Iniciar bot
            bot_id_started = st.session_state.controller.start_bot(
                symbol, float(entry), mode, targets,
                float(interval), float(size), float(funds), start_dry,
                eternal_mode=eternal_mode,
            )

            st.session_state.bot_id = bot_id_started
            st.session_state.bot_running = True
            time.sleep(0.5)
            st.query_params = {"bot": [bot_id_started]}
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao iniciar bot: {e}")

    if kill_bot:
        try:
            if bot_id:
                st.session_state.controller.stop_bot(bot_id)
                st.session_state.bot_id = None
                st.session_state.bot_running = False
                st.query_params = {}
                st.success("✅ Bot encerrado")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("Nenhum bot ativo para encerrar")
        except Exception as e:
            st.error(f"Erro ao encerrar bot: {e}")

    # =====================================================
    # TERMINAL
    # =====================================================
    st.divider()
    st.subheader("🖥️ Terminal do Bot")

    if not bot_id:
        st.info("Nenhum bot ativo.")
        st.text_area("Bot Logs", "Inicie um bot para ver os logs aqui", height=400, disabled=True)
    else:
        # Usar fragment para refresh parcial (só atualiza este bloco)
        @st.fragment(run_every=3)  # Atualiza a cada 3 segundos automaticamente
        def render_live_logs():
            # Ler logs do banco de dados
            try:
                db = DatabaseManager()
                logs = db.get_bot_logs(bot_id, limit=30)
            except Exception as e:
                st.error(f"Erro ao conectar banco de dados: {e}")
                logs = []
            # Obter target do session_state
            target_pct = st.session_state.get("target_profit_pct", 2.0)

            # Renderizar gauge COBOL estático (baseado nos logs carregados)
            if logs:
                render_cobol_gauge_static(logs, bot_id, target_pct)

            # Terminal de logs
            theme = get_current_theme()

            if logs:
                # Formatar logs como HTML
                log_html_items = []
                for log in reversed(logs):  # Mais antigos primeiro
                    level = log.get('level', 'INFO')
                    msg = log.get('message', '')

                    # Determinar classe de cor
                    txt = (level + " " + msg).upper()
                    if any(w in txt for w in ['ERROR', 'ERRO', '❌', 'EXCEPTION']):
                        color_class = "color: #ff6b6b; border-left-color: #ff6b6b; font-weight: bold;"
                    elif any(w in txt for w in ['PROFIT', 'LUCRO', 'SUCCESS', '✅', 'TARGET', 'GANHO']):
                        color_class = "color: #4ade80; border-left-color: #4ade80; font-weight: bold;"
                    elif any(w in txt for w in ['WARNING', 'AVISO', '⚠', 'WARN']):
                        color_class = "color: #fbbf24; border-left-color: #fbbf24;"
                    elif any(w in txt for w in ['TRADE', 'ORDER', 'BUY', 'SELL', 'COMPRA', 'VENDA']):
                        color_class = "color: #60a5fa; border-left-color: #60a5fa;"
                    elif any(w in txt for w in ['INFO', 'BOT', 'INICIADO', 'CONECTADO']):
                        color_class = "color: #22d3ee; border-left-color: #22d3ee;"
                    else:
                        color_class = "color: #cccccc; border-left-color: #333;"

                    # Formatar mensagem JSON se possível
                    try:
                        import json as json_lib
                        data = json_lib.loads(msg)
                        parts = []
                        if data.get('event'): parts.append(data['event'].upper())
                        if data.get('price'): parts.append(f"${float(data['price']):,.2f}")
                        if data.get('cycle'): parts.append(f"Cycle:{data['cycle']}")
                        if data.get('executed'): parts.append(f"Exec:{data['executed']}")
                        if data.get('message'): parts.append(data['message'])
                        formatted_msg = " | ".join(parts) if parts else msg
                    except:
                        formatted_msg = msg

                    safe_msg = html.escape(formatted_msg)
                    log_html_items.append(f'''
                        <div style="padding: 6px 10px; margin: 3px 0; border-radius: 4px;
                                    font-size: 13px; line-height: 1.5; background: #0a0a0a;
                                    border-left: 3px solid #333; {color_class}">
                            <span style="font-weight: bold; margin-right: 8px;">[{level}]</span>{safe_msg}
                        </div>
                    ''')

                log_html_content = "".join(log_html_items)
                now_str = time.strftime("%H:%M:%S")

                terminal_html = f'''
<style>
    @keyframes blink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.3; }}
    }}
    .live-indicator {{
        animation: blink 1s infinite;
        color: #4ade80;
        font-weight: bold;
    }}
</style>
<div style="font-family: 'Courier New', monospace;">
    <div style="background: #0a0a0a; border: 2px solid {theme["border"]}; border-radius: 8px;
                box-shadow: 0 0 20px {theme["glow"]}; overflow: hidden;">

        <div style="background: #111; padding: 10px 15px; border-bottom: 1px solid {theme["border"]};
                    display: flex; justify-content: space-between; align-items: center;">
            <span style="color: {theme["text"]}; font-size: 13px; font-weight: bold;">
                ◉ LOG TERMINAL — {bot_id[:12]}...
            </span>
            <span style="font-size: 11px;">
                <span class="live-indicator">● LIVE</span>
                <span style="color: #888;"> | {now_str}</span>
            </span>
        </div>

        <div style="max-height: 350px; overflow-y: auto; padding: 10px;" id="logScroll">
            {log_html_content}
        </div>

        <div style="background: #111; padding: 8px 15px; border-top: 1px solid #222;
                    font-size: 10px; color: #666; display: flex; justify-content: space-between;">
            <span>{len(logs)} logs</span>
            <span style="color: #4ade80;">↻ Auto-refresh: 3s</span>
        </div>
    </div>
</div>
<script>
    var logDiv = document.getElementById('logScroll');
    if (logDiv) logDiv.scrollTop = logDiv.scrollHeight;
</script>
'''
                components.html(terminal_html, height=450, scrolling=False)
            else:
                st.info("Aguardando logs do bot...")

        # Chamar o fragment
        render_live_logs()

        # =====================================================
        # ETERNAL RUNS HISTORY (oculta se não há registros)
        # =====================================================
        render_eternal_runs_history(bot_id)