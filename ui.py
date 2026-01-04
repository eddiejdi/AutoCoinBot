"""Shim for moved module: ui."""
from autocoinbot.ui import *

if __name__ == "__main__":
    import autocoinbot.ui as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
