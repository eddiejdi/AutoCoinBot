 # ui.py
import time
import hashlib
import os
import signal
import subprocess
import shlex
import threading
import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
import html
import json
from pathlib import Path
import sys

# Ensure current directory is in sys.path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Imports dos módulos UI componentizados
from ui_components import (
    set_logged_in,
    _pid_alive,
    _kill_pid_best_effort,
    _kill_pid_sigkill_only,
    _safe_container,
    _fmt_ts,
    _safe_float,
    _contrast_text_for_bg,
    THEMES,
    get_current_theme,
    inject_global_css,
    render_theme_selector,
    render_html_smooth,
    _load_saved_theme,
    _save_theme,
    render_top_nav_bar,
    _set_view,
    _qs_get_any,
    _merge_query_params,
    _build_relative_url_with_query_updates,
    _hide_sidebar_for_fullscreen_pages,
    _hide_sidebar_everywhere,
)

# Mantém LOGIN_FILE para compatibilidade
LOGIN_FILE = os.path.join(os.path.dirname(__file__), '.login_status')

from bot_controller import BotController
from database import DatabaseManager
from sidebar_controller import SidebarController

try:
    from wallet_releases_rss import render_wallet_releases_widget
except Exception:
    render_wallet_releases_widget = None

try:
    from market import analyze_market_regime_5m
except Exception:
    analyze_market_regime_5m = None

# =====================================================
# CONTROLLER GLOBAL
# =====================================================
@st.cache_resource
def get_global_controller():
    """Retorna uma instância global do BotController (cached)"""
    return BotController()

# =====================================================
# UTILITÁRIOS
# =====================================================

try:
    from terminal_component import render_terminal as render_terminal
    from terminal_component import start_api_server as start_api_server
    HAS_TERMINAL = True
except Exception:
    HAS_TERMINAL = False


ROOT = Path(__file__).resolve().parent


@st.cache_data(ttl=20, show_spinner=False)
def _get_strategy_snapshot_cached(symbol: str):
        if not symbol or not analyze_market_regime_5m:
                return None
        try:
                return analyze_market_regime_5m(symbol)
        except Exception:
                return None


def render_strategy_semaphore(snapshot: dict, theme: dict) -> str:
        if not snapshot:
                return ""

        bias = (snapshot.get("bias") or "WAIT").upper()
        strategy = snapshot.get("strategy") or "-"
        regime = snapshot.get("regime") or "-"
        confidence = float(snapshot.get("confidence") or 0.0)

        success = theme.get("success", "#00C853")
        warning = theme.get("warning", "#FFAB00")
        error = theme.get("error", "#FF5252")
        text = theme.get("text", "#FFFFFF")
        panel = theme.get("bg2", theme.get("bg", "#0E1117"))
        border = theme.get("border", "rgba(255,255,255,0.12)")

        red_on = bias == "SELL"
        yellow_on = bias == "WAIT"
        green_on = bias == "BUY"

        def _light(color: str, on: bool) -> str:
                return (
                        f"<div style=\"width:18px;height:18px;border-radius:50%;"
                        f"background:{color};opacity:{1.0 if on else 0.22};"
                        f"box-shadow:0 0 10px {color if on else 'transparent'};\"></div>"
                )

        conf_pct = int(round(confidence * 100))
        title = f"{strategy.replace('_',' ').title()} • {regime.replace('_',' ').title()}"
        subtitle = f"Bias: {bias} • Confiança: {conf_pct}% (5m)"

        return f"""
        <div style="background:{panel};border:1px solid {border};border-radius:12px;padding:12px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="display:flex;gap:8px;align-items:center;">
                    {_light(error, red_on)}
                    {_light(warning, yellow_on)}
                    {_light(success, green_on)}
                </div>
                <div style="flex:1;">
                    <div style="color:{text};font-weight:700;font-size:14px;line-height:1.2;">{title}</div>
                    <div style="color:{text};opacity:0.85;font-size:12px;margin-top:2px;">{subtitle}</div>
                </div>
            </div>
        </div>
        """

# Streamlit creates a separate "session" per browser tab/user. Anything guarded only by
# st.session_state will run once per browser session, not once per server process.
# For kill-on-start behavior we want a single best-effort pass per server process.
_KILL_ON_START_DONE = False
_KILL_ON_START_LOCK = threading.Lock()


try:
    @st.cache_resource(show_spinner=False)
    def _KILL_ON_START_GUARD_RESOURCE():
        return {"lock": threading.Lock(), "done": False}
except Exception:
    _KILL_ON_START_GUARD_RESOURCE = None


def _get_kill_on_start_guard():
    """Return a (lock, done_flag_container) that is shared across Streamlit sessions.

    Streamlit re-executes the script for each session/tab, so plain module globals may not
    be reliable for cross-session coordination. We prefer st.cache_resource for a true
    per-server-process singleton.
    """
    try:
        if _KILL_ON_START_GUARD_RESOURCE is not None:
            return _KILL_ON_START_GUARD_RESOURCE()
    except Exception:
        pass

    # Fallback: best-effort globals (works within a single script context)
    return {"lock": _KILL_ON_START_LOCK, "done": _KILL_ON_START_DONE}

# _pid_alive, _kill_pid_best_effort, _kill_pid_sigkill_only movidos para ui_components.utils


def _confirm_pid_dead(pid: int, checks: int = 3, delay_s: float = 0.1) -> bool:
    """Confirma que um PID está realmente morto após múltiplas verificações.
    
    Args:
        pid: O ID do processo a verificar
        checks: Número de verificações a fazer
        delay_s: Intervalo entre verificações em segundos
    
    Returns:
        True se o PID estiver morto em todas as verificações, False caso contrário
    """
    for i in range(checks):
        if _pid_alive(pid):
            return False
        if i < checks - 1 and delay_s > 0:
            time.sleep(delay_s)
    return True


def _kill_active_bot_sessions_on_start(controller: BotController | None = None):
    """Kill any leftover running bot sessions when the app starts.

    Runs at most once per Streamlit *server process*.
    """
    global _KILL_ON_START_DONE

    # Guard once per server process. This prevents a new browser tab/session from
    # re-running the cleanup and killing bots started by an existing session.
    try:
        g = _get_kill_on_start_guard()
        lock = g.get("lock")
        if lock is None:
            raise RuntimeError("missing lock")
        with lock:
            if bool(g.get("done")):
                return
            g["done"] = True
            _KILL_ON_START_DONE = True
    except Exception:
        # Very last resort: per-session guard.
        try:
            if st.session_state.get("_killed_active_sessions_on_start"):
                return
            st.session_state["_killed_active_sessions_on_start"] = True
        except Exception:
            return

    killed_any = False

    # Stop any continuous-mode runners (they respawn bots when a process exits)
    try:
        try:
            BotController.stop_all_continuous()
        except Exception:
            pass

        if controller is not None:
            cont = getattr(controller, "_continuous_stop", None)
            if isinstance(cont, dict) and cont:
                for _, ev in list(cont.items()):
                    try:
                        ev.set()
                    except Exception:
                        pass
                try:
                    cont.clear()
                except Exception:
                    pass
    except Exception:
        pass

    db_sessions_by_id: dict[str, dict] = {}
    ps_pids_by_id: dict[str, int] = {}

    # 1) DB sessions
    try:
        db = DatabaseManager()
        for sess in db.get_active_bots() or []:
            bot_id = sess.get("id") or sess.get("bot_id")
            if not bot_id:
                continue
            db_sessions_by_id[str(bot_id)] = sess
    except Exception:
        db = None

    # 2) ps scan for bots
    try:
        r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, check=False)
        out = (r.stdout or "").splitlines()
        for line in out[1:]:
            line = line.strip()
            if not line:
                continue
            try:
                pid_s, args_s = line.split(None, 1)
                pid_i = int(pid_s)
            except Exception:
                continue
            if "bot_core.py" not in args_s:
                continue
            try:
                argv = shlex.split(args_s)
            except Exception:
                argv = args_s.split()
            if "--bot-id" in argv:
                try:
                    idx = argv.index("--bot-id")
                    bot_id = argv[idx + 1]
                except Exception:
                    bot_id = None
                if bot_id:
                    bot_id_s = str(bot_id)
                    # IMPORTANT: Only consider killing processes that are tracked as active
                    # sessions in the DB. This avoids the UI killing manually launched bots.
                    if bot_id_s in db_sessions_by_id:
                        ps_pids_by_id[bot_id_s] = pid_i
    except Exception:
        pass

    # Build candidates strictly from DB sessions (with ps as a fallback PID source).
    candidates: dict[str, int] = {}
    for bot_id, sess in db_sessions_by_id.items():
        pid_i: int | None = None
        try:
            pid = sess.get("pid")
            if pid is not None:
                pid_i = int(pid)
        except Exception:
            pid_i = None

        if not pid_i:
            try:
                pid_i = int(ps_pids_by_id.get(bot_id) or 0) or None
            except Exception:
                pid_i = None

        if pid_i:
            candidates[bot_id] = pid_i

    # Kill
    for bot_id, pid in list(candidates.items()):
        if not _pid_alive(pid):
            # mark stopped in DB if it was listed as active
            try:
                if db is not None and bot_id in db_sessions_by_id:
                    db.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
                    # Free any quota possibly left behind
                    try:
                        db.release_bot_quota(bot_id)
                    except Exception:
                        pass
            except Exception:
                pass
            continue

        ok = _kill_pid_best_effort(pid)
        if ok:
            killed_any = True
        # best-effort: mark stopped
        try:
            if db is not None:
                db.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
                # Free quota even if the bot was SIGKILL'ed (avoids orphan allocations)
                try:
                    db.release_bot_quota(bot_id)
                except Exception:
                    pass
        except Exception:
            pass

        # best-effort: remove from controller process map
        try:
            if controller is not None and getattr(controller, "processes", None):
                controller.processes.pop(bot_id, None)
        except Exception:
            pass

    # Also release any orphaned allocated quotas (no live PID found for that bot_id)
    try:
        if db is not None:
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT bot_id FROM bot_quotas WHERE status = 'allocated'")
            rows = cur.fetchall() or []
            conn.close()
            for (qid,) in rows:
                qid_s = str(qid)
                live_pid = None
                try:
                    sess = db_sessions_by_id.get(qid_s)
                    if sess and sess.get("pid") is not None:
                        live_pid = int(sess.get("pid"))
                except Exception:
                    live_pid = None
                # Check ps scan as fallback
                if live_pid is None:
                    try:
                        live_pid = int(ps_pids_by_id.get(qid_s) or 0) or None
                    except Exception:
                        live_pid = None
                if live_pid is not None and _pid_alive(live_pid):
                    continue
                try:
                    db.release_bot_quota(qid_s)
                except Exception:
                    pass
    except Exception:
        pass

    # Clear UI lists if anything was killed
    if killed_any:
        try:
            st.session_state.active_bots = []
            st.session_state.selected_bot = None
            st.session_state.bot_running = False
        except Exception:
            pass


def _contrast_text_for_bg(bg: str, light: str = "#ffffff", dark: str = "#000000") -> str:
    """Pick a readable text color (light/dark) for a given hex background."""
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
        # Relative luminance (sRGB)
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
        return dark if lum > 0.6 else light
    except Exception:
        return light


def _maybe_start_background_kucoin_trade_sync():
    """Sincroniza trades reais da KuCoin em background.

    - Roda no máximo 1x por sessão Streamlit.
    - Não bloqueia a UI.
    - Faz best-effort: se não houver credenciais, não faz nada.
    """
    try:
        if st.session_state.get("_kucoin_trade_sync_started"):
            return
        st.session_state["_kucoin_trade_sync_started"] = True
    except Exception:
        return

    import threading

    def _worker():
        try:
            # Import local (evita custo no caminho crítico da UI)
            try:
                import api as kucoin_api
            except Exception:
                import api as kucoin_api  # type: ignore

            # Sem credenciais? Sai silenciosamente.
            try:
                if not getattr(kucoin_api, "_has_keys", lambda: False)():
                    return
            except Exception:
                return

            now_ms = int(time.time() * 1000)
            # janela simples (últimos 90 dias) para popular o histórico
            start_ms = now_ms - (90 * 24 * 3600 * 1000)

            fills = []
            try:
                fills = kucoin_api.get_all_fills(start_at=start_ms, end_at=now_ms, page_size=200, max_pages=50)
            except Exception:
                # se falhar, não derruba a UI
                return

            if not fills:
                return

            db = DatabaseManager()
            for f in fills:
                if not isinstance(f, dict):
                    continue

                trade_id = f.get("tradeId") or f.get("id")
                order_id = f.get("orderId")
                created_at = f.get("createdAt")  # ms

                # fallback de id estável
                if not trade_id:
                    trade_id = f"kucoin_{order_id or 'no_order'}_{created_at or int(time.time()*1000)}"

                # timestamp (segundos)
                ts_s = None
                try:
                    if created_at is not None:
                        ca = float(created_at)
                        ts_s = ca / 1000.0 if ca > 1e12 else ca
                except Exception:
                    ts_s = None

                symbol = f.get("symbol")
                side = f.get("side")

                try:
                    price = float(f.get("price")) if f.get("price") is not None else None
                except Exception:
                    price = None

                try:
                    size = float(f.get("size")) if f.get("size") is not None else None
                except Exception:
                    size = None

                try:
                    funds = float(f.get("funds")) if f.get("funds") is not None else None
                except Exception:
                    funds = None

                try:
                    fee = float(f.get("fee")) if f.get("fee") is not None else None
                except Exception:
                    fee = None

                trade_data = {
                    "id": str(trade_id),
                    "timestamp": ts_s or time.time(),
                    "symbol": symbol or "",
                    "side": (side or "").lower(),
                    "price": price or 0.0,
                    "size": size,
                    "funds": funds,
                    "profit": None,
                    "commission": fee,
                    "order_id": str(order_id) if order_id is not None else None,
                    "bot_id": "KUCOIN",
                    "strategy": "kucoin_fill",
                    "dry_run": False,
                    "metadata": {"source": "kucoin", "fill": f},
                }

                db.insert_trade_ignore(trade_data)
        except Exception:
            return

    try:
        t = threading.Thread(target=_worker, name="kucoin_trade_sync", daemon=True)
        t.start()
    except Exception:
        return


def _maybe_start_background_equity_snapshot():
    """Snapshots equity (balances) em background periodicamente."""
    try:
        if st.session_state.get("_equity_snapshot_started"):
            return
        st.session_state["_equity_snapshot_started"] = True
    except Exception:
        return

    import threading

    def _worker():
        import time
        while True:
            try:
                from equity import snapshot_equity
                snapshot_equity()
            except Exception as e:
                print(f"Erro no snapshot equity: {e}")
            time.sleep(300)  # every 5 minutes

    # Schedule immediate snapshot on start in a background thread (non-blocking)
    try:
        from equity import snapshot_equity

        def _run_once_snapshot():
            try:
                snapshot_equity()
            except Exception as e:
                print(f"Erro no snapshot inicial: {e}")

        try:
            threading.Thread(target=_run_once_snapshot, name="equity_snapshot_once", daemon=True).start()
        except Exception:
            # last-resort fallback: run synchronously (should be rare)
            try:
                snapshot_equity()
            except Exception as e:
                print(f"Erro no snapshot inicial (fallback): {e}")
    except Exception as e:
        print(f"Erro ao importar snapshot_equity: {e}")

    try:
        t = threading.Thread(target=_worker, name="equity_snapshot", daemon=True)
        t.start()
    except Exception:
        return


def render_trade_report_page():
    """Página de relatório: histórico de trades (abre em nova aba via ?report=1).

    Nota: existe também a versão HTML dedicada servida em /report pelo API server local.
    """
    theme = get_current_theme()

    # Em uma nova aba, é uma nova sessão Streamlit: dispara sync em background aqui também.
    _maybe_start_background_kucoin_trade_sync()

    st.markdown(
        f"""
        <div style="text-align:center; padding: 10px 0 16px 0;">
            <div style="display:inline-block; border: 1px solid {theme['border']}; border-radius: 8px; padding: 12px 16px; background:{theme['bg2']};">
                <div style="font-family: 'Courier New', monospace; font-weight: 700; color:{theme['accent']};">📑 RELATÓRIO</div>
                <div style="font-family: 'Courier New', monospace; color:{theme['text2']}; font-size: 12px;">Histórico de Trades (SQLite)</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_trades, tab_learning = st.tabs(["Trades", "Aprendizado"])

    with tab_trades:
        bot_id_filter = _qs_get_any(st.query_params, "bot", None)
        real_q = _qs_get_any(st.query_params, "real", None)
        default_only_real = str(real_q).strip() in ("1", "true", "yes")

        only_real = st.checkbox("Somente movimentações reais (não dry-run)", value=default_only_real)

        group_q = _qs_get_any(st.query_params, "group", None)
        default_group = True
        try:
            if group_q is not None and str(group_q).strip() in ("0", "false", "no"):
                default_group = False
        except Exception:
            default_group = True

        group_by_order = st.checkbox(
            "Agrupar por order_id (dedupe fill + estratégia)",
            value=default_group,
        )

        db = DatabaseManager()
        try:
            rows = db.get_trade_history_grouped(
                limit=2000,
                bot_id=bot_id_filter,
                only_real=only_real,
                group_by_order_id=group_by_order,
            )
        except Exception as e:
            st.error(f"Erro ao carregar trades: {e}")
            rows = []

        st.caption(
            f"Mostrando até 2000 trades"
            f"{' do bot ' + str(bot_id_filter) if bot_id_filter else ''}"
            f"{' (somente reais)' if only_real else ''}"
            f" (mais recentes primeiro)."
        )

        if not rows:
            st.info("Nenhum trade encontrado no banco.")
            return

        # Formatação + destaque por cor (real efetivado vs não efetivado)
        import datetime as _dt

        formatted = []
        for r in rows:
            ts = r.get("timestamp")
            try:
                dt = _dt.datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S") if ts else ""
            except Exception:
                dt = ""

            dry_run_val = r.get("dry_run")
            try:
                is_real = int(dry_run_val) == 0
            except Exception:
                is_real = False

            order_id = r.get("order_id")
            is_executed = bool(is_real and order_id and str(order_id).strip())

            # PnL líquido (somente quando houver PnL realizado)
            net_profit = None
            try:
                p = r.get("profit")
                c = r.get("commission")
                if p is not None:
                    net_profit = float(p) - float(c or 0.0)
            except Exception:
                net_profit = None

            formatted.append({
                "datetime": dt,
                "symbol": r.get("symbol"),
                "side": r.get("side"),
                "price": r.get("price"),
                "size": r.get("size"),
                "funds": r.get("funds"),
                "profit": r.get("profit"),
                "net_profit": net_profit,
                "commission": r.get("commission"),
                "bot_id": r.get("bot_id"),
                "strategy": r.get("strategy"),
                "real": 1 if is_real else 0,
                "efetivada": 1 if is_executed else 0,
                "order_id": order_id,
                "id": r.get("id"),
            })

        # Preferir pandas para permitir coloração por linha; fallback sem estilo
        try:
            import pandas as pd  # type: ignore

            df = pd.DataFrame(formatted)

            success = theme.get("success", "#00ff88")
            warning = theme.get("warning", "#ffaa00")
            muted_bg = theme.get("bg2", "#111")
            txt = theme.get("text", "#ffffff")

            def _contrast_text(bg: str, fallback: str = "#ffffff") -> str:
                """Pick black/white for contrast against a hex background."""
                try:
                    s = str(bg).strip()
                    if not s.startswith("#"):
                        return fallback
                    h = s.lstrip("#")
                    if len(h) == 3:
                        h = "".join([c * 2 for c in h])
                    if len(h) != 6:
                        return fallback
                    r = int(h[0:2], 16)
                    g = int(h[2:4], 16)
                    b = int(h[4:6], 16)
                    lum = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                    return "#000000" if lum > 160 else "#ffffff"
                except Exception:
                    return fallback

            def _row_style(row):
                try:
                    is_real_row = int(row.get("real", 0)) == 1
                except Exception:
                    is_real_row = False
                try:
                    is_exec_row = int(row.get("efetivada", 0)) == 1
                except Exception:
                    is_exec_row = False

                if is_real_row and is_exec_row:
                    fg = _contrast_text(success, fallback="#ffffff")
                    return [f"background-color: {success}; color: {fg};"] * len(row)
                if is_real_row and not is_exec_row:
                    fg = _contrast_text(warning, fallback="#000000")
                    return [f"background-color: {warning}; color: {fg};"] * len(row)
                return [f"background-color: {muted_bg}; color: {txt};"] * len(row)

            st.dataframe(
                df.style.apply(_row_style, axis=1),
                use_container_width=True,
                hide_index=True,
            )
        except Exception:
            st.dataframe(formatted, use_container_width=True, hide_index=True)

        # Equity chart
        st.subheader("📈 Patrimônio Global")
        try:
            import pandas as pd
            import plotly.express as px
            db = DatabaseManager()
            eq_rows = db.get_equity_history(days=30)
            if eq_rows:
                df_eq = pd.DataFrame(eq_rows)
                if not df_eq.empty:
                    df_eq["timestamp"] = df_eq["timestamp"].astype(float)
                    df_eq["datetime"] = df_eq["timestamp"].apply(lambda x: _fmt_ts(x))
                    df_eq["total"] = df_eq["balance_usdt"].astype(float)
                    
                    # Plot total
                    fig = px.line(df_eq, x="datetime", y="total", title="Patrimônio Total (USDT)")
                    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # If we have per-coin data, show it
                    if 'balances' in df_eq.columns and df_eq['balances'].notna().any():
                        st.subheader("Por Moeda")
                        # For simplicity, show last snapshot
                        last_row = df_eq.iloc[-1]
                        balances = last_row.get('balances', {})
                        if balances:
                            cols = st.columns(len(balances))
                            for i, (coin, value) in enumerate(balances.items()):
                                cols[i].metric(f"{coin}", f"{value:.2f}")
            elif not eq_rows:
                st.info("Nenhum snapshot de patrimônio encontrado. Aguarde o próximo ciclo (5min).")
            else:
                st.info("Dados indisponíveis.")
        except Exception as e:
            st.error(f"Erro ao carregar gráfico: {e}")

    with tab_learning:
        db = DatabaseManager()
        symbols = []
        try:
            symbols = db.get_learning_symbols()
        except Exception:
            symbols = []

        if not symbols:
            st.info("Nenhum dado de aprendizado ainda. Inicie bots e aguarde SELLs para gerar histórico.")
            return

        sym_default = symbols[0]
        sym = st.selectbox("Símbolo", options=symbols, index=0)

        param_name = "take_profit_trailing_pct"
        st.caption("Este relatório mostra como o bot está aprendendo a escolher o trailing para sair mais alto.")

        stats = db.get_learning_stats(sym, param_name)
        hist = db.get_learning_history(sym, param_name, limit=2000)

        try:
            import pandas as pd  # type: ignore
            import plotly.express as px  # type: ignore
            import datetime as _dt

            df_stats = pd.DataFrame(stats or [])
            if not df_stats.empty:
                # Friendly formatting
                try:
                    df_stats["param_value"] = df_stats["param_value"].astype(float)
                except Exception:
                    pass
                st.subheader("Ranking de candidatos")
                st.dataframe(df_stats, use_container_width=True, hide_index=True)

                # Bar chart of mean_reward
                try:
                    fig = px.bar(df_stats.sort_values("param_value"), x="param_value", y="mean_reward", color="n",
                                 title="Média de recompensa (profit_pct) por trailing")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    pass

            df_hist = pd.DataFrame(hist or [])
            if not df_hist.empty:
                df_hist["timestamp"] = df_hist["timestamp"].apply(lambda x: float(x) if x is not None else 0.0)
                df_hist["datetime"] = df_hist["timestamp"].apply(lambda t: _dt.datetime.fromtimestamp(t))
                try:
                    df_hist["param_value"] = df_hist["param_value"].astype(float)
                    df_hist["reward"] = df_hist["reward"].astype(float)
                except Exception:
                    pass

                df_hist = df_hist.sort_values("timestamp")
                st.subheader("Evolução (recompensas)")
                try:
                    fig2 = px.scatter(df_hist, x="datetime", y="reward", color="param_value",
                                      title="Recompensas por trade (profit_pct) ao longo do tempo")
                    st.plotly_chart(fig2, use_container_width=True)
                except Exception:
                    pass

                # Cumulative mean per candidate
                try:
                    df_hist["cum_n"] = df_hist.groupby("param_value").cumcount() + 1
                    df_hist["cum_mean"] = df_hist.groupby("param_value")["reward"].expanding().mean().reset_index(level=0, drop=True)
                    fig3 = px.line(df_hist, x="datetime", y="cum_mean", color="param_value",
                                   title="Média acumulada de recompensa (por trailing)")
                    st.plotly_chart(fig3, use_container_width=True)
                except Exception:
                    pass
            else:
                st.info("Ainda não há histórico suficiente para gráficos. Aguarde novos SELLs.")
        except Exception:
            # Minimal fallback without pandas/plotly
            st.write({"stats": stats, "history": hist[:10] if isinstance(hist, list) else hist})

# _qs_get_any, _merge_query_params, _build_relative_url_with_query_updates, _set_view, _hide_sidebar_* movidos para ui_components.navigation
# _safe_container, _fmt_ts, _safe_float movidos para ui_components.utils


def _extract_latest_price_from_logs(log_rows: list[dict]) -> float | None:
    """Best-effort: parse JSON log messages to find last price."""
    if not log_rows:
        return None
    try:
        import json as _json
    except Exception:
        _json = None

    for row in log_rows:
        try:
            msg = row.get("message") if isinstance(row, dict) else None
            if not msg or not isinstance(msg, str):
                continue
            if _json is None:
                continue
            obj = _json.loads(msg)
            if not isinstance(obj, dict):
                continue
            # prefer explicit price events
            if "price" in obj:
                p = obj.get("price")
                try:
                    p = float(p)
                    if p > 0:
                        return p
                except Exception:
                    pass
        except Exception:
            continue
    return None


def render_monitor_dashboard(theme: dict, preselected_bot: str | None = None):
    """Streamlit-native monitor: multi-bot overview + per-bot performance."""
    st.header("Monitor — Painel de Performance")
    st.caption("Acompanhe rendimento, trades, status e logs dos bots (múltiplos).")

    # --- Load summary data (SQL aggregates are fast and UI-friendly)
    db = DatabaseManager()
    conn = None
    sessions: list[dict] = []
    trade_agg: dict[str, dict] = {}
    log_agg: dict[str, dict] = {}
    try:
        conn = db.get_connection()
        cur = conn.cursor()

        # Recent sessions (running + recently stopped)
        cur.execute(
            """
            SELECT id, status, pid, symbol, mode, entry_price, start_ts, end_ts, dry_run
            FROM bot_sessions
            ORDER BY COALESCE(start_ts, 0) DESC
            LIMIT 200
            """
        )
        rows = cur.fetchall() or []
        sessions = [dict(r) for r in rows]

        # Reconcile: sessions marked running but PID not alive => mark stopped.
        # This keeps Monitor consistent with the Dashboard "Bots Ativos" list.
        now_ts = time.time()
        for sess in sessions:
            try:
                if str(sess.get("status") or "").lower() != "running":
                    continue
                pid = sess.get("pid")
                if _pid_alive(pid):
                    continue
                bot_id = str(sess.get("id") or "").strip()
                if not bot_id:
                    continue
                try:
                    cur.execute(
                        "UPDATE bot_sessions SET status = ?, end_ts = ? WHERE id = ?",
                        ("stopped", now_ts, bot_id),
                    )
                    conn.commit()
                    sess["status"] = "stopped"
                    sess["end_ts"] = now_ts
                except Exception:
                    pass
            except Exception:
                continue

        # Trades aggregation
        cur.execute(
            """
            SELECT bot_id,
                   COUNT(1) AS trades,
                   COALESCE(SUM(COALESCE(profit,0)),0) AS profit_sum,
                   MAX(COALESCE(timestamp,0)) AS last_trade_ts
            FROM trades
            WHERE bot_id IS NOT NULL AND bot_id != ''
            GROUP BY bot_id
            """
        )
        for r in (cur.fetchall() or []):
            d = dict(r)
            bid = str(d.get("bot_id") or "")
            if bid:
                trade_agg[bid] = d

        # Logs aggregation
        cur.execute(
            """
            SELECT bot_id,
                   COUNT(1) AS logs,
                   MAX(COALESCE(timestamp,0)) AS last_log_ts
            FROM bot_logs
            WHERE bot_id IS NOT NULL AND bot_id != ''
            GROUP BY bot_id
            """
        )
        for r in (cur.fetchall() or []):
            d = dict(r)
            bid = str(d.get("bot_id") or "")
            if bid:
                log_agg[bid] = d
    except Exception:
        sessions = sessions or []
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    bot_ids = []
    for s in sessions:
        try:
            bid = str(s.get("id") or "").strip()
            if bid and bid not in bot_ids:
                bot_ids.append(bid)
        except Exception:
            continue

    if not bot_ids:
        st.warning("Nenhuma sessão de bot encontrada no banco. Inicie um bot no Dashboard para ver dados aqui.")
        return

    def _bot_label(bot_id: str) -> str:
        sess = next((x for x in sessions if str(x.get("id")) == str(bot_id)), None)
        if not sess:
            return str(bot_id)
        symbol = sess.get("symbol") or ""
        mode = (sess.get("mode") or "")
        status = (sess.get("status") or "")
        dry = "DRY" if int(sess.get("dry_run") or 0) == 1 else "REAL"
        return f"{bot_id[:12]}…  {symbol}  {mode}  {dry}  [{status}]"

    # Resolve selection
    selected_bot = preselected_bot if preselected_bot in bot_ids else (bot_ids[0] if bot_ids else None)
    try:
        idx = bot_ids.index(selected_bot) if selected_bot in bot_ids else 0
    except Exception:
        idx = 0

    with _safe_container(border=True):
        cols = st.columns([2.2, 1.0])
        selected_bot = cols[0].selectbox(
            "Bot para monitorar",
            options=bot_ids,
            index=idx,
            format_func=_bot_label,
            key="monitor_selected_bot",
        )
        if cols[1].button("🔄 Atualizar", use_container_width=True, key="monitor_refresh"):
            # Set a session flag to indicate a manual refresh request. Avoid immediate st.rerun()
            st.session_state['_monitor_manual_refresh_ts'] = time.time()

    # Persist selection for nav bar context
    try:
        st.session_state.selected_bot = selected_bot
        if selected_bot and selected_bot not in st.session_state.active_bots:
            st.session_state.active_bots.append(selected_bot)
    except Exception:
        pass

    # --- Overview table (multi-bot)
    try:
        import pandas as pd
        import datetime as _dt
    except Exception:
        pd = None
        _dt = None

    overview_rows: list[dict] = []
    for s in sessions:
        bid = str(s.get("id") or "")
        if not bid:
            continue
        ta = trade_agg.get(bid, {})
        la = log_agg.get(bid, {})
        pid_val = s.get("pid")
        alive_val = _pid_alive(pid_val)
        overview_rows.append({
            "bot_id": bid,
            "status": s.get("status"),
            "pid": pid_val,
            "alive": bool(alive_val),
            "symbol": s.get("symbol"),
            "mode": s.get("mode"),
            "real/dry": "DRY" if int(s.get("dry_run") or 0) == 1 else "REAL",
            "start": _fmt_ts(s.get("start_ts")),
            "end": _fmt_ts(s.get("end_ts")),
            "trades": int(ta.get("trades") or 0),
            "profit_sum": round(_safe_float(ta.get("profit_sum")), 6),
            "last_trade": _fmt_ts(ta.get("last_trade_ts")),
            "logs": int(la.get("logs") or 0),
            "last_log": _fmt_ts(la.get("last_log_ts")),
        })

    if pd is not None:
        df_over = pd.DataFrame(overview_rows)
        st.subheader("Bots (visão geral)")
        st.dataframe(df_over, use_container_width=True, hide_index=True)

    # --- Selected bot details
    sel_sess = next((x for x in sessions if str(x.get("id")) == str(selected_bot)), None) or {}

    # Best-effort live-ish price (from recent logs)
    recent_logs = []
    try:
        # Use the direct DB for >30 logs if needed; default view uses 60.
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT * FROM bot_logs WHERE bot_id = ? ORDER BY timestamp DESC LIMIT 60""",
            (str(selected_bot),)
        )
        recent_logs = [dict(r) for r in (cur.fetchall() or [])]
        conn.close()
    except Exception:
        try:
            recent_logs = db.get_bot_logs(str(selected_bot), limit=30)
        except Exception:
            recent_logs = []

    latest_price = _extract_latest_price_from_logs(recent_logs)
    # Prefer live market price when available; fallback to logs
    price_source = "logs"
    live_price = None
    try:
        try:
            from . import api as kucoin_api
        except Exception:
            import api as kucoin_api  # type: ignore
        sym = str(sel_sess.get("symbol") or "").strip()
        if sym:
            live_price = kucoin_api.get_price_fast(sym)
            if live_price and float(live_price) > 0:
                price_source = "live"
    except Exception:
        live_price = None

    if live_price and float(live_price) > 0:
        preferred_price = float(live_price)
    elif latest_price:
        preferred_price = float(latest_price)
    else:
        preferred_price = 0.0

    # Keep `latest_price` name for compatibility
    latest_price = preferred_price

    # Trades (for charts + table)
    trades = []
    try:
        # Pull more than the report default to build time-series.
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT timestamp, side, price, size, funds, profit, dry_run, strategy
            FROM trades
            WHERE bot_id = ?
            ORDER BY COALESCE(timestamp,0) ASC
            LIMIT 4000
            """,
            (str(selected_bot),)
        )
        rows = cur.fetchall() or []
        conn.close()
        for r in rows:
            trades.append(dict(r))
    except Exception:
        trades = []

    total_profit = 0.0
    try:
        total_profit = sum(_safe_float(t.get("profit")) for t in trades)
    except Exception:
        total_profit = 0.0

    # Equity snapshots (preferred performance series)
    equity_rows = []
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT timestamp, balance_usdt
            FROM equity_snapshots
            WHERE bot_id = ?
            ORDER BY COALESCE(timestamp,0) ASC
            LIMIT 3000
            """,
            (str(selected_bot),)
        )
        eq = cur.fetchall() or []
        conn.close()
        equity_rows = [dict(r) for r in eq]
    except Exception:
        equity_rows = []

    st.subheader("Bot selecionado")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Status", str(sel_sess.get("status") or ""))
    m2.metric("Symbol", str(sel_sess.get("symbol") or ""))
    # Show a clear badge if this is a DRY run
    dry_flag = int(sel_sess.get("dry_run") or 0) == 1
    mode_label = str(sel_sess.get("mode") or "")
    if dry_flag:
        m3.metric("Modo (DRY)", mode_label)
    else:
        m3.metric("Modo", mode_label)
    m4.metric("Realizado (USDT)", f"{total_profit:.6f}")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Trades", str(len(trades)))
    m6.metric("Entry", str(sel_sess.get("entry_price") or ""))
    m7.metric("Preço (último)", f"{latest_price:.2f}" if latest_price else "")
    m8.metric("Início", _fmt_ts(sel_sess.get("start_ts")))

    # --- Charts
    st.subheader("Gráficos de rendimento")

    try:
        import pandas as pd
    except Exception:
        pd = None

    if pd is not None and equity_rows:
        df_eq = pd.DataFrame(equity_rows)
        try:
            df_eq["timestamp"] = df_eq["timestamp"].astype(float)
            df_eq["datetime"] = df_eq["timestamp"].apply(lambda x: _fmt_ts(x))
            df_eq["balance_usdt"] = df_eq["balance_usdt"].astype(float)
        except Exception:
            pass
        try:
            import plotly.express as px
            fig = px.line(df_eq, x="datetime", y="balance_usdt", title="Equity (balance_usdt)")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=360)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.line_chart(df_eq.set_index("datetime")["balance_usdt"], height=240)
    elif pd is not None and trades:
        # Fallback: cumulative profit from trades
        df_t = pd.DataFrame(trades)
        try:
            df_t["timestamp"] = df_t["timestamp"].astype(float)
            df_t["datetime"] = df_t["timestamp"].apply(lambda x: _fmt_ts(x))
            df_t["profit"] = df_t["profit"].apply(_safe_float)
            df_t["cum_profit"] = df_t["profit"].cumsum()
            import plotly.express as px
            fig = px.line(df_t, x="datetime", y="cum_profit", title="Lucro acumulado (fallback)")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass
    else:
        st.info("Sem dados suficientes para plotar rendimento (equity/trades).")

    # Recent trades
    st.subheader("Trades recentes")
    if pd is not None and trades:
        df_tr = pd.DataFrame(trades)
        try:
            df_tr["datetime"] = df_tr["timestamp"].apply(lambda x: _fmt_ts(x))
        except Exception:
            pass
        show_cols = [c for c in ["datetime", "side", "price", "size", "funds", "profit", "dry_run", "strategy"] if c in df_tr.columns]
        st.dataframe(df_tr[show_cols].tail(50).iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.caption("Nenhum trade encontrado para este bot ainda.")

    # Recent logs - Terminal estilo com cores por evento
    st.subheader("📟 Terminal de Logs (tempo real)")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 Auto-refresh (5s)", value=True, key=f"log_autorefresh_{selected_bot}")
    
    if recent_logs:
        # Criar HTML do terminal com cores por tipo de evento
        log_lines = []
        for row in recent_logs[:50]:  # últimos 50 logs
            try:
                ts = _fmt_ts(row.get("timestamp"))
                lvl = str(row.get("level") or "INFO").upper()
                msg = str(row.get("message") or "")
                
                # Determinar cor baseado no conteúdo/level
                color = "#33ff33"  # verde padrão
                icon = "📝"
                
                msg_lower = msg.lower()
                if lvl == "ERROR" or "error" in msg_lower or "❌" in msg:
                    color = "#ff3333"  # vermelho
                    icon = "❌"
                elif lvl == "WARNING" or "warning" in msg_lower or "⚠️" in msg:
                    color = "#ffaa00"  # amarelo/laranja
                    icon = "⚠️"
                elif "buy" in msg_lower or "compra" in msg_lower or "bought" in msg_lower:
                    color = "#00ff00"  # verde brilhante
                    icon = "🟢"
                elif "sell" in msg_lower or "venda" in msg_lower or "sold" in msg_lower:
                    color = "#ff6666"  # vermelho claro
                    icon = "🔴"
                elif "profit" in msg_lower or "lucro" in msg_lower:
                    color = "#00ffff"  # ciano
                    icon = "💰"
                elif "cycle" in msg_lower or "ciclo" in msg_lower:
                    color = "#aaaaaa"  # cinza
                    icon = "🔄"
                elif "start" in msg_lower or "iniciado" in msg_lower:
                    color = "#66ff66"  # verde claro
                    icon = "🚀"
                elif "stop" in msg_lower or "encerrado" in msg_lower:
                    color = "#ff9999"  # rosa
                    icon = "🛑"
                elif "price" in msg_lower or "preço" in msg_lower:
                    color = "#99ccff"  # azul claro
                    icon = "📊"
                
                # Escapar HTML no msg
                import html as html_module
                msg_escaped = html_module.escape(msg)
                
                log_lines.append(
                    f'<div style="color: {color}; font-family: monospace; padding: 2px 0; border-bottom: 1px solid #333;">'
                    f'{icon} <span style="color: #888;">{ts}</span> '
                    f'<span style="color: {color}; font-weight: bold;">[{lvl}]</span> '
                    f'{msg_escaped}</div>'
                )
            except Exception:
                continue
        
        # Montar terminal HTML
        terminal_html = f'''
        <div id="log-terminal" style="
            background: #0a0a0a;
            border: 2px solid {theme.get('border', '#33ff33')};
            border-radius: 8px;
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            box-shadow: 0 0 20px {theme.get('glow', 'rgba(51, 255, 51, 0.3)')};
        ">
            <div style="color: {theme.get('accent', '#00ffff')}; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid {theme.get('border', '#33ff33')}; padding-bottom: 5px;">
                🖥️ Bot: {selected_bot[:12]}... | Logs: {len(recent_logs)}
            </div>
            {''.join(log_lines)}
        </div>
        <script>
            // Auto-scroll para o final
            var terminal = document.getElementById('log-terminal');
            if (terminal) terminal.scrollTop = terminal.scrollHeight;
        </script>
        '''
        
        st.markdown(terminal_html, unsafe_allow_html=True)
        
        # Legenda de cores
        with st.expander("🎨 Legenda de Cores"):
            leg_cols = st.columns(4)
            leg_cols[0].markdown("🟢 **Compra** (verde)")
            leg_cols[1].markdown("🔴 **Venda** (vermelho)")
            leg_cols[2].markdown("💰 **Lucro** (ciano)")
            leg_cols[3].markdown("⚠️ **Warning** (amarelo)")
        
        # Auto-refresh com JavaScript
        if auto_refresh:
            st.markdown(
                '''
                <script>
                    setTimeout(function() {
                        window.parent.postMessage({type: 'streamlit:rerun'}, '*');
                    }, 5000);
                </script>
                ''',
                unsafe_allow_html=True
            )
    else:
        st.info("📭 Nenhum log recente encontrado para este bot.")

# render_top_nav_bar movido para ui_components.navigation


def _list_theme_packs() -> list[str]:
    themes_root = ROOT / "themes"
    if not themes_root.exists() or not themes_root.is_dir():
        return []
    packs: list[str] = []
    for p in sorted(themes_root.iterdir(), key=lambda x: x.name.lower()):
        # Hide internal/template packs from the UI by default
        if p.is_dir() and not p.name.startswith('.') and not p.name.startswith('_'):
            packs.append(p.name)
    return packs


def _read_pack_manifest(pack: str) -> dict | None:
    if not pack:
        return None
    mf = ROOT / "themes" / pack / "manifest.json"
    if not mf.exists() or not mf.is_file():
        return None
    try:
        import json as _json
        data = _json.loads(mf.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _get_pack_default_background(pack: str) -> str | None:
    """Return a preferred background stem for a pack.

    Supports the template-style manifest.json:
    {"backgrounds": {"default": "..."}}
    """
    manifest = _read_pack_manifest(pack) or {}
    try:
        default_bg = (manifest.get("backgrounds") or {}).get("default")
        if isinstance(default_bg, str) and default_bg.strip():
            return default_bg.strip()
    except Exception:
        pass
    return None


def _maybe_apply_smw_monitor_pack(theme: dict):
    """When the SMW theme is selected, default the monitor background pack.

    With the simplified UX (no Pack/Imagem selectors), the theme drives the monitor background.
    """
    try:
        if not theme or theme.get("name") != "Super Mario World":
            return

        packs = _list_theme_packs()
        if not packs:
            return

        preferred = None
        for candidate in ("smw", "super_mario_world", "super-mario-world", "user_sprite_pack"):
            if candidate in packs:
                preferred = candidate
                break
        if not preferred:
            return

        bgs = _list_pack_backgrounds(preferred)
        if not bgs:
            return

        # Default behavior for SMW: random background on each reload.
        chosen = "random"

        # Set backing state (used when building the /monitor URL)
        st.session_state["monitor_bg_pack"] = preferred
        st.session_state["monitor_bg"] = chosen
    except Exception:
        return


def _list_pack_backgrounds(pack: str) -> list[str]:
    if not pack:
        return []
    bg_dir = ROOT / "themes" / pack / "backgrounds"
    if not bg_dir.exists() or not bg_dir.is_dir():
        return []
    out: list[str] = []
    for p in sorted(bg_dir.iterdir(), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            out.append(p.stem)
    return out


def render_bot_window(bot_id: str, controller):
    """Renderiza janela flutuante com gauge e terminal de um bot específico"""
    theme = get_current_theme()
    
    # Header da janela
    st.markdown(f'''
    <div style="text-align: center; padding: 15px; background: {theme['header_bg']}; 
                border: 2px solid {theme['border']}; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="color: {theme['accent']}; margin: 0;">🪟 Bot Monitor - {bot_id[:12]}</h2>
        <p style="color: {theme['text2']}; margin: 5px 0 0 0; font-size: 12px;">Janela Flutuante</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Botões de controle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader("📊 Monitor em Tempo Real")
    with col2:
        auto_refresh = st.checkbox("🔄 Auto", value=True, key="window_auto_refresh",
                                   help="Atualiza automaticamente a cada 5s")
    with col3:
        if st.button("🔃 Refresh", key="window_refresh", width='stretch'):
            st.rerun()

    # Auto-refresh para janela (não-bloqueante):
    # NÃO usar sleep+rerun aqui, pois isso impede o resto do layout de renderizar.
    # Em vez disso, agenda um reload do browser após 5s.
    if auto_refresh:
                # The gauge uses internal polling; avoid full-page reload to reduce flicker.
                pass
    
    # Cache key
    cache_key = f"logs_cache_{bot_id}"
    
    # Fragment para renderização
    @st.fragment
    def render_bot_content():
        try:
            db = DatabaseManager()
            logs = db.get_bot_logs(bot_id, limit=30)
        except Exception as e:
            st.error(f"Erro ao conectar banco de dados: {e}")
            logs = []
        
        # Atualiza cache
        logs_hash = hashlib.md5(str(logs).encode()).hexdigest() if logs else ""
        st.session_state[cache_key] = logs_hash
        
        # Target
        target_pct = st.session_state.get("target_profit_pct", 2.0)
        
        # Renderizar gauge
        if logs:
            # Best-effort: detect DRY flag from sessions table
            is_dry_db = False
            try:
                conn2 = db.get_connection()
                cur2 = conn2.cursor()
                cur2.execute("SELECT dry_run FROM bot_sessions WHERE id = ? LIMIT 1", (str(bot_id),))
                rr = cur2.fetchone()
                if rr:
                    is_dry_db = int(rr[0] or 0) == 1
                conn2.close()
            except Exception:
                is_dry_db = False
            render_cobol_gauge_static(logs, bot_id, target_pct, is_dry_db)
        
        # Renderizar terminal
        st.divider()
        is_mario_theme = theme.get("name") == "Super Mario World"
        
        if logs:
            log_html_items = []
            for log in reversed(logs):
                level = log.get('level', 'INFO')
                msg = log.get('message', '')
                
                txt = (level + " " + msg).upper()
                if any(w in txt for w in ['ERROR', 'ERRO', '❌', 'EXCEPTION']):
                    log_class = "smw-log-error"
                    mario_icon = "☠"
                elif any(w in txt for w in ['PROFIT', 'LUCRO', 'SUCCESS', '✅', 'TARGET', 'GANHO']):
                    log_class = "smw-log-success"
                    mario_icon = "★"
                elif any(w in txt for w in ['WARNING', 'AVISO', '⚠', 'WARN']):
                    log_class = "smw-log-warning"
                    mario_icon = "?"
                elif any(w in txt for w in ['TRADE', 'ORDER', 'BUY', 'SELL', 'COMPRA', 'VENDA']):
                    log_class = "smw-log-trade"
                    mario_icon = "◆"
                elif any(w in txt for w in ['INFO', 'BOT', 'INICIADO', 'CONECTADO']):
                    log_class = "smw-log-info"
                    mario_icon = "●"
                else:
                    log_class = "smw-log-info"
                    mario_icon = "▸"
                
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
                
                if is_mario_theme:
                    log_html_items.append(f'''
                        <div class="smw-log-line {log_class}">
                            <span class="smw-log-icon">{mario_icon}</span>
                            <span class="smw-log-level">[{level}]</span>{safe_msg}
                        </div>
                    ''')
                else:
                    log_html_items.append(f'''
                        <div style="padding: 6px 10px; margin: 3px 0; border-radius: 4px; 
                                    font-size: 13px; line-height: 1.5; background: #0a0a0a; 
                                    border-left: 3px solid #333; color: #cccccc;">
                            <span style="font-weight: bold; margin-right: 8px;">[{level}]</span>{safe_msg}
                        </div>
                    ''')
            
            log_html_content = "".join(log_html_items)
            now_str = time.strftime("%H:%M:%S")
            
            if is_mario_theme:
                terminal_html = f'''
<style>
    /* === SMW CSS (versão compacta) === */
    @keyframes smw-coin-spin {{
        0% {{ transform: scaleX(1); }}
        50% {{ transform: scaleX(0.3); }}
        100% {{ transform: scaleX(1); }}
    }}
    .smw-message-box {{ font-family: 'Press Start 2P', 'Courier New', monospace; }}
    .smw-border {{
        background: #000000;
        border: 4px solid #f8d830;
        box-shadow: 0 0 0 2px #000000, 0 0 0 4px #a85800, 6px 6px 0 rgba(0,0,0,0.5);
    }}
    .smw-header {{
        background: linear-gradient(180deg, #0068f8 0%, #003080 100%);
        padding: 8px 12px;
        border-bottom: 3px solid #f8d830;
        display: flex;
        justify-content: space-between;
    }}
    .smw-header-title {{ color: #f8f8f8; font-size: 9px; text-shadow: 2px 2px #000000; }}
    .smw-text-area {{
        background: linear-gradient(180deg, #0000a8 0%, #000080 50%, #000060 100%);
        padding: 12px;
        max-height: 400px;
        overflow-y: auto;
    }}
    .smw-log-line {{
        padding: 5px 8px;
        margin: 4px 0;
        font-size: 9px;
        line-height: 1.6;
        border-left: 3px solid transparent;
        background: rgba(0,0,0,0.3);
        color: #f8f8f8;
        text-shadow: 1px 1px #000000;
    }}
    .smw-log-error {{ color: #f85858; border-left-color: #f85858; background: rgba(248,88,88,0.15); }}
    .smw-log-success {{ color: #58f858; border-left-color: #58f858; background: rgba(88,248,88,0.15); }}
    .smw-log-warning {{ color: #f8d830; border-left-color: #f8d830; background: rgba(248,216,48,0.15); }}
    .smw-log-trade {{ color: #58d8f8; border-left-color: #58d8f8; background: rgba(88,216,248,0.15); }}
    .smw-log-info {{ color: #f8f8f8; border-left-color: #a8a8a8; }}
    .smw-log-icon {{ margin-right: 8px; font-size: 10px; }}
    .smw-log-level {{ color: #f8d830; font-weight: bold; margin-right: 6px; }}
    .smw-footer {{
        background: linear-gradient(180deg, #58d858 0%, #38a838 20%, #285828 40%, #804020 60%, #583010 100%);
        padding: 6px 12px;
        border-top: 3px solid #f8d830;
        display: flex;
        justify-content: space-between;
        font-size: 8px;
        color: #f8f8f8;
        text-shadow: 1px 1px #000000;
    }}
    .smw-live-coin {{ color: #f8d830; animation: smw-coin-spin 1s infinite; }}
</style>

<div class="smw-message-box">
    <div class="smw-border">
        <div class="smw-header">
            <span class="smw-header-title">▸ MESSAGE ▸ {bot_id[:8]}</span>
            <span style="font-size: 8px;">
                <span class="smw-live-coin">●</span>
                <span style="color: #f8f8f8;">LIVE ★ {now_str}</span>
            </span>
        </div>
        <div class="smw-text-area" id="logScroll">
            {log_html_content}
        </div>
        <div class="smw-footer">
            <span>★×{len(logs):03d}</span>
            <span style="color: #f8d830;">◀ WINDOW MODE ▶</span>
            <span>YOSHI'S HOUSE</span>
        </div>
    </div>
</div>
<script>
    var logDiv = document.getElementById('logScroll');
    if (logDiv) logDiv.scrollTop = logDiv.scrollHeight;
</script>
'''
            else:
                terminal_html = f'''
<style>
    @keyframes blink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.3; }}
    }}
    .live-indicator {{ animation: blink 1s infinite; color: #4ade80; font-weight: bold; }}
</style>
<div style="font-family: 'Courier New', monospace;">
    <div style="background: #0a0a0a; border: 2px solid {theme["border"]}; border-radius: 8px; 
                box-shadow: 0 0 20px {theme["glow"]}; overflow: hidden;">
        <div style="background: #111; padding: 10px 15px; border-bottom: 1px solid {theme["border"]}; 
                    display: flex; justify-content: space-between;">
            <span style="color: {theme["text"]}; font-size: 13px; font-weight: bold;">
                ◉ WINDOW MODE — {bot_id[:12]}
            </span>
            <span style="font-size: 11px;">
                <span class="live-indicator">● LIVE</span>
                <span style="color: #888;"> | {now_str}</span>
            </span>
        </div>
        <div style="max-height: 400px; overflow-y: auto; padding: 10px;" id="logScroll">
            {log_html_content}
        </div>
        <div style="background: #111; padding: 8px 15px; border-top: 1px solid #222; 
                    font-size: 10px; color: #666; display: flex; justify-content: space-between;">
            <span>{len(logs)} logs</span>
            <span style="color: #4ade80;">🪟 Floating Window</span>
        </div>
    </div>
</div>
<script>
    var logDiv = document.getElementById('logScroll');
    if (logDiv) logDiv.scrollTop = logDiv.scrollHeight;
</script>
'''
            render_html_smooth(terminal_html, height=500, key=f"window_logs_{bot_id}")
        else:
            st.info("Aguardando logs do bot...")
        
        # Eternal runs
        render_eternal_runs_history(bot_id)
    
    # Chamar fragment
    render_bot_content()


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
        
        render_html_smooth(table_html, height=350, key=f"eternal_table_{bot_id}")


def render_cobol_gauge_static(logs: list, bot_id: str, target_pct: float = 2.0, is_dry: bool = False):
    """
    Renderiza gauge estilo terminal COBOL/mainframe inline (versão estática).
    Usa dados dos logs já carregados, sem polling.
    """
    import json as json_lib
    from datetime import datetime
    
    # Obter tema atual
    theme = get_current_theme()
    is_mario_theme = theme.get("name") == "Super Mario World"
    
    def _is_dry_from_logs(logs_list: list) -> bool:
        try:
            for l in logs_list:
                # logs may include a dry_run field or mention 'dry' in message
                if isinstance(l, dict) and (str(l.get('dry_run') or '').strip() in ('1','True','true','true') or 'dry' in str(l.get('message','')).lower()):
                    return True
        except Exception:
            pass
        return False

    # Merge detection: honor explicit param or infer from logs
    is_dry = bool(is_dry) or _is_dry_from_logs(logs)

    # Try live price first
    price_source = "logs"
    live_price = None
    try:
        try:
            import api as kucoin_api
        except Exception:
            import api as kucoin_api  # type: ignore
        # default symbol if not present in logs
        sym = None
        if logs and isinstance(logs, list) and len(logs) > 0:
            try:
                maybe = json_lib.loads(logs[0].get('message','') or '{}')
                sym = maybe.get('symbol')
            except Exception:
                sym = None
        if not sym:
            sym = 'BTC-USDT'
        live_price = kucoin_api.get_price_fast(sym)
        if live_price and float(live_price) > 0:
            price_source = 'live'
    except Exception:
        live_price = None

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
                if 'price' in data and price_source != 'live':
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
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Renderizar tema Mario ou padrão, passando is_dry para watermark
    if is_mario_theme:
        render_mario_gauge(bot_id, symbol, mode, entry_price, current_price, 
                          profit_pct, target_pct, progress, cycle, executed, 
                          last_event, now, price_source, theme, is_dry)
    else:
        render_terminal_gauge(bot_id, symbol, mode, entry_price, current_price,
                             profit_pct, target_pct, progress, cycle, executed,
                             last_event, now, price_source, theme, is_dry)


def render_mario_gauge(bot_id, symbol, mode, entry_price, current_price, 
                       profit_pct, target_pct, progress, cycle, executed,
                       last_event, now, price_source, theme, is_dry: bool = False):
    """Renderiza gauge no estilo Super Mario World - com sprites originais do SNES"""
    
    # Barra de progresso com blocos do Mario
    bar_width = 20
    filled = int(bar_width * progress / 100)
    
    # Blocos de progresso (pixel art style)
    blocks_filled = "🟨" * filled   # Blocos coletados
    blocks_empty = "⬜" * (bar_width - filled)  # Blocos restantes
    
    # Status baseado nos power-ups do SMW
    if profit_pct >= target_pct:
        status = "GOAL!"
        status_color = "#fbd000"
        mario_char = "🏆"
    elif profit_pct > 2:
        status = "POWER UP!"
        status_color = "#fbd000"
        mario_char = "🪶"
    elif profit_pct > 0:
        status = "SUPER!"
        status_color = "#43b047"
        mario_char = "🍄"
    elif profit_pct < -3:
        status = "GAME OVER"
        status_color = "#e52521"
        mario_char = "💀"
    elif profit_pct < 0:
        status = "CAUTION!"
        status_color = "#ffaa00"
        mario_char = "⚠️"
    else:
        status = "PLAYING"
        status_color = "#ffffff"
        mario_char = "🎮"
    
    # Cor do rótulo indicando origem do preço
    price_label_color = "#43b047" if str(price_source).lower() == "live" else "#fbd000"

    # Sprites CSS Pixel Art do Super Mario World (16x16 pixels escalados)
    # Usando box-shadow para criar pixel art autêntico
    
    gauge_html = f'''
<div style="
    font-family: 'Press Start 2P', 'Courier New', monospace;
    font-size: 10px;
    background: linear-gradient(180deg, #5c94fc 0%, #5c94fc 60%, #43b047 90%, #8b4513 100%);
    border: 4px solid #e52521;
    box-shadow: 0 0 0 4px #fbd000, 0 8px 20px rgba(0,0,0,0.5);
    padding: 0;
    max-width: 540px;
    color: #ffffff;
    border-radius: 0px;
    margin: 10px 0;
    position: relative;
    overflow: hidden;
    image-rendering: pixelated;
">
    <style>
        /* ========== SPRITES PIXEL ART SUPER MARIO WORLD - SNES AUTHENTIC ========== */
        /* Referência: sprites originais 16x16 do SNES (1990) */
        
        /* Small Mario correndo - sprite autêntico SMW */
        .smw-mario {{
            width: 24px; height: 32px;
            background: transparent;
            position: absolute;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
            animation: mario-run 6s linear infinite;
        }}
        .smw-mario::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === SMALL MARIO SMW (12x16 base) === */
                /* Chapéu vermelho - topo */
                3px 0 #d82800, 4px 0 #d82800, 5px 0 #d82800, 6px 0 #d82800, 7px 0 #d82800,
                2px 1px #d82800, 3px 1px #d82800, 4px 1px #d82800, 5px 1px #d82800, 6px 1px #d82800, 7px 1px #d82800, 8px 1px #d82800, 9px 1px #d82800,
                /* Cabelo/rosto */
                2px 2px #6b4423, 3px 2px #6b4423, 4px 2px #6b4423, 5px 2px #fccca8, 6px 2px #fccca8, 7px 2px #fccca8, 8px 2px #000000,
                1px 3px #6b4423, 2px 3px #fccca8, 3px 3px #6b4423, 4px 3px #fccca8, 5px 3px #fccca8, 6px 3px #fccca8, 7px 3px #fccca8, 8px 3px #000000, 9px 3px #000000,
                1px 4px #6b4423, 2px 4px #fccca8, 3px 4px #6b4423, 4px 4px #fccca8, 5px 4px #fccca8, 6px 4px #fccca8, 7px 4px #fccca8, 8px 4px #fccca8, 9px 4px #000000,
                1px 5px #6b4423, 2px 5px #6b4423, 3px 5px #fccca8, 4px 5px #fccca8, 5px 5px #fccca8, 6px 5px #fccca8, 7px 5px #000000, 8px 5px #000000, 9px 5px #000000,
                3px 6px #fccca8, 4px 6px #fccca8, 5px 6px #fccca8, 6px 6px #fccca8, 7px 6px #fccca8,
                /* Corpo - camisa vermelha */
                2px 7px #d82800, 3px 7px #d82800, 4px 7px #0068f8, 5px 7px #d82800, 6px 7px #d82800, 7px 7px #d82800,
                1px 8px #d82800, 2px 8px #d82800, 3px 8px #d82800, 4px 8px #0068f8, 5px 8px #d82800, 6px 8px #0068f8, 7px 8px #d82800, 8px 8px #d82800,
                1px 9px #d82800, 2px 9px #d82800, 3px 9px #d82800, 4px 9px #0068f8, 5px 9px #0068f8, 6px 9px #0068f8, 7px 9px #0068f8, 8px 9px #d82800,
                0px 10px #fccca8, 1px 10px #fccca8, 2px 10px #d82800, 3px 10px #0068f8, 4px 10px #fcb8a8, 5px 10px #0068f8, 6px 10px #fcb8a8, 7px 10px #0068f8, 8px 10px #fccca8, 9px 10px #fccca8,
                0px 11px #fccca8, 1px 11px #fccca8, 2px 11px #fccca8, 3px 11px #0068f8, 4px 11px #0068f8, 5px 11px #0068f8, 6px 11px #0068f8, 7px 11px #0068f8, 8px 11px #fccca8, 9px 11px #fccca8,
                0px 12px #fccca8, 1px 12px #fccca8, 2px 12px #0068f8, 3px 12px #0068f8, 4px 12px #0068f8, 5px 12px #0068f8, 6px 12px #0068f8, 7px 12px #0068f8, 8px 12px #fccca8, 9px 12px #fccca8,
                /* Macacão azul */
                2px 13px #0068f8, 3px 13px #0068f8, 4px 13px #0068f8, 6px 13px #0068f8, 7px 13px #0068f8, 8px 13px #0068f8,
                1px 14px #6b4423, 2px 14px #6b4423, 3px 14px #6b4423, 7px 14px #6b4423, 8px 14px #6b4423, 9px 14px #6b4423,
                0px 15px #6b4423, 1px 15px #6b4423, 2px 15px #6b4423, 8px 15px #6b4423, 9px 15px #6b4423, 10px 15px #6b4423;
            transform: scale(2);
        }}
        
        /* Yoshi verde - sprite autêntico SMW */
        .smw-yoshi {{
            width: 28px; height: 32px;
            position: absolute;
            animation: yoshi-bounce 0.8s ease-in-out infinite;
        }}
        .smw-yoshi::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === YOSHI SMW (14x16 base) === */
                /* Cabeça verde - focinho grande */
                0px 2px #2c9f2c, 1px 2px #2c9f2c, 2px 2px #2c9f2c, 3px 2px #2c9f2c,
                0px 3px #2c9f2c, 1px 3px #58d858, 2px 3px #58d858, 3px 3px #2c9f2c, 4px 3px #2c9f2c,
                0px 4px #2c9f2c, 1px 4px #58d858, 2px 4px #58d858, 3px 4px #58d858, 4px 4px #2c9f2c, 5px 4px #2c9f2c, 6px 4px #2c9f2c,
                0px 5px #2c9f2c, 1px 5px #2c9f2c, 2px 5px #58d858, 3px 5px #2c9f2c, 4px 5px #ffffff, 5px 5px #ffffff, 6px 5px #2c9f2c, 7px 5px #2c9f2c,
                1px 6px #2c9f2c, 2px 6px #2c9f2c, 3px 6px #2c9f2c, 4px 6px #ffffff, 5px 6px #000000, 6px 6px #2c9f2c, 7px 6px #d82800, 8px 6px #d82800,
                /* Crista vermelha */
                7px 3px #d82800, 8px 3px #d82800,
                7px 4px #d82800, 8px 4px #d82800, 9px 4px #d82800,
                8px 5px #d82800, 9px 5px #d82800,
                /* Corpo */
                2px 7px #2c9f2c, 3px 7px #2c9f2c, 4px 7px #2c9f2c, 5px 7px #2c9f2c, 6px 7px #2c9f2c, 7px 7px #d82800,
                3px 8px #2c9f2c, 4px 8px #58d858, 5px 8px #58d858, 6px 8px #2c9f2c,
                2px 9px #2c9f2c, 3px 9px #58d858, 4px 9px #ffffff, 5px 9px #ffffff, 6px 9px #58d858, 7px 9px #2c9f2c,
                2px 10px #2c9f2c, 3px 10px #58d858, 4px 10px #ffffff, 5px 10px #ffffff, 6px 10px #58d858, 7px 10px #2c9f2c,
                3px 11px #2c9f2c, 4px 11px #58d858, 5px 11px #58d858, 6px 11px #2c9f2c,
                /* Pés laranja */
                1px 12px #e86818, 2px 12px #e86818, 3px 12px #2c9f2c, 4px 12px #2c9f2c, 5px 12px #e86818, 6px 12px #e86818,
                0px 13px #e86818, 1px 13px #e86818, 2px 13px #e86818, 5px 13px #e86818, 6px 13px #e86818, 7px 13px #e86818;
            transform: scale(2);
        }}
        
        /* Koopa Troopa verde - sprite autêntico SMW */
        .smw-koopa {{
            width: 20px; height: 28px;
            position: absolute;
            animation: koopa-walk 4s linear infinite;
        }}
        .smw-koopa::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === KOOPA TROOPA SMW === */
                /* Cabeça verde */
                3px 0px #2c9f2c, 4px 0px #2c9f2c, 5px 0px #2c9f2c,
                2px 1px #2c9f2c, 3px 1px #58d858, 4px 1px #ffffff, 5px 1px #000000, 6px 1px #2c9f2c,
                2px 2px #2c9f2c, 3px 2px #58d858, 4px 2px #58d858, 5px 2px #58d858, 6px 2px #2c9f2c,
                2px 3px #2c9f2c, 3px 3px #2c9f2c, 4px 3px #2c9f2c, 5px 3px #2c9f2c,
                /* Casco amarelo */
                1px 4px #f8d830, 2px 4px #f8d830, 3px 4px #2c9f2c, 4px 4px #2c9f2c, 5px 4px #2c9f2c, 6px 4px #f8d830, 7px 4px #f8d830,
                0px 5px #f8d830, 1px 5px #f8f898, 2px 5px #58d858, 3px 5px #2c9f2c, 4px 5px #2c9f2c, 5px 5px #2c9f2c, 6px 5px #58d858, 7px 5px #f8d830, 8px 5px #f8d830,
                0px 6px #f8d830, 1px 6px #f8f898, 2px 6px #58d858, 3px 6px #58d858, 4px 6px #2c9f2c, 5px 6px #58d858, 6px 6px #58d858, 7px 6px #f8d830, 8px 6px #f8d830,
                1px 7px #f8d830, 2px 7px #f8d830, 3px 7px #2c9f2c, 4px 7px #2c9f2c, 5px 7px #2c9f2c, 6px 7px #f8d830, 7px 7px #f8d830,
                /* Pés laranja */
                1px 8px #e86818, 2px 8px #e86818, 3px 8px #e86818, 5px 8px #e86818, 6px 8px #e86818, 7px 8px #e86818,
                0px 9px #e86818, 1px 9px #e86818, 2px 9px #e86818, 6px 9px #e86818, 7px 9px #e86818, 8px 9px #e86818;
            transform: scale(2);
        }}
        
        /* Galoomba (Goomba do SMW) - sprite autêntico */
        .smw-goomba {{
            width: 20px; height: 20px;
            position: absolute;
            animation: goomba-walk 5s linear infinite reverse;
        }}
        .smw-goomba::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === GALOOMBA SMW (redondo, não o goomba clássico) === */
                3px 0px #a05820, 4px 0px #a05820, 5px 0px #a05820,
                2px 1px #a05820, 3px 1px #d89050, 4px 1px #d89050, 5px 1px #d89050, 6px 1px #a05820,
                1px 2px #a05820, 2px 2px #d89050, 3px 2px #ffffff, 4px 2px #000000, 5px 2px #d89050, 6px 2px #ffffff, 7px 2px #000000,
                1px 3px #a05820, 2px 3px #d89050, 3px 3px #d89050, 4px 3px #d89050, 5px 3px #d89050, 6px 3px #d89050, 7px 3px #a05820,
                1px 4px #a05820, 2px 4px #a05820, 3px 4px #d89050, 4px 4px #d89050, 5px 4px #d89050, 6px 4px #a05820, 7px 4px #a05820,
                2px 5px #a05820, 3px 5px #a05820, 4px 5px #a05820, 5px 5px #a05820, 6px 5px #a05820,
                /* Pés */
                1px 6px #282828, 2px 6px #282828, 6px 6px #282828, 7px 6px #282828,
                1px 7px #282828, 2px 7px #282828, 6px 7px #282828, 7px 7px #282828;
            transform: scale(2);
        }}
        
        /* ? Block - sprite autêntico SMW */
        .smw-block {{
            width: 24px; height: 24px;
            position: absolute;
            animation: block-bump 0.5s ease-in-out infinite;
        }}
        .smw-block::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === ? BLOCK SMW (16x16) === */
                /* Borda preta */
                1px 0px #000000, 2px 0px #000000, 3px 0px #000000, 4px 0px #000000, 5px 0px #000000, 6px 0px #000000, 7px 0px #000000, 8px 0px #000000, 9px 0px #000000, 10px 0px #000000,
                0px 1px #000000, 11px 1px #000000,
                /* Interior amarelo */
                1px 1px #f8d830, 2px 1px #f8d830, 3px 1px #f8d830, 4px 1px #f8d830, 5px 1px #f8d830, 6px 1px #f8d830, 7px 1px #f8d830, 8px 1px #f8d830, 9px 1px #f8d830, 10px 1px #f8d830,
                0px 2px #000000, 1px 2px #f8f898, 2px 2px #f8d830, 3px 2px #f8d830, 4px 2px #f8d830, 5px 2px #f8d830, 6px 2px #f8d830, 7px 2px #f8d830, 8px 2px #f8d830, 9px 2px #f8d830, 10px 2px #a85800, 11px 2px #000000,
                0px 3px #000000, 1px 3px #f8f898, 2px 3px #f8d830, 3px 3px #f8d830, 4px 3px #000000, 5px 3px #000000, 6px 3px #f8d830, 7px 3px #000000, 8px 3px #f8d830, 9px 3px #f8d830, 10px 3px #a85800, 11px 3px #000000,
                0px 4px #000000, 1px 4px #f8f898, 2px 4px #f8d830, 3px 4px #000000, 4px 4px #f8d830, 5px 4px #f8d830, 6px 4px #000000, 7px 4px #f8d830, 8px 4px #000000, 9px 4px #f8d830, 10px 4px #a85800, 11px 4px #000000,
                0px 5px #000000, 1px 5px #f8f898, 2px 5px #f8d830, 3px 5px #f8d830, 4px 5px #f8d830, 5px 5px #f8d830, 6px 5px #000000, 7px 5px #f8d830, 8px 5px #f8d830, 9px 5px #f8d830, 10px 5px #a85800, 11px 5px #000000,
                0px 6px #000000, 1px 6px #f8f898, 2px 6px #f8d830, 3px 6px #f8d830, 4px 6px #f8d830, 5px 6px #f8d830, 6px 6px #000000, 7px 6px #f8d830, 8px 6px #f8d830, 9px 6px #f8d830, 10px 6px #a85800, 11px 6px #000000,
                0px 7px #000000, 1px 7px #f8f898, 2px 7px #f8d830, 3px 7px #f8d830, 4px 7px #f8d830, 5px 7px #f8d830, 6px 7px #000000, 7px 7px #000000, 8px 7px #f8d830, 9px 7px #f8d830, 10px 7px #a85800, 11px 7px #000000,
                0px 8px #000000, 1px 8px #f8f898, 2px 8px #f8d830, 3px 8px #f8d830, 4px 8px #f8d830, 5px 8px #f8d830, 6px 8px #f8d830, 7px 8px #f8d830, 8px 8px #f8d830, 9px 8px #f8d830, 10px 8px #a85800, 11px 8px #000000,
                0px 9px #000000, 1px 9px #f8d830, 2px 9px #a85800, 3px 9px #a85800, 4px 9px #a85800, 5px 9px #a85800, 6px 9px #a85800, 7px 9px #a85800, 8px 9px #a85800, 9px 9px #a85800, 10px 9px #a85800, 11px 9px #000000,
                0px 10px #000000, 11px 10px #000000,
                1px 10px #000000, 2px 10px #000000, 3px 10px #000000, 4px 10px #000000, 5px 10px #000000, 6px 10px #000000, 7px 10px #000000, 8px 10px #000000, 9px 10px #000000, 10px 10px #000000;
            transform: scale(2);
        }}
        
        /* Super Mushroom - sprite autêntico SMW */
        .smw-mushroom {{
            width: 20px; height: 24px;
            position: absolute;
        }}
        .smw-mushroom::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === SUPER MUSHROOM SMW === */
                /* Topo vermelho com manchas brancas */
                3px 0px #d82800, 4px 0px #d82800, 5px 0px #d82800, 6px 0px #d82800, 7px 0px #d82800,
                2px 1px #d82800, 3px 1px #ffffff, 4px 1px #d82800, 5px 1px #d82800, 6px 1px #ffffff, 7px 1px #d82800, 8px 1px #d82800,
                1px 2px #d82800, 2px 2px #ffffff, 3px 2px #ffffff, 4px 2px #d82800, 5px 2px #d82800, 6px 2px #ffffff, 7px 2px #ffffff, 8px 2px #d82800, 9px 2px #d82800,
                1px 3px #d82800, 2px 3px #d82800, 3px 3px #d82800, 4px 3px #d82800, 5px 3px #d82800, 6px 3px #d82800, 7px 3px #d82800, 8px 3px #d82800, 9px 3px #d82800,
                2px 4px #d82800, 3px 4px #d82800, 4px 4px #d82800, 5px 4px #d82800, 6px 4px #d82800, 7px 4px #d82800, 8px 4px #d82800,
                /* Caule bege */
                3px 5px #fccca8, 4px 5px #fccca8, 5px 5px #fccca8, 6px 5px #fccca8, 7px 5px #fccca8,
                3px 6px #fccca8, 4px 6px #ffffff, 5px 6px #fccca8, 6px 6px #ffffff, 7px 6px #fccca8,
                3px 7px #fccca8, 4px 7px #fccca8, 5px 7px #000000, 6px 7px #fccca8, 7px 7px #fccca8,
                4px 8px #fccca8, 5px 8px #fccca8, 6px 8px #fccca8;
            transform: scale(2);
        }}
        
        /* Super Star - sprite autêntico SMW */
        .smw-star {{
            width: 20px; height: 24px;
            position: absolute;
            animation: star-spin 1.5s linear infinite;
        }}
        .smw-star::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === SUPER STAR SMW === */
                4px 0px #f8d830, 5px 0px #f8d830,
                3px 1px #f8d830, 4px 1px #f8f898, 5px 1px #f8f898, 6px 1px #f8d830,
                2px 2px #f8d830, 3px 2px #f8f898, 4px 2px #000000, 5px 2px #f8f898, 6px 2px #000000, 7px 2px #f8d830,
                1px 3px #f8d830, 2px 3px #f8d830, 3px 3px #f8d830, 4px 3px #f8d830, 5px 3px #f8d830, 6px 3px #f8d830, 7px 3px #f8d830, 8px 3px #f8d830,
                0px 4px #f8d830, 1px 4px #f8d830, 2px 4px #f8d830, 3px 4px #f8d830, 4px 4px #f8d830, 5px 4px #f8d830, 6px 4px #f8d830, 7px 4px #f8d830, 8px 4px #f8d830, 9px 4px #f8d830,
                1px 5px #f8d830, 2px 5px #f8d830, 3px 5px #f8d830, 4px 5px #f8d830, 5px 5px #f8d830, 6px 5px #f8d830, 7px 5px #f8d830, 8px 5px #f8d830,
                2px 6px #f8d830, 3px 6px #f8d830, 4px 6px #f8d830, 5px 6px #f8d830, 6px 6px #f8d830, 7px 6px #f8d830,
                2px 7px #f8d830, 3px 7px #f8d830, 6px 7px #f8d830, 7px 7px #f8d830,
                1px 8px #f8d830, 2px 8px #f8d830, 7px 8px #f8d830, 8px 8px #f8d830;
            transform: scale(2);
        }}
        
        /* Coin - sprite autêntico SMW */
        .smw-coin {{
            width: 12px; height: 20px;
            position: absolute;
            animation: coin-spin 1s infinite;
        }}
        .smw-coin::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === COIN SMW === */
                2px 0px #f8d830, 3px 0px #f8d830,
                1px 1px #f8d830, 2px 1px #f8f898, 3px 1px #f8f898, 4px 1px #f8d830,
                0px 2px #f8d830, 1px 2px #f8f898, 2px 2px #f8f898, 3px 2px #f8d830, 4px 2px #f8d830, 5px 2px #a85800,
                0px 3px #f8d830, 1px 3px #f8f898, 2px 3px #f8d830, 3px 3px #f8d830, 4px 3px #a85800, 5px 3px #a85800,
                0px 4px #f8d830, 1px 4px #f8f898, 2px 4px #f8d830, 3px 4px #f8d830, 4px 4px #a85800, 5px 4px #a85800,
                0px 5px #f8d830, 1px 5px #f8f898, 2px 5px #f8d830, 3px 5px #f8d830, 4px 5px #a85800, 5px 5px #a85800,
                0px 6px #f8d830, 1px 6px #f8d830, 2px 6px #f8d830, 3px 6px #a85800, 4px 6px #a85800, 5px 6px #a85800,
                1px 7px #f8d830, 2px 7px #a85800, 3px 7px #a85800, 4px 7px #a85800;
            transform: scale(2);
        }}
        
        /* Warp Pipe - sprite autêntico SMW */
        .smw-pipe {{
            width: 40px; height: 40px;
            position: absolute;
        }}
        .smw-pipe::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === WARP PIPE SMW (borda do topo) === */
                0px 0px #003800, 1px 0px #003800, 2px 0px #003800, 3px 0px #003800, 4px 0px #003800, 5px 0px #003800, 6px 0px #003800, 7px 0px #003800, 8px 0px #003800, 9px 0px #003800, 10px 0px #003800, 11px 0px #003800, 12px 0px #003800, 13px 0px #003800, 14px 0px #003800, 15px 0px #003800,
                0px 1px #003800, 1px 1px #58d858, 2px 1px #58d858, 3px 1px #2c9f2c, 4px 1px #2c9f2c, 5px 1px #2c9f2c, 6px 1px #2c9f2c, 7px 1px #2c9f2c, 8px 1px #2c9f2c, 9px 1px #2c9f2c, 10px 1px #2c9f2c, 11px 1px #2c9f2c, 12px 1px #2c9f2c, 13px 1px #003800, 14px 1px #003800, 15px 1px #003800,
                0px 2px #003800, 1px 2px #58d858, 2px 2px #58d858, 3px 2px #2c9f2c, 4px 2px #2c9f2c, 5px 2px #2c9f2c, 6px 2px #2c9f2c, 7px 2px #2c9f2c, 8px 2px #2c9f2c, 9px 2px #2c9f2c, 10px 2px #2c9f2c, 11px 2px #2c9f2c, 12px 2px #2c9f2c, 13px 2px #003800, 14px 2px #003800, 15px 2px #003800,
                0px 3px #003800, 1px 3px #003800, 2px 3px #003800, 3px 3px #003800, 4px 3px #003800, 5px 3px #003800, 6px 3px #003800, 7px 3px #003800, 8px 3px #003800, 9px 3px #003800, 10px 3px #003800, 11px 3px #003800, 12px 3px #003800, 13px 3px #003800, 14px 3px #003800, 15px 3px #003800,
                /* Corpo do cano */
                1px 4px #003800, 2px 4px #58d858, 3px 4px #58d858, 4px 4px #2c9f2c, 5px 4px #2c9f2c, 6px 4px #2c9f2c, 7px 4px #2c9f2c, 8px 4px #2c9f2c, 9px 4px #2c9f2c, 10px 4px #2c9f2c, 11px 4px #2c9f2c, 12px 4px #003800, 13px 4px #003800, 14px 4px #003800,
                1px 5px #003800, 2px 5px #58d858, 3px 5px #58d858, 4px 5px #2c9f2c, 5px 5px #2c9f2c, 6px 5px #2c9f2c, 7px 5px #2c9f2c, 8px 5px #2c9f2c, 9px 5px #2c9f2c, 10px 5px #2c9f2c, 11px 5px #2c9f2c, 12px 5px #003800, 13px 5px #003800, 14px 5px #003800,
                1px 6px #003800, 2px 6px #58d858, 3px 6px #58d858, 4px 6px #2c9f2c, 5px 6px #2c9f2c, 6px 6px #2c9f2c, 7px 6px #2c9f2c, 8px 6px #2c9f2c, 9px 6px #2c9f2c, 10px 6px #2c9f2c, 11px 6px #2c9f2c, 12px 6px #003800, 13px 6px #003800, 14px 6px #003800,
                1px 7px #003800, 2px 7px #58d858, 3px 7px #58d858, 4px 7px #2c9f2c, 5px 7px #2c9f2c, 6px 7px #2c9f2c, 7px 7px #2c9f2c, 8px 7px #2c9f2c, 9px 7px #2c9f2c, 10px 7px #2c9f2c, 11px 7px #2c9f2c, 12px 7px #003800, 13px 7px #003800, 14px 7px #003800,
                1px 8px #003800, 2px 8px #003800, 3px 8px #003800, 4px 8px #003800, 5px 8px #003800, 6px 8px #003800, 7px 8px #003800, 8px 8px #003800, 9px 8px #003800, 10px 8px #003800, 11px 8px #003800, 12px 8px #003800, 13px 8px #003800, 14px 8px #003800;
            transform: scale(2);
        }}
        
        /* Cloud (nuvem SMW) - sprite autêntico */
        .smw-cloud {{
            width: 40px; height: 24px;
            position: absolute;
            animation: cloud-float 6s ease-in-out infinite;
        }}
        .smw-cloud::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === NUVEM SMW === */
                4px 0px #f8f8f8, 5px 0px #f8f8f8, 6px 0px #f8f8f8, 7px 0px #f8f8f8,
                2px 1px #f8f8f8, 3px 1px #f8f8f8, 4px 1px #f8f8f8, 5px 1px #f8f8f8, 6px 1px #f8f8f8, 7px 1px #f8f8f8, 8px 1px #f8f8f8, 9px 1px #f8f8f8, 10px 1px #f8f8f8, 11px 1px #f8f8f8,
                1px 2px #f8f8f8, 2px 2px #f8f8f8, 3px 2px #f8f8f8, 4px 2px #f8f8f8, 5px 2px #f8f8f8, 6px 2px #f8f8f8, 7px 2px #f8f8f8, 8px 2px #f8f8f8, 9px 2px #f8f8f8, 10px 2px #f8f8f8, 11px 2px #f8f8f8, 12px 2px #f8f8f8, 13px 2px #f8f8f8,
                0px 3px #f8f8f8, 1px 3px #f8f8f8, 2px 3px #f8f8f8, 3px 3px #f8f8f8, 4px 3px #f8f8f8, 5px 3px #f8f8f8, 6px 3px #f8f8f8, 7px 3px #f8f8f8, 8px 3px #f8f8f8, 9px 3px #f8f8f8, 10px 3px #f8f8f8, 11px 3px #f8f8f8, 12px 3px #f8f8f8, 13px 3px #f8f8f8, 14px 3px #f8f8f8,
                0px 4px #d8d8d8, 1px 4px #f8f8f8, 2px 4px #f8f8f8, 3px 4px #f8f8f8, 4px 4px #f8f8f8, 5px 4px #f8f8f8, 6px 4px #f8f8f8, 7px 4px #f8f8f8, 8px 4px #f8f8f8, 9px 4px #f8f8f8, 10px 4px #f8f8f8, 11px 4px #f8f8f8, 12px 4px #f8f8f8, 13px 4px #f8f8f8, 14px 4px #d8d8d8,
                1px 5px #d8d8d8, 2px 5px #d8d8d8, 3px 5px #f8f8f8, 4px 5px #f8f8f8, 5px 5px #f8f8f8, 6px 5px #f8f8f8, 7px 5px #f8f8f8, 8px 5px #f8f8f8, 9px 5px #f8f8f8, 10px 5px #f8f8f8, 11px 5px #f8f8f8, 12px 5px #d8d8d8, 13px 5px #d8d8d8;
            transform: scale(2);
        }}
        
        /* Piranha Plant (planta carnívora) - sprite autêntico SMW */
        .smw-piranha {{
            width: 24px; height: 36px;
            position: absolute;
            animation: piranha-peek 2.5s ease-in-out infinite;
        }}
        .smw-piranha::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === PIRANHA PLANT SMW === */
                /* Dentes superiores */
                1px 0px #f8f8f8, 5px 0px #f8f8f8, 9px 0px #f8f8f8,
                0px 1px #38a818, 1px 1px #f8f8f8, 2px 1px #38a818, 4px 1px #38a818, 5px 1px #f8f8f8, 6px 1px #38a818, 8px 1px #38a818, 9px 1px #f8f8f8, 10px 1px #38a818,
                /* Boca aberta vermelha */
                0px 2px #d82800, 1px 2px #d82800, 2px 2px #d82800, 3px 2px #d82800, 4px 2px #d82800, 5px 2px #d82800, 6px 2px #d82800, 7px 2px #d82800, 8px 2px #d82800, 9px 2px #d82800, 10px 2px #d82800,
                0px 3px #d82800, 1px 3px #800000, 2px 3px #800000, 3px 3px #800000, 4px 3px #800000, 5px 3px #800000, 6px 3px #800000, 7px 3px #800000, 8px 3px #800000, 9px 3px #800000, 10px 3px #d82800,
                /* Dentes inferiores */
                0px 4px #d82800, 1px 4px #f8f8f8, 2px 4px #d82800, 4px 4px #d82800, 5px 4px #f8f8f8, 6px 4px #d82800, 8px 4px #d82800, 9px 4px #f8f8f8, 10px 4px #d82800,
                1px 5px #38a818, 2px 5px #38a818, 3px 5px #38a818, 4px 5px #38a818, 5px 5px #38a818, 6px 5px #38a818, 7px 5px #38a818, 8px 5px #38a818, 9px 5px #38a818,
                /* Cabeça com bolinhas */
                2px 6px #d82800, 3px 6px #f8f8f8, 4px 6px #d82800, 5px 6px #d82800, 6px 6px #f8f8f8, 7px 6px #d82800, 8px 6px #d82800,
                2px 7px #d82800, 3px 7px #d82800, 4px 7px #d82800, 5px 7px #d82800, 6px 7px #d82800, 7px 7px #d82800, 8px 7px #d82800,
                /* Caule verde */
                4px 8px #38a818, 5px 8px #58d858, 6px 8px #38a818,
                4px 9px #38a818, 5px 9px #38a818, 6px 9px #38a818,
                4px 10px #38a818, 5px 10px #58d858, 6px 10px #38a818,
                4px 11px #38a818, 5px 11px #38a818, 6px 11px #38a818;
            transform: scale(2);
        }}
        
        /* Banzai Bill (projétil gigante) - sprite autêntico SMW */
        .smw-banzai {{
            width: 40px; height: 32px;
            position: absolute;
            animation: banzai-fly 4s linear infinite;
        }}
        .smw-banzai::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === BANZAI BILL SMW === */
                /* Ponta */
                0px 4px #282828, 0px 5px #282828, 0px 6px #282828, 0px 7px #282828,
                1px 3px #282828, 1px 4px #505050, 1px 5px #505050, 1px 6px #505050, 1px 7px #282828, 1px 8px #282828,
                /* Corpo principal */
                2px 2px #282828, 2px 3px #505050, 2px 4px #787878, 2px 5px #787878, 2px 6px #505050, 2px 7px #282828, 2px 8px #282828, 2px 9px #282828,
                3px 1px #282828, 3px 2px #505050, 3px 3px #787878, 3px 4px #a8a8a8, 3px 5px #a8a8a8, 3px 6px #787878, 3px 7px #505050, 3px 8px #282828, 3px 9px #282828, 3px 10px #282828,
                /* Olho */
                4px 1px #282828, 4px 2px #787878, 4px 3px #f8f8f8, 4px 4px #f8f8f8, 4px 5px #a8a8a8, 4px 6px #787878, 4px 7px #505050, 4px 8px #282828, 4px 9px #282828, 4px 10px #282828,
                5px 0px #282828, 5px 1px #505050, 5px 2px #787878, 5px 3px #000000, 5px 4px #f8f8f8, 5px 5px #a8a8a8, 5px 6px #787878, 5px 7px #505050, 5px 8px #282828, 5px 9px #282828, 5px 10px #282828, 5px 11px #282828,
                /* Corpo traseiro */
                6px 0px #282828, 6px 1px #505050, 6px 2px #787878, 6px 3px #a8a8a8, 6px 4px #a8a8a8, 6px 5px #787878, 6px 6px #505050, 6px 7px #282828, 6px 8px #e86818, 6px 9px #e86818, 6px 10px #282828, 6px 11px #282828,
                7px 0px #282828, 7px 1px #282828, 7px 2px #505050, 7px 3px #787878, 7px 4px #787878, 7px 5px #505050, 7px 6px #282828, 7px 7px #e86818, 7px 8px #f8a848, 7px 9px #e86818, 7px 10px #282828, 7px 11px #282828,
                8px 1px #282828, 8px 2px #282828, 8px 3px #505050, 8px 4px #505050, 8px 5px #282828, 8px 6px #e86818, 8px 7px #f8a848, 8px 8px #f8a848, 8px 9px #e86818, 8px 10px #282828,
                9px 2px #282828, 9px 3px #282828, 9px 4px #282828, 9px 5px #e86818, 9px 6px #f8a848, 9px 7px #f8a848, 9px 8px #e86818, 9px 9px #282828;
            transform: scale(2);
        }}
        
        /* Lakitu na nuvem - sprite autêntico SMW */
        .smw-lakitu {{
            width: 36px; height: 40px;
            position: absolute;
            animation: lakitu-float 6s ease-in-out infinite;
        }}
        .smw-lakitu::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === LAKITU SMW === */
                /* Cabelo/casco */
                4px 0px #38a818, 5px 0px #58d858, 6px 0px #38a818,
                3px 1px #38a818, 4px 1px #58d858, 5px 1px #58d858, 6px 1px #58d858, 7px 1px #38a818,
                /* Cabeça */
                3px 2px #f8d878, 4px 2px #f8d878, 5px 2px #f8d878, 6px 2px #f8d878, 7px 2px #f8d878,
                2px 3px #f8d878, 3px 3px #f8d878, 4px 3px #000000, 5px 3px #f8d878, 6px 3px #000000, 7px 3px #f8d878, 8px 3px #f8d878,
                2px 4px #f8d878, 3px 4px #f8d878, 4px 4px #f8d878, 5px 4px #f8d878, 6px 4px #f8d878, 7px 4px #f8d878, 8px 4px #f8d878,
                3px 5px #f8d878, 4px 5px #d82800, 5px 5px #d82800, 6px 5px #d82800, 7px 5px #f8d878,
                /* Óculos/mãos */
                1px 6px #f8d878, 2px 6px #f8d878, 8px 6px #f8d878, 9px 6px #f8d878,
                /* === NUVEM DE LAKITU === */
                3px 7px #f8f8f8, 4px 7px #f8f8f8, 5px 7px #f8f8f8, 6px 7px #f8f8f8, 7px 7px #f8f8f8,
                2px 8px #f8f8f8, 3px 8px #f8f8f8, 4px 8px #f8f8f8, 5px 8px #f8f8f8, 6px 8px #f8f8f8, 7px 8px #f8f8f8, 8px 8px #f8f8f8,
                1px 9px #f8f8f8, 2px 9px #f8f8f8, 3px 9px #f8f8f8, 4px 9px #f8f8f8, 5px 9px #f8f8f8, 6px 9px #f8f8f8, 7px 9px #f8f8f8, 8px 9px #f8f8f8, 9px 9px #f8f8f8,
                2px 10px #d8d8d8, 3px 10px #f8f8f8, 4px 10px #f8f8f8, 5px 10px #f8f8f8, 6px 10px #f8f8f8, 7px 10px #f8f8f8, 8px 10px #d8d8d8;
            transform: scale(2);
        }}
        
        /* Animações */
        @keyframes mario-run {{
            0% {{ left: -40px; }}
            100% {{ left: calc(100% + 40px); }}
        }}
        @keyframes yoshi-bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-12px); }}
        }}
        @keyframes koopa-walk {{
            0%, 100% {{ transform: translateX(0); }}
            50% {{ transform: translateX(-15px); }}
        }}
        @keyframes goomba-walk {{
            0% {{ left: -30px; }}
            100% {{ left: calc(100% + 30px); }}
        }}
        @keyframes block-bump {{
            0%, 70%, 100% {{ transform: translateY(0); }}
            35% {{ transform: translateY(-10px); }}
        }}
        @keyframes star-spin {{
            0% {{ transform: rotate(0deg) scale(1); filter: brightness(1); }}
            50% {{ transform: rotate(180deg) scale(1.2); filter: brightness(1.5); }}
            100% {{ transform: rotate(360deg) scale(1); filter: brightness(1); }}
        }}
        @keyframes coin-spin {{
            0%, 100% {{ transform: scaleX(1); }}
            50% {{ transform: scaleX(0.2); }}
        }}
        @keyframes cloud-float {{
            0%, 100% {{ transform: translateX(0); }}
            50% {{ transform: translateX(20px); }}
        }}
        @keyframes piranha-peek {{
            0%, 60%, 100% {{ transform: translateY(15px); opacity: 0.5; }}
            70%, 90% {{ transform: translateY(0); opacity: 1; }}
        }}
        @keyframes banzai-fly {{
            0% {{ left: calc(100% + 30px); }}
            100% {{ left: -50px; }}
        }}
        @keyframes lakitu-float {{
            0%, 100% {{ transform: translateX(0) translateY(0); }}
            25% {{ transform: translateX(20px) translateY(-5px); }}
            50% {{ transform: translateX(40px) translateY(0); }}
            75% {{ transform: translateX(20px) translateY(5px); }}
        }}
    </style>
    
    <!-- Nuvens pixel art -->
    <div class="smw-cloud" style="top: 15px; left: 8%;"></div>
    <div class="smw-cloud" style="top: 25px; right: 12%; animation-delay: 2s;"></div>
    <div class="smw-cloud" style="top: 8px; right: 35%; transform: scale(0.7); animation-delay: 1s;"></div>
    
    <!-- Mario correndo -->
    <div class="smw-mario" style="bottom: 58px; z-index: 10;"></div>
    
    <!-- Yoshi -->
    <div class="smw-yoshi" style="bottom: 56px; right: 60px; z-index: 10;"></div>
    
    <!-- Koopa Troopa -->
    <div class="smw-koopa" style="bottom: 56px; right: 25%; z-index: 8;"></div>
    
    <!-- Goomba (Galoomba) -->
    <div class="smw-goomba" style="bottom: 56px; z-index: 7;"></div>
    
    <!-- ? Block -->
    <div class="smw-block" style="top: 70px; right: 15%;"></div>
    <div class="smw-block" style="top: 70px; left: 20%; animation-delay: 0.3s;"></div>
    
    <!-- Super Star -->
    <div class="smw-star" style="top: 95px; left: 45%;"></div>
    
    <!-- Coins -->
    <div class="smw-coin" style="top: 85px; left: 12%;"></div>
    <div class="smw-coin" style="top: 105px; right: 22%; animation-delay: 0.3s;"></div>
    <div class="smw-coin" style="top: 115px; left: 35%; animation-delay: 0.6s;"></div>
    
    <!-- Pipe -->
    <div class="smw-pipe" style="bottom: 48px; left: 30%;"></div>
    
    <!-- Piranha Plant saindo do Pipe -->
    <div class="smw-piranha" style="bottom: 70px; left: 32%;"></div>
    
    <!-- Super Mushroom (decorativo) -->
    <div class="smw-mushroom" style="bottom: 58px; left: 65%;"></div>
    
    <!-- Banzai Bill voando -->
    <div class="smw-banzai" style="top: 140px; z-index: 5;"></div>
    
    <!-- Lakitu na nuvem -->
    <div class="smw-lakitu" style="top: 30px; left: 50%;"></div>
    
    <!-- Header - Estilo HUD do Super Mario World -->
    <div style="
        background: linear-gradient(180deg, #e52521 0%, #b01e1e 100%);
        border-bottom: 4px solid #fbd000;
        padding: 10px 15px;
        text-align: center;
        position: relative;
        z-index: 10;
    ">
        <div class="smw-yoshi" style="width: 14px; height: 18px; position: relative; display: inline-block; margin-right: 8px; animation: none;"></div>
        <span style="color: #fbd000; font-weight: bold; text-shadow: 2px 2px #000;"> DINOSAUR LAND TRADING </span>
        <div class="smw-yoshi" style="width: 14px; height: 18px; position: relative; display: inline-block; margin-left: 8px; animation: none; transform: scaleX(-1);"></div>
        <div style="font-size: 8px; color: rgba(255,255,255,0.7); margin-top: 2px;">
            ★ YOSHI'S ISLAND ★ DONUT PLAINS ★ VANILLA DOME ★
        </div>
    </div>
    
    <!-- Conteúdo principal -->
    <div style="padding: 15px; position: relative; z-index: 10;">
        
        <!-- Info boxes estilo HUD do SMW original -->
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <div style="background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">
                <div style="font-size: 9px; color: #fbd000;">MARIO</div>
                <div style="font-size: 12px; font-weight: bold; color: #ffffff;">{symbol[:3]}</div>
            </div>
            <div style="background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">
                <div style="font-size: 9px; color: #fbd000;">★×</div>
                <div style="font-size: 12px; font-weight: bold; color: #ffffff; animation: coin-spin 1s infinite;">{cycle}</div>
            </div>
            <div style="background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">
                <div style="font-size: 9px; color: #fbd000;">WORLD</div>
                <div style="font-size: 12px; font-weight: bold; color: #ffffff;">{mode}</div>
            </div>
            <div style="background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">
                <div style="font-size: 9px; color: #fbd000;">TIME</div>
                <div style="font-size: 12px; font-weight: bold; color: #ffffff;">{now.split()[1][:5] if ' ' in now else now[:5]}</div>
            </div>
        </div>
        
        <!-- Preços -->
        <div style="
            background: rgba(0,0,0,0.6);
            border: 3px solid #43b047;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        ">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="color: #fbd000;">🏠 ENTRY:</span>
                <span style="font-weight: bold;">${entry_price:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #fbd000;">📍 CURRENT:</span>
                <span style="font-weight: bold; color: #43b047;">${current_price:,.2f}</span>
            </div>
        </div>
        
        <!-- Status -->
        <div style="
            text-align: center;
            font-size: 14px;
            font-weight: bold;
            color: {status_color};
            text-shadow: 2px 2px #000;
            margin-bottom: 10px;
            animation: mario-jump 0.5s infinite;
        ">
            {mario_char} {status}
        </div>
        
        <!-- Profit com Power Meter estilo SMW -->
        <div style="
            text-align: center;
            margin-bottom: 10px;
        ">
            <span style="font-size: 9px; color: #fbd000;">POWER:</span>
            <span style="font-size: 18px; font-weight: bold; color: {status_color}; text-shadow: 2px 2px #000;">
                {profit_pct:+.2f}%
            </span>
        </div>
        
        <!-- Barra de progresso - Giant Gate (portão de fim de fase) -->
        <div style="
            background: rgba(0,0,0,0.7);
            border: 3px solid #8b4513;
            border-radius: 0px;
            padding: 8px;
            margin-bottom: 10px;
        ">
            <div style="font-size: 9px; color: #fbd000; margin-bottom: 5px; text-align: center;">
                🚩 GIANT GATE — TARGET {target_pct:.1f}%
            </div>
            <div style="
                font-size: 14px;
                letter-spacing: -1px;
                text-align: center;
                line-height: 1.2;
            ">
                {blocks_filled}{blocks_empty}
            </div>
            <div style="text-align: center; margin-top: 5px; font-size: 10px;">
                <span style="color: #43b047;">★</span> {progress:.0f}/100 BONUS STARS <span style="color: #43b047;">★</span>
            </div>
        </div>
        
        <!-- Info estilo SMW com Dragon Coins e Secret Exit -->
        <div style="
            display: flex;
            justify-content: center;
            gap: 8px;
            font-size: 10px;
        ">
            <div style="background: #000000; border: 2px solid #fbd000; border-radius: 0px; padding: 4px 8px; display: flex; align-items: center; gap: 4px;">
                <div class="smw-coin" style="position: relative; width: 10px; height: 14px; animation: none;"></div>
                <span>×{executed}</span>
            </div>
            <div style="background: #e52521; border: 2px solid #fbd000; border-radius: 0px; padding: 4px 8px;">
                🔑 {last_event[:12]}
            </div>
        </div>
        
    </div>
    
    <!-- Footer - Chão do Dinosaur Land (grama + terra com pixel texture) -->
    <div style="
        background: linear-gradient(180deg, #43b047 0%, #2d8a35 30%, #8b4513 70%, #5a3010 100%);
        border-top: 3px solid #fbd000;
        padding: 8px;
        text-align: center;
        font-size: 9px;
        color: #ffffff;
        position: relative;
    ">
        <div style="display: flex; justify-content: center; align-items: center; gap: 12px;">
            <span style="display: flex; align-items: center; gap: 4px;">
                <div class="smw-mushroom" style="position: relative; width: 12px; height: 12px; transform: scale(0.8);"></div>
                <span>1-UP</span>
            </span>
            <span style="color: #fbd000;">{now}</span>
            <span style="color: {price_label_color}; font-weight: bold;">PRICE: {price_source.upper()}</span>
            <span style="display: flex; align-items: center; gap: 4px;">
                <div class="smw-star" style="position: relative; width: 12px; height: 12px; transform: scale(0.7); animation: none;"></div>
                <span>ONLINE</span>
            </span>
        </div>
        </div>
        <!-- Watermark for DRY runs -->
        {'<div style="position:absolute; top:40%; left:50%; transform:translate(-50%,-50%) rotate(-20deg); font-size:48px; color: rgba(255,255,255,0.12); font-weight:900; pointer-events:none; z-index:9999;">DRY RUN</div>' if is_dry else ''}
</div>
'''
    render_html_smooth(gauge_html, height=520, key=f"mario_gauge_{bot_id}")



def render_terminal_gauge(bot_id, symbol, mode, entry_price, current_price,
                          profit_pct, target_pct, progress, cycle, executed,
                          last_event, now, price_source, theme, is_dry: bool = False):
    """Renderiza gauge no estilo terminal COBOL padrão"""
    
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
    
    # Escolhe cor do rótulo de origem de preço
    price_label_color = theme.get("success") if str(price_source).lower() == "live" else theme.get("accent")

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
            <span style="color: {price_label_color}; font-weight:bold;">PRICE: {price_source.upper()}</span> |
            <span style="color: {theme["text"]};">◄</span> REFRESH MANUAL
        </div>
    </div>
</div>
'''
    # Renderiza sem flicker
    # Append watermark for DRY runs into same key wrapper
    if is_dry:
        # Inject a small badge overlay by appending an absolutely positioned div
        gauge_html = gauge_html.replace('</div>\n</div>\n\n', '<div style="position:absolute; top:8px; right:8px; background: rgba(255,255,255,0.08); padding:6px 8px; color:#ffd; border-radius:6px; font-weight:700; z-index:9999;">DRY RUN</div>\n</div>\n</div>\n\n')
    render_html_smooth(gauge_html, height=420, key=f"terminal_gauge_{bot_id}")


def render_cobol_gauge(logs: list, bot_id: str, target_pct: float = 2.0, api_port: int = 8765, is_dry: bool = False):
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
        
        {('<div style="position:absolute; top:40%; left:50%; transform:translate(-50%,-50%) rotate(-20deg); font-size:48px; color: rgba(255,255,255,0.12); font-weight:900; pointer-events:none; z-index:9999;">DRY RUN</div>') if is_dry else ''}
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
    # Renderiza sem flicker
    render_html_smooth(gauge_html, height=400, key=f"cobol_gauge_{bot_id}")


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
    
    render_html_smooth(html_content, height=height + 20, key=f"realtime_terminal_{bot_id}")


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
    # Entry point: call the full UI renderer (kept separate so we can recover safely).
    try:
        controller = None
        try:
            controller = get_global_controller()
            st.write(f"Debug: controller = {controller}")  # Debug line
        except Exception as e:
            st.warning(f"⚠️ Erro ao obter controller: {e}")
            controller = None
        
        _render_full_ui(controller)
    except Exception as e:
        st.error(f"❌ Erro ao renderizar UI: {e}")
        import traceback
        with st.expander("Detalhes do erro"):
            st.code(traceback.format_exc())
    return


def _render_full_ui(controller=None):
    # =====================================================
    # PAGE CONFIG & TEMA GLOBAL
    # =====================================================
    # st.set_page_config já foi chamado no streamlit_app.py, não chamar novamente

    # Injetar CSS do tema terminal
    try:
        inject_global_css()
    except Exception:
        pass

    # Remover coluna lateral (sidebar) globalmente
    # _hide_sidebar_everywhere()

    # ---------- Session state initialization (defensive) ----------
    # Ensure commonly used keys exist to avoid AttributeError during render.
    try:
        if not isinstance(st.session_state.get("active_bots", None), list):
            st.session_state["active_bots"] = []
        if "selected_bot" not in st.session_state:
            st.session_state["selected_bot"] = None
        if "controller" not in st.session_state:
            st.session_state["controller"] = None
        if "bot_running" not in st.session_state:
            st.session_state["bot_running"] = False
        if "_api_port" not in st.session_state:
            st.session_state["_api_port"] = None
        if "_equity_snapshot_started" not in st.session_state:
            st.session_state["_equity_snapshot_started"] = False
        if "target_profit_pct" not in st.session_state:
            st.session_state["target_profit_pct"] = 2.0
        if "monitor_bg_pack" not in st.session_state:
            st.session_state["monitor_bg_pack"] = None
        if "monitor_bg" not in st.session_state:
            st.session_state["monitor_bg"] = None
    except Exception:
        # If Streamlit session-state API is unavailable, continue silently.
        pass
    # Ensure a usable controller object is present in session state.
    try:
        if controller is None:
            try:
                controller = get_global_controller()
            except Exception:
                controller = None
        # store controller into session state for other places that expect it
        try:
            st.session_state["controller"] = controller
        except Exception:
            pass
    except Exception:
        pass

    # Ensure the local API server is started once (non-blocking) so /report and /monitor links work.
    try:
        if not st.session_state.get("_api_server_start_attempted"):
            st.session_state["_api_server_start_attempted"] = True
            if "start_api_server" in globals() and st.session_state.get("_api_port") is None:
                import threading

                def _start_api():
                    try:
                        # prefer default 8765 but allow automatic port selection
                        p = start_api_server(8765)
                        if p:
                            try:
                                st.session_state["_api_port"] = int(p)
                            except Exception:
                                pass
                    except Exception:
                        pass

                try:
                    threading.Thread(target=_start_api, name="start-api-server", daemon=True).start()
                except Exception:
                    # best-effort synchronous fallback (rare)
                    try:
                        p = start_api_server(8765)
                        if p:
                            st.session_state["_api_port"] = int(p)
                    except Exception:
                        pass
        elif st.session_state.get("_api_port") is None:
            # Se já tentou mas não tem porta, tentar sync uma vez
            if "start_api_server" in globals() and not st.session_state.get("_api_sync_tried"):
                st.session_state["_api_sync_tried"] = True
                try:
                    p = start_api_server(8765)
                    if p:
                        st.session_state["_api_port"] = int(p)
                except Exception:
                    pass
    except Exception:
        pass
    # ----------------------------------------------------------------

    # =====================================================
    # QUERY STRING
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

    def _qs_truthy(v) -> bool:
        try:
            s = str(v).strip().lower()
        except Exception:
            return False
        return s in ("1", "true", "yes", "y", "on")

    # =====================================================
    # VIEW MODE (no new tabs): view=dashboard|monitor|report
    # Also supports legacy params report=1 and window=1.
    # =====================================================
    raw_view = _qs_get("view", None)
    try:
        view = str(raw_view or "").strip().lower()
    except Exception:
        view = ""

    is_report_mode = _qs_truthy(_qs_get("report", None))
    is_window_mode = _qs_truthy(_qs_get("window", None))

    if not view:
        if is_report_mode:
            view = "report"
        elif is_window_mode:
            view = "monitor"
        else:
            view = "dashboard"

    # Header estilo terminal (somente no modo principal)
    theme = get_current_theme()
    # If the user picked SMW theme, default the monitor background pack.
    # Important: must run before sidebar widgets are created.
    _maybe_apply_smw_monitor_pack(theme)

    # Build theme query-string for the dedicated /monitor window.
    theme_qs = (
        f"&t_bg={urllib.parse.quote(theme.get('bg', ''))}"
        f"&t_bg2={urllib.parse.quote(theme.get('bg2', ''))}"
        f"&t_border={urllib.parse.quote(theme.get('border', ''))}"
        f"&t_accent={urllib.parse.quote(theme.get('accent', ''))}"
        f"&t_text={urllib.parse.quote(theme.get('text', ''))}"
        f"&t_text2={urllib.parse.quote(theme.get('text2', ''))}"
        f"&t_muted={urllib.parse.quote('#8b949e')}"
        f"&t_warning={urllib.parse.quote(theme.get('warning', ''))}"
        f"&t_error={urllib.parse.quote(theme.get('error', ''))}"
        f"&t_success={urllib.parse.quote(theme.get('success', ''))}"
        f"&t_header_bg={urllib.parse.quote(theme.get('header_bg', ''))}"
        f"&t_is_light={'1' if theme.get('is_light', False) else '0'}"
    )

    # Optional background selection for the monitor window (served by /themes/*)
    mon_pack = st.session_state.get("monitor_bg_pack")
    mon_bg = st.session_state.get("monitor_bg")
    try:
        if theme.get("name") == "Super Mario World" and not mon_pack:
            mon_pack = "smw"
        if theme.get("name") == "Super Mario World" and not mon_bg:
            mon_bg = "random"
    except Exception:
        pass
    if mon_pack:
        theme_qs += f"&bg_pack={urllib.parse.quote(str(mon_pack))}"
    if mon_bg:
        theme_qs += f"&bg={urllib.parse.quote(str(mon_bg))}"

    # Selected bot resolution (query param wins)
    query_bot = _qs_get("bot", None) or _qs_get("bot_id", None)
    if query_bot:
        st.session_state.selected_bot = query_bot
        if query_bot not in st.session_state.active_bots:
            st.session_state.active_bots.append(query_bot)

    selected_bot = st.session_state.get("selected_bot")

    # Top navigation bar on all pages
    render_top_nav_bar(theme, view, selected_bot=selected_bot)

    # Fullscreen pages: also reduce padding
    if view in ("monitor", "report"):
        _hide_sidebar_for_fullscreen_pages()

    # Route views
    if view == "report":
        # Prefer dedicated HTML report (/report) embedded in-app
        api_port = st.session_state.get("_api_port")
        if api_port:
            theme_query = str(theme_qs).lstrip('&')
            report_url = f"http://127.0.0.1:{int(api_port)}/report?{theme_query}" if theme_query else f"http://127.0.0.1:{int(api_port)}/report"

            # Provide a safe return URL for the HTML window to navigate back.
            try:
                try:
                    st_port = int(st.get_option("server.port"))
                except Exception:
                    st_port = 8501
                home_url = f"http://127.0.0.1:{st_port}/?view=dashboard"
                home_val = urllib.parse.quote(home_url, safe='')
            except Exception:
                home_val = ''
            report_url += ("&" if "?" in report_url else "?") + f"home={home_val or ''}"

            if selected_bot:
                report_url += f"&bot={urllib.parse.quote(str(selected_bot))}"
            components.iframe(report_url, height=900, scrolling=True)
        else:
            # Fallback to Streamlit report mode (same tab)
            render_trade_report_page()
        st.stop()

    if view == "monitor":
        render_monitor_dashboard(theme, preselected_bot=selected_bot)
        st.stop()

    # Dashboard header (compact, readable)
    st.header("KuCoin PRO — Trading Terminal")
    st.caption("Dashboard para iniciar e acompanhar bots. Use a barra no topo para Monitor/Relatório.")

    # Se a página for aberta com ?start=1 e parâmetros, iniciar o bot aqui
    q = st.query_params
    start_param = _qs_get("start", None)
    if start_param and not st.session_state.get("_started_from_qs", False):
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

            # Adiciona à lista de bots ativos
            if bot_id_started not in st.session_state.active_bots:
                st.session_state.active_bots.append(bot_id_started)
            st.session_state.selected_bot = bot_id_started
            time.sleep(0.5)  # Deixa bot subprocess começar a gravar logs

            # Mark as done before touching query params to avoid loops.
            st.session_state["_started_from_qs"] = True

            # substitui a query para exibir ?bot=... evitando reinícios
            # Preserve theme/bg selections in URL
            _merge_query_params({"bot": bot_id_started, "start": None})
            st.rerun()
        except Exception as e:
            # Avoid infinite retries if something goes wrong.
            st.session_state["_started_from_qs"] = True
            st.error(f"Erro iniciando bot via query: {e}")

    # =====================================================
    # HIDRATAR BOTS ATIVOS (persistência + processos vivos)
    # =====================================================
    # Bugfix: processos que continuam rodando após reload/F5 (ou iniciados fora
    # desta sessão Streamlit) não apareciam porque a UI dependia apenas de
    # st.session_state.active_bots + registry em memória.
    st.session_state.active_bots = []  # Reset to avoid stale data
    db_sessions_by_id: dict[str, dict] = {}
    ps_pids_by_id: dict[str, int] = {}

    # 1) DB (bot_sessions) — fonte canônica quando disponível
    try:
        db_sync = DatabaseManager()
        for sess in db_sync.get_active_bots() or []:
            bot_id = sess.get("id") or sess.get("bot_id")
            if not bot_id:
                continue
            db_sessions_by_id[str(bot_id)] = sess

        # Marcar sessões 'running' cujo PID não existe mais
        for bot_id, sess in list(db_sessions_by_id.items()):
            if not _pid_alive(sess.get("pid")):
                try:
                    db_sync.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
                except Exception:
                    pass
                db_sessions_by_id.pop(bot_id, None)
    except Exception:
        pass

    # 2) ps scan — cobre casos onde o DB falhou em registrar
    try:
        r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, check=False)
        out = (r.stdout or "").splitlines()
        for line in out[1:]:
            line = line.strip()
            if not line:
                continue
            try:
                pid_s, args_s = line.split(None, 1)
                pid_i = int(pid_s)
            except Exception:
                continue
            if "bot_core.py" not in args_s:
                continue
            try:
                argv = shlex.split(args_s)
            except Exception:
                argv = args_s.split()
            if "--bot-id" in argv:
                try:
                    idx = argv.index("--bot-id")
                    bot_id = argv[idx + 1]
                except Exception:
                    bot_id = None
                if bot_id:
                    ps_pids_by_id[str(bot_id)] = pid_i
    except Exception:
        pass

    # Merge em st.session_state.active_bots preservando ordem e removendo mortos
    discovered_ids: list[str] = []
    for bot_id, sess in db_sessions_by_id.items():
        pid = sess.get("pid")
        # Se tem PID válido, verificar se está vivo; senão, confiar no status
        if pid and _pid_alive(pid):
            discovered_ids.append(bot_id)
        elif sess.get("status") == "running":
            # Bot marcado como running sem PID verificável (pode estar em container)
            discovered_ids.append(bot_id)
            
    for bot_id, pid in ps_pids_by_id.items():
        if _pid_alive(pid) and bot_id not in discovered_ids:
            discovered_ids.append(bot_id)

    controller_alive: list[str] = []
    try:
        for bot_id, proc in getattr(controller, "processes", {}).items():
            try:
                if proc is not None and proc.poll() is None:
                    controller_alive.append(str(bot_id))
            except Exception:
                continue
    except Exception:
        pass

    alive_set = set(discovered_ids) | set(controller_alive)

    merged_active: list[str] = []
    for b in (list(st.session_state.active_bots) + discovered_ids):
        if not b:
            continue
        if b not in merged_active:
            merged_active.append(b)
    # Remove stale entries that have no live PID/process backing.
    st.session_state.active_bots = [b for b in merged_active if b in alive_set]

    # =====================================================
    # DASHBOARD LAYOUT (boas práticas: cards + hierarquia)
    # =====================================================
    sidebar_controller = SidebarController()
    # Sidebar controls
    try:
        sidebar_controller.render_balances(st.sidebar)
        st.sidebar.divider()
        sidebar_controller.render_inputs(st.sidebar)
    except Exception as e:
        st.error(f"Erro no sidebar: {e}")

    # Prepare theme and semaphore snapshot for rendering in the main layout
    try:
        theme = get_current_theme()
    except Exception:
        theme = {}

    try:
        symbol_for_ai = st.session_state.get("symbol")
        if not symbol_for_ai and st.session_state.get("selected_bot"):
            try:
                sess = db_sessions_by_id.get(str(st.session_state.get("selected_bot")))
                symbol_for_ai = sess.get("symbol") if sess else None
            except Exception:
                symbol_for_ai = None

        snapshot = _get_strategy_snapshot_cached(str(symbol_for_ai)) if symbol_for_ai else None
    except Exception:
        snapshot = None

    # adjust columns so the right column fills all remaining space responsively
    # use a very large relative ratio for the right column so it expands to fill the frame
    # PAINEL DE CONTROLE (empilhado acima dos bots ativos)
    # Theme selector: render inside Streamlit sidebar menu (expander)
    try:
        exp = st.sidebar.expander("🎨 Tema do Terminal", expanded=False)
        render_theme_selector(ui=exp)
    except Exception:
        try:
            render_theme_selector(ui=st.sidebar)
        except Exception:
            pass

    # Pipelines panel in sidebar: quick view of recent GitHub Actions runs
    try:
        with st.sidebar.expander("🔁 Pipelines (CI/CD)", expanded=False):
            try:
                import requests
                owner = "eddiejdi"
                repo = "AutoCoinBot"
                gh_token = None
                try:
                    gh_token = st.secrets.get("GITHUB_TOKEN")
                except Exception:
                    gh_token = None
                if not gh_token:
                    gh_token = os.getenv("GITHUB_TOKEN")
                if not gh_token:
                    gh_token = st.session_state.get("_gh_token_temp")

                if not gh_token:
                    t = st.text_input("GitHub token (optional)", value="", type="password", key="gh_token_input")
                    if t:
                        st.session_state["_gh_token_temp"] = t
                        gh_token = t

                headers = {"Accept": "application/vnd.github+json"}
                if gh_token:
                    headers["Authorization"] = f"token {gh_token}"

                api_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=10"
                resp = requests.get(api_url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    st.error(f"GitHub API error: {resp.status_code}")
                else:
                    data = resp.json()
                    runs = data.get("workflow_runs", []) or []
                    if not runs:
                        st.info("Nenhum run recente encontrado.")
                    else:
                        try:
                            import pandas as _pd
                            rows = []
                            for r in runs:
                                rows.append({
                                    "Workflow": r.get("name") or r.get("path"),
                                    "Branch": r.get("head_branch"),
                                    "Status": r.get("status"),
                                    "Conclusion": r.get("conclusion") or "",
                                    "Created": r.get("created_at"),
                                    "URL": r.get("html_url"),
                                })
                            df = _pd.DataFrame(rows)
                            df["Open"] = df["URL"].apply(lambda u: f"[open]({u})" if u else "")
                            st.table(df[["Workflow", "Branch", "Status", "Conclusion", "Created", "Open"]])
                        except Exception:
                            for r in runs:
                                st.markdown(f"- **{r.get('name')}** ({r.get('head_branch')}) — {r.get('status')}/{r.get('conclusion')} — [{r.get('created_at')}]({r.get('html_url')})")
            except Exception as e:
                st.error(f"Erro ao obter runs: {e}")
    except Exception:
        pass

    st.subheader("🚀 Bot Control")
    col1, col2 = st.columns(2)
    with col1:
        start_real = st.button("▶️ START (REAL)", type="primary", key="start_real")
    with col2:
        kill_bot = st.button("🛑 KILL BOT", type="secondary", key="kill_bot")
    start_dry = st.button("🧪 START (DRY-RUN)", key="start_dry")
    num_bots = st.session_state.get("num_bots", 1)

    # STATUS + BOTS ATIVOS (logo abaixo do painel de controle)
    with _safe_container(border=True):
        st.subheader("📋 Status")
        selected_bot_txt = st.session_state.get("selected_bot")
        api_port_txt = st.session_state.get("_api_port")
        st.caption(
            f"Bot selecionado: {str(selected_bot_txt)[:12] + '…' if selected_bot_txt else '(nenhum)'} | "
            f"API local: {api_port_txt if api_port_txt else '(indisponível)'}"
        )

        # Semáforo de estratégia (restaurado ao centro do dashboard)
        try:
            if snapshot:
                components.html(render_strategy_semaphore(snapshot, theme), height=95)
        except Exception:
            pass

    with _safe_container(border=True):
        st.subheader("📰 Lançamentos de Carteiras (RSS)")
        if render_wallet_releases_widget is None:
            st.caption("RSS indisponível (módulo não carregou).")
        else:
            # Compact + scrollable + autorefresh (real-time-ish)
            render_wallet_releases_widget(
                theme,
                height_px=210,
                limit=18,
                refresh_ms=30000,
                key="dash_wallet_rss",
            )

    with _safe_container(border=True):
        active_bots = st.session_state.active_bots
        if active_bots:
            st.subheader(f"🤖 Bots Ativos ({len(active_bots)})")

            # Header row
            header_cols = st.columns([0.5, 2.5, 3.5, 1.5])
            header_cols[0].markdown("**☑️**")
            header_cols[1].markdown("**🆔 Bot ID**")
            header_cols[2].markdown("**📝 Último Evento**")
            header_cols[3].markdown("**📜 Log**")

            db_for_logs = DatabaseManager()
            
            # Initialize selected bots in session state
            if "kill_selected_bots" not in st.session_state:
                st.session_state.kill_selected_bots = set()

            for bot_id in list(active_bots):
                sess = db_sessions_by_id.get(str(bot_id))
                
                # Get last event from logs
                last_event = "Sem eventos"
                try:
                    logs = db_for_logs.get_bot_logs(bot_id, limit=1)
                    if logs:
                        last_log = logs[0]
                        msg = last_log.get('message', '')
                        ts = last_log.get('timestamp', '')
                        if len(msg) > 50:
                            msg = msg[:50] + "..."
                        last_event = f"{ts[:19] if ts else ''} - {msg}"
                except Exception:
                    pass

                row = st.columns([0.5, 2.5, 3.5, 1.5])
                
                # Checkbox para seleção
                is_selected = row[0].checkbox(
                    "sel",
                    key=f"sel_{bot_id}",
                    value=bot_id in st.session_state.kill_selected_bots,
                    label_visibility="collapsed"
                )
                if is_selected:
                    st.session_state.kill_selected_bots.add(bot_id)
                else:
                    st.session_state.kill_selected_bots.discard(bot_id)
                
                # Bot ID
                row[1].code(str(bot_id)[:12])
                
                # Último Evento
                row[2].caption(last_event)
                
                # Abrir Log button - abre a view monitor do Streamlit
                log_url = f"/?view=monitor&bot={bot_id}"
                if hasattr(st, "link_button"):
                    row[3].link_button("📜 Log", log_url, use_container_width=True)
                else:
                    row[3].markdown(f'<a href="{log_url}" target="_blank">📜 Log</a>', unsafe_allow_html=True)

            # Botão Kill único para os selecionados
            st.markdown("---")
            kill_cols = st.columns([3, 1])
            selected_count = len(st.session_state.kill_selected_bots)
            kill_cols[0].caption(f"🎯 {selected_count} bot(s) selecionado(s)")
            
            if kill_cols[1].button(
                f"🛑 Kill Selecionados",
                disabled=selected_count == 0,
                type="primary" if selected_count > 0 else "secondary",
                use_container_width=True
            ):
                killed = []
                for bot_id in list(st.session_state.kill_selected_bots):
                    try:
                        sess = db_sessions_by_id.get(str(bot_id))
                        pid = sess.get("pid") if sess else None
                        if pid:
                            _kill_pid_sigkill_only(int(pid))
                        controller.stop_bot(str(bot_id))
                        DatabaseManager().update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
                        st.session_state.active_bots = [b for b in st.session_state.active_bots if b != bot_id]
                        killed.append(str(bot_id)[:8])
                    except Exception as e:
                        st.error(f"Erro ao encerrar {str(bot_id)[:8]}: {e}")
                
                if killed:
                    st.session_state.kill_selected_bots.clear()
                    st.success(f"✅ Bots encerrados: {', '.join(killed)}")
                    st.rerun()
        else:
            st.info("🚦 Nenhum bot ativo. Use os controles à esquerda para iniciar um novo bot.")

        with _safe_container(border=True):
            # Bots encerrados hoje (sessões com end_ts dentro do dia atual)
            stopped_today: list[dict] = []
            trade_agg_today: dict[str, dict] = {}
            try:
                import datetime as _dt

                now = _dt.datetime.now()
                start_day = _dt.datetime(now.year, now.month, now.day)
                start_ts = float(start_day.timestamp())
                end_ts = start_ts + 86400.0

                db_today = DatabaseManager()
                conn_today = db_today.get_connection()
                cur_today = conn_today.cursor()
                cur_today.execute(
                    """
                    SELECT id, status, pid, symbol, mode, entry_price, start_ts, end_ts, dry_run
                    FROM bot_sessions
                    WHERE COALESCE(status, '') != 'running'
                      AND end_ts IS NOT NULL
                      AND end_ts >= ? AND end_ts < ?
                    ORDER BY COALESCE(end_ts, 0) DESC
                    LIMIT 20
                    """,
                    (start_ts, end_ts),
                )
                stopped_today = [dict(r) for r in (cur_today.fetchall() or [])]

                # Aggregates (lucro + trades) para mostrar no progresso
                bot_ids = [str(s.get("id")) for s in stopped_today if s.get("id")]
                if bot_ids:
                    placeholders = ",".join(["?"] * len(bot_ids))
                    cur_today.execute(
                        f"""
                        SELECT bot_id,
                               COUNT(1) AS trades,
                               COALESCE(SUM(COALESCE(profit,0)),0) AS profit_sum
                        FROM trades
                        WHERE bot_id IN ({placeholders})
                        GROUP BY bot_id
                        """,
                        tuple(bot_ids),
                    )
                    for r in (cur_today.fetchall() or []):
                        d = dict(r)
                        bid = str(d.get("bot_id") or "")
                        if bid:
                            trade_agg_today[bid] = d

                try:
                    conn_today.close()
                except Exception:
                    pass
            except Exception:
                stopped_today = []
                trade_agg_today = {}

            st.subheader(f"🧾 Bots Encerrados Hoje ({len(stopped_today)})")

            header_cols = st.columns([2.0, 1.8, 1.0, 2.7, 1.4, 1.7])
            header_cols[0].markdown("**🆔 Bot ID**")
            header_cols[1].markdown("**📊 Símbolo**")
            header_cols[2].markdown("**⚙️ Modo**")
            header_cols[3].markdown("**📑 Relatório**")
            header_cols[4].markdown("**🛑 Kill**")
            header_cols[5].markdown("**📈 Progresso**")

            if not stopped_today:
                st.caption("Nenhum bot encerrado hoje.")
            else:
                target_pct_global = st.session_state.get("target_profit_pct", 2.0)

                # Reusar o mesmo servidor/links do bloco de ativos
                api_port = st.session_state.get("_api_port")
                try:
                    if not api_port and 'start_api_server' in globals():
                        p = start_api_server(8765)
                        if p:
                            st.session_state["_api_port"] = int(p)
                            api_port = int(p)
                except Exception:
                    pass

                for sess in stopped_today:
                    bot_id = str(sess.get("id") or "")
                    if not bot_id:
                        continue

                    symbol = sess.get("symbol") or "N/A"
                    mode = sess.get("mode") or "N/A"
                    end_ts_val = sess.get("end_ts")
                    end_txt = _fmt_ts(end_ts_val)

                    ta = trade_agg_today.get(bot_id, {})
                    try:
                        profit_sum = float(ta.get("profit_sum") or 0.0)
                    except Exception:
                        profit_sum = 0.0
                    try:
                        trades_n = int(ta.get("trades") or 0)
                    except Exception:
                        trades_n = 0

                    row = st.columns([2.0, 1.8, 1.0, 2.7, 1.4, 1.7])
                    row[0].write(str(bot_id)[:12])
                    row[1].write(symbol)
                    row[2].write(str(mode).upper())

                    with row[3]:
                        c_log, c_rep = st.columns(2)
                        if not api_port:
                            c_log.caption("LOG: off")
                            c_rep.caption("REP: off")
                        else:
                            theme_query = str(theme_qs).lstrip('&')
                            base = f"http://127.0.0.1:{int(api_port)}"
                            try:
                                try:
                                    st_port = int(st.get_option("server.port"))
                                except Exception:
                                    st_port = 8501
                                home_url = f"http://127.0.0.1:{st_port}/?view=dashboard"
                                home_val = urllib.parse.quote(home_url, safe='')
                            except Exception:
                                home_val = ''

                            log_url = (
                                f"{base}/monitor?{theme_query}&home={home_val}&bot={urllib.parse.quote(str(bot_id))}"
                                if theme_query
                                else f"{base}/monitor?home={home_val}&bot={urllib.parse.quote(str(bot_id))}"
                            )
                            rep_url = (
                                f"{base}/report?{theme_query}&home={home_val}&bot={urllib.parse.quote(str(bot_id))}"
                                if theme_query
                                else f"{base}/report?home={home_val}&bot={urllib.parse.quote(str(bot_id))}"
                            )

                            if hasattr(st, "link_button"):
                                c_log.link_button("📜 LOG", log_url, use_container_width=True)
                                c_rep.link_button("📑 REL.", rep_url, use_container_width=True)
                            else:
                                c_log.markdown(
                                    f'<a href="{log_url}" target="_blank" rel="noopener noreferrer">📜 LOG</a>',
                                    unsafe_allow_html=True,
                                )
                                c_rep.markdown(
                                    f'<a href="{rep_url}" target="_blank" rel="noopener noreferrer">📑 REL.</a>',
                                    unsafe_allow_html=True,
                                )

                    # Kill não faz sentido para sessão já encerrada
                    row[4].button("✅ Enc.", key=f"kill_stopped_{bot_id}", disabled=True, use_container_width=True)

                    # Progresso: concluído + resumo de lucro/trades (mantém a mesma coluna visual)
                    row[5].progress(1.0)
                    row[5].caption(
                        f"Encerrado {end_txt} • Realizado ${profit_sum:+.2f} • Trades {trades_n} • alvo {float(target_pct_global):.2f}%"
                    )

    # =====================================================
    # TRATAMENTO DOS BOTÕES
    # =====================================================
    if start_real or start_dry:
        try:
            if not st.session_state.get("controller"):
                st.error("Controller não disponível. Tente recarregar a página.")
                return
            
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
            num_bots = st.session_state.get("num_bots", 1)
            
            # Iniciar múltiplos bots se num_bots > 1
            started_bots = []
            for i in range(num_bots):
                try:
                    # Pequena variação nos parâmetros para bots múltiplos
                    varied_entry = float(entry) * (1 + (i * 0.001))  # Variação de 0.1% por bot
                    varied_size = float(size) * (1 + (i * 0.01))    # Variação de 1% no size
                    
                    bot_id_started = st.session_state.controller.start_bot(
                        symbol, varied_entry, mode, targets,
                        float(interval), varied_size, float(funds), start_dry,
                        eternal_mode=eternal_mode,
                    )
                    
                    started_bots.append(bot_id_started)
                    
                    # Adiciona à lista de bots ativos
                    if bot_id_started not in st.session_state.active_bots:
                        st.session_state.active_bots.append(bot_id_started)
                        
                except Exception as bot_error:
                    st.warning(f"Erro ao iniciar bot {i+1}: {bot_error}")
                    continue
            
            if started_bots:
                st.session_state.selected_bot = started_bots[0]  # Seleciona o primeiro
                st.session_state.bot_running = True
                time.sleep(0.5)
                
                # Navegar para o monitor (mesma aba) após iniciar
                _merge_query_params({"bot": started_bots[0], "view": "monitor"})
                bot_count = len(started_bots)
                st.success(f"✅ {bot_count} bot{'s' if bot_count > 1 else ''} iniciado{'s' if bot_count > 1 else ''}! Abrindo Monitor na mesma aba.")
                st.rerun()
            else:
                st.error("Falha ao iniciar todos os bots.")
                
        except Exception as e:
            st.error(f"Erro ao iniciar bots: {e}")

    # =====================================================
    # TELA PRINCIPAL
    # =====================================================
    # Aqui só chegamos se NÃO estivermos em modo janela

