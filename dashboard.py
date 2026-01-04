"""Shim for moved module: dashboard."""
from autocoinbot.dashboard import *

if __name__ == "__main__":
    import autocoinbot.dashboard as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
