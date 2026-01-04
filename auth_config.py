"""Shim for moved module: auth_config."""
from autocoinbot.auth_config import *

if __name__ == "__main__":
    import autocoinbot.auth_config as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
