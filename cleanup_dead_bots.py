"""Shim for moved module: cleanup_dead_bots."""
from autocoinbot.cleanup_dead_bots import *

if __name__ == "__main__":
    import autocoinbot.cleanup_dead_bots as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
