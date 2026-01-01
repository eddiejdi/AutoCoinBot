#!/usr/bin/env python3
"""
Cross-platform start helper for AutoCoinBot.

Usage:
  python scripts/start.py [--detach]

Behavior:
  - Detecta Windows vs Linux/WSL
  - Cria `.env` a partir de `.env.example` se necessário
  - Cria/ativa `venv`, instala `requirements.txt`
  - Inicia Streamlit (em background se `--detach` for passado)
  - Grava PID no arquivo `streamlit.pid` e logs em `streamlit.log`

Designed to replace separate start scripts for Linux and Windows.
"""

from __future__ import annotations
import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse


ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / "venv"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
STREAMLIT_LOG = ROOT / "streamlit.log"
PID_FILE = ROOT / "streamlit.pid"


def copy_env_if_missing():
    if not ENV_FILE.exists() and ENV_EXAMPLE.exists():
        try:
            shutil.copy(ENV_EXAMPLE, ENV_FILE)
            print("Created .env from .env.example (edit with real secrets)")
        except Exception as e:
            print("Warning: could not copy .env.example:", e)


def ensure_venv():
    python = sys.executable
    if not VENV_DIR.exists():
        print("Creating virtualenv in venv/")
        subprocess.check_call([python, "-m", "venv", str(VENV_DIR)])


def get_venv_python() -> str:
    if sys.platform.startswith("win"):
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def pip_install(requirements: str = "requirements.txt"):
    vpy = get_venv_python()
    if not Path(vpy).exists():
        raise RuntimeError("venv python not found: " + vpy)
    print("Installing requirements...")
    subprocess.check_call([vpy, "-m", "pip", "install", "-r", requirements])


def start_streamlit(detach: bool = True):
    vpy = get_venv_python()
    cmd = [vpy, "-m", "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]

    # Redirect outputs to streamlit.log
    logf = open(STREAMLIT_LOG, "a", buffering=1)

    if sys.platform.startswith("win"):
        # Windows: use creationflags to detach if requested
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        flags = 0
        if detach:
            flags = CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS
        proc = subprocess.Popen(cmd, stdout=logf, stderr=logf, cwd=str(ROOT), creationflags=flags)
    else:
        # POSIX: start daemonized process via Popen and close file descriptors
        proc = subprocess.Popen(cmd, stdout=logf, stderr=logf, cwd=str(ROOT), preexec_fn=os.setpgrp)

    pid = proc.pid
    try:
        with open(PID_FILE, "w") as pf:
            pf.write(str(pid))
    except Exception:
        pass
    print(f"Started Streamlit (pid={pid}), logs -> {STREAMLIT_LOG}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--detach", action="store_true", help="run Streamlit detached/in background")
    args = parser.parse_args()

    copy_env_if_missing()
    ensure_venv()
    try:
        pip_install()
    except subprocess.CalledProcessError as e:
        print("pip install failed:", e)
        print("Continuing — if dependencies are already installed this may be fine.")

    start_streamlit(detach=args.detach)


if __name__ == "__main__":
    main()
