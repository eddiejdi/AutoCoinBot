# ui_components/terminal.py
"""Componentes de terminal: logs coloridos, output formatado."""

import html
import time
import streamlit as st
from .theme import get_current_theme, render_html_smooth
from .utils import _fmt_ts


def render_log_terminal(
    logs: list[dict],
    bot_id: str,
    height: int = 400,
    auto_scroll: bool = True,
    show_header: bool = True
) -> None:
    """Renderiza terminal de logs com cores por tipo de evento.
    
    Args:
        logs: Lista de dicts com keys: timestamp, level, message
        bot_id: ID do bot para exibir no header
        height: Altura do terminal em pixels
        auto_scroll: Se True, scrolla para o final automaticamente
        show_header: Se True, mostra header com info do bot
    """
    theme = get_current_theme()
    
    if not logs:
        st.info("📭 Nenhum log disponível.")
        return
    
    log_lines = []
    for log in logs:
        try:
            ts = _fmt_ts(log.get("timestamp"))
            lvl = str(log.get("level") or "INFO").upper()
            msg = str(log.get("message") or "")
            
            # Determinar cor e ícone baseado no conteúdo
            color, icon = _get_log_style(lvl, msg, theme)
            
            # Escapar HTML
            msg_escaped = html.escape(msg)
            
            log_lines.append(
                f'<div style="color: {color}; font-family: monospace; padding: 3px 0; '
                f'border-bottom: 1px solid #222;">'
                f'{icon} <span style="color: #666;">{ts}</span> '
                f'<span style="color: {color}; font-weight: bold;">[{lvl}]</span> '
                f'{msg_escaped}</div>'
            )
        except Exception:
            continue
    
    # Header
    header_html = ""
    if show_header:
        now_str = time.strftime("%H:%M:%S")
        header_html = f'''
        <div style="color: {theme.get('accent', '#00ffff')}; font-weight: bold; 
                    margin-bottom: 10px; border-bottom: 1px solid {theme.get('border', '#333')}; 
                    padding-bottom: 5px; display: flex; justify-content: space-between;">
            <span>🖥️ Bot: {bot_id[:12]}...</span>
            <span style="color: {theme.get('success', '#00ff88')};">● LIVE {now_str}</span>
        </div>
        '''
    
    # Montar terminal
    scroll_js = """
    <script>
        var terminal = document.getElementById('log-terminal');
        if (terminal) terminal.scrollTop = terminal.scrollHeight;
    </script>
    """ if auto_scroll else ""
    
    terminal_html = f'''
    <div id="log-terminal" style="
        background: #0a0a0a;
        border: 2px solid {theme.get('border', '#333')};
        border-radius: 8px;
        padding: 15px;
        height: {height}px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        box-shadow: 0 0 20px {theme.get('glow', 'rgba(51,255,51,0.2)')};
    ">
        {header_html}
        {''.join(log_lines)}
    </div>
    {scroll_js}
    '''
    
    st.markdown(terminal_html, unsafe_allow_html=True)


def _get_log_style(level: str, message: str, theme: dict) -> tuple[str, str]:
    """Retorna (cor, ícone) baseado no level/conteúdo do log."""
    msg_lower = message.lower()
    
    # Por level
    if level == "ERROR" or "error" in msg_lower or "❌" in message:
        return theme.get("error", "#ff4444"), "❌"
    if level == "WARNING" or "warning" in msg_lower or "⚠️" in message:
        return theme.get("warning", "#ffaa00"), "⚠️"
    
    # Por conteúdo
    if any(w in msg_lower for w in ["buy", "compra", "bought"]):
        return theme.get("success", "#00ff88"), "🟢"
    if any(w in msg_lower for w in ["sell", "venda", "sold"]):
        return "#ff6666", "🔴"
    if any(w in msg_lower for w in ["profit", "lucro", "ganho"]):
        return "#00ffff", "💰"
    if any(w in msg_lower for w in ["cycle", "ciclo"]):
        return "#aaaaaa", "🔄"
    if any(w in msg_lower for w in ["start", "iniciado", "conectado"]):
        return "#66ff66", "🚀"
    if any(w in msg_lower for w in ["stop", "encerrado", "finalizado"]):
        return "#ff9999", "🛑"
    if any(w in msg_lower for w in ["price", "preço"]):
        return "#99ccff", "📊"
    
    # Default
    return theme.get("text", "#ffffff"), "📝"


def render_command_output(
    output: str,
    title: str = "Output",
    success: bool = True
) -> None:
    """Renderiza output de comando estilo terminal.
    
    Args:
        output: Texto do output
        title: Título do bloco
        success: Se True, borda verde; se False, borda vermelha
    """
    theme = get_current_theme()
    border_color = theme.get("success", "#00ff88") if success else theme.get("error", "#ff4444")
    
    output_escaped = html.escape(output)
    
    html_content = f'''
    <div style="font-family: 'Courier New', monospace; background: #0a0a0a;
                border: 2px solid {border_color}; border-radius: 6px; margin: 10px 0;">
        <div style="background: #111; padding: 8px 12px; border-bottom: 1px solid #333;
                    color: {theme.get('accent', '#00ffff')}; font-size: 12px; font-weight: bold;">
            $ {title}
        </div>
        <pre style="padding: 12px; margin: 0; color: {theme.get('text', '#fff')}; 
                    font-size: 12px; overflow-x: auto; white-space: pre-wrap;">{output_escaped}</pre>
    </div>
    '''
    st.markdown(html_content, unsafe_allow_html=True)


def render_log_legend() -> None:
    """Renderiza legenda de cores dos logs."""
    theme = get_current_theme()
    
    items = [
        ("🟢", "Compra", theme.get("success", "#00ff88")),
        ("🔴", "Venda", "#ff6666"),
        ("💰", "Lucro", "#00ffff"),
        ("⚠️", "Warning", theme.get("warning", "#ffaa00")),
        ("❌", "Erro", theme.get("error", "#ff4444")),
        ("🔄", "Ciclo", "#aaaaaa"),
    ]
    
    cols = st.columns(len(items))
    for i, (icon, label, color) in enumerate(items):
        cols[i].markdown(
            f'<span style="color: {color};">{icon} **{label}**</span>',
            unsafe_allow_html=True
        )


__all__ = [
    "render_log_terminal",
    "render_command_output",
    "render_log_legend",
]
