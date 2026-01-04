"""Shim for moved module: bot."""
from autocoinbot.bot import *

if __name__ == "__main__":
    import autocoinbot.bot as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
