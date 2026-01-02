# ui_components/gauges.py
"""Componentes visuais: gauges de progresso, indicadores de status."""

import streamlit as st
from .theme import get_current_theme, render_html_smooth


def render_progress_gauge(
    progress: float,
    label: str = "Progress",
    color: str | None = None,
    height: int = 60
) -> None:
    """Renderiza uma barra de progresso estilizada.
    
    Args:
        progress: Valor de 0-100
        label: Texto do label
        color: Cor da barra (usa accent do tema se None)
        height: Altura do componente em pixels
    """
    theme = get_current_theme()
    bar_color = color or theme.get("accent", "#00ffff")
    
    progress = max(0, min(100, progress))
    bar_width = 30
    filled = int(bar_width * progress / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    html = f'''
    <div style="font-family: 'Courier New', monospace; background: {theme.get('bg2', '#111')}; 
                border: 1px solid {theme.get('border', '#333')}; border-radius: 4px; padding: 8px;">
        <div style="color: {theme.get('text2', '#888')}; font-size: 11px; margin-bottom: 4px;">{label}</div>
        <div style="color: {bar_color}; font-size: 13px;">{bar} {progress:.1f}%</div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_status_indicator(
    status: str,
    active: bool = True,
    size: str = "medium"
) -> None:
    """Renderiza um indicador de status (semáforo).
    
    Args:
        status: Texto do status (ex: "RUNNING", "STOPPED")
        active: Se True, mostra como ativo (verde), senão inativo (vermelho)
        size: "small", "medium" ou "large"
    """
    theme = get_current_theme()
    
    sizes = {
        "small": {"font": "10px", "dot": "8px", "padding": "4px 8px"},
        "medium": {"font": "12px", "dot": "10px", "padding": "6px 12px"},
        "large": {"font": "14px", "dot": "12px", "padding": "8px 16px"},
    }
    s = sizes.get(size, sizes["medium"])
    
    color = theme.get("success", "#00ff88") if active else theme.get("error", "#ff4444")
    
    html = f'''
    <div style="display: inline-flex; align-items: center; gap: 6px; 
                font-family: 'Courier New', monospace; font-size: {s['font']};
                background: {theme.get('bg2', '#111')}; border: 1px solid {theme.get('border', '#333')};
                border-radius: 4px; padding: {s['padding']};">
        <span style="width: {s['dot']}; height: {s['dot']}; background: {color}; 
                     border-radius: 50%; display: inline-block;"></span>
        <span style="color: {color}; font-weight: bold;">{status}</span>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(
    label: str,
    value: str | float,
    delta: float | None = None,
    prefix: str = "",
    suffix: str = ""
) -> None:
    """Renderiza um card de métrica estilizado.
    
    Args:
        label: Nome da métrica
        value: Valor principal
        delta: Variação (positivo=verde, negativo=vermelho)
        prefix: Prefixo do valor (ex: "$")
        suffix: Sufixo do valor (ex: "%")
    """
    theme = get_current_theme()
    
    # Formatar valor
    if isinstance(value, float):
        value_str = f"{prefix}{value:,.4f}{suffix}"
    else:
        value_str = f"{prefix}{value}{suffix}"
    
    # Delta
    delta_html = ""
    if delta is not None:
        delta_color = theme.get("success", "#00ff88") if delta >= 0 else theme.get("error", "#ff4444")
        delta_sign = "+" if delta >= 0 else ""
        delta_html = f'<div style="color: {delta_color}; font-size: 11px;">{delta_sign}{delta:.2f}%</div>'
    
    html = f'''
    <div style="font-family: 'Courier New', monospace; background: {theme.get('bg2', '#111')}; 
                border: 1px solid {theme.get('border', '#333')}; border-radius: 6px; 
                padding: 12px; text-align: center;">
        <div style="color: {theme.get('text2', '#888')}; font-size: 10px; text-transform: uppercase; 
                    margin-bottom: 4px;">{label}</div>
        <div style="color: {theme.get('text', '#fff')}; font-size: 18px; font-weight: bold;">{value_str}</div>
        {delta_html}
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_pnl_badge(
    profit_pct: float,
    target_pct: float = 2.0
) -> None:
    """Renderiza badge de P&L com cor baseada no progresso.
    
    Args:
        profit_pct: Percentual de lucro/prejuízo atual
        target_pct: Meta de lucro em %
    """
    theme = get_current_theme()
    
    if profit_pct >= target_pct:
        color = theme.get("success", "#00ff88")
        status = "TARGET ✓"
    elif profit_pct > 0:
        color = theme.get("accent", "#00ffff")
        status = "PROFIT"
    elif profit_pct > -1:
        color = theme.get("warning", "#ffaa00")
        status = "NEUTRAL"
    else:
        color = theme.get("error", "#ff4444")
        status = "LOSS"
    
    html = f'''
    <div style="display: inline-flex; align-items: center; gap: 8px; 
                font-family: 'Courier New', monospace;
                background: {theme.get('bg2', '#111')}; border: 2px solid {color};
                border-radius: 6px; padding: 8px 16px;">
        <span style="color: {theme.get('text2', '#888')}; font-size: 11px;">{status}</span>
        <span style="color: {color}; font-size: 16px; font-weight: bold;">{profit_pct:+.2f}%</span>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


__all__ = [
    "render_progress_gauge",
    "render_status_indicator",
    "render_metric_card",
    "render_pnl_badge",
]
