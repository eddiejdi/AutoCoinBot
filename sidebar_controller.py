"""Shim for moved module: sidebar_controller."""
from autocoinbot.sidebar_controller import *

if __name__ == "__main__":
    import autocoinbot.sidebar_controller as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
