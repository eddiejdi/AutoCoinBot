# ui_components/dashboard.py
"""Widgets de dashboard: cards de resumo, estatísticas, overview de bots."""

import time
import streamlit as st
from .theme import get_current_theme
from .utils import _fmt_ts, _safe_float


def render_bot_overview_card(
    bot_id: str,
    symbol: str,
    status: str,
    mode: str,
    profit: float = 0.0,
    trades: int = 0,
    is_dry: bool = False
) -> None:
    """Renderiza card de overview de um bot.
    
    Args:
        bot_id: ID do bot
        symbol: Par de trading (ex: BTC-USDT)
        status: Status atual (running, stopped, etc)
        mode: Modo do bot (sell, buy, mixed, flow)
        profit: Lucro acumulado em USDT
        trades: Número de trades executados
        is_dry: Se é dry-run
    """
    theme = get_current_theme()
    
    # Cor do status
    if status.lower() == "running":
        status_color = theme.get("success", "#00ff88")
        status_icon = "🟢"
    elif status.lower() == "stopped":
        status_color = theme.get("error", "#ff4444")
        status_icon = "🔴"
    else:
        status_color = theme.get("warning", "#ffaa00")
        status_icon = "🟡"
    
    # Cor do profit
    profit_color = theme.get("success", "#00ff88") if profit >= 0 else theme.get("error", "#ff4444")
    
    # Badge dry-run
    dry_badge = '<span style="background: #444; color: #ffd; padding: 2px 6px; border-radius: 3px; font-size: 9px; margin-left: 8px;">DRY</span>' if is_dry else ""
    
    html = f'''
    <div style="font-family: 'Courier New', monospace; background: {theme.get('bg2', '#111')};
                border: 1px solid {theme.get('border', '#333')}; border-radius: 8px;
                padding: 16px; margin: 8px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div>
                <span style="color: {theme.get('text', '#fff')}; font-weight: bold; font-size: 14px;">
                    {bot_id[:16]}
                </span>
                {dry_badge}
            </div>
            <div style="display: flex; align-items: center; gap: 6px;">
                <span>{status_icon}</span>
                <span style="color: {status_color}; font-weight: bold; font-size: 12px;">{status.upper()}</span>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
            <div>
                <span style="color: {theme.get('text2', '#888')};">Symbol:</span>
                <span style="color: {theme.get('accent', '#00ffff')}; margin-left: 4px;">{symbol}</span>
            </div>
            <div>
                <span style="color: {theme.get('text2', '#888')};">Mode:</span>
                <span style="color: {theme.get('warning', '#ffaa00')}; margin-left: 4px;">{mode.upper()}</span>
            </div>
            <div>
                <span style="color: {theme.get('text2', '#888')};">Profit:</span>
                <span style="color: {profit_color}; margin-left: 4px; font-weight: bold;">${profit:,.4f}</span>
            </div>
            <div>
                <span style="color: {theme.get('text2', '#888')};">Trades:</span>
                <span style="color: {theme.get('text', '#fff')}; margin-left: 4px;">{trades}</span>
            </div>
        </div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_summary_stats(
    total_bots: int,
    active_bots: int,
    total_profit: float,
    total_trades: int,
    win_rate: float | None = None
) -> None:
    """Renderiza estatísticas resumidas do sistema.
    
    Args:
        total_bots: Total de bots registrados
        active_bots: Bots atualmente rodando
        total_profit: Lucro total em USDT
        total_trades: Total de trades executados
        win_rate: Taxa de acerto (0-100), opcional
    """
    theme = get_current_theme()
    
    profit_color = theme.get("success", "#00ff88") if total_profit >= 0 else theme.get("error", "#ff4444")
    
    # Win rate HTML
    win_html = ""
    if win_rate is not None:
        wr_color = theme.get("success", "#00ff88") if win_rate >= 50 else theme.get("error", "#ff4444")
        win_html = f'''
        <div style="text-align: center;">
            <div style="color: {theme.get('text2', '#888')}; font-size: 10px; text-transform: uppercase;">Win Rate</div>
            <div style="color: {wr_color}; font-size: 20px; font-weight: bold;">{win_rate:.1f}%</div>
        </div>
        '''
    
    html = f'''
    <div style="font-family: 'Courier New', monospace; background: {theme.get('bg2', '#111')};
                border: 2px solid {theme.get('border', '#333')}; border-radius: 10px;
                padding: 20px; margin: 16px 0;">
        <div style="text-align: center; margin-bottom: 16px; padding-bottom: 12px; 
                    border-bottom: 1px solid {theme.get('border', '#333')};">
            <span style="color: {theme.get('accent', '#00ffff')}; font-weight: bold; font-size: 14px;">
                📊 DASHBOARD SUMMARY
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 16px;">
            <div style="text-align: center;">
                <div style="color: {theme.get('text2', '#888')}; font-size: 10px; text-transform: uppercase;">Total Bots</div>
                <div style="color: {theme.get('text', '#fff')}; font-size: 24px; font-weight: bold;">{total_bots}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: {theme.get('text2', '#888')}; font-size: 10px; text-transform: uppercase;">Active</div>
                <div style="color: {theme.get('success', '#00ff88')}; font-size: 24px; font-weight: bold;">{active_bots}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: {theme.get('text2', '#888')}; font-size: 10px; text-transform: uppercase;">Total Profit</div>
                <div style="color: {profit_color}; font-size: 20px; font-weight: bold;">${total_profit:,.2f}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: {theme.get('text2', '#888')}; font-size: 10px; text-transform: uppercase;">Trades</div>
                <div style="color: {theme.get('text', '#fff')}; font-size: 24px; font-weight: bold;">{total_trades}</div>
            </div>
            {win_html}
        </div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_recent_trades_table(
    trades: list[dict],
    max_rows: int = 10
) -> None:
    """Renderiza tabela de trades recentes estilizada.
    
    Args:
        trades: Lista de dicts com keys: timestamp, symbol, side, price, size, profit
        max_rows: Máximo de linhas a exibir
    """
    theme = get_current_theme()
    
    if not trades:
        st.info("Nenhum trade registrado ainda.")
        return
    
    rows_html = []
    for trade in trades[:max_rows]:
        ts = _fmt_ts(trade.get("timestamp"))
        symbol = trade.get("symbol", "")
        side = str(trade.get("side", "")).upper()
        price = _safe_float(trade.get("price"))
        size = _safe_float(trade.get("size"))
        profit = _safe_float(trade.get("profit"))
        
        # Cor do side
        side_color = theme.get("success", "#00ff88") if side == "BUY" else theme.get("error", "#ff4444")
        
        # Cor do profit
        profit_color = theme.get("success", "#00ff88") if profit >= 0 else theme.get("error", "#ff4444")
        
        rows_html.append(f'''
        <tr style="border-bottom: 1px solid #222;">
            <td style="padding: 8px; color: {theme.get('text2', '#888')};">{ts}</td>
            <td style="padding: 8px; color: {theme.get('accent', '#00ffff')};">{symbol}</td>
            <td style="padding: 8px; color: {side_color}; font-weight: bold;">{side}</td>
            <td style="padding: 8px; color: {theme.get('text', '#fff')};">${price:,.2f}</td>
            <td style="padding: 8px; color: {theme.get('text', '#fff')};">{size:.6f}</td>
            <td style="padding: 8px; color: {profit_color}; font-weight: bold;">${profit:,.4f}</td>
        </tr>
        ''')
    
    html = f'''
    <div style="font-family: 'Courier New', monospace; overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; background: {theme.get('bg2', '#111')};
                      border: 1px solid {theme.get('border', '#333')}; border-radius: 6px;">
            <thead>
                <tr style="background: {theme.get('header_bg', '#1a1a1a')}; border-bottom: 2px solid {theme.get('border', '#333')};">
                    <th style="padding: 10px; text-align: left; color: {theme.get('accent', '#00ffff')}; font-size: 11px;">TIME</th>
                    <th style="padding: 10px; text-align: left; color: {theme.get('accent', '#00ffff')}; font-size: 11px;">SYMBOL</th>
                    <th style="padding: 10px; text-align: left; color: {theme.get('accent', '#00ffff')}; font-size: 11px;">SIDE</th>
                    <th style="padding: 10px; text-align: left; color: {theme.get('accent', '#00ffff')}; font-size: 11px;">PRICE</th>
                    <th style="padding: 10px; text-align: left; color: {theme.get('accent', '#00ffff')}; font-size: 11px;">SIZE</th>
                    <th style="padding: 10px; text-align: left; color: {theme.get('accent', '#00ffff')}; font-size: 11px;">PROFIT</th>
                </tr>
            </thead>
            <tbody style="font-size: 12px;">
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_eternal_mode_status(
    bot_id: str,
    run_number: int,
    total_cycles: int,
    total_profit: float,
    current_status: str = "running"
) -> None:
    """Renderiza status do Eternal Mode de um bot.
    
    Args:
        bot_id: ID do bot
        run_number: Número do ciclo atual
        total_cycles: Total de ciclos completados
        total_profit: Lucro acumulado de todos os ciclos
        current_status: Status atual do ciclo
    """
    theme = get_current_theme()
    
    profit_color = theme.get("success", "#00ff88") if total_profit >= 0 else theme.get("error", "#ff4444")
    status_color = theme.get("success", "#00ff88") if current_status == "running" else theme.get("warning", "#ffaa00")
    
    html = f'''
    <div style="font-family: 'Courier New', monospace; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 2px solid {theme.get('accent', '#00ffff')}; border-radius: 10px;
                padding: 16px; margin: 12px 0;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="font-size: 20px;">🔄</span>
            <span style="color: {theme.get('accent', '#00ffff')}; font-weight: bold; font-size: 14px;">
                ETERNAL MODE
            </span>
            <span style="color: {status_color}; font-size: 12px; margin-left: auto;">
                ● {current_status.upper()}
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; text-align: center;">
            <div>
                <div style="color: {theme.get('text2', '#888')}; font-size: 10px;">CICLO ATUAL</div>
                <div style="color: {theme.get('warning', '#ffaa00')}; font-size: 18px; font-weight: bold;">#{run_number}</div>
            </div>
            <div>
                <div style="color: {theme.get('text2', '#888')}; font-size: 10px;">TOTAL CICLOS</div>
                <div style="color: {theme.get('text', '#fff')}; font-size: 18px; font-weight: bold;">{total_cycles}</div>
            </div>
            <div>
                <div style="color: {theme.get('text2', '#888')}; font-size: 10px;">PROFIT TOTAL</div>
                <div style="color: {profit_color}; font-size: 18px; font-weight: bold;">${total_profit:,.2f}</div>
            </div>
        </div>
        
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #333;
                    color: {theme.get('text2', '#666')}; font-size: 10px; text-align: center;">
            Bot reinicia automaticamente após cada target atingido
        </div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


__all__ = [
    "render_bot_overview_card",
    "render_summary_stats",
    "render_recent_trades_table",
    "render_eternal_mode_status",
]
