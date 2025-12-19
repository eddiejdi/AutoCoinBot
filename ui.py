# ui.py
import time
import logging
import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
import html
from pathlib import Path

from .bot_controller import BotController
from .bot_session import BotSession
from .database import DatabaseManager
from .sidebar_controller import SidebarController

try:
    from .terminal_component import render_terminal as render_terminal
    HAS_TERMINAL = True
except Exception:
    HAS_TERMINAL = False


ROOT = Path(__file__).resolve().parent

# =====================================================
# TEMAS COBOL/TERMINAL
# =====================================================
THEMES = {
    "COBOL Verde": {
        "name": "COBOL Verde",
        "bg": "#0a0a0a",
        "bg2": "#050505",
        "border": "#33ff33",
        "text": "#33ff33",
        "text2": "#aaffaa",
        "accent": "#00ffff",
        "warning": "#ffaa00",
        "error": "#ff3333",
        "success": "#00ff00",
        "header_bg": "linear-gradient(180deg, #1a3a1a 0%, #0d1f0d 100%)",
        "glow": "rgba(51, 255, 51, 0.3)",
    },
    "Amber CRT": {
        "name": "Amber CRT",
        "bg": "#0a0800",
        "bg2": "#050400",
        "border": "#ffaa00",
        "text": "#ffaa00",
        "text2": "#ffcc66",
        "accent": "#ffffff",
        "warning": "#ff6600",
        "error": "#ff3333",
        "success": "#ffff00",
        "header_bg": "linear-gradient(180deg, #3a2a0a 0%, #1f1505 100%)",
        "glow": "rgba(255, 170, 0, 0.3)",
    },
    "IBM Blue": {
        "name": "IBM Blue",
        "bg": "#000033",
        "bg2": "#000022",
        "border": "#3399ff",
        "text": "#3399ff",
        "text2": "#99ccff",
        "accent": "#ffffff",
        "warning": "#ffaa00",
        "error": "#ff6666",
        "success": "#66ff66",
        "header_bg": "linear-gradient(180deg, #0a1a3a 0%, #050d1f 100%)",
        "glow": "rgba(51, 153, 255, 0.3)",
    },
    "Matrix": {
        "name": "Matrix",
        "bg": "#000000",
        "bg2": "#001100",
        "border": "#00ff00",
        "text": "#00ff00",
        "text2": "#88ff88",
        "accent": "#ffffff",
        "warning": "#ffff00",
        "error": "#ff0000",
        "success": "#00ff00",
        "header_bg": "linear-gradient(180deg, #002200 0%, #001100 100%)",
        "glow": "rgba(0, 255, 0, 0.5)",
    },
    "Cyberpunk": {
        "name": "Cyberpunk",
        "bg": "#0d0221",
        "bg2": "#1a0533",
        "border": "#ff00ff",
        "text": "#ff00ff",
        "text2": "#ff99ff",
        "accent": "#00ffff",
        "warning": "#ffff00",
        "error": "#ff3333",
        "success": "#00ff00",
        "header_bg": "linear-gradient(180deg, #2d0a4e 0%, #1a0533 100%)",
        "glow": "rgba(255, 0, 255, 0.4)",
    },
}


def get_current_theme():
    """Retorna o tema atual selecionado"""
    theme_name = st.session_state.get("terminal_theme", "COBOL Verde")
    return THEMES.get(theme_name, THEMES["COBOL Verde"])


def inject_global_css():
    """Injeta CSS global para estilizar toda a página no tema terminal"""
    theme = get_current_theme()
    
    css = f'''
    <style>
        /* Reset e base */
        .stApp {{
            background-color: {theme["bg"]} !important;
            font-family: 'Courier New', 'Lucida Console', monospace !important;
        }}
        
        /* Main container */
        .main .block-container {{
            background-color: {theme["bg"]} !important;
            border: 2px solid {theme["border"]} !important;
            border-radius: 8px !important;
            box-shadow: 0 0 30px {theme["glow"]}, inset 0 0 50px rgba(0,0,0,0.5) !important;
            padding: 20px !important;
            margin: 10px !important;
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {theme["text"]} !important;
            font-family: 'Courier New', monospace !important;
            text-shadow: 0 0 10px {theme["glow"]} !important;
        }}
        
        h1::before {{ content: ">>> "; color: {theme["accent"]}; }}
        h2::before {{ content: ">> "; color: {theme["accent"]}; }}
        h3::before {{ content: "> "; color: {theme["accent"]}; }}
        
        /* Paragraphs and text */
        p, span, label, .stMarkdown {{
            color: {theme["text2"]} !important;
            font-family: 'Courier New', monospace !important;
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {theme["bg2"]} !important;
            border-right: 2px solid {theme["border"]} !important;
        }}
        
        [data-testid="stSidebar"] * {{
            color: {theme["text2"]} !important;
        }}
        
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: {theme["text"]} !important;
        }}
        
        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div {{
            background-color: {theme["bg2"]} !important;
            color: {theme["text"]} !important;
            border: 1px solid {theme["border"]} !important;
            font-family: 'Courier New', monospace !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {{
            box-shadow: 0 0 10px {theme["glow"]} !important;
            border-color: {theme["accent"]} !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: {theme["bg2"]} !important;
            color: {theme["text"]} !important;
            border: 2px solid {theme["border"]} !important;
            font-family: 'Courier New', monospace !important;
            font-weight: bold !important;
            text-transform: uppercase !important;
            transition: all 0.3s ease !important;
        }}
        
        .stButton > button:hover {{
            background-color: {theme["border"]} !important;
            color: {theme["bg"]} !important;
            box-shadow: 0 0 20px {theme["glow"]} !important;
        }}
        
        /* Primary button */
        .stButton > button[kind="primary"] {{
            background-color: {theme["border"]} !important;
            color: {theme["bg"]} !important;
        }}
        
        .stButton > button[kind="primary"]:hover {{
            background-color: {theme["success"]} !important;
        }}
        
        /* Alerts */
        .stAlert {{
            background-color: {theme["bg2"]} !important;
            border: 1px solid {theme["border"]} !important;
            font-family: 'Courier New', monospace !important;
        }}
        
        [data-testid="stAlertContainer"] {{
            background-color: {theme["bg2"]} !important;
            border-left: 4px solid {theme["success"]} !important;
        }}
        
        /* Success alert */
        .stAlert [data-testid="stAlertContentSuccess"] {{
            color: {theme["success"]} !important;
        }}
        
        /* Warning alert */
        .stAlert [data-testid="stAlertContentWarning"] {{
            color: {theme["warning"]} !important;
        }}
        
        /* Error alert */
        .stAlert [data-testid="stAlertContentError"] {{
            color: {theme["error"]} !important;
        }}
        
        /* Dividers */
        hr {{
            border-color: {theme["border"]} !important;
            box-shadow: 0 0 5px {theme["glow"]} !important;
        }}
        
        /* Metrics */
        [data-testid="stMetric"] {{
            background-color: {theme["bg2"]} !important;
            border: 1px solid {theme["border"]} !important;
            padding: 10px !important;
            border-radius: 4px !important;
        }}
        
        [data-testid="stMetricValue"] {{
            color: {theme["accent"]} !important;
            font-family: 'Courier New', monospace !important;
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {theme["text2"]} !important;
        }}
        
        /* Selectbox dropdown */
        [data-baseweb="select"] {{
            background-color: {theme["bg2"]} !important;
        }}
        
        [data-baseweb="menu"] {{
            background-color: {theme["bg2"]} !important;
            border: 1px solid {theme["border"]} !important;
        }}
        
        [data-baseweb="menu"] li {{
            color: {theme["text"]} !important;
        }}
        
        [data-baseweb="menu"] li:hover {{
            background-color: {theme["border"]} !important;
            color: {theme["bg"]} !important;
        }}
        
        /* Caption text */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {theme["text2"]} !important;
            opacity: 0.8;
        }}
        
        /* Info boxes */
        .stInfo {{
            background-color: {theme["bg2"]} !important;
            border-left: 4px solid {theme["accent"]} !important;
        }}
        
        /* Text area */
        .stTextArea textarea {{
            background-color: {theme["bg2"]} !important;
            color: {theme["text"]} !important;
            border: 1px solid {theme["border"]} !important;
            font-family: 'Courier New', monospace !important;
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {theme["bg2"]} !important;
            color: {theme["text"]} !important;
            border: 1px solid {theme["border"]} !important;
        }}
        
        /* Radio buttons */
        .stRadio > div {{
            background-color: {theme["bg2"]} !important;
            padding: 10px !important;
            border-radius: 4px !important;
        }}
        
        .stRadio label {{
            color: {theme["text2"]} !important;
        }}
        
        /* Checkbox */
        .stCheckbox label {{
            color: {theme["text2"]} !important;
        }}
        
        /* Progress bar */
        .stProgress > div > div {{
            background-color: {theme["border"]} !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {theme["bg"]} !important;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {theme["border"]} !important;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {theme["accent"]} !important;
        }}
        
        /* CRT scan line effect */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 0, 0, 0.1),
                rgba(0, 0, 0, 0.1) 1px,
                transparent 1px,
                transparent 2px
            );
            z-index: 9999;
        }}
        
        /* Flicker animation for authentic CRT feel */
        @keyframes flicker {{
            0% {{ opacity: 0.97; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.98; }}
        }}
        
        .stApp {{
            animation: flicker 0.15s infinite;
        }}
        
        /* FORCE ALL BACKGROUNDS TO DARK */
        div, section, header, footer, main, aside, article {{
            background-color: transparent !important;
        }}
        
        /* Streamlit specific white backgrounds */
        [data-testid="stAppViewContainer"] {{
            background-color: {theme["bg"]} !important;
        }}
        
        [data-testid="stHeader"] {{
            background-color: {theme["bg"]} !important;
        }}
        
        [data-testid="stToolbar"] {{
            background-color: {theme["bg"]} !important;
        }}
        
        [data-testid="stDecoration"] {{
            background-color: {theme["bg"]} !important;
        }}
        
        [data-testid="stBottomBlockContainer"] {{
            background-color: {theme["bg"]} !important;
        }}
        
        /* Main area */
        .main {{
            background-color: {theme["bg"]} !important;
        }}
        
        /* All iframes and embeds */
        iframe {{
            background-color: {theme["bg"]} !important;
        }}
        
        /* Form elements */
        [data-testid="stForm"] {{
            background-color: {theme["bg2"]} !important;
            border: 1px solid {theme["border"]} !important;
        }}
        
        /* Popover and modals */
        [data-baseweb="popover"] {{
            background-color: {theme["bg2"]} !important;
            border: 1px solid {theme["border"]} !important;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {theme["bg"]} !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background-color: {theme["bg2"]} !important;
            color: {theme["text"]} !important;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {theme["border"]} !important;
        }}
        
        /* Data editor / table */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            background-color: {theme["bg2"]} !important;
        }}
        
        /* Column config */
        .stColumn {{
            background-color: transparent !important;
        }}
        
        /* Element container */
        [data-testid="stElementContainer"] {{
            background-color: transparent !important;
        }}
        
        /* Vertical block */
        [data-testid="stVerticalBlock"] {{
            background-color: transparent !important;
        }}
        
        /* Horizontal block */
        [data-testid="stHorizontalBlock"] {{
            background-color: transparent !important;
        }}
        
        /* Widget label */
        .stWidgetLabel {{
            color: {theme["text2"]} !important;
        }}
        
        /* Toast notifications */
        [data-testid="stToast"] {{
            background-color: {theme["bg2"]} !important;
            border: 1px solid {theme["border"]} !important;
            color: {theme["text"]} !important;
        }}
        
        /* Spinner */
        .stSpinner {{
            background-color: transparent !important;
        }}
        
        /* Number input buttons */
        .stNumberInput button {{
            background-color: {theme["bg2"]} !important;
            color: {theme["text"]} !important;
            border-color: {theme["border"]} !important;
        }}
        
        /* Select all white/light backgrounds */
        [style*="background-color: white"],
        [style*="background-color: #fff"],
        [style*="background-color: rgb(255, 255, 255)"],
        [style*="background: white"],
        [style*="background: #fff"] {{
            background-color: {theme["bg"]} !important;
        }}
        
        /* Base web components */
        [data-baseweb] {{
            background-color: {theme["bg2"]} !important;
        }}
        
        /* Input containers */
        [data-baseweb="input"] {{
            background-color: {theme["bg2"]} !important;
        }}
        
        [data-baseweb="base-input"] {{
            background-color: {theme["bg2"]} !important;
        }}
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)


def render_theme_selector():
    """Renderiza seletor de tema no sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎨 TEMA DO TERMINAL")
    
    current_theme = st.session_state.get("terminal_theme", "COBOL Verde")
    
    selected_theme = st.sidebar.selectbox(
        "Selecionar Tema",
        options=list(THEMES.keys()),
        index=list(THEMES.keys()).index(current_theme),
        key="theme_selector"
    )
    
    if selected_theme != current_theme:
        st.session_state.terminal_theme = selected_theme
        st.rerun()


def render_eternal_runs_history(bot_id: str):
    """Renderiza histórico de ciclos do Eternal Mode"""
    try:
        db = DatabaseManager()
        runs = db.get_eternal_runs(bot_id, limit=15)
        summary = db.get_eternal_runs_summary(bot_id)
    except Exception as e:
        runs = []
        summary = {}
    
    # Ocultar completamente se não há registros
    has_runs = runs and len(runs) > 0
    has_summary = summary and summary.get('total_runs', 0) > 0
    
    if not has_runs and not has_summary:
        return  # Nada a exibir - oculta a seção completamente
    
    theme = get_current_theme()
    
    st.divider()
    st.subheader("🔄 Eternal Mode — Histórico de Ciclos")
    
    # Resumo geral
    if summary and summary.get('total_runs', 0) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_runs = summary.get('total_runs', 0)
            st.metric("Total Ciclos", total_runs)
        
        with col2:
            total_profit = summary.get('total_profit_usdt', 0) or 0
            color = "normal" if total_profit >= 0 else "inverse"
            st.metric("Lucro Total", f"${total_profit:.2f}", delta_color=color)
        
        with col3:
            avg_pct = summary.get('avg_profit_pct', 0) or 0
            st.metric("Média %", f"{avg_pct:.2f}%")
        
        with col4:
            profitable = summary.get('profitable_runs', 0) or 0
            total = summary.get('completed_runs', 0) or 1
            win_rate = (profitable / total * 100) if total > 0 else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
    
    # Tabela de ciclos
    if runs:
        # Construir HTML da tabela no estilo terminal
        rows_html = ""
        for run in runs:
            run_num = run.get('run_number', '?')
            status = run.get('status', 'running')
            profit_pct = run.get('profit_pct', 0) or 0
            profit_usdt = run.get('profit_usdt', 0) or 0
            targets_hit = run.get('targets_hit', 0)
            total_targets = run.get('total_targets', 0)
            entry = run.get('entry_price', 0) or 0
            exit_p = run.get('exit_price', 0)
            
            # Cores baseadas no resultado
            if status == 'running':
                status_color = "#fbbf24"
                status_icon = "⏳"
                profit_color = "#888"
            elif profit_pct > 0:
                status_color = "#4ade80"
                status_icon = "✅"
                profit_color = "#4ade80"
            else:
                status_color = "#ff6b6b"
                status_icon = "❌"
                profit_color = "#ff6b6b"
            
            exit_str = f"${exit_p:.2f}" if exit_p else "—"
            
            rows_html += f'''
            <tr style="border-bottom: 1px solid {theme["border"]}30;">
                <td style="padding: 8px; color: {theme["text"]}; font-weight: bold;">#{run_num}</td>
                <td style="padding: 8px; color: {status_color};">{status_icon} {status.upper()}</td>
                <td style="padding: 8px; color: {theme["text2"]};">${entry:.2f}</td>
                <td style="padding: 8px; color: {theme["text2"]};">{exit_str}</td>
                <td style="padding: 8px; color: {profit_color}; font-weight: bold;">{profit_pct:+.2f}%</td>
                <td style="padding: 8px; color: {profit_color}; font-weight: bold;">${profit_usdt:+.2f}</td>
                <td style="padding: 8px; color: {theme["text2"]};">{targets_hit}/{total_targets}</td>
            </tr>
            '''
        
        table_html = f'''
        <div style="font-family: 'Courier New', monospace; background: {theme["bg2"]}; 
                    border: 2px solid {theme["border"]}; border-radius: 8px; 
                    box-shadow: 0 0 15px {theme["glow"]}; overflow: hidden; margin-top: 10px;">
            <div style="background: #111; padding: 10px 15px; border-bottom: 1px solid {theme["border"]};">
                <span style="color: {theme["text"]}; font-size: 14px; font-weight: bold;">
                    📊 ETERNAL RUNS LOG
                </span>
            </div>
            <div style="max-height: 300px; overflow-y: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead>
                        <tr style="background: #0a0a0a; border-bottom: 2px solid {theme["border"]};">
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">CICLO</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">STATUS</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">ENTRY</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">EXIT</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">PROFIT %</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">PROFIT $</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">TARGETS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        '''
        
        components.html(table_html, height=350, scrolling=False)


def render_cobol_gauge_static(logs: list, bot_id: str, target_pct: float = 2.0):
    """
    Renderiza gauge estilo terminal COBOL/mainframe inline (versão estática).
    Usa dados dos logs já carregados, sem polling.
    """
    import json as json_lib
    from datetime import datetime
    
    # Obter tema atual
    theme = get_current_theme()
    
    # Extrair dados dos logs
    current_price = 0.0
    entry_price = 0.0
    symbol = "BTC-USDT"
    cycle = 0
    executed = "0/0"
    mode = "---"
    last_event = "AGUARDANDO"
    profit_pct = 0.0
    
    for log in logs:
        try:
            msg = log.get('message', '')
            try:
                data = json_lib.loads(msg)
                if 'price' in data:
                    current_price = float(data['price'])
                if 'entry_price' in data:
                    entry_price = float(data['entry_price'])
                if 'symbol' in data:
                    symbol = data['symbol']
                if 'cycle' in data:
                    cycle = int(data['cycle'])
                if 'executed' in data:
                    executed = data['executed']
                if 'mode' in data:
                    mode = data['mode'].upper()
                if 'event' in data:
                    last_event = data['event'].upper().replace('_', ' ')
            except:
                pass
        except:
            pass
    
    # Calcular P&L
    if entry_price > 0 and current_price > 0:
        profit_pct = ((current_price - entry_price) / entry_price) * 100
    
    # Calcular progresso do gauge (0-100%)
    progress = min(100, max(0, (profit_pct / target_pct) * 100)) if target_pct > 0 else 0
    bar_width = 40
    filled = int(bar_width * progress / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    # Cor baseada no P&L
    if profit_pct >= target_pct:
        pnl_color = theme["success"]
        status = "TARGET ATINGIDO"
    elif profit_pct > 0:
        pnl_color = theme["text"]
        status = "EM LUCRO"
    elif profit_pct < -1:
        pnl_color = theme["error"]
        status = "PREJUIZO"
    else:
        pnl_color = theme["warning"]
        status = "NEUTRO"
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    gauge_html = f'''
<div style="
    font-family: 'Courier New', 'Lucida Console', monospace;
    font-size: 13px;
    background: {theme["bg"]};
    border: 2px solid {theme["border"]};
    box-shadow: 0 0 20px {theme["glow"]}, inset 0 0 30px rgba(0,0,0,0.8);
    padding: 0;
    max-width: 500px;
    color: {theme["text"]};
    border-radius: 4px;
    margin: 10px 0;
">
    <div style="
        background: {theme["header_bg"]};
        border-bottom: 1px solid {theme["border"]};
        padding: 8px 12px;
        text-align: center;
    ">
        <span style="color: {theme["warning"]};">╔═══════════════════════════════════════════════╗</span><br>
        <span style="color: {theme["accent"]};">║</span>
        <span style="color: #ffffff; font-weight: bold;"> ◉ KUCOIN TRADING TERMINAL v2.0 ◉ </span>
        <span style="color: {theme["accent"]};">║</span><br>
        <span style="color: {theme["warning"]};">╚═══════════════════════════════════════════════╝</span>
    </div>
    
    <div style="padding: 12px; background: {theme["bg2"]};">
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">┌──────────────────────────────────────────────┐</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ BOT: <span style="color: #ffffff;">{bot_id[:16]:<16}</span>                       │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ SYM: <span style="color: {theme["accent"]};">{symbol:<12}</span> MODE: <span style="color: {theme["warning"]};">{mode:<6}</span>         │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ ENTRY.....: <span style="color: #ffffff;">${entry_price:>12,.2f}</span>                │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ CURRENT...: <span style="color: {theme["accent"]}; font-weight: bold;">${current_price:>12,.2f}</span>                │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ P&amp;L STATUS: <span style="color: {pnl_color}; font-weight: bold;">{status:<16}</span>              │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ PROFIT: <span style="color: {pnl_color}; font-weight: bold;">{profit_pct:>+10.4f}%</span>                      │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ TARGET: <span style="color: {theme["warning"]};">{target_pct:>10.2f}%</span>                      │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ PROGRESS TO TARGET:                          │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ <span style="color: {pnl_color};">{bar}</span>   │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ <span style="color: #ffffff;">{progress:>6.1f}%</span> COMPLETE                          │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ CYCLE: <span style="color: {theme["accent"]};">{cycle:>6}</span>  EXEC: <span style="color: #ffffff;">{executed:<8}</span>          │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ EVENT: <span style="color: {theme["warning"]};">{last_event[:20]:<20}</span>              │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">└──────────────────────────────────────────────┘</pre>
        
        <div style="
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px dashed {theme["border"]}44;
            color: #666666;
            font-size: 10px;
            text-align: center;
        ">
            <span style="color: {theme["text"]};">●</span> ONLINE | 
            <span style="color: #aaaaaa;">{now}</span> |
            <span style="color: {theme["text"]};">◄</span> REFRESH MANUAL
        </div>
    </div>
</div>
'''
    # Renderiza usando components.html 
    components.html(gauge_html, height=420, scrolling=False)


def render_cobol_gauge(logs: list, bot_id: str, target_pct: float = 2.0, api_port: int = 8765):
    """
    Renderiza gauge estilo terminal COBOL/mainframe inline com polling realtime.
    Visual retro com bordas ASCII, usa tema selecionado.
    """
    from datetime import datetime
    
    # Obter tema atual
    theme = get_current_theme()
    
    gauge_html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            background: transparent;
            font-family: 'Courier New', 'Lucida Console', monospace;
            font-size: 13px;
        }}
        .gauge-container {{
            background: {theme["bg"]};
            border: 2px solid {theme["border"]};
            box-shadow: 0 0 20px {theme["glow"]}, inset 0 0 30px rgba(0,0,0,0.8);
            max-width: 520px;
            color: {theme["text"]};
            border-radius: 4px;
        }}
        .gauge-header {{
            background: {theme["header_bg"]};
            border-bottom: 1px solid {theme["border"]};
            padding: 8px 12px;
            text-align: center;
        }}
        .gauge-content {{
            padding: 12px;
            background: {theme["bg2"]};
        }}
        pre {{
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.3;
        }}
        .border-char {{ color: {theme["accent"]}; }}
        .label {{ color: {theme["text2"]}; }}
        .value {{ color: #ffffff; }}
        .highlight {{ color: {theme["accent"]}; font-weight: bold; }}
        .profit-positive {{ color: {theme["success"]}; font-weight: bold; }}
        .profit-negative {{ color: {theme["error"]}; font-weight: bold; }}
        .profit-neutral {{ color: {theme["warning"]}; }}
        .gauge-footer {{
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px dashed {theme["border"]}44;
            color: #666666;
            font-size: 10px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="gauge-container">
        <div class="gauge-header">
            <span style="color: {theme["warning"]};">╔═══════════════════════════════════════════════╗</span><br>
            <span style="color: {theme["accent"]};">║</span>
            <span style="color: #ffffff; font-weight: bold;"> ◉ KUCOIN TRADING TERMINAL v2.0 ◉ </span>
            <span style="color: {theme["accent"]};">║</span><br>
            <span style="color: {theme["warning"]};">╚═══════════════════════════════════════════════╝</span>
        </div>
        
        <div class="gauge-content" id="gaugeContent">
            <pre class="border-char">┌──────────────────────────────────────────────┐</pre>
            <pre class="label">│ <span id="loading">Carregando dados...</span></pre>
            <pre class="border-char">└──────────────────────────────────────────────┘</pre>
        </div>
    </div>
    
    <script>
        const botId = "{bot_id}";
        const targetPct = {target_pct};
        const apiUrl = window.location.protocol + "//" + window.location.hostname + ":{api_port}/api/logs?bot=" + encodeURIComponent(botId) + "&limit=15";
        
        function parseNumber(val) {{
            const n = parseFloat(val);
            return isNaN(n) ? 0 : n;
        }}
        
        function formatPrice(p) {{
            return "$" + p.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}
        
        function makeBar(progress, width) {{
            const filled = Math.floor(width * progress / 100);
            return "█".repeat(filled) + "░".repeat(width - filled);
        }}
        
        function renderGauge(data) {{
            let currentPrice = 0, entryPrice = 0, symbol = "BTC-USDT", cycle = 0;
            let executed = "0/0", mode = "---", lastEvent = "AGUARDANDO";
            
            // Parse logs mais recentes
            for (const log of data) {{
                try {{
                    const parsed = JSON.parse(log.message || "{{}}");
                    if (parsed.price) currentPrice = parseNumber(parsed.price);
                    if (parsed.entry_price) entryPrice = parseNumber(parsed.entry_price);
                    if (parsed.symbol) symbol = parsed.symbol;
                    if (parsed.cycle) cycle = parseInt(parsed.cycle) || 0;
                    if (parsed.executed) executed = parsed.executed;
                    if (parsed.mode) mode = parsed.mode.toUpperCase();
                    if (parsed.event) lastEvent = parsed.event.toUpperCase().replace(/_/g, " ");
                }} catch(e) {{}}
            }}
            
            // Calcular P&L
            let profitPct = 0;
            if (entryPrice > 0 && currentPrice > 0) {{
                profitPct = ((currentPrice - entryPrice) / entryPrice) * 100;
            }}
            
            // Progress para o target
            const progress = Math.min(100, Math.max(0, targetPct > 0 ? (profitPct / targetPct) * 100 : 0));
            const bar = makeBar(progress, 40);
            
            // Cores e status
            let pnlClass = "profit-neutral";
            let status = "NEUTRO";
            if (profitPct >= targetPct) {{
                pnlClass = "profit-positive";
                status = "TARGET ATINGIDO";
            }} else if (profitPct > 0) {{
                pnlClass = "highlight";
                status = "EM LUCRO";
            }} else if (profitPct < -1) {{
                pnlClass = "profit-negative";
                status = "PREJUIZO";
            }}
            
            const now = new Date().toLocaleString('pt-BR');
            const botIdShort = botId.substring(0, 16).padEnd(16, ' ');
            
            document.getElementById("gaugeContent").innerHTML = `
<pre class="border-char">┌──────────────────────────────────────────────┐</pre>
<pre class="label">│ BOT: <span class="value">${{botIdShort}}</span>                       │</pre>
<pre class="label">│ SYM: <span class="highlight">${{symbol.padEnd(12, ' ')}}</span> MODE: <span style="color: {theme["warning"]};">${{mode.padEnd(6, ' ')}}</span>         │</pre>
<pre class="border-char">├──────────────────────────────────────────────┤</pre>
<pre class="label">│ ENTRY.....: <span class="value">${{formatPrice(entryPrice).padStart(12, ' ')}}</span>                │</pre>
<pre class="label">│ CURRENT...: <span class="highlight">${{formatPrice(currentPrice).padStart(12, ' ')}}</span>                │</pre>
<pre class="border-char">├──────────────────────────────────────────────┤</pre>
<pre class="label">│ P&L STATUS: <span class="${{pnlClass}}">${{status.padEnd(16, ' ')}}</span>              │</pre>
<pre class="label">│ PROFIT: <span class="${{pnlClass}}">${{profitPct >= 0 ? '+' : ''}}${{profitPct.toFixed(4).padStart(9, ' ')}}%</span>                      │</pre>
<pre class="label">│ TARGET: <span style="color: {theme["warning"]};">${{targetPct.toFixed(2).padStart(10, ' ')}}%</span>                      │</pre>
<pre class="border-char">├──────────────────────────────────────────────┤</pre>
<pre class="label">│ PROGRESS TO TARGET:                          │</pre>
<pre class="label">│ <span class="${{pnlClass}}">${{bar}}</span>   │</pre>
<pre class="label">│ <span class="value">${{progress.toFixed(1).padStart(6, ' ')}}%</span> COMPLETE                          │</pre>
<pre class="border-char">├──────────────────────────────────────────────┤</pre>
<pre class="label">│ CYCLE: <span class="highlight">${{String(cycle).padStart(6, ' ')}}</span>  EXEC: <span class="value">${{executed.padEnd(8, ' ')}}</span>          │</pre>
<pre class="label">│ EVENT: <span style="color: {theme["warning"]};">${{lastEvent.substring(0,20).padEnd(20, ' ')}}</span>              │</pre>
<pre class="border-char">└──────────────────────────────────────────────┘</pre>
<div class="gauge-footer">
    <span style="color: {theme["text"]};">●</span> ONLINE | 
    <span style="color: #aaaaaa;">${{now}}</span> |
    <span style="color: {theme["text"]};">◄</span> AUTO-REFRESH 2s
</div>
            `;
        }}
        
        async function fetchAndRender() {{
            try {{
                const resp = await fetch(apiUrl, {{ cache: "no-store" }});
                if (!resp.ok) return;
                const data = await resp.json();
                renderGauge(data);
            }} catch (e) {{
                console.error("Gauge fetch error:", e);
            }}
        }}
        
        // Inicia polling
        fetchAndRender();
        setInterval(fetchAndRender, 2000);
    </script>
</body>
</html>
'''
    # Renderiza usando components.html 
    components.html(gauge_html, height=400, scrolling=False)


def render_realtime_terminal(bot_id: str, api_port: int = 8765, height: int = 400, poll_ms: int = 2000):
    """
    Terminal de logs em tempo real com polling da API.
    Estilo combina com tema selecionado e mantém boa legibilidade.
    """
    theme = get_current_theme()
    
    html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            background: {theme["bg"]};
            font-family: 'Courier New', 'Lucida Console', monospace;
            padding: 0;
            margin: 0;
        }}
        
        .terminal {{
            background: {theme["bg2"]};
            border: 2px solid {theme["border"]};
            border-radius: 8px;
            overflow: hidden;
            height: {height}px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 0 20px {theme["glow"]}, inset 0 0 30px rgba(0,0,0,0.5);
        }}
        
        .header {{
            background: {theme["header_bg"]};
            padding: 10px 15px;
            border-bottom: 1px solid {theme["border"]};
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }}
        
        .header-title {{
            color: {theme["text"]};
            font-size: 13px;
            font-weight: bold;
        }}
        
        .header-status {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
        }}
        
        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {theme["success"]};
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .status-text {{
            color: {theme["text2"]};
        }}
        
        .content {{
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            font-size: 13px;
            line-height: 1.6;
        }}
        
        .log-line {{
            padding: 6px 10px;
            margin: 3px 0;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            word-wrap: break-word;
            white-space: pre-wrap;
        }}
        
        .log-info {{
            background: {theme["bg"]};
            color: {theme["text2"]};
            border-left: 3px solid {theme["accent"]};
        }}
        
        .log-success {{
            background: {theme["bg"]};
            color: {theme["success"]};
            border-left: 3px solid {theme["success"]};
            font-weight: bold;
        }}
        
        .log-warning {{
            background: {theme["bg"]};
            color: {theme["warning"]};
            border-left: 3px solid {theme["warning"]};
        }}
        
        .log-error {{
            background: {theme["bg"]};
            color: {theme["error"]};
            border-left: 3px solid {theme["error"]};
            font-weight: bold;
        }}
        
        .log-trade {{
            background: {theme["bg"]};
            color: {theme["accent"]};
            border-left: 3px solid {theme["text"]};
        }}
        
        .log-neutral {{
            background: {theme["bg"]};
            color: {theme["text2"]};
            border-left: 3px solid {theme["border"]}44;
        }}
        
        .log-level {{
            font-weight: bold;
            margin-right: 8px;
        }}
        
        .log-time {{
            color: {theme["text2"]}88;
            font-size: 11px;
            margin-right: 8px;
        }}
        
        .empty-state {{
            text-align: center;
            color: {theme["text2"]};
            padding: 40px;
            opacity: 0.7;
        }}
        
        .footer {{
            background: {theme["bg"]};
            padding: 8px 15px;
            border-top: 1px solid {theme["border"]}44;
            font-size: 10px;
            color: {theme["text2"]}88;
            display: flex;
            justify-content: space-between;
            flex-shrink: 0;
        }}
        
        /* Scrollbar */
        .content::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .content::-webkit-scrollbar-track {{
            background: {theme["bg"]};
        }}
        
        .content::-webkit-scrollbar-thumb {{
            background: {theme["border"]};
            border-radius: 4px;
        }}
        
        .content::-webkit-scrollbar-thumb:hover {{
            background: {theme["accent"]};
        }}
    </style>
</head>
<body>
    <div class="terminal">
        <div class="header">
            <span class="header-title">◉ LOG TERMINAL — {bot_id[:12]}...</span>
            <div class="header-status">
                <div class="status-dot"></div>
                <span class="status-text">POLLING</span>
            </div>
        </div>
        
        <div class="content" id="logContent">
            <div class="empty-state">Conectando ao servidor de logs...</div>
        </div>
        
        <div class="footer">
            <span id="logCount">0 logs</span>
            <span id="lastUpdate">--:--:--</span>
        </div>
    </div>
    
    <script>
        const botId = "{bot_id}";
        const apiUrl = window.location.protocol + "//" + window.location.hostname + ":{api_port}/api/logs?bot=" + encodeURIComponent(botId) + "&limit=30";
        const container = document.getElementById("logContent");
        const logCountEl = document.getElementById("logCount");
        const lastUpdateEl = document.getElementById("lastUpdate");
        let lastHash = "";
        
        function getLogClass(level, message) {{
            const upper = (level + " " + message).toUpperCase();
            
            if (upper.includes("ERROR") || upper.includes("ERRO") || upper.includes("EXCEPTION") || upper.includes("❌")) {{
                return "log-error";
            }}
            if (upper.includes("PROFIT") || upper.includes("LUCRO") || upper.includes("SUCCESS") || upper.includes("✅") || upper.includes("TARGET")) {{
                return "log-success";
            }}
            if (upper.includes("WARNING") || upper.includes("AVISO") || upper.includes("⚠")) {{
                return "log-warning";
            }}
            if (upper.includes("TRADE") || upper.includes("ORDER") || upper.includes("BUY") || upper.includes("SELL") || upper.includes("COMPRA") || upper.includes("VENDA")) {{
                return "log-trade";
            }}
            if (upper.includes("INFO") || upper.includes("INICIADO") || upper.includes("BOT")) {{
                return "log-info";
            }}
            return "log-neutral";
        }}
        
        function formatMessage(msg) {{
            // Tenta parsear JSON para exibir de forma mais legível
            try {{
                const data = JSON.parse(msg);
                // Formata campos importantes
                let parts = [];
                if (data.event) parts.push("EVENT: " + data.event);
                if (data.price) parts.push("PRICE: $" + parseFloat(data.price).toLocaleString('en-US', {{minimumFractionDigits: 2}}));
                if (data.cycle) parts.push("CYCLE: " + data.cycle);
                if (data.executed) parts.push("EXEC: " + data.executed);
                if (data.message) parts.push(data.message);
                if (data.symbol) parts.push("SYM: " + data.symbol);
                if (data.mode) parts.push("MODE: " + data.mode);
                if (data.entry_price) parts.push("ENTRY: $" + parseFloat(data.entry_price).toLocaleString('en-US', {{minimumFractionDigits: 2}}));
                
                return parts.length > 0 ? parts.join(" | ") : msg;
            }} catch (e) {{
                return msg;
            }}
        }}
        
        function renderLogs(logs) {{
            const hash = JSON.stringify(logs);
            if (hash === lastHash) return;
            lastHash = hash;
            
            container.innerHTML = "";
            
            if (!logs || logs.length === 0) {{
                container.innerHTML = '<div class="empty-state">Aguardando logs do bot...</div>';
                logCountEl.textContent = "0 logs";
                return;
            }}
            
            logs.forEach(log => {{
                const div = document.createElement("div");
                const logClass = getLogClass(log.level || "INFO", log.message || "");
                div.className = "log-line " + logClass;
                
                const level = log.level || "INFO";
                const message = formatMessage(log.message || "");
                
                div.innerHTML = '<span class="log-level">[' + level + ']</span>' + message;
                container.appendChild(div);
            }});
            
            container.scrollTop = container.scrollHeight;
            logCountEl.textContent = logs.length + " logs";
            
            const now = new Date();
            lastUpdateEl.textContent = now.toLocaleTimeString('pt-BR');
        }}
        
        async function fetchLogs() {{
            try {{
                const response = await fetch(apiUrl, {{ cache: "no-store" }});
                if (!response.ok) {{
                    console.error("API error:", response.status);
                    return;
                }}
                const logs = await response.json();
                renderLogs(logs);
            }} catch (error) {{
                console.error("Fetch error:", error);
            }}
        }}
        
        // Inicia polling
        fetchLogs();
        setInterval(fetchLogs, {poll_ms});
    </script>
</body>
</html>
'''
    
    components.html(html_content, height=height + 20, scrolling=False)


def colorize_logs_html(log_text: str) -> str:
    """Gera HTML com texto colorido em fundo preto. Boa legibilidade."""
    theme = get_current_theme()
    lines = log_text.split("\n")
    html_lines = []

    # Fundo sempre escuro para boa legibilidade
    bg = "#0a0a0a"

    for line in lines:
        if not line.strip():
            html_lines.append("<div style='height:4px'>&nbsp;</div>")
            continue

        safe = html.escape(line)
        upper_line = line.upper()

        # Defaults - texto claro
        fg = "#cccccc"
        weight = "400"
        border_color = "#333333"

        if any(word in upper_line for word in ['ERROR', 'ERRO', 'EXCEPTION', 'TRACEBACK', '❌']):
            fg, weight, border_color = "#ff6b6b", "700", "#ff6b6b"  # Vermelho claro
        elif any(word in upper_line for word in ['LOSS', 'PREJUÍZO', 'STOP LOSS', '❌ LOSS']):
            fg, weight, border_color = "#ff6b6b", "700", "#ff6b6b"  # Vermelho claro
        elif any(word in upper_line for word in ['PROFIT', 'LUCRO', 'GANHO', 'TARGET', '✅', 'SUCCESS']):
            fg, weight, border_color = "#4ade80", "700", "#4ade80"  # Verde claro
        elif any(word in upper_line for word in ['WARNING', 'AVISO', '⚠️', 'WARN']):
            fg, weight, border_color = "#fbbf24", "600", "#fbbf24"  # Amarelo
        elif any(word in upper_line for word in ['TRADE', 'ORDER', 'BUY', 'SELL', 'ORDEM', 'COMPRA', 'VENDA']):
            fg, weight, border_color = "#60a5fa", "600", "#60a5fa"  # Azul claro
        elif any(word in upper_line for word in ['INFO', 'CONECTADO', 'INICIADO', 'BOT', 'INICIANDO']):
            fg, weight, border_color = "#22d3ee", "500", "#22d3ee"  # Cyan

        style = (
            f"background:{bg}; color:{fg}; padding:6px 10px; margin:3px 0; "
            f"border-radius:4px; font-family:'Courier New',monospace; font-size:13px; "
            f"font-weight:{weight}; white-space:pre-wrap; border-left: 3px solid {border_color};"
        )
        html_lines.append(f"<div style=\"{style}\">{safe}</div>")

    return "".join(html_lines)


def render_bot_control():
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
    render_theme_selector()

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
