"""Shim for moved module: terminal_component."""
from autocoinbot.terminal_component import *

if __name__ == "__main__":
    import autocoinbot.terminal_component as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
