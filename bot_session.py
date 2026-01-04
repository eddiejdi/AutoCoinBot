"""Shim for moved module: bot_session."""
from autocoinbot.bot_session import *

if __name__ == "__main__":
    import autocoinbot.bot_session as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
