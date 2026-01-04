"""Shim for moved module: log_colorizer."""
from autocoinbot.log_colorizer import *

if __name__ == "__main__":
    import autocoinbot.log_colorizer as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
