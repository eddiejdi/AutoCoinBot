
"""Wallet releases RSS/Atom widget.

Goal:
- Provide a compact, scrollable, fail-fast widget for the Dashboard.
- Keep data rich (tag/version, date, summary) to support future features (e.g., copy-bot start).

Design constraints:
- Avoid blocking Streamlit render: short timeouts + caching.
- Avoid expanding layout: fixed-height scroll container.
"""

from __future__ import annotations
import time
from typing import Any

import requests
import streamlit as st
import streamlit.components.v1 as components
import html


WALLET_RELEASE_FEEDS: list[dict[str, str]] = [
    {"name": "MetaMask", "url": "https://github.com/MetaMask/metamask-extension/releases.atom"},
    {"name": "Ledger Live", "url": "https://github.com/LedgerHQ/ledger-live/releases.atom"},
    {"name": "Trezor Suite", "url": "https://github.com/trezor/trezor-suite/releases.atom"},
    {"name": "Rabby", "url": "https://github.com/RabbyHub/Rabby/releases.atom"},
    {"name": "Trust Wallet (core)", "url": "https://github.com/trustwallet/wallet-core/releases.atom"},
]


def _strip_html_to_text(value: Any) -> str:
    if value is None:
        return ""
    s = str(value)
    try:
        import re

        s = re.sub(r"<[^>]+>", " ", s)
        s = html.unescape(s)
        s = re.sub(r"\s+", " ", s).strip()
    except Exception:
        s = html.unescape(s).strip()
    return s


def _extract_release_tag(title: str, link: str) -> str:
    t = str(title or "")
    l = str(link or "")
    try:
        import re

        m = re.search(r"/tag/([^/?#]+)", l)
        if m:
            return m.group(1)
        m2 = re.search(r"\b(v?\d+(?:\.\d+){1,3}(?:[-+._a-zA-Z0-9]+)?)\b", t)
        if m2:
            return m2.group(1)
    except Exception:
        return ""
    return ""


@st.cache_data(ttl=120, show_spinner=False)
def get_wallet_release_items(limit: int = 20) -> list[dict[str, Any]]:
    """Return enriched release items across multiple wallet feeds.

    Each item contains:
    - id, wallet, title, tag, link, ts, published, summary

    NOTE: cached to avoid repeated network calls.
    """
    try:
        import feedparser  # type: ignore
    except Exception:
        return []

    headers = {"User-Agent": "kucoin_app/1.0 (+streamlit; rss)"}
    items: list[dict[str, Any]] = []

    for feed in WALLET_RELEASE_FEEDS:
        wallet = str(feed.get("name") or "").strip()
        url = str(feed.get("url") or "").strip()
        if not wallet or not url:
            continue

        try:
            r = requests.get(url, timeout=3.0, headers=headers)
            if int(getattr(r, "status_code", 0) or 0) >= 400:
                continue
            parsed = feedparser.parse(r.text or "")
        except Exception:
            continue

        for e in (getattr(parsed, "entries", None) or [])[:8]:
            title = str(e.get("title") or "")
            link = str(e.get("link") or "")

            published_ts = 0.0
            try:
                pp = e.get("published_parsed") or e.get("updated_parsed")
                if pp:
                    published_ts = float(time.mktime(pp))
            except Exception:
                published_ts = 0.0

            published_txt = ""
            try:
                published_txt = str(e.get("published") or e.get("updated") or "")
            except Exception:
                published_txt = ""

            summary_raw = ""
            try:
                content = e.get("content")
                if isinstance(content, list) and content:
                    summary_raw = str(content[0].get("value") or "")
            except Exception:
                summary_raw = ""
            if not summary_raw:
                try:
                    summary_raw = str(e.get("summary") or "")
                except Exception:
                    summary_raw = ""

            summary = _strip_html_to_text(summary_raw)
            tag = _extract_release_tag(title, link)

            item_id = ""
            try:
                item_id = str(e.get("id") or e.get("guid") or link or "")
            except Exception:
                item_id = str(link or "")

            items.append(
                {
                    "id": item_id,
                    "wallet": wallet,
                    "title": title,
                    "tag": tag,
                    "link": link,
                    "ts": published_ts,
                    "published": published_txt,
                    "summary": summary,
                    "source": "rss",
                }
            )

    items.sort(key=lambda d: float(d.get("ts") or 0.0), reverse=True)
    if limit and int(limit) > 0:
        return items[: int(limit)]
    return items


def _render_scroll_html(items: list[dict[str, Any]], theme: dict, height_px: int) -> str:
    bg = theme.get("bg2", theme.get("bg", "#0E1117"))
    border = theme.get("border", "rgba(255,255,255,0.12)")
    text = theme.get("text", "#FFFFFF")

    rows = []
    for it in items:
        wallet = html.escape(str(it.get("wallet") or ""))
        title = html.escape(str(it.get("title") or ""))
        tag = html.escape(str(it.get("tag") or "")).strip()
        link = str(it.get("link") or "").strip()
        summary = html.escape(str(it.get("summary") or ""))

        dt_txt = ""
        ts = float(it.get("ts") or 0.0)
        if ts > 0:
            try:
                import datetime as dt

                dt_txt = dt.datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")
            except Exception:
                dt_txt = ""

        meta = " • ".join([p for p in [tag, dt_txt] if p])
        meta_html = f"<div class='kc-rss-meta'>{meta}</div>" if meta else ""

        if link:
            title_html = f"<a class='kc-rss-link' href='{html.escape(link)}' target='_blank' rel='noopener noreferrer'>{title}</a>"
        else:
            title_html = f"<span class='kc-rss-title'>{title}</span>"

        # Keep it compact: 1-line title + optional 2-line summary.
        rows.append(
            """
            <div class="kc-rss-item">
              <div class="kc-rss-head">
                <span class="kc-rss-wallet">{wallet}</span>
                {meta_html}
              </div>
              <div class="kc-rss-main">{title_html}</div>
              <div class="kc-rss-summary">{summary}</div>
            </div>
            """.format(wallet=wallet, meta_html=meta_html, title_html=title_html, summary=summary)
        )

    body = "\n".join(rows) if rows else "<div class='kc-rss-empty'>Sem dados.</div>"

    return f"""
    <div class="kc-rss-wrap" style="background:{bg};border:1px solid {border};border-radius:12px;">
      <div class="kc-rss-scroll" style="max-height:{int(height_px)}px;overflow-y:auto;padding:10px 12px;">
        {body}
      </div>
    </div>

    <style>
      .kc-rss-item {{ padding: 8px 0; border-bottom: 1px solid {border}; }}
      .kc-rss-item:last-child {{ border-bottom: none; }}
      .kc-rss-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; }}
      .kc-rss-wallet {{ color:{text}; font-weight:700; font-size: 12px; opacity:0.95; white-space:nowrap; }}
      .kc-rss-meta {{ color:{text}; font-size: 11px; opacity:0.70; white-space:nowrap; }}
      .kc-rss-main {{ margin-top: 2px; }}
      .kc-rss-link, .kc-rss-title {{ color:{text}; font-size: 12px; text-decoration:none; opacity:0.92; }}
      .kc-rss-link:hover {{ text-decoration: underline; opacity: 1.0; }}
      .kc-rss-summary {{ color:{text}; font-size: 11px; opacity:0.65; margin-top: 2px;
                        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
                        overflow: hidden; }}
      .kc-rss-empty {{ color:{text}; opacity:0.7; font-size: 12px; padding: 6px 0; }}
    </style>
    """


def render_wallet_releases_widget(
    theme: dict,
    *,
    height_px: int = 220,
    limit: int = 18,
    refresh_ms: int = 30000,
    key: str = "wallet_rss",
) -> list[dict[str, Any]]:
    """Render the widget and return items (structured) for future actions.

    - Compact: fixed height + scrolling.
    - Real-time-ish: uses st_autorefresh to refresh periodically.
    """
    # Trigger a periodic rerun so the cache TTL can be refreshed.
    # Optional dependency: if not installed, just skip autorefresh.
    try:
        from streamlit_autorefresh import st_autorefresh  # type: ignore

        st_autorefresh(interval=int(refresh_ms), key=f"{key}_autorefresh")
    except Exception:
        # No autorefresh; widget still works via Streamlit manual reruns.
        pass

    items = get_wallet_release_items(limit=limit)

    # Expose the structured payload for future "copy bot" actions.
    try:
        st.session_state["wallet_rss_items"] = items
    except Exception:
        pass

    html_block = _render_scroll_html(items, theme, height_px=height_px)
    components.html(html_block, height=height_px + 22, scrolling=False)
    return items
