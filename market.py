"""Shim for moved module: market."""
from autocoinbot.market import *

if __name__ == "__main__":
    import autocoinbot.market as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
