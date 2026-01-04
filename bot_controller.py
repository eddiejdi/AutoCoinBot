"""Shim for moved module: bot_controller."""
from autocoinbot.bot_controller import *

if __name__ == "__main__":
    import autocoinbot.bot_controller as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
