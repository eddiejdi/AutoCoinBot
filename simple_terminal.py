"""Shim for moved module: simple_terminal."""
from autocoinbot.simple_terminal import *

if __name__ == "__main__":
    import autocoinbot.simple_terminal as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
