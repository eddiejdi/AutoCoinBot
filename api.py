"""Shim for moved module: api."""
from autocoinbot.api import *

if __name__ == "__main__":
    import autocoinbot.api as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
