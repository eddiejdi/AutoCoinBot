# ui_components/navigation.py
"""Componentes de navegação: barra de navegação, query params, rotas."""

import html
import urllib.parse
import streamlit as st


def _qs_get_any(q, key: str, default=None):
    """Lê um query param que pode ser scalar ou lista."""
    try:
        v = q.get(key, None)
    except Exception:
        v = None
    if v is None:
        return default
    try:
        if isinstance(v, (list, tuple)):
            return v[0] if v else default
    except Exception:
        pass
    return v


def _merge_query_params(updates: dict[str, str | None]):
    """Mescla updates nos query params atuais do Streamlit."""
    try:
        q = st.query_params
    except Exception:
        return

    merged: dict[str, list[str]] = {}
    try:
        for k in q.keys():
            v = q.get(k)
            if isinstance(v, (list, tuple)):
                merged[k] = [str(vv) for vv in v]
            else:
                merged[k] = [str(v)]
    except Exception:
        return

    for k, v in (updates or {}).items():
        if v is None or str(v).strip() == "":
            merged.pop(k, None)
        else:
            merged[k] = [str(v)]

    try:
        qp = st.query_params
        if hasattr(qp, "clear") and hasattr(qp, "update"):
            qp.clear()
            payload: dict[str, str | list[str]] = {}
            for k, vs in merged.items():
                if not vs:
                    continue
                payload[str(k)] = str(vs[0]) if len(vs) == 1 else [str(x) for x in vs]
            qp.update(payload)
            return
    except Exception:
        pass

    try:
        st.query_params = merged
        return
    except Exception:
        pass

    try:
        payload2: dict[str, str] = {}
        for k, vs in merged.items():
            if not vs:
                continue
            payload2[str(k)] = str(vs[0])
        st.experimental_set_query_params(**payload2)
    except Exception:
        return


def _build_relative_url_with_query_updates(updates: dict[str, str | None]) -> str:
    """Constrói uma URL relativa como '?a=1&b=2' mesclando query params."""
    try:
        q = st.query_params
    except Exception:
        q = {}

    merged: dict[str, list[str]] = {}
    try:
        for k in getattr(q, "keys", lambda: [])():
            v = q.get(k)
            if isinstance(v, (list, tuple)):
                merged[k] = [str(vv) for vv in v]
            else:
                merged[k] = [str(v)]
    except Exception:
        merged = {}

    for k, v in (updates or {}).items():
        if v is None or str(v).strip() == "":
            merged.pop(k, None)
        else:
            merged[k] = [str(v)]

    items: list[tuple[str, str]] = []
    for k, vs in merged.items():
        for vv in (vs or []):
            items.append((str(k), str(vv)))

    qs = urllib.parse.urlencode(items, doseq=True)
    return f"?{qs}" if qs else ""


def _set_view(view: str, bot_id: str | None = None, clear_bot: bool = False):
    """Navega dentro do app Streamlit usando query params."""
    updates: dict[str, str | None] = {
        "view": str(view or "").strip() or None,
        "window": None,
        "report": None,
    }
    if clear_bot:
        updates["bot"] = None
        updates["bot_id"] = None
    if bot_id is not None:
        updates["bot"] = str(bot_id)
    _merge_query_params(updates)


def _hide_sidebar_for_fullscreen_pages():
    """Esconde a sidebar para páginas fullscreen."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            section[data-testid="stSidebar"] { display: none !important; }
            .stMainBlockContainer { padding-top: 1rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _hide_sidebar_everywhere():
    """Sempre esconde a sidebar; navegação é via top bar."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            section[data-testid="stSidebar"] { display: none !important; }
            .stMainBlockContainer { padding-top: 1rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_nav_bar(theme: dict, current_view: str, selected_bot: str | None = None, set_logged_in_func=None):
    """Barra de navegação horizontal no topo de todas as páginas."""
    try:
        view = str(current_view or "dashboard").strip().lower()
    except Exception:
        view = "dashboard"

    # Botão de logout no topo direito
    col_logout = st.columns([10, 1])[1]
    logout_key = f"logout_btn_{view}_{abs(hash(str(selected_bot or 'none')))}"
    if col_logout.button("🚪 Logout", key=logout_key):
        if set_logged_in_func:
            set_logged_in_func(False)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown(
        f"""
        <style>
          .kc-nav-wrap {{
            border: 1px solid {theme.get('border')};
            background: {theme.get('bg2')};
            border-radius: 10px;
            padding: 10px 10px;
            margin: 6px 0 16px 0;
          }}
          .kc-nav-title {{
            font-family: 'Courier New', monospace;
            font-weight: 800;
            color: {theme.get('accent')};
            font-size: clamp(0.78rem, 0.95vw, 0.95rem);
            text-transform: uppercase;
            letter-spacing: 1px;
          }}
          .kc-nav-sub {{
            font-family: 'Courier New', monospace;
            color: {theme.get('text2')};
            font-size: clamp(0.72rem, 0.85vw, 0.9rem);
          }}
          .kc-link-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            background: {theme.get('bg2')};
            color: {theme.get('text')};
            border: 2px solid {theme.get('border')};
            border-radius: 8px;
            padding: clamp(0.55rem, 0.9vw, 0.7rem) clamp(0.85rem, 1.2vw, 1.05rem);
            min-height: 44px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            text-transform: uppercase;
            text-decoration: none;
            font-size: clamp(0.78rem, 0.95vw, 0.95rem);
          }}
          .kc-link-btn:hover {{
            filter: brightness(1.05);
            text-decoration: none;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown(
            f"""
            <div class="kc-nav-wrap">
              <div class="kc-nav-title">NAVEGAÇÃO</div>
              <div class="kc-nav-sub">Dashboard • Relatório</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    cols = st.columns([1.15, 1.15, 4.70])
    dash_active = (view == "dashboard")
    report_active = (view == "report")

    if cols[0].button("🏠 Home", type="primary" if dash_active else "secondary", use_container_width=True, key="nav_home"):
        try:
            st.session_state.selected_bot = None
        except Exception:
            pass
        _set_view("dashboard", clear_bot=True)
        st.rerun()

    if cols[1].button("📑 Relatório", type="primary" if report_active else "secondary", use_container_width=True, key="nav_rep"):
        _set_view("report", bot_id=selected_bot)
        st.rerun()

    try:
        bot_txt = (str(selected_bot)[:12] + "…") if selected_bot else "(nenhum bot selecionado)"
    except Exception:
        bot_txt = "(nenhum bot selecionado)"
    cols[2].markdown(
        f"<div style=\"text-align:right;font-family:'Courier New',monospace;font-size:clamp(0.78rem,0.95vw,0.95rem);color:{theme.get('muted','#8b949e')};padding-top:10px;\">Bot: <b style=\"color:{theme.get('text')};\">{html.escape(bot_txt)}</b></div>",
        unsafe_allow_html=True,
    )
