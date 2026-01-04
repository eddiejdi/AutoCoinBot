"""Shim for moved module: equity."""
from autocoinbot.equity import *

if __name__ == "__main__":
    import autocoinbot.equity as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
