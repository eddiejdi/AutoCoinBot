# ui_components - Módulos separados da UI
"""
Componentes modulares da interface:
- utils: funções utilitárias (pid, kill, helpers)
- theme: gerenciamento de temas e CSS
- gauges: componentes visuais (gauges, semáforos)
- terminal: componentes de terminal e logs
- navigation: barra de navegação e rotas
- dashboard: dashboard principal e widgets
"""

from .utils import (
    set_logged_in,
    _pid_alive,
    _kill_pid_best_effort,
    _kill_pid_sigkill_only,
    _safe_container,
    _fmt_ts,
    _safe_float,
    _contrast_text_for_bg,
)

from .theme import (
    THEMES,
    get_current_theme,
    inject_global_css,
    render_theme_selector,
    render_html_smooth,
    _load_saved_theme,
    _save_theme,
)

from .navigation import (
    render_top_nav_bar,
    _set_view,
    _qs_get_any,
    _merge_query_params,
    _build_relative_url_with_query_updates,
    _hide_sidebar_for_fullscreen_pages,
    _hide_sidebar_everywhere,
)

__all__ = [
    # utils
    "set_logged_in",
    "_pid_alive",
    "_kill_pid_best_effort",
    "_kill_pid_sigkill_only",
    "_safe_container",
    "_fmt_ts",
    "_safe_float",
    "_contrast_text_for_bg",
    # theme
    "THEMES",
    "get_current_theme",
    "inject_global_css",
    "render_theme_selector",
    "render_html_smooth",
    "_load_saved_theme",
    "_save_theme",
    # navigation
    "render_top_nav_bar",
    "_set_view",
    "_qs_get_any",
    "_merge_query_params",
    "_build_relative_url_with_query_updates",
    "_hide_sidebar_for_fullscreen_pages",
    "_hide_sidebar_everywhere",
]
