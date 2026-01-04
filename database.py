"""Shim for moved module: database."""
from autocoinbot.database import *

if __name__ == "__main__":
    import autocoinbot.database as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
