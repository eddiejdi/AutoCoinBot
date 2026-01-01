# ui_components/theme.py
"""Gerenciamento de temas e CSS global da UI."""

import json
import hashlib
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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
    "Super Mario World": {
        "name": "Super Mario World",
        "bg": "#5c94fc",
        "bg2": "#4a7acc",
        "border": "#e52521",
        "text": "#ffffff",
        "text2": "#1a1a1a",
        "accent": "#43b047",
        "warning": "#fbd000",
        "error": "#e52521",
        "success": "#43b047",
        "header_bg": "linear-gradient(180deg, #5c94fc 0%, #3878d8 100%)",
        "glow": "rgba(251, 208, 0, 0.5)",
        "is_light": True,
    },
}


def get_current_theme() -> dict:
    """Retorna o tema atual selecionado."""
    theme_name = st.session_state.get("terminal_theme", "COBOL Verde")
    return THEMES.get(theme_name, THEMES["COBOL Verde"])


def _theme_config_path() -> Path:
    return ROOT / ".last_theme.json"


def _load_saved_theme() -> str | None:
    """Carrega o tema salvo do disco."""
    try:
        p = _theme_config_path()
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8") or "{}")
        name = data.get("terminal_theme")
        if name and name in THEMES:
            return name
    except Exception:
        pass
    return None


def _save_theme(name: str) -> None:
    """Salva o tema no disco."""
    try:
        p = _theme_config_path()
        p.write_text(json.dumps({"terminal_theme": name}), encoding="utf-8")
    except Exception:
        pass


def _contrast_text_for_bg(bg: str, light: str = "#ffffff", dark: str = "#000000") -> str:
    """Escolhe uma cor de texto legível (clara/escura) para um fundo hex."""
    try:
        s = str(bg or "").strip()
        if not s.startswith("#"):
            return light
        h = s[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        if len(h) != 6:
            return light
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
        return dark if lum > 0.6 else light
    except Exception:
        return light


# Ensure session state has the saved theme on first run of a session
try:
    if "terminal_theme" not in st.session_state:
        saved = _load_saved_theme()
        if saved:
            st.session_state["terminal_theme"] = saved
        else:
            st.session_state.setdefault("terminal_theme", "COBOL Verde")
except Exception:
    pass


def inject_global_css():
    """Injeta CSS global para estilizar toda a página no tema terminal."""
    theme = get_current_theme()
    is_light_theme = theme.get("is_light", False)

    btn_text = _contrast_text_for_bg(theme.get("border"), light="#ffffff", dark="#000000")
    btn_hover_text = _contrast_text_for_bg(theme.get("accent"), light="#ffffff", dark="#000000")
    btn_primary_text = _contrast_text_for_bg(theme.get("success"), light="#ffffff", dark="#000000")
    
    input_text_color = "#1a1a1a" if is_light_theme else theme["text"]
    input_bg_color = "#ffffff" if is_light_theme else theme["bg2"]
    label_color = "#1a1a1a" if is_light_theme else theme["text2"]
    
    crt_effect = "" if is_light_theme else f'''
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
        @keyframes flicker {{
            0% {{ opacity: 0.97; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.98; }}
        }}
        .stApp {{
            animation: flicker 0.15s infinite;
        }}
    '''
    
    css = f'''
    <style>
        {crt_effect}
        
        .stApp {{
            background-color: {theme["bg"]} !important;
            color: {theme["text"]} !important;
            font-family: 'Courier New', 'IBM Plex Mono', monospace !important;
        }}
        
        .stMarkdown, .stText, p, span, div {{
            color: {theme["text"]} !important;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: {theme["text"]} !important;
            text-shadow: 0 0 10px {theme["glow"]};
        }}
        
        .stButton button {{
            background-color: transparent !important;
            color: {btn_text} !important;
            border: 2px solid {theme["border"]} !important;
            font-family: 'Courier New', monospace !important;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: all 0.3s ease;
        }}
        
        .stButton button:hover {{
            background-color: {theme["accent"]} !important;
            color: {btn_hover_text} !important;
            box-shadow: 0 0 20px {theme["glow"]};
        }}
        
        .stButton button[kind="primary"] {{
            background-color: {theme["success"]} !important;
            color: {btn_primary_text} !important;
        }}
        
        .stTextInput input, .stNumberInput input, .stSelectbox select {{
            background-color: {input_bg_color} !important;
            color: {input_text_color} !important;
            border: 2px solid {theme["border"]} !important;
            font-family: 'Courier New', monospace !important;
        }}
        
        .stTextInput label, .stNumberInput label, .stSelectbox label {{
            color: {label_color} !important;
        }}
        
        .stSidebar {{
            background-color: {theme["bg2"]} !important;
            border-right: 2px solid {theme["border"]} !important;
        }}
        
        .stProgress > div > div {{
            background-color: {theme["success"]} !important;
        }}
        
        .stAlert {{
            background-color: {theme["bg2"]} !important;
            border: 1px solid {theme["border"]} !important;
        }}
        
        code {{
            background-color: {theme["bg2"]} !important;
            color: {theme["accent"]} !important;
            border: 1px solid {theme["border"]} !important;
        }}
        
        .stDataFrame {{
            background-color: {theme["bg"]} !important;
            color: {theme["text"]} !important;
        }}
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)


def render_theme_selector(ui=None):
    """Renderiza seletor de tema."""
    if ui is None and not st.session_state.get("_allow_inline_theme_selector", False):
        return

    def _render_body():
        st.markdown("---")
        st.markdown("### 🎨 Tema do Terminal")

        current_theme = st.session_state.get("terminal_theme", "COBOL Verde")
        theme_keys = list(THEMES.keys())
        try:
            idx = theme_keys.index(current_theme)
        except Exception:
            idx = 0

        new_theme = st.selectbox(
            "Selecione o tema:",
            theme_keys,
            index=idx,
            key="theme_selector_widget",
        )

        if new_theme != current_theme:
            st.session_state["terminal_theme"] = new_theme
            _save_theme(new_theme)
            st.rerun()

        theme = THEMES[new_theme]
        preview_html = f'''
        <div style="
            background: {theme['bg']};
            border: 2px solid {theme['border']};
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
        ">
            <div style="color: {theme['text']}; margin-bottom: 10px;">
                > SISTEMA PRONTO_
            </div>
            <div style="color: {theme['text2']}; font-size: 12px;">
                Texto secundário
            </div>
            <div style="color: {theme['accent']}; margin-top: 5px;">
                [DESTAQUE]
            </div>
            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <span style="color: {theme['success']};">● OK</span>
                <span style="color: {theme['warning']};">● ALERTA</span>
                <span style="color: {theme['error']};">● ERRO</span>
            </div>
        </div>
        '''
        st.markdown(preview_html, unsafe_allow_html=True)

    if ui is not None:
        with ui:
            _render_body()
    else:
        _render_body()


def render_html_smooth(html_content: str, height: int, key: str = None):
    """Renderiza HTML sem piscar usando CSS anti-flicker."""
    if key is None:
        content_hash = hashlib.md5(html_content.encode()).hexdigest()[:12]
        key = f"html_{content_hash}"
    
    cache_key = f"html_cache_{key}"
    cached_hash = st.session_state.get(cache_key, "")
    current_hash = hashlib.md5(html_content.encode()).hexdigest()
    
    if cached_hash == current_hash:
        return
    
    st.session_state[cache_key] = current_hash
    
    smooth_html = f'''
    <style>
        * {{
            -webkit-backface-visibility: hidden;
            backface-visibility: hidden;
            -webkit-font-smoothing: antialiased;
        }}
        html, body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: transparent !important;
        }}
        .smooth-wrapper {{
            opacity: 1;
            transform: translateZ(0);
        }}
        .content-stable {{
            contain: layout style paint;
            min-height: {height - 20}px;
            position: relative;
        }}
    </style>
    <div class="smooth-wrapper content-stable" id="wrapper_{key}">
        {html_content}
    </div>
    '''
    
    ph_key = f"placeholder_{key}"
    placeholder = st.session_state.get(ph_key)
    try:
        if placeholder is None:
            placeholder = st.empty()
            st.session_state[ph_key] = placeholder
        placeholder.html(smooth_html, height=height, scrolling=False)
    except Exception:
        try:
            components.html(smooth_html, height=height, scrolling=False)
        except Exception:
            pass
