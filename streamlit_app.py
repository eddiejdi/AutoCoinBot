"""Shim for moved module: streamlit_app."""
from autocoinbot.streamlit_app import *

if __name__ == "__main__":
    import autocoinbot.streamlit_app as _m
    _main = getattr(_m, "main", None)
    if callable(_main):
        _main()
