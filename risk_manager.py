"""Shim for moved module: risk_manager."""
from autocoinbot.risk_manager import *

if __name__ == "__main__":
    import autocoinbot.risk_manager as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
