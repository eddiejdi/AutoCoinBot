"""Shim for moved module: balance."""
from autocoinbot.balance import *

if __name__ == "__main__":
    import autocoinbot.balance as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
