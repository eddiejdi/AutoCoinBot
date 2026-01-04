"""Shim for moved module: bot_core."""
from autocoinbot.bot_core import *

if __name__ == "__main__":
    import autocoinbot.bot_core as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
