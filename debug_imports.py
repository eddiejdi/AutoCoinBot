#!/usr/bin/env python3
"""Test ui_components imports"""
import sys
sys.path.insert(0, '/home/eddie/AutoCoinBot')

from ui_components import (
    set_logged_in,
    get_current_theme,
    render_top_nav_bar,
    _pid_alive,
    _kill_pid_best_effort,
    inject_global_css,
)

print("All imports OK")
print(f"Functions: {set_logged_in}, {get_current_theme}, {render_top_nav_bar}")
