"""Shim for moved module: public_flow_intel."""
from autocoinbot.public_flow_intel import *

if __name__ == "__main__":
    import autocoinbot.public_flow_intel as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
