"""Shim for moved module: bot_registry."""
from autocoinbot.bot_registry import *

if __name__ == "__main__":
    import autocoinbot.bot_registry as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
