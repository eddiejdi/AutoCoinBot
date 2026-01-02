# ui_components/utils.py
"""Funções utilitárias para a UI: gerenciamento de processos, helpers, etc."""

import os
import signal
import time
import streamlit as st
from pathlib import Path

# Persistência de login
LOGIN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.login_status')


def set_logged_in(status: bool) -> None:
    """Define o status de login persistente."""
    if status:
        with open(LOGIN_FILE, 'w') as f:
            f.write('logged_in')
    else:
        if os.path.exists(LOGIN_FILE):
            os.remove(LOGIN_FILE)


def _pid_alive(pid: int | None) -> bool:
    """Verifica se um processo com o PID dado está vivo."""
    if pid is None:
        return False
    try:
        pid_i = int(pid)
    except Exception:
        return False
    if pid_i <= 0:
        return False
    try:
        os.kill(pid_i, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _kill_pid_best_effort(pid: int, timeout_s: float = 0.4) -> bool:
    """Tenta SIGTERM e depois SIGKILL. Retorna True se o processo foi encerrado."""
    try:
        pid_i = int(pid)
    except Exception:
        return False
    if pid_i <= 0:
        return False
    if not _pid_alive(pid_i):
        return True

    pgrp = None
    try:
        pgrp = os.getpgid(pid_i)
    except Exception:
        pgrp = None

    def _kill_term():
        if pgrp and pgrp > 0:
            try:
                if pgrp != os.getpgrp():
                    os.killpg(pgrp, signal.SIGTERM)
                    return
            except Exception:
                pass
        try:
            os.kill(pid_i, signal.SIGTERM)
        except Exception:
            pass

    def _kill_kill():
        if pgrp and pgrp > 0:
            try:
                if pgrp != os.getpgrp():
                    os.killpg(pgrp, signal.SIGKILL)
                    return
            except Exception:
                pass
        try:
            os.kill(pid_i, signal.SIGKILL)
        except Exception:
            pass

    _kill_term()
    try:
        time.sleep(max(0.0, float(timeout_s)))
    except Exception:
        pass
    if not _pid_alive(pid_i):
        return True

    _kill_kill()
    try:
        time.sleep(0.1)
    except Exception:
        pass
    return not _pid_alive(pid_i)


def _kill_pid_sigkill_only(pid: int) -> bool:
    """Kill forçado (SIGKILL / kill -9). Retorna True se o processo foi encerrado."""
    try:
        pid_i = int(pid)
    except Exception:
        return False
    if pid_i <= 0:
        return False
    if not _pid_alive(pid_i):
        return True

    pgrp = None
    try:
        pgrp = os.getpgid(pid_i)
    except Exception:
        pgrp = None

    if pgrp and pgrp > 0:
        try:
            if pgrp != os.getpgrp():
                os.killpg(pgrp, signal.SIGKILL)
        except Exception:
            pass
    try:
        os.kill(pid_i, signal.SIGKILL)
    except Exception:
        pass

    try:
        time.sleep(0.1)
    except Exception:
        pass
    return not _pid_alive(pid_i)


def _safe_container(border: bool = False):
    """Retorna um container com suporte a border (compatível com versões antigas do Streamlit)."""
    try:
        return st.container(border=bool(border))
    except TypeError:
        return st.container()


def _fmt_ts(ts: float | int | None) -> str:
    """Formata um timestamp Unix para string legível."""
    try:
        if ts is None:
            return ""
        v = float(ts)
        if v <= 0:
            return ""
        import datetime as _dt
        return _dt.datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _safe_float(v) -> float:
    """Converte valor para float de forma segura."""
    try:
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0


def _contrast_text_for_bg(bg: str, light: str = "#ffffff", dark: str = "#000000") -> str:
    """Escolhe uma cor de texto legível (clara/escura) para um fundo hex."""
    try:
        s = str(bg or "").strip()
        if not s.startswith("#"):
            return light
        h = s[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        if len(h) != 6:
            return light
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
        return dark if lum > 0.6 else light
    except Exception:
        return light


def _extract_latest_price_from_logs(log_rows: list[dict]) -> float | None:
    """Extrai o preço mais recente dos logs do bot."""
    if not log_rows:
        return None
    import json
    for row in log_rows:
        msg = row.get("message") or ""
        try:
            data = json.loads(msg)
            if "price" in data and data["price"] is not None:
                return float(data["price"])
        except Exception:
            continue
    return None
