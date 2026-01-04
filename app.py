"""Shim for moved module: app."""
from autocoinbot.app import *

if __name__ == "__main__":
    import autocoinbot.app as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
