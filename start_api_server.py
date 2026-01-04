"""Shim for moved module: start_api_server."""
from autocoinbot.start_api_server import *

if __name__ == "__main__":
    import autocoinbot.start_api_server as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
