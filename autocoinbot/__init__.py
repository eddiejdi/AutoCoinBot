"""
AutoCoinBot package bootstrapper.

Aggregates core modules in a single namespace for backward compatibility.
"""

__all__ = [
    "api",
    "app",
    "auth_config",
    "balance",
    "bot",
    "bot_controller",
    "bot_core",
    "bot_registry",
    "bot_session",
    "cleanup_dead_bots",
    "database",
    "dashboard",
    "equity",
    "log_colorizer",
    "market",
    "public_flow_intel",
    "risk_manager",
    "sidebar_controller",
    "simple_terminal",
    "streamlit_app",
    "terminal_component",
    "ui",
    "start_api_server",
]

from importlib import import_module as _import

for _mod in __all__:
    try:
        globals()[_mod] = _import(f"{__name__}.{_mod}")
    except Exception:
        # Módulos opcionais podem não carregar se dependências faltarem.
        pass

del _import
