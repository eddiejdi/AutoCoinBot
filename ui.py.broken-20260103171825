# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  ⚠️  ATENÇÃO: NÃO MODIFICAR ESTRUTURA DESTE ARQUIVO SEM TESTAR UI           ║
# ║                                                                              ║
# ║  Este arquivo controla toda a renderização do Streamlit. Alterações          ║
# ║  incorretas causam "loading eterno" (tela travada).                          ║
# ║                                                                              ║
# ║  ANTES DE QUALQUER ALTERAÇÃO:                                                ║
# ║  1. Faça backup: git stash ou git checkout -b feature/minha-mudanca          ║
# ║  2. Teste localmente: python -m streamlit run streamlit_app.py               ║
# ║  3. Valide com Selenium: python selenium_dashboard.py                        ║
# ║  4. Se travar, restaure: git checkout main -- ui.py                          ║
# ║                                                                              ║
# ║  PADRÕES CRÍTICOS (não violar):                                              ║
# ║  - Imports devem ter try/except para fallback                                ║
# ║  - Não usar st.write() para debug (causa reloads infinitos)                  ║
# ║  - session_state init deve ser idempotente (checar "if X not in")            ║
# ║  - Widgets com key= NÃO devem ter value= se session_state já inicializa      ║
# ║                                                                              ║
# ║  Última versão estável: commit 1b1a6d4 (main)                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

try:
    import html
except Exception:
    class _HTMLShim:
        @staticmethod
        def escape(s):
            try:
                return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            except Exception:
                return str(s)

    html = _HTMLShim()
import logging
# Setup lightweight UI debug logger writing into workspace so container user can inspect
try:
    ui_logger = logging.getLogger("autocoin_ui_debug")
    if not ui_logger.handlers:
        fh = logging.FileHandler("ui_debug.log")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        ui_logger.addHandler(fh)
    ui_logger.setLevel(logging.DEBUG)
except Exception:
    ui_logger = None

import os
import shlex
import signal
import subprocess
import time
import threading
import json
import urllib.parse
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent

# How many consecutive checks are required to consider a PID dead
# and avoid aggressive cleanup when multiple Streamlit instances run.tive checks are required to consider a PID dead
_PID_DEATH_CONFIRM_CHECKS = 3oid aggressive cleanup when multiple Streamlit instances run.
# Seconds to wait between checks
_PID_DEATH_CONFIRM_SLEEP = 0.45

def get_version():
    try:on():
        result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:rocess.run(['git', 'rev-list', '--count', 'HEAD'], capture_output=True, text=True, cwd=os.getcwd())
            count = int(result.stdout.strip())urncode == 0:
            return f"v{count}.0"            count = int(result.stdout.strip())
        else:}.0"
            return "v1.0"
    except Exception:turn "v1.0"
        return "v1.0"

LOGIN_FILE = ".login_status"
def set_logged_in(status):
    if status:
        with open(LOGIN_FILE, 'w') as f:    if status:
            f.write('logged_in')
    else:        f.write('logged_in')
        if os.path.exists(LOGIN_FILE):
            os.remove(LOGIN_FILE)

# ⚠️ CRÍTICO: Imports com try/except - NÃO REMOVER os fallbacks
try:orts com try/except - NÃO REMOVER os fallbacks
    # Quando importado como pacote (AutoCoinBot.ui)
    from .bot_controller import BotControllerBot.ui)
    from .database import DatabaseManageroller
    from .sidebar_controller import SidebarController
except Exception:    from .sidebar_controller import SidebarController
    # Fallback para execução direta como módulo/script (import ui)
    from bot_controller import BotController/script (import ui)
    from database import DatabaseManager    from bot_controller import BotController
    from sidebar_controller import SidebarController
mport SidebarController
# Global singleton controller used across Streamlit sessions/tabs
_global_controller: BotController | None = Noneoss Streamlit sessions/tabs

def get_global_controller() -> BotController:
    global _global_controllertController:
    try:
        if _global_controller is None:    try:
            _global_controller = BotController()    if _global_controller is None:
    except Exception:
        _global_controller = Noneion:
    return _global_controller
return _global_controller
try:
    from wallet_releases_rss import render_wallet_releases_widget
except Exception: render_wallet_releases_widget
    render_wallet_releases_widget = Nonept Exception:
try:
    from terminal_component import render_terminal_live_api
except Exception: import render_terminal_live_api
    render_terminal_live_api = None
try:_api = None
    from terminal_component import start_api_server
except Exception:    from terminal_component import start_api_server
    start_api_server = None
def render_strategy_semaphore(snapshot: dict, theme: dict) -> str:
        if not snapshot:theme: dict) -> str:
                return ""
                return ""
        bias = (snapshot.get("bias") or "WAIT").upper()
        strategy = snapshot.get("strategy") or "-"pper()
        regime = snapshot.get("regime") or "-"r "-"
        confidence = float(snapshot.get("confidence") or 0.0)"-"
)
        success = theme.get("success", "#00C853")
        warning = theme.get("warning", "#FFAB00")        success = theme.get("success", "#00C853")
        error = theme.get("error", "#FF5252")rning", "#FFAB00")
        text = theme.get("text", "#FFFFFF") "#FF5252")
        panel = theme.get("bg2", theme.get("bg", "#0E1117")) "#FFFFFF")
        border = theme.get("border", "rgba(255,255,255,0.12)")        panel = theme.get("bg2", theme.get("bg", "#0E1117"))
55,255,0.12)")
        red_on = bias == "SELL"
        yellow_on = bias == "WAIT"
        green_on = bias == "BUY"

        def _light(color: str, on: bool) -> str:
                return (        def _light(color: str, on: bool) -> str:
                        f"<div style=\"width:18px;height:18px;border-radius:50%;"
                        f"background:{color};opacity:{1.0 if on else 0.22};"
                        f"box-shadow:0 0 10px {color if on else 'transparent'};\"></div>"else 0.22};"
                )                        f"box-shadow:0 0 10px {color if on else 'transparent'};\"></div>"

        conf_pct = int(round(confidence * 100))
        title = f"{strategy.replace('_',' ').title()} • {regime.replace('_',' ').title()}"
        subtitle = f"Bias: {bias} • Confiança: {conf_pct}% (5m)"e('_',' ').title()}"
ça: {conf_pct}% (5m)"
        return f"""
        <div style="background:{panel};border:1px solid {border};border-radius:12px;padding:12px;">
            <div style="display:flex;align-items:center;gap:10px;">ckground:{panel};border:1px solid {border};border-radius:12px;padding:12px;">
                <div style="display:flex;gap:8px;align-items:center;">align-items:center;gap:10px;">
                    {_light(error, red_on)}
                    {_light(warning, yellow_on)}
                    {_light(success, green_on)}light(warning, yellow_on)}
                </div>  {_light(success, green_on)}
                <div style="flex:1;">  </div>
                    <div style="color:{text};font-weight:700;font-size:14px;line-height:1.2;">{title}</div>     <div style="flex:1;">
                    <div style="color:{text};opacity:0.85;font-size:12px;margin-top:2px;">{subtitle}</div>                    <div style="color:{text};font-weight:700;font-size:14px;line-height:1.2;">{title}</div>
                </div>;">{subtitle}</div>
            </div>
        </div>
        """

# Streamlit creates a separate "session" per browser tab/user. Anything guarded only by
# st.session_state will run once per browser session, not once per server process.# Streamlit creates a separate "session" per browser tab/user. Anything guarded only by
# For kill-on-start behavior we want a single best-effort pass per server process..session_state will run once per browser session, not once per server process.
_KILL_ON_START_DONE = Falsegle best-effort pass per server process.
_KILL_ON_START_LOCK = threading.Lock()


try:
    @st.cache_resource(show_spinner=False)try:
    def _KILL_ON_START_GUARD_RESOURCE():    @st.cache_resource(show_spinner=False)
        return {"lock": threading.Lock(), "done": False}SOURCE():
except Exception:
    _KILL_ON_START_GUARD_RESOURCE = Noneexcept Exception:


def _get_kill_on_start_guard():
    """Return a (lock, done_flag_container) that is shared across Streamlit sessions.t_kill_on_start_guard():
eturn a (lock, done_flag_container) that is shared across Streamlit sessions.
    Streamlit re-executes the script for each session/tab, so plain module globals may not
    be reliable for cross-session coordination. We prefer st.cache_resource for a trueion/tab, so plain module globals may not
    per-server-process singleton.ross-session coordination. We prefer st.cache_resource for a true
    """er-process singleton.
    try:    """
        if _KILL_ON_START_GUARD_RESOURCE is not None:
            return _KILL_ON_START_GUARD_RESOURCE()
    except Exception:            return _KILL_ON_START_GUARD_RESOURCE()
        pass    except Exception:

    # Fallback: best-effort globals (works within a single script context)
    return {"lock": _KILL_ON_START_LOCK, "done": _KILL_ON_START_DONE}-effort globals (works within a single script context)
rn {"lock": _KILL_ON_START_LOCK, "done": _KILL_ON_START_DONE}

def _pid_alive(pid: int | None) -> bool:
    if pid is None:int | None) -> bool:
        return False:
    try:
        pid_i = int(pid)
    except Exception:
        return Falsen:
    if pid_i <= 0:
        return False
    try:
        os.kill(pid_i, 0)
        return True, 0)
    except ProcessLookupError:
        return False    except ProcessLookupError:
    except PermissionError:
        return True
    except Exception:
        return False

def _confirm_pid_dead(pid: int | None, checks: int = None, delay_s: float = None) -> bool:
    """Return True only if PID appears dead for `checks` consecutive checks."""ad(pid: int | None, checks: int = None, delay_s: float = None) -> bool:
    if checks is None:only if PID appears dead for `checks` consecutive checks."""
        checks = _PID_DEATH_CONFIRM_CHECKShecks is None:
    if delay_s is None:ATH_CONFIRM_CHECKS
        delay_s = _PID_DEATH_CONFIRM_SLEEPe:
    if pid is None:PID_DEATH_CONFIRM_SLEEP
        return True:
    try:
        pid_i = int(pid)
    except Exception:i = int(pid)
        return True
    if pid_i <= 0:
        return True
    for _ in range(int(checks)):
        try:
            if _pid_alive(pid_i):
                return False
        except Exception:
            return Falsept Exception:
        # Avoid blocking the main render loop with sleeps; perform immediate rechecks.
        # Previously we waited `delay_s` between checks, but in a UI render pathking the main render loop with sleeps; perform immediate rechecks.
        # this can cause perceptible hangs. Keeping the fast consecutive checksaited `delay_s` between checks, but in a UI render path
        # still reduces false-positives for transient PIDs without sleeping.an cause perceptible hangs. Keeping the fast consecutive checks
        try:sitives for transient PIDs without sleeping.
            # quick no-op to keep structure similar; do not sleep here        try:
            _ = None            # quick no-op to keep structure similar; do not sleep here
        except Exception:
            pass
    return not _pid_alive(pid_i)
    return not _pid_alive(pid_i)

# Lightweight cached `ps` scanner to avoid calling `subprocess.run` on every render.
# Returns list of lines (like `ps` output). Cache is refreshed in background if stale.
_ps_cache = {"ts": 0.0, "out": []} Cache is refreshed in background if stale.
0, "out": []}
def _update_ps_cache():
    try:
        r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, check=False, timeout=2)
        out = (r.stdout or "").splitlines()        r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, check=False, timeout=2)
    except Exception:)
        out = []pt Exception:
    _ps_cache["out"] = out
    _ps_cache["ts"] = time.time()
s"] = time.time()
def _ps_scan_cached(max_age: float = 2.0):
    try:float = 2.0):
        now = time.time()
        if now - _ps_cache.get("ts", 0.0) > float(max_age):ime()
            try:
                threading.Thread(target=_update_ps_cache, daemon=True).start()
            except Exception:target=_update_ps_cache, daemon=True).start()
                # fallback: attempt synchronous with very short timeout
                try:chronous with very short timeout
                    r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, check=False, timeout=1)
                    return (r.stdout or "").splitlines()   r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, check=False, timeout=1)
                except Exception:                    return (r.stdout or "").splitlines()
                    return _ps_cache.get("out", [])                except Exception:
        return _ps_cache.get("out", [])
    except Exception:
        return []pt Exception:


def _kill_pid_best_effort(pid: int, timeout_s: float = 0.4) -> bool:
    """Try SIGTERM then SIGKILL. Returns True if process appears gone."""_effort(pid: int, timeout_s: float = 0.4) -> bool:
    try:hen SIGKILL. Returns True if process appears gone."""
        pid_i = int(pid)
    except Exception:(pid)
        return False    except Exception:
    if pid_i <= 0:
        return False
    if not _pid_alive(pid_i):False
        return Trueot _pid_alive(pid_i):

    # Prefer killing the whole process group (bot + any children) when it is safe.
    # This is safe when bots are started with start_new_session=True (separate pgrp).g the whole process group (bot + any children) when it is safe.
    pgrp = None    # This is safe when bots are started with start_new_session=True (separate pgrp).
    try:
        pgrp = os.getpgid(pid_i)
    except Exception: = os.getpgid(pid_i)
        pgrp = None

    # Try SIGTERM to process group first
    if pgrp and pgrp > 0:M to process group first
        try:    if pgrp and pgrp > 0:
            if pgrp != os.getpgrp():
                os.killpg(pgrp, signal.SIGTERM)    if pgrp != os.getpgrp():
        except Exception:.SIGTERM)
            passion:
pass
    # Fallback: SIGTERM to the process itself
    try: itself
        os.kill(pid_i, signal.SIGTERM)
    except Exception:.SIGTERM)
        pass

    # Wait a bit for graceful shutdown
    try: shutdown
        time.sleep(timeout_s)
    except Exception:        time.sleep(timeout_s)
        pass

    if not _pid_alive(pid_i):
        return True

    # If still alive, escalate to SIGKILL
    if pgrp and pgrp > 0:live, escalate to SIGKILL
        try:grp and pgrp > 0:
            if pgrp != os.getpgrp():
                os.killpg(pgrp, signal.SIGKILL)= os.getpgrp():
        except Exception:    os.killpg(pgrp, signal.SIGKILL)
            pass        except Exception:
    try:    pass
        os.kill(pid_i, signal.SIGKILL)
    except Exception:, signal.SIGKILL)
        passxception:

    try:
        time.sleep(0.1)    try:
    except Exception:
        pass
    return not _pid_alive(pid_i)pass
e(pid_i)

def _kill_pid_sigkill_only(pid: int) -> bool:
    """Hard kill (SIGKILL / kill -9). Returns True if process appears gone."""ill_only(pid: int) -> bool:
    try:GKILL / kill -9). Returns True if process appears gone."""
        pid_i = int(pid)
    except Exception:(pid)
        return False    except Exception:
    if pid_i <= 0:False
        return Falseid_i <= 0:
    if not _pid_alive(pid_i):
        return True(pid_i):

    pgrp = None
    try:
        pgrp = os.getpgid(pid_i)
    except Exception:
        pgrp = None

    if pgrp and pgrp > 0:
        try:grp and pgrp > 0:
            if pgrp != os.getpgrp():
                os.killpg(pgrp, signal.SIGKILL)= os.getpgrp():
        except Exception:    os.killpg(pgrp, signal.SIGKILL)
            pass        except Exception:
    try:    pass
        os.kill(pid_i, signal.SIGKILL)
    except Exception:, signal.SIGKILL)
        passxception:

    try:
        time.sleep(0.1)    try:
    except Exception:
        pass
    return not _pid_alive(pid_i)        pass


def _kill_active_bot_sessions_on_start(controller: BotController | None = None):
    """Kill any leftover running bot sessions when the app starts.def _kill_active_bot_sessions_on_start(controller: BotController | None = None):

    Runs at most once per Streamlit *server process*.
    """ at most once per Streamlit *server process*.
    global _KILL_ON_START_DONE
NE
    # Guard once per server process. This prevents a new browser tab/session from
    # re-running the cleanup and killing bots started by an existing session.ents a new browser tab/session from
    try:he cleanup and killing bots started by an existing session.
        g = _get_kill_on_start_guard()
        lock = g.get("lock")on_start_guard()
        if lock is None:
            raise RuntimeError("missing lock")
        with lock:timeError("missing lock")
            if bool(g.get("done")):
                returnif bool(g.get("done")):
            g["done"] = True
            _KILL_ON_START_DONE = True= True
    except Exception:
        # Very last resort: per-session guard.
        try:t resort: per-session guard.
            if st.session_state.get("_killed_active_sessions_on_start"):        try:
                returnion_state.get("_killed_active_sessions_on_start"):
            st.session_state["_killed_active_sessions_on_start"] = True                return
        except Exception:
            returnexcept Exception:
return
    killed_any = False

    # Stop any continuous-mode runners (they respawn bots when a process exits)
    try:    # Stop any continuous-mode runners (they respawn bots when a process exits)
        try:
            BotController.stop_all_continuous()
        except Exception:
            pass

        if controller is not None:
            cont = getattr(controller, "_continuous_stop", None)
            if isinstance(cont, dict) and cont:ontroller, "_continuous_stop", None)
                for _, ev in list(cont.items()):tance(cont, dict) and cont:
                    try:t(cont.items()):
                        ev.set()
                    except Exception:ev.set()
                        passxcept Exception:
                try:            pass
                    cont.clear()                try:
                except Exception:
                    pass
    except Exception:                    pass
        pass:
pass
    db_sessions_by_id: dict[str, dict] = {}
    ps_pids_by_id: dict[str, int] = {}

    # 1) DB sessions
    try:
        db = DatabaseManager()
        for sess in db.get_active_bots() or []:Manager()
            bot_id = sess.get("id") or sess.get("bot_id")in db.get_active_bots() or []:
            if not bot_id:            bot_id = sess.get("id") or sess.get("bot_id")
                continue
            db_sessions_by_id[str(bot_id)] = sess        continue
    except Exception:tr(bot_id)] = sess
        db = None

    # 2) ps scan for bots (cached, non-blocking)
    try:s (cached, non-blocking)
        out = _ps_scan_cached()
        for line in out[1:]:
            line = line.strip()
            if not line:()
                continue
            try:
                pid_s, args_s = line.split(None, 1)
                pid_i = int(pid_s)pid_s, args_s = line.split(None, 1)
            except Exception:
                continue
            if "bot_core.py" not in args_s:
                continuen args_s:
            try:inue
                argv = shlex.split(args_s)
            except Exception:
                argv = args_s.split()
            if "--bot-id" in argv:it()
                try:in argv:
                    idx = argv.index("--bot-id")
                    bot_id = argv[idx + 1]
                except Exception:
                    bot_id = None
                if bot_id:
                    bot_id_s = str(bot_id)t_id:
                    # IMPORTANT: Only consider killing processes that are tracked as active        bot_id_s = str(bot_id)
                    # sessions in the DB. This avoids the UI killing manually launched bots.                    # IMPORTANT: Only consider killing processes that are tracked as active
                    if bot_id_s in db_sessions_by_id:ed bots.
                        ps_pids_by_id[bot_id_s] = pid_idb_sessions_by_id:
    except Exception:pid_i
        pass

    # Build candidates strictly from DB sessions (with ps as a fallback PID source).
    candidates: dict[str, int] = {} from DB sessions (with ps as a fallback PID source).
    for bot_id, sess in db_sessions_by_id.items(): {}
        pid_i: int | None = Noneb_sessions_by_id.items():
        try:e = None
            pid = sess.get("pid")        try:
            if pid is not None:s.get("pid")
                pid_i = int(pid)id is not None:
        except Exception:
            pid_i = None

        if not pid_i:
            try:d_i:
                pid_i = int(ps_pids_by_id.get(bot_id) or 0) or None
            except Exception:                pid_i = int(ps_pids_by_id.get(bot_id) or 0) or None
                pid_i = None  except Exception:

        if pid_i:
            candidates[bot_id] = pid_i

    # Kill
    for bot_id, pid in list(candidates.items()):
        # Only mark stopped when PID is confirmed dead across multiple checks
        if _confirm_pid_dead(pid):ross multiple checks
            # mark stopped in DB if it was listed as activedead(pid):
            try: active
                if db is not None and bot_id in db_sessions_by_id:
                    db.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()}) None and bot_id in db_sessions_by_id:
                    # Free any quota possibly left behind_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
                    try:# Free any quota possibly left behind
                        db.release_bot_quota(bot_id)try:
                    except Exception:                        db.release_bot_quota(bot_id)
                        pass
            except Exception:
                passcept Exception:
            continue

        # If PID still appears alive, attempt best-effort graceful kill and then confirm
        ok = _kill_pid_best_effort(pid) graceful kill and then confirm
        if ok:
            killed_any = True
        # best-effort: mark stopped only if confirmed deadny = True
        try:irmed dead
            if db is not None and _confirm_pid_dead(pid):
                db.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()}) None and _confirm_pid_dead(pid):
                # Free quota even if the bot was SIGKILL'ed (avoids orphan allocations)_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
                try:# Free quota even if the bot was SIGKILL'ed (avoids orphan allocations)
                    db.release_bot_quota(bot_id)                try:
                except Exception:
                    pass    except Exception:
        except Exception:
            pass

        # best-effort: remove from controller process map
        try:        # best-effort: remove from controller process map
            if controller is not None and getattr(controller, "processes", None):
                controller.processes.pop(bot_id, None)    if controller is not None and getattr(controller, "processes", None):
        except Exception:.processes.pop(bot_id, None)
            pass

    # Also release any orphaned allocated quotas (no live PID found for that bot_id)
    try:ed quotas (no live PID found for that bot_id)
        if db is not None:
            conn = db.get_connection()
            cur = conn.cursor()tion()
            cur.execute("SELECT bot_id FROM bot_quotas WHERE status = 'allocated'")
            rows = cur.fetchall() or []ute("SELECT bot_id FROM bot_quotas WHERE status = 'allocated'")
            conn.close()
            for (qid,) in rows:
                qid_s = str(qid)
                live_pid = None
                try:
                    sess = db_sessions_by_id.get(qid_s)
                    if sess and sess.get("pid") is not None:ns_by_id.get(qid_s)
                        live_pid = int(sess.get("pid"))ess and sess.get("pid") is not None:
                except Exception:
                    live_pid = None
                # Check ps scan as fallback
                if live_pid is None:
                    try:is None:
                        live_pid = int(ps_pids_by_id.get(qid_s) or 0) or Nonetry:
                    except Exception:by_id.get(qid_s) or 0) or None
                        live_pid = Noneion:
                if live_pid is not None and _pid_alive(live_pid):live_pid = None
                    continueve_pid is not None and _pid_alive(live_pid):
                try:        continue
                    db.release_bot_quota(qid_s)                try:
                except Exception:d_s)
                    passcept Exception:
    except Exception:        pass
        pass

    # Clear UI lists if anything was killed
    if killed_any:nything was killed
        try:y:
            st.session_state.active_bots = []        try:
            st.session_state.selected_bot = None            st.session_state.active_bots = []
            st.session_state.bot_running = False
        except Exception:
            passexcept Exception:


def _contrast_text_for_bg(bg: str, light: str = "#ffffff", dark: str = "#000000") -> str:
    """Pick a readable text color (light/dark) for a given hex background."""t_for_bg(bg: str, light: str = "#ffffff", dark: str = "#000000") -> str:
    try:text color (light/dark) for a given hex background."""
        s = str(bg or "").strip()
        if not s.startswith("#"):").strip()
            return lightith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        if len(h) != 6:ch in h)
            return light
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)], 16)
        b = int(h[4:6], 16)4], 16)
        # Relative luminance (sRGB)        b = int(h[4:6], 16)
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0        # Relative luminance (sRGB)
        return dark if lum > 0.6 else light* b) / 255.0
    except Exception:
        return light    except Exception:


def _maybe_start_background_kucoin_trade_sync():
    """Sincroniza trades reais da KuCoin em background.ybe_start_background_kucoin_trade_sync():
incroniza trades reais da KuCoin em background.
    - Roda no máximo 1x por sessão Streamlit.
    - Não bloqueia a UI.mo 1x por sessão Streamlit.
    - Faz best-effort: se não houver credenciais, não faz nada.
    """: se não houver credenciais, não faz nada.
    try:
        if st.session_state.get("_kucoin_trade_sync_started"):    try:
            returnn_state.get("_kucoin_trade_sync_started"):
        st.session_state["_kucoin_trade_sync_started"] = True            return
    except Exception:_state["_kucoin_trade_sync_started"] = True
        returnxception:

    import threading

    def _worker():
        try:
            # Import local (evita custo no caminho crítico da UI)        try:
            try:crítico da UI)
                import api as kucoin_api
            except Exception:
                import api as kucoin_api  # type: ignoreon:
 kucoin_api  # type: ignore
            # Sem credenciais? Sai silenciosamente.
            try:            # Sem credenciais? Sai silenciosamente.
                if not getattr(kucoin_api, "_has_keys", lambda: False)():
                    return):
            except Exception:
                return            except Exception:

            now_ms = int(time.time() * 1000)
            # janela simples (últimos 90 dias) para popular o histórico
            start_ms = now_ms - (90 * 24 * 3600 * 1000)(últimos 90 dias) para popular o histórico
00 * 1000)
            fills = []
            try:            fills = []
                fills = kucoin_api.get_all_fills(start_at=start_ms, end_at=now_ms, page_size=200, max_pages=50)
            except Exception:= kucoin_api.get_all_fills(start_at=start_ms, end_at=now_ms, page_size=200, max_pages=50)
                # se falhar, não derruba a UI            except Exception:
                returnerruba a UI

            if not fills:
                return
                return
            db = DatabaseManager()
            for f in fills:
                if not isinstance(f, dict):
                    continue                if not isinstance(f, dict):

                trade_id = f.get("tradeId") or f.get("id")
                order_id = f.get("orderId")
                created_at = f.get("createdAt")  # ms                order_id = f.get("orderId")
eatedAt")  # ms
                # fallback de id estável
                if not trade_id:llback de id estável
                    trade_id = f"kucoin_{order_id or 'no_order'}_{created_at or int(time.time()*1000)}"
_id or 'no_order'}_{created_at or int(time.time()*1000)}"
                # timestamp (segundos)
                ts_s = Nonendos)
                try:
                    if created_at is not None:                try:
                        ca = float(created_at) None:
                        ts_s = ca / 1000.0 if ca > 1e12 else careated_at)
                except Exception:                        ts_s = ca / 1000.0 if ca > 1e12 else ca
                    ts_s = Nonept Exception:

                symbol = f.get("symbol")
                side = f.get("side")symbol")
                side = f.get("side")
                try:
                    price = float(f.get("price")) if f.get("price") is not None else None
                except Exception:(f.get("price")) if f.get("price") is not None else None
                    price = Nonen:
                    price = None
                try:
                    size = float(f.get("size")) if f.get("size") is not None else None
                except Exception:f.get("size")) if f.get("size") is not None else None
                    size = None:
                    size = None
                try:
                    funds = float(f.get("funds")) if f.get("funds") is not None else None
                except Exception:(f.get("funds")) if f.get("funds") is not None else None
                    funds = Noneon:
                    funds = None
                try:
                    fee = float(f.get("fee")) if f.get("fee") is not None else None
                except Exception:t("fee") is not None else None
                    fee = None

                trade_data = {
                    "id": str(trade_id),
                    "timestamp": ts_s or time.time(),_id),
                    "symbol": symbol or "",_s or time.time(),
                    "side": (side or "").lower(),r "",
                    "price": price or 0.0,
                    "size": size,.0,
                    "funds": funds,
                    "profit": None,
                    "commission": fee,
                    "order_id": str(order_id) if order_id is not None else None,   "commission": fee,
                    "bot_id": "KUCOIN",                    "order_id": str(order_id) if order_id is not None else None,
                    "strategy": "kucoin_fill",
                    "dry_run": False,tegy": "kucoin_fill",
                    "metadata": {"source": "kucoin", "fill": f},  "dry_run": False,
                }                    "metadata": {"source": "kucoin", "fill": f},
        }
                db.insert_trade_ignore(trade_data)
        except Exception:b.insert_trade_ignore(trade_data)
            returnion:
turn
    try:
        t = threading.Thread(target=_worker, name="kucoin_trade_sync", daemon=True)    try:
        t.start()ame="kucoin_trade_sync", daemon=True)
    except Exception:
        returnpt Exception:


def _maybe_start_background_equity_snapshot():
    """Snapshots equity (balances) em background periodicamente."""ground_equity_snapshot():
    try:ts equity (balances) em background periodicamente."""
        if st.session_state.get("_equity_snapshot_started"):    try:
            returnn_state.get("_equity_snapshot_started"):
        st.session_state["_equity_snapshot_started"] = True            return
    except Exception:_state["_equity_snapshot_started"] = True
        returnn:

    import threading

    def _worker():
        import time
        while True:
            try:
                from equity import snapshot_equity
                snapshot_equity()
            except Exception as e:
                if ui_logger:            except Exception as e:
                    ui_logger.error(f"Erro no snapshot equity: {e}")
                else:            ui_logger.error(f"Erro no snapshot equity: {e}")
                    pass  # Fallback: no logging available
            time.sleep(300)  # every 5 minutes                    pass  # Fallback: no logging available
ery 5 minutes
    # Schedule immediate snapshot on start in a background thread (non-blocking)
    try: on start in a background thread (non-blocking)
        from equity import snapshot_equity
apshot_equity
        def _run_once_snapshot():
            try:_snapshot():
                snapshot_equity()
            except Exception as e:                snapshot_equity()
                if ui_logger:except Exception as e:
                    ui_logger.error(f"Erro no snapshot inicial: {e}")
                else:gger.error(f"Erro no snapshot inicial: {e}")
                    pass
    pass
        try:
            threading.Thread(target=_run_once_snapshot, name="equity_snapshot_once", daemon=True).start()
        except Exception:target=_run_once_snapshot, name="equity_snapshot_once", daemon=True).start()
            # last-resort fallback: run synchronously (should be rare)
            try:sort fallback: run synchronously (should be rare)
                snapshot_equity()
            except Exception as e:quity()
                if ui_logger:ception as e:
                    ui_logger.error(f"Erro no snapshot inicial (fallback): {e}")
                else:       ui_logger.error(f"Erro no snapshot inicial (fallback): {e}")
                    passelse:
    except Exception as e:                    pass
        if ui_logger:pt Exception as e:
            ui_logger.error(f"Erro ao importar snapshot_equity: {e}")
        else:gger.error(f"Erro ao importar snapshot_equity: {e}")
            pass
ss
    try:
        t = threading.Thread(target=_worker, name="equity_snapshot", daemon=True)    try:
        t.start()rget=_worker, name="equity_snapshot", daemon=True)
    except Exception:
        return    except Exception:


def render_trade_report_page():
    """Página de relatório: histórico de trades (abre em nova aba via ?report=1).def render_trade_report_page():

    Nota: existe também a versão HTML dedicada servida em /report pelo API server local.
    """    Nota: existe também a versão HTML dedicada servida em /report pelo API server local.
    theme = get_current_theme()
get_current_theme()
    # Em uma nova aba, é uma nova sessão Streamlit: dispara sync em background aqui também.
    _maybe_start_background_kucoin_trade_sync()

    st.markdown(
        f"""
        <div style="text-align:center; padding: 10px 0 16px 0;">
            <div style="display:inline-block; border: 1px solid {theme['border']}; border-radius: 8px; padding: 12px 16px; background:{theme['bg2']};"> style="text-align:center; padding: 10px 0 16px 0;">
                <div style="font-family: 'Courier New', monospace; font-weight: 700; color:{theme['accent']};">📑 RELATÓRIO</div>:inline-block; border: 1px solid {theme['border']}; border-radius: 8px; padding: 12px 16px; background:{theme['bg2']};">
                <div style="font-family: 'Courier New', monospace; color:{theme['text2']}; font-size: 12px;">Histórico de Trades</div>           <div style="font-family: 'Courier New', monospace; font-weight: 700; color:{theme['accent']};">📑 RELATÓRIO</div>
            </div>                <div style="font-family: 'Courier New', monospace; color:{theme['text2']}; font-size: 12px;">Histórico de Trades</div>
        </div>
        """,        </div>
        unsafe_allow_html=True,
    )

    tab_trades, tab_learning = st.tabs(["Trades", "Aprendizado"])
    tab_trades, tab_learning = st.tabs(["Trades", "Aprendizado"])
    with tab_trades:
        bot_id_filter = _qs_get_any(st.query_params, "bot", None)    with tab_trades:
        real_q = _qs_get_any(st.query_params, "real", None)one)
        default_only_real = str(real_q).strip() in ("1", "true", "yes")(st.query_params, "real", None)
ult_only_real = str(real_q).strip() in ("1", "true", "yes")
        only_real = st.checkbox("Somente movimentações reais (não dry-run)", value=default_only_real)
nte movimentações reais (não dry-run)", value=default_only_real)
        group_q = _qs_get_any(st.query_params, "group", None)
        default_group = True.query_params, "group", None)
        try:        default_group = True
            if group_q is not None and str(group_q).strip() in ("0", "false", "no"):
                default_group = False ("0", "false", "no"):
        except Exception:False
            default_group = Truexcept Exception:
            default_group = True
        group_by_order = st.checkbox(
            "Agrupar por order_id (dedupe fill + estratégia)",p_by_order = st.checkbox(
            value=default_group, estratégia)",
        )roup,

        db = DatabaseManager()
        try:
            rows = db.get_trade_history_grouped(
                limit=2000,e_history_grouped(
                bot_id=bot_id_filter,
                only_real=only_real,d=bot_id_filter,
                group_by_order_id=group_by_order,                only_real=only_real,
            )up_by_order_id=group_by_order,
        except Exception as e:
            st.error(f"Erro ao carregar trades: {e}")
            rows = []

        st.caption(
            f"Mostrando até 2000 trades"        st.caption(
            f"{' do bot ' + str(bot_id_filter) if bot_id_filter else ''}"ndo até 2000 trades"
            f"{' (somente reais)' if only_real else ''}"_filter else ''}"
            f" (mais recentes primeiro)."somente reais)' if only_real else ''}"
        )            f" (mais recentes primeiro)."

        if not rows:
            st.info("Nenhum trade encontrado no banco.")        if not rows:
            returnenhum trade encontrado no banco.")

        # Formatação + destaque por cor (real efetivado vs não efetivado)
        import datetime as _dtação + destaque por cor (real efetivado vs não efetivado)

        formatted = []
        for r in rows:
            ts = r.get("timestamp")        for r in rows:
            try:
                dt = _dt.datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S") if ts else ""
            except Exception:(float(ts)).strftime("%Y-%m-%d %H:%M:%S") if ts else ""
                dt = ""

            dry_run_val = r.get("dry_run")
            try:")
                is_real = int(dry_run_val) == 0
            except Exception:                is_real = int(dry_run_val) == 0
                is_real = False
se
            order_id = r.get("order_id")
            is_executed = bool(is_real and order_id and str(order_id).strip())_id")
and order_id and str(order_id).strip())
            # PnL líquido (somente quando houver PnL realizado)
            net_profit = Noneado)
            try:
                p = r.get("profit")
                c = r.get("commission")                p = r.get("profit")
                if p is not None:mission")
                    net_profit = float(p) - float(c or 0.0)e:
            except Exception:- float(c or 0.0)
                net_profit = None

            formatted.append({
                "datetime": dt,
                "symbol": r.get("symbol"),
                "side": r.get("side"),,
                "price": r.get("price"),
                "size": r.get("size"),
                "funds": r.get("funds"),
                "profit": r.get("profit"),
                "net_profit": net_profit,
                "commission": r.get("commission"),fit,
                "bot_id": r.get("bot_id"),t("commission"),
                "strategy": r.get("strategy"),  "bot_id": r.get("bot_id"),
                "real": 1 if is_real else 0,                "strategy": r.get("strategy"),
                "efetivada": 1 if is_executed else 0,
                "order_id": order_id,    "efetivada": 1 if is_executed else 0,
                "id": r.get("id"),
            })                "id": r.get("id"),

        # Preferir pandas para permitir coloração por linha; fallback sem estilo
        try: linha; fallback sem estilo
            import pandas as pd  # type: ignore

            df = pd.DataFrame(formatted)
            df = pd.DataFrame(formatted)
            success = theme.get("success", "#00ff88")
            warning = theme.get("warning", "#ffaa00")
            muted_bg = theme.get("bg2", "#111")= theme.get("warning", "#ffaa00")
            txt = theme.get("text", "#ffffff") "#111")
)
            def _contrast_text(bg: str, fallback: str = "#ffffff") -> str:
                """Pick black/white for contrast against a hex background."""r, fallback: str = "#ffffff") -> str:
                try: for contrast against a hex background."""
                    s = str(bg).strip()
                    if not s.startswith("#"):ip()
                        return fallback("#"):
                    h = s.lstrip("#")
                    if len(h) == 3:
                        h = "".join([c * 2 for c in h])
                    if len(h) != 6:
                        return fallback
                    r = int(h[0:2], 16)llback
                    g = int(h[2:4], 16) 16)
                    b = int(h[4:6], 16)                    g = int(h[2:4], 16)
                    lum = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)6], 16)
                    return "#000000" if lum > 160 else "#ffffff"lum = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                except Exception:f"
                    return fallback

            def _row_style(row):
                try:
                    is_real_row = int(row.get("real", 0)) == 1
                except Exception:ow.get("real", 0)) == 1
                    is_real_row = False                except Exception:
                try:
                    is_exec_row = int(row.get("efetivada", 0)) == 1
                except Exception:
                    is_exec_row = False

                if is_real_row and is_exec_row:
                    fg = _contrast_text(success, fallback="#ffffff")
                    return [f"background-color: {success}; color: {fg};"] * len(row)                    fg = _contrast_text(success, fallback="#ffffff")
                if is_real_row and not is_exec_row:n [f"background-color: {success}; color: {fg};"] * len(row)
                    fg = _contrast_text(warning, fallback="#000000")
                    return [f"background-color: {warning}; color: {fg};"] * len(row)arning, fallback="#000000")
                return [f"background-color: {muted_bg}; color: {txt};"] * len(row)ckground-color: {warning}; color: {fg};"] * len(row)
   return [f"background-color: {muted_bg}; color: {txt};"] * len(row)
            st.dataframe(
                df.style.apply(_row_style, axis=1),
                use_container_width=True,                df.style.apply(_row_style, axis=1),
                hide_index=True,ntainer_width=True,
            )
        except Exception:)
            st.dataframe(formatted, use_container_width=True, hide_index=True)
_container_width=True, hide_index=True)
        # Equity chart
        st.subheader("📈 Patrimônio Global")
        try: Patrimônio Global")
            import pandas as pd
            import plotly.express as px
            db = DatabaseManager()
            eq_rows = db.get_equity_history(days=30)
            if eq_rows:
                df_eq = pd.DataFrame(eq_rows)ws:
                if not df_eq.empty:rame(eq_rows)
                    df_eq["timestamp"] = df_eq["timestamp"].astype(float)
                    df_eq["datetime"] = df_eq["timestamp"].apply(lambda x: _fmt_ts(x))
                    df_eq["total"] = df_eq["balance_usdt"].astype(float)ambda x: _fmt_ts(x))
                    df_eq["total"] = df_eq["balance_usdt"].astype(float)
                    # Plot total
                    fig = px.line(df_eq, x="datetime", y="total", title="Patrimônio Total (USDT)")
                    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=300)ime", y="total", title="Patrimônio Total (USDT)")
                    st.plotly_chart(fig, use_container_width=True), t=40, b=10), height=300)
                    ainer_width=True)
                    # If we have per-coin data, show it
                    if 'balances' in df_eq.columns and df_eq['balances'].notna().any():-coin data, show it
                        st.subheader("Por Moeda")['balances'].notna().any():
                        # For simplicity, show last snapshot
                        last_row = df_eq.iloc[-1]
                        balances = last_row.get('balances', {})row = df_eq.iloc[-1]
                        if balances:
                            cols = st.columns(len(balances))       if balances:
                            for i, (coin, value) in enumerate(balances.items()):en(balances))
                                cols[i].metric(f"{coin}", f"{value:.2f}")r i, (coin, value) in enumerate(balances.items()):
            elif not eq_rows:}", f"{value:.2f}")
                st.info("Nenhum snapshot de patrimônio encontrado. Aguarde o próximo ciclo (5min).")            elif not eq_rows:
            else:o("Nenhum snapshot de patrimônio encontrado. Aguarde o próximo ciclo (5min).")
                st.info("Dados indisponíveis.")
        except Exception as e:nfo("Dados indisponíveis.")
            st.error(f"Erro ao carregar gráfico: {e}")pt Exception as e:
: {e}")
    with tab_learning:
        db = DatabaseManager()
        symbols = []        db = DatabaseManager()
        try:
            symbols = db.get_learning_symbols()
        except Exception:s = db.get_learning_symbols()
            symbols = []        except Exception:

        if not symbols:
            st.info("Nenhum dado de aprendizado ainda. Inicie bots e aguarde SELLs para gerar histórico.")        if not symbols:
            return ainda. Inicie bots e aguarde SELLs para gerar histórico.")

        sym_default = symbols[0]
        sym = st.selectbox("Símbolo", options=symbols, index=0)

        param_name = "take_profit_trailing_pct"
        st.caption("Este relatório mostra como o bot está aprendendo a escolher o trailing para sair mais alto.")m_name = "take_profit_trailing_pct"
o bot está aprendendo a escolher o trailing para sair mais alto.")
        stats = db.get_learning_stats(sym, param_name)
        hist = db.get_learning_history(sym, param_name, limit=2000)ats(sym, param_name)
        hist = db.get_learning_history(sym, param_name, limit=2000)
        try:
            import pandas as pd  # type: ignore
            import plotly.express as px  # type: ignorepe: ignore
            import datetime as _dtlotly.express as px  # type: ignore

            df_stats = pd.DataFrame(stats or [])
            if not df_stats.empty:d.DataFrame(stats or [])
                # Friendly formatting
                try:
                    df_stats["param_value"] = df_stats["param_value"].astype(float)                try:
                except Exception:] = df_stats["param_value"].astype(float)
                    passpt Exception:
                st.subheader("Ranking de candidatos")
                st.dataframe(df_stats, use_container_width=True, hide_index=True)
ide_index=True)
                # Bar chart of mean_reward
                try:art of mean_reward
                    fig = px.bar(df_stats.sort_values("param_value"), x="param_value", y="mean_reward", color="n",                try:
                                 title="Média de recompensa (profit_pct) por trailing")_values("param_value"), x="param_value", y="mean_reward", color="n",
                    st.plotly_chart(fig, use_container_width=True)title="Média de recompensa (profit_pct) por trailing")
                except Exception:
                    pass
pass
            df_hist = pd.DataFrame(hist or [])
            if not df_hist.empty:
                df_hist["timestamp"] = df_hist["timestamp"].apply(lambda x: float(x) if x is not None else 0.0)
                df_hist["datetime"] = df_hist["timestamp"].apply(lambda t: _dt.datetime.fromtimestamp(t))"timestamp"] = df_hist["timestamp"].apply(lambda x: float(x) if x is not None else 0.0)
                try:                df_hist["datetime"] = df_hist["timestamp"].apply(lambda t: _dt.datetime.fromtimestamp(t))
                    df_hist["param_value"] = df_hist["param_value"].astype(float)
                    df_hist["reward"] = df_hist["reward"].astype(float)param_value"].astype(float)
                except Exception:df_hist["reward"] = df_hist["reward"].astype(float)
                    pass

                df_hist = df_hist.sort_values("timestamp")
                st.subheader("Evolução (recompensas)").sort_values("timestamp")
                try:ader("Evolução (recompensas)")
                    fig2 = px.scatter(df_hist, x="datetime", y="reward", color="param_value",                try:
                                      title="Recompensas por trade (profit_pct) ao longo do tempo")x="datetime", y="reward", color="param_value",
                    st.plotly_chart(fig2, use_container_width=True)                  title="Recompensas por trade (profit_pct) ao longo do tempo")
                except Exception:
                    pass

                # Cumulative mean per candidate
                try:
                    df_hist["cum_n"] = df_hist.groupby("param_value").cumcount() + 1
                    df_hist["cum_mean"] = df_hist.groupby("param_value")["reward"].expanding().mean().reset_index(level=0, drop=True)ist["cum_n"] = df_hist.groupby("param_value").cumcount() + 1
                    fig3 = px.line(df_hist, x="datetime", y="cum_mean", color="param_value",   df_hist["cum_mean"] = df_hist.groupby("param_value")["reward"].expanding().mean().reset_index(level=0, drop=True)
                                   title="Média acumulada de recompensa (por trailing)")
                    st.plotly_chart(fig3, use_container_width=True)          title="Média acumulada de recompensa (por trailing)")
                except Exception:ner_width=True)
                    pass
            else:                    pass
                st.info("Ainda não há histórico suficiente para gráficos. Aguarde novos SELLs.")            else:
        except Exception:rico suficiente para gráficos. Aguarde novos SELLs.")
            # Minimal fallback without pandas/plotly
            st.write({"stats": stats, "history": hist[:10] if isinstance(hist, list) else hist})    # Minimal fallback without pandas/plotly
": stats, "history": hist[:10] if isinstance(hist, list) else hist})

def _qs_get_any(q, key: str, default=None):
    """Read a query param that may be stored as a scalar or a list.""", key: str, default=None):
    try:ram that may be stored as a scalar or a list."""
        v = q.get(key, None)
    except Exception:
        v = None
    if v is None:
        return defaultNone:
    try:rn default
        if isinstance(v, (list, tuple)):
            return v[0] if v else defaultv, (list, tuple)):
    except Exception:    return v[0] if v else default
        pass
    return v
    if v is None:
        return defaultNone:
    try:rn default
        if isinstance(v, (list, tuple)):    try:
            return v[0] if v else default        if isinstance(v, (list, tuple)):
    except Exception:
        pass
    return v        pass


def _merge_query_params(updates: dict[str, str | None]):
    """Merge updates into current Streamlit query params.ge_query_params(updates: dict[str, str | None]):
urrent Streamlit query params.
    - Keeps existing params unless overwritten.
    - Removes params when value is None/empty.isting params unless overwritten.
    """    - Removes params when value is None/empty.
    try:
        q = st.query_params
    except Exception:s
        return

    merged: dict[str, list[str]] = {}
    try:str, list[str]] = {}
        for k in q.keys():
            v = q.get(k)ys():
            if isinstance(v, (list, tuple)):
                merged[k] = [str(vv) for vv in v] isinstance(v, (list, tuple)):
            else:                merged[k] = [str(vv) for vv in v]
                merged[k] = [str(v)]
    except Exception:
        # best-effort: if query_params isn't iterable, bail
        returnt-effort: if query_params isn't iterable, bail

    for k, v in (updates or {}).items():
        if v is None or str(v).strip() == "":
            merged.pop(k, None)
        else:    merged.pop(k, None)
            merged[k] = [str(v)]

    # Streamlit query param APIs vary by version.
    # Prefer in-place mutation of the existing mapping when available.
    try:ng when available.
        qp = st.query_params
        if hasattr(qp, "clear") and hasattr(qp, "update"):ms
            qp.clear()r") and hasattr(qp, "update"):
            # Preserve multi-values when present, but prefer scalars for singletons.
            payload: dict[str, str | list[str]] = {}alues when present, but prefer scalars for singletons.
            for k, vs in merged.items():d: dict[str, str | list[str]] = {}
                if not vs: in merged.items():
                    continue    if not vs:
                payload[str(k)] = str(vs[0]) if len(vs) == 1 else [str(x) for x in vs]                    continue
            qp.update(payload)tr(vs[0]) if len(vs) == 1 else [str(x) for x in vs]
            return    qp.update(payload)
    except Exception:
        passeption:

    # Fallbacks for older versions.
    try:    # Fallbacks for older versions.
        st.query_params = merged
        return
    except Exception:
        pass

    try:
        # Legacy API accepts scalars; best-effort collapse to singletons.
        payload2: dict[str, str] = {}llapse to singletons.
        for k, vs in merged.items():t[str, str] = {}
            if not vs: vs in merged.items():
                continue            if not vs:
            payload2[str(k)] = str(vs[0])                continue
        st.experimental_set_query_params(**payload2)
    except Exception:
        return    except Exception:


def _build_relative_url_with_query_updates(updates: dict[str, str | None]) -> str:
    """Build a relative URL like '?a=1&b=2' merging current query params.ld_relative_url_with_query_updates(updates: dict[str, str | None]) -> str:
 like '?a=1&b=2' merging current query params.
    Useful for links that should open in a new tab (target=_blank) without
    forcing Streamlit reruns/navigation in the current tab. links that should open in a new tab (target=_blank) without
    """    forcing Streamlit reruns/navigation in the current tab.
    try:
        q = st.query_params
    except Exception:
        q = {}

    merged: dict[str, list[str]] = {}
    try:str, list[str]] = {}
        for k in getattr(q, "keys", lambda: [])():
            v = q.get(k)ttr(q, "keys", lambda: [])():
            if isinstance(v, (list, tuple)):et(k)
                merged[k] = [str(vv) for vv in v]            if isinstance(v, (list, tuple)):
            else: vv in v]
                merged[k] = [str(v)]
    except Exception:r(v)]
        merged = {}ception:

    for k, v in (updates or {}).items():
        if v is None or str(v).strip() == "":():
            merged.pop(k, None)trip() == "":
        else:e)
            merged[k] = [str(v)]
            merged[k] = [str(v)]
    items: list[tuple[str, str]] = []
    for k, vs in merged.items():= []
        for vv in (vs or []):    for k, vs in merged.items():
            items.append((str(k), str(vv)))        for vv in (vs or []):

    qs = urllib.parse.urlencode(items, doseq=True)
    return f"?{qs}" if qs else "" doseq=True)


def _set_view(view: str, bot_id: str | None = None, clear_bot: bool = False):
    """Navigate within the Streamlit app using query params (no new tabs).""", bot_id: str | None = None, clear_bot: bool = False):
    updates: dict[str, str | None] = {y params (no new tabs)."""
        "view": str(view or "").strip() or None,, str | None] = {
        # clear legacy modesew or "").strip() or None,
        "window": None,   # clear legacy modes
        "report": None, None,
        # ensure old navigation flags don't persist
        "home": None,flags don't persist
        "start": None,
    }
    if clear_bot:
        updates["bot"] = None    if clear_bot:
        updates["bot_id"] = None        updates["bot"] = None
    if bot_id is not None:
        updates["bot"] = str(bot_id) not None:
    _merge_query_params(updates)ates["bot"] = str(bot_id)
y_params(updates)

def _hide_sidebar_for_fullscreen_pages():
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            section[data-testid="stSidebar"] { display: none !important; }       [data-testid="stSidebar"] { display: none !important; }
            .stMainBlockContainer { padding-top: 1rem !important; }            section[data-testid="stSidebar"] { display: none !important; }
        </style>            .stMainBlockContainer { padding-top: 1rem !important; }
        """,
        unsafe_allow_html=True,
    )_html=True,


def _hide_sidebar_everywhere():
        """Always hide Streamlit sidebar; navigation is top bar + in-page controls."""
        st.markdown(treamlit sidebar; navigation is top bar + in-page controls."""
                """
                <style>
                    [data-testid="stSidebar"] { display: none !important; }       <style>
                    section[data-testid="stSidebar"] { display: none !important; }                    [data-testid="stSidebar"] { display: none !important; }
                </style>                    section[data-testid="stSidebar"] { display: none !important; }
                """,
                unsafe_allow_html=True,
        )                unsafe_allow_html=True,


def _safe_container(border: bool = False):
    """Return a container context manager with best-effort border support.e_container(border: bool = False):
est-effort border support.
    Streamlit versions differ on whether `st.container(border=...)` exists.
    This helper keeps the layout stable across versions. on whether `st.container(border=...)` exists.
    """    This helper keeps the layout stable across versions.
    try:    """
        return st.container(border=bool(border))
    except TypeError:return st.container(border=bool(border))
        return st.container()
tainer()

def _fmt_ts(ts: float | int | None) -> str:
    try: | int | None) -> str:
        if ts is None:
            return ""
        v = float(ts)
        if v <= 0:(ts)
            return ""        if v <= 0:
        import datetime as _dt            return ""
        return _dt.datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")dt
    except Exception:return _dt.datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")
        return ""


def _safe_float(v) -> float:
    try: -> float:
        if v is None:    try:
            return 0.0        if v is None:
        return float(v)
    except Exception:
        return 0.0:


def _extract_latest_price_from_logs(log_rows: list[dict]) -> float | None:
    """Best-effort: parse JSON log messages to find last price."""rice_from_logs(log_rows: list[dict]) -> float | None:
    if not log_rows:parse JSON log messages to find last price."""
        return None    if not log_rows:
    try:
        import json as _json
    except Exception:
        _json = None

    for row in log_rows:
        try:
            msg = row.get("message") if isinstance(row, dict) else None
            if not msg or not isinstance(msg, str):sinstance(row, dict) else None
                continuer not isinstance(msg, str):
            if _json is None:
                continue
            obj = _json.loads(msg)
            if not isinstance(obj, dict):son.loads(msg)
                continuej, dict):
            # prefer explicit price events
            if "price" in obj:ice events
                p = obj.get("price")
                try:get("price")
                    p = float(p)
                    if p > 0:p = float(p)
                        return p     if p > 0:
                except Exception:                        return p
                    pass                except Exception:
        except Exception:
            continue
    return None


def render_monitor_dashboard(theme: dict, preselected_bot: str | None = None):
    """Streamlit-native monitor: multi-bot overview + per-bot performance.""" = None):
    st.title("KuCoin PRO — Trading Terminal")nitor: multi-bot overview + per-bot performance."""
    st.header("Monitor — Painel de Performance")ading Terminal")
    st.caption("Acompanhe rendimento, trades, status e logs dos bots (múltiplos).")Performance")
nto, trades, status e logs dos bots (múltiplos).")
    # --- Load summary data (SQL aggregates are fast and UI-friendly)
    db = DatabaseManager()ggregates are fast and UI-friendly)
    sessions: list[dict] = []
    trade_agg: dict[str, dict] = {}    sessions: list[dict] = []
    log_agg: dict[str, dict] = {}
    try:r, dict] = {}
        conn = db.get_connection()
        cur = conn.cursor()

        # Recent sessions (running + recently stopped)
        cur.execute(ions (running + recently stopped)
            """cute(
            SELECT id, status, pid, symbol, mode, entry_price, start_ts, end_ts, dry_run   """
            FROM bot_sessions symbol, mode, entry_price, start_ts, end_ts, dry_run
            ORDER BY COALESCE(start_ts, 0) DESC
            LIMIT 200            ORDER BY COALESCE(start_ts, 0) DESC
            """
        )
        rows = cur.fetchall() or []
        sessions = [dict(r) for r in rows] or []
 = [dict(r) for r in rows]
        # Reconcile: sessions marked running but PID not alive => mark stopped.
        # This keeps Monitor consistent with the Dashboard "Bots Ativos" list.s marked running but PID not alive => mark stopped.
        now_ts = time.time()nt with the Dashboard "Bots Ativos" list.
        for sess in sessions:
            try::
                if str(sess.get("status") or "").lower() != "running":
                    continuet("status") or "").lower() != "running":
                pid = sess.get("pid")
                if _pid_alive(pid):= sess.get("pid")
                    continued):
                bot_id = str(sess.get("id") or "").strip()
                if not bot_id:trip()
                    continuet bot_id:
                try:
                    cur.execute(
                        "UPDATE bot_sessions SET status = ?, end_ts = ? WHERE id = ?",
                        ("stopped", now_ts, bot_id),ot_sessions SET status = ?, end_ts = ? WHERE id = ?",
                    )("stopped", now_ts, bot_id),
                    conn.commit()
                    sess["status"] = "stopped".commit()
                    sess["end_ts"] = now_ts                    sess["status"] = "stopped"
                except Exception:d_ts"] = now_ts
                    passpt Exception:
            except Exception:     pass
                continueon:

        # Trades aggregation
        cur.execute(
            """
            SELECT bot_id,
                   COUNT(1) AS trades,
                   COALESCE(SUM(COALESCE(profit,0)),0) AS profit_sum,    COUNT(1) AS trades,
                   MAX(COALESCE(timestamp,0)) AS last_trade_ts          COALESCE(SUM(COALESCE(profit,0)),0) AS profit_sum,
            FROM tradesp,0)) AS last_trade_ts
            WHERE bot_id IS NOT NULL AND bot_id != ''
            GROUP BY bot_id_id != ''
            """Y bot_id
        )
        for r in (cur.fetchall() or []):        )
            d = dict(r)hall() or []):
            bid = str(d.get("bot_id") or "")(r)
            if bid: = str(d.get("bot_id") or "")
                trade_agg[bid] = d

        # Logs aggregation
        cur.execute(n
            """
            SELECT bot_id,
                   COUNT(1) AS logs,ECT bot_id,
                   MAX(COALESCE(timestamp,0)) AS last_log_ts          COUNT(1) AS logs,
            FROM bot_logsp,0)) AS last_log_ts
            WHERE bot_id IS NOT NULL AND bot_id != ''gs
            GROUP BY bot_id_id != ''
            """Y bot_id
        )
        for r in (cur.fetchall() or []):
            d = dict(r)or []):
            bid = str(d.get("bot_id") or "")d = dict(r)
            if bid:bid = str(d.get("bot_id") or "")
                log_agg[bid] = d
    except Exception: = d
        sessions = sessions or []
    finally: = sessions or []
        try:    finally:
            if conn is not None:
                conn.close() not None:
        except Exception:    conn.close()
            pass

    bot_ids = []
    for s in sessions:
        try:s:
            bid = str(s.get("id") or "").strip()        try:
            if bid and bid not in bot_ids:tr(s.get("id") or "").strip()
                bot_ids.append(bid)
        except Exception:  bot_ids.append(bid)
            continue        except Exception:

    if not bot_ids:
        st.warning("Nenhuma sessão de bot encontrada no banco. Inicie um bot no Dashboard para ver dados aqui.")
        returnssão de bot encontrada no banco. Inicie um bot no Dashboard para ver dados aqui.")

    def _bot_label(bot_id: str) -> str:
        sess = next((x for x in sessions if str(x.get("id")) == str(bot_id)), None)
        if not sess:ot_id)), None)
            return str(bot_id)
        symbol = sess.get("symbol") or ""            return str(bot_id)
        mode = (sess.get("mode") or "")        symbol = sess.get("symbol") or ""
        status = (sess.get("status") or "")
        dry = "DRY" if int(sess.get("dry_run") or 0) == 1 else "REAL"
        return f"{bot_id[:12]}…  {symbol}  {mode}  {dry}  [{status}]"= 1 else "REAL"
eturn f"{bot_id[:12]}…  {symbol}  {mode}  {dry}  [{status}]"

    # Seleção automática do bot mais recente se não houver seleção manual
    if 'selected_bot' not in st.session_state or st.session_state.selected_bot not in bot_ids:
        selected_bot = bot_ids[0] if bot_ids else None not in st.session_state or st.session_state.selected_bot not in bot_ids:
    else:d_bot = bot_ids[0] if bot_ids else None
        selected_bot = st.session_state.selected_bot    else:
    try:e.selected_bot
        idx = bot_ids.index(selected_bot) if selected_bot in bot_ids else 0
    except Exception: if selected_bot in bot_ids else 0
        idx = 0

    with _safe_container(border=True):
        cols = st.columns([2.2, 1.0])e):
        selected_bot = cols[0].selectbox(
            "Bot para monitorar",elected_bot = cols[0].selectbox(
            options=bot_ids,
            index=idx,
            format_func=_bot_label,
            key="monitor_selected_bot",            format_func=_bot_label,
        )
        if cols[1].button("🔄 Atualizar", use_container_width=True, key="monitor_refresh"):)
            # Set a session flag to indicate a manual refresh request. Avoid immediate st.rerun()ner_width=True, key="monitor_refresh"):
            st.session_state['_monitor_manual_refresh_ts'] = time.time()immediate st.rerun()
time.time()
    # Persist selection for nav bar context
    try:t selection for nav bar context
        st.session_state.selected_bot = selected_bot    try:
        if selected_bot and selected_bot not in st.session_state.active_bots:t = selected_bot
            st.session_state.active_bots.append(selected_bot)if selected_bot and selected_bot not in st.session_state.active_bots:
    except Exception:e.active_bots.append(selected_bot)
        pass

    # --- Overview table (multi-bot)
    try: table (multi-bot)
        import pandas as pd    try:
        import datetime as _dt
    except Exception:e as _dt
        pd = None
        _dt = None

    overview_rows: list[dict] = []
    for s in sessions:]
        bid = str(s.get("id") or "")
        if not bid:
            continue
        ta = trade_agg.get(bid, {})
        la = log_agg.get(bid, {})
        pid_val = s.get("pid")d, {})
        alive_val = _pid_alive(pid_val)
        overview_rows.append({)
            "bot_id": bid,
            "status": s.get("status"),
            "pid": pid_val,
            "alive": bool(alive_val),
            "symbol": s.get("symbol"),
            "mode": s.get("mode"),
            "real/dry": "DRY" if int(s.get("dry_run") or 0) == 1 else "REAL",
            "start": _fmt_ts(s.get("start_ts")),ry_run") or 0) == 1 else "REAL",
            "end": _fmt_ts(s.get("end_ts")),
            "trades": int(ta.get("trades") or 0),  "end": _fmt_ts(s.get("end_ts")),
            "profit_sum": round(_safe_float(ta.get("profit_sum")), 6),            "trades": int(ta.get("trades") or 0),
            "last_trade": _fmt_ts(ta.get("last_trade_ts")),m": round(_safe_float(ta.get("profit_sum")), 6),
            "logs": int(la.get("logs") or 0),t_trade_ts")),
            "last_log": _fmt_ts(la.get("last_log_ts")),0),
        })

    if pd is not None:
        df_over = pd.DataFrame(overview_rows)
        st.subheader("Bots (visão geral)")
        # use module-level `_pid_alive` (defined at top of file)isão geral)")
        import oslive` (defined at top of file)

        db = DatabaseManager()
        active_bots_db = db.get_active_bots()
        real_active_bots = []ts_db = db.get_active_bots()
        for bot in active_bots_db:
            pid = bot.get('pid')        for bot in active_bots_db:
            if pid and _pid_alive(pid):
                real_active_bots.append(bot)
            else:       real_active_bots.append(bot)
                db.update_bot_session(bot['id'], {"status": "stopped", "end_ts": time.time()})
                db.update_bot_session(bot['id'], {"status": "stopped", "end_ts": time.time()})
        count_real = len(real_active_bots)
        # ...exibição de bots ativos já ocorre na seção principal, evitar duplicidade...e_bots)
    else:corre na seção principal, evitar duplicidade...
        st.info("Sem dados suficientes para plotar rendimento (equity/trades).")
es para plotar rendimento (equity/trades).")
    # Recent trades
    st.subheader("Trades recentes")
    trades = locals().get('trades', None)recentes")
    if pd is not None and trades:als().get('trades', None)
        df_tr = pd.DataFrame(trades)
        try:
            df_tr["datetime"] = df_tr["timestamp"].apply(lambda x: _fmt_ts(x))ry:
        except Exception: _fmt_ts(x))
            pass        except Exception:
        show_cols = [c for c in ["datetime", "side", "price", "size", "funds", "profit", "dry_run", "strategy"] if c in df_tr.columns]
        st.dataframe(df_tr[show_cols].tail(50).iloc[::-1], use_container_width=True, hide_index=True)"datetime", "side", "price", "size", "funds", "profit", "dry_run", "strategy"] if c in df_tr.columns]
    else:[::-1], use_container_width=True, hide_index=True)
        st.caption("Nenhum trade encontrado para este bot ainda.")
 ainda.")
    # Recent logs
    st.subheader("Logs recentes")s
    recent_logs = locals().get('recent_logs', None)
    if recent_logs:
        # Show newest first; keep compact for readability
        for row in recent_logs[:25]:
            try:s[:25]:
                ts = _fmt_ts(row.get("timestamp"))
                lvl = str(row.get("level") or "INFO")       ts = _fmt_ts(row.get("timestamp"))
                msg = str(row.get("message") or "")
                st.code(f"{ts} [{lvl}] {msg}", language="json")                msg = str(row.get("message") or "")
            except Exception:                st.code(f"{ts} [{lvl}] {msg}", language="json")
                continue            except Exception:
    else:
        st.caption("Nenhum log recente encontrado para este bot.")
st.caption("Nenhum log recente encontrado para este bot.")


def render_top_nav_bar(theme: dict, current_view: str, selected_bot: str | None = None):
    """Top horizontal nav bar shown on all pages."""def render_top_nav_bar(theme: dict, current_view: str, selected_bot: str | None = None):
    try:n all pages."""
        view = str(current_view or "dashboard").strip().lower()
    except Exception:
        view = "dashboard"

    # Botão de logout no topo direito
    col_logout = st.columns([10, 1])[1]
    if col_logout.button("🚪 Logout", key=f"logout_btn_{view}"):t.columns([10, 1])[1]
        # Limpar estado de sessão    if col_logout.button("🚪 Logout", key=f"logout_btn_{view}"):
        set_logged_in(False) estado de sessão
        for key in list(st.session_state.keys()):logged_in(False)
            del st.session_state[key] in list(st.session_state.keys()):
        st.rerun()n_state[key]

    st.markdown(
        f"""
        <style>
          .kc-nav-wrap {{
            border: 1px solid {theme.get('border')};c-nav-wrap {{
            background: {theme.get('bg2')};lid {theme.get('border')};
            border-radius: 10px;
            padding: 10px 10px;px;
            margin: 6px 0 16px 0;
          }}
          .kc-nav-title {{
            font-family: 'Courier New', monospace;
            font-weight: 800;font-family: 'Courier New', monospace;
            color: {theme.get('accent')}; 800;
                        font-size: clamp(0.78rem, 0.95vw, 0.95rem);
            text-transform: uppercase;(0.78rem, 0.95vw, 0.95rem);
            letter-spacing: 1px;
          }}letter-spacing: 1px;
          .kc-nav-sub {{          }}
            font-family: 'Courier New', monospace;
            color: {theme.get('text2')};ew', monospace;
                        font-size: clamp(0.72rem, 0.85vw, 0.9rem);
          }}2rem, 0.85vw, 0.9rem);

                    /* Link styled like a button (used for opening report in a new tab) */
                    .kc-link-btn {{for opening report in a new tab) */
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;;
                        width: 100%;
                        background: {theme.get('bg2')};
                        color: {theme.get('text')};
                        border: 2px solid {theme.get('border')};'text')};
                        border-radius: 8px;et('border')};
                        padding: clamp(0.55rem, 0.9vw, 0.7rem) clamp(0.85rem, 1.2vw, 1.05rem);
                        min-height: 44px;p(0.85rem, 1.2vw, 1.05rem);
                        font-family: 'Courier New', monospace;  min-height: 44px;
                        font-weight: bold;rier New', monospace;
                        text-transform: uppercase;
                        text-decoration: none;ase;
                        font-size: clamp(0.78rem, 0.95vw, 0.95rem);  text-decoration: none;
                    }}        font-size: clamp(0.78rem, 0.95vw, 0.95rem);
                    .kc-link-btn:hover {{        }}
                        filter: brightness(1.05);n:hover {{
                        text-decoration: none;                   filter: brightness(1.05);
                    }}                        text-decoration: none;
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown(ner():
            f"""own(
            <div class="kc-nav-wrap">
              <div class="kc-nav-title">NAVEGAÇÃO</div>   <div class="kc-nav-wrap">
              <div class="kc-nav-sub">Dashboard • Relatório</div>              <div class="kc-nav-title">NAVEGAÇÃO</div>
            </div>hboard • Relatório</div>
            """,
            unsafe_allow_html=True,
        )            unsafe_allow_html=True,

    cols = st.columns([1.15, 1.15, 4.70])
    dash_active = (view == "dashboard")
    report_active = (view == "report")= "dashboard")
e = (view == "report")
    if cols[0].button("🏠 Home", type="primary" if dash_active else "secondary", use_container_width=True, key="nav_home"):
        try:se "secondary", use_container_width=True, key="nav_home"):
            st.session_state.selected_bot = None        try:
        except Exception:
            pass
        _set_view("dashboard", clear_bot=True)
        # st.rerun()  # Removido para evitar reload desnecessário        _set_view("dashboard", clear_bot=True)
# st.rerun()  # Removido para evitar reload desnecessário
    if cols[1].button("📑 Relatório", type="primary" if report_active else "secondary", use_container_width=True, key="nav_rep"):
        _set_view("report", bot_id=selected_bot)("📑 Relatório", type="primary" if report_active else "secondary", use_container_width=True, key="nav_rep"):
        # st.rerun()  # Removido para evitar reload desnecessáriobot)
 # Removido para evitar reload desnecessário
    try:
        bot_txt = (str(selected_bot)[:12] + "…") if selected_bot else "(nenhum bot selecionado)"
    except Exception:   bot_txt = (str(selected_bot)[:12] + "…") if selected_bot else "(nenhum bot selecionado)"
        bot_txt = "(nenhum bot selecionado)"    except Exception:
    cols[2].markdown(        bot_txt = "(nenhum bot selecionado)"
        f"<div style=\"text-align:right;font-family:'Courier New',monospace;font-size:clamp(0.78rem,0.95vw,0.95rem);color:{theme.get('muted','#8b949e')};padding-top:10px;\">Bot: <b style=\"color:{theme.get('text')};\">{html.escape(bot_txt)}</b></div>",
        unsafe_allow_html=True,:right;font-family:'Courier New',monospace;font-size:clamp(0.78rem,0.95vw,0.95rem);color:{theme.get('muted','#8b949e')};padding-top:10px;\">Bot: <b style=\"color:{theme.get('text')};\">{html.escape(bot_txt)}</b></div>",
    )


def _list_theme_packs() -> list[str]:
    themes_root = ROOT / "themes"
    if not themes_root.exists() or not themes_root.is_dir():
        return []or not themes_root.is_dir():
    packs: list[str] = []]
    for p in sorted(themes_root.iterdir(), key=lambda x: x.name.lower()):    packs: list[str] = []
        # Hide internal/template packs from the UI by default    for p in sorted(themes_root.iterdir(), key=lambda x: x.name.lower()):
        if p.is_dir() and not p.name.startswith('.') and not p.name.startswith('_'): by default
            packs.append(p.name)dir() and not p.name.startswith('.') and not p.name.startswith('_'):
    return packsppend(p.name)


def _read_pack_manifest(pack: str) -> dict | None:
    if not pack:d_pack_manifest(pack: str) -> dict | None:
        return None
    mf = ROOT / "themes" / pack / "manifest.json"
    if not mf.exists() or not mf.is_file():
        return None) or not mf.is_file():
    try:
        import json as _json    try:
        data = _json.loads(mf.read_text(encoding="utf-8"))        import json as _json
        return data if isinstance(data, dict) else None
    except Exception:ne
        return None    except Exception:


def _get_pack_default_background(pack: str) -> str | None:
    """Return a preferred background stem for a pack. str | None:
eturn a preferred background stem for a pack.
    Supports the template-style manifest.json:
    {"backgrounds": {"default": "..."}}
    """}}
    manifest = _read_pack_manifest(pack) or {}
    try: = _read_pack_manifest(pack) or {}
        default_bg = (manifest.get("backgrounds") or {}).get("default")
        if isinstance(default_bg, str) and default_bg.strip():        default_bg = (manifest.get("backgrounds") or {}).get("default")
            return default_bg.strip()        if isinstance(default_bg, str) and default_bg.strip():
    except Exception:
        pass
    return None        pass


def _maybe_apply_smw_monitor_pack(theme: dict):
    """When the SMW theme is selected, default the monitor background pack.
W theme is selected, default the monitor background pack.
    With the simplified UX (no Pack/Imagem selectors), the theme drives the monitor background.
    """/Imagem selectors), the theme drives the monitor background.
    try:
        if not theme or theme.get("name") != "Super Mario World":
            return        if not theme or theme.get("name") != "Super Mario World":

        packs = _list_theme_packs()
        if not packs:)
            return

        preferred = None
        for candidate in ("smw", "super_mario_world", "super-mario-world", "user_sprite_pack"):= None
            if candidate in packs:        for candidate in ("smw", "super_mario_world", "super-mario-world", "user_sprite_pack"):
                preferred = candidate
                breakferred = candidate
        if not preferred:eak
            return        if not preferred:

        bgs = _list_pack_backgrounds(preferred)
        if not bgs:        bgs = _list_pack_backgrounds(preferred)
            return

        # Default behavior for SMW: random background on each reload.
        chosen = "random"avior for SMW: random background on each reload.
 = "random"
        # Set backing state (used when building the /monitor URL)
        st.session_state["monitor_bg_pack"] = preferred        # Set backing state (used when building the /monitor URL)
        st.session_state["monitor_bg"] = chosenrred
    except Exception:on_state["monitor_bg"] = chosen
        returnion:


def _list_pack_backgrounds(pack: str) -> list[str]:
    if not pack:nds(pack: str) -> list[str]:
        return []
    bg_dir = ROOT / "themes" / pack / "backgrounds"
    if not bg_dir.exists() or not bg_dir.is_dir(): pack / "backgrounds"
        return []dir.exists() or not bg_dir.is_dir():
    out: list[str] = []        return []
    for p in sorted(bg_dir.iterdir(), key=lambda x: x.name.lower()):    out: list[str] = []
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):ame.lower()):
            out.append(p.stem)) in (".png", ".jpg", ".jpeg", ".webp"):
    return out


# =====================================================
# FUNÇÃO ANTI-FLICKER PARA COMPONENTS.HTML
# =====================================================O ANTI-FLICKER PARA COMPONENTS.HTML
def render_html_smooth(html_content: str, height: int, key: str = None):
    """oth(html_content: str, height: int, key: str = None):
    Renderiza HTML sem piscar usando CSS anti-flicker e placeholder estável.
    Envolve o conteúdo em um wrapper estável sem animações de entrada.l.
    """ estável sem animações de entrada.
    # Gera uma key ESTÁVEL baseada no hash do conteúdo se não fornecida"""
    if key is None:fornecida
        # Usa hash completo do conteúdo para key estável
        content_hash = hashlib.md5(html_content.encode()).hexdigest()[:12]vel
        key = f"html_{content_hash}"st()[:12]
        key = f"html_{content_hash}"
    # Verifica se o conteúdo mudou desde a última renderização
    cache_key = f"html_cache_{key}"desde a última renderização
    cached_hash = st.session_state.get(cache_key, "")= f"html_cache_{key}"
    current_hash = hashlib.md5(html_content.encode()).hexdigest()cached_hash = st.session_state.get(cache_key, "")
    hlib.md5(html_content.encode()).hexdigest()
    # Se o conteúdo não mudou, não recria o iframe
    if cached_hash == current_hash:# Se o conteúdo não mudou, não recria o iframe
        return
    
    # Atualiza o cache
    st.session_state[cache_key] = current_hash
    on_state[cache_key] = current_hash
    # CSS anti-flicker wrapper SEM animação de fade-in (causa flash)
    smooth_html = f'''ção de fade-in (causa flash)
    <style>
        /* Anti-flicker e suavização global */
        * {{ Anti-flicker e suavização global */
            -webkit-backface-visibility: hidden;
            backface-visibility: hidden;ckface-visibility: hidden;
            -webkit-font-smoothing: antialiased;sibility: hidden;
            -moz-osx-font-smoothing: grayscale;thing: antialiased;
        }}
        html, body {{
            margin: 0;html, body {{
            padding: 0;
            overflow: hidden;
            background: transparent !important;idden;
        }}important;
        
        /* Container principal ESTÁTICO - sem animação de entrada */
        .smooth-wrapper {{/* Container principal ESTÁTICO - sem animação de entrada */
            opacity: 1;
            transform: translateZ(0);
            -webkit-transform: translateZ(0);
        }}Z(0);
        
        /* Previne layout shift e reflow */
        .content-stable {{/* Previne layout shift e reflow */
            contain: layout style paint;
            min-height: {height - 20}px;
            position: relative;
        }}  position: relative;
        }}
        /* Performance para elementos animados - sempre rodando */
        [class*="smw-"], [style*="animation"] {{rmance para elementos animados - sempre rodando */
            will-change: transform, opacity;*="animation"] {{
        }}  will-change: transform, opacity;
        
        /* Iframe background fix */
        :root {{ground fix */
            color-scheme: dark;oot {{
        }}     color-scheme: dark;
    </style>    }}
    <div class="smooth-wrapper content-stable" id="wrapper_{key}">
        {html_content}ntent-stable" id="wrapper_{key}">
    </div>
    '''v>
    
    # Use a stable placeholder DeltaGenerator to update HTML in-place (reduces flicker)
    ph_key = f"placeholder_{key}"pdate HTML in-place (reduces flicker)
    placeholder = st.session_state.get(ph_key)
    try:
        if placeholder is None:
            placeholder = st.empty()
            st.session_state[ph_key] = placeholderplaceholder = st.empty()
        # Use the placeholder's html renderer which updates in-place
        placeholder.html(smooth_html, height=height, scrolling=False)lder's html renderer which updates in-place
    except Exception:der.html(smooth_html, height=height, scrolling=False)
        # Fallback: direct render    except Exception:
        try:
            components.html(smooth_html, height=height, scrolling=False)
        except Exception: scrolling=False)
            passcept Exception:

# =====================================================
# TEMAS COBOL/TERMINAL===============================
# =====================================================
THEMES = {===========================
    "COBOL Verde": {
        "name": "COBOL Verde",
        "bg": "#0a0a0a",",
        "bg2": "#050505",
        "border": "#33ff33",
        "text": "#33ff33",
        "text2": "#aaffaa",
        "accent": "#00ffff",
        "warning": "#ffaa00",  "accent": "#00ffff",
        "error": "#ff3333", "#ffaa00",
        "success": "#00ff00",
        "header_bg": "linear-gradient(180deg, #1a3a1a 0%, #0d1f0d 100%)",f00",
        "glow": "rgba(51, 255, 51, 0.3)",ear-gradient(180deg, #1a3a1a 0%, #0d1f0d 100%)",
    },5, 51, 0.3)",
    "Amber CRT": {
        "name": "Amber CRT",
        "bg": "#0a0800",
        "bg2": "#050400",
        "border": "#ffaa00",
        "text": "#ffaa00",
        "text2": "#ffcc66",
        "accent": "#ffffff",
        "warning": "#ff6600",  "accent": "#ffffff",
        "error": "#ff3333",: "#ff6600",
        "success": "#ffff00",
        "header_bg": "linear-gradient(180deg, #3a2a0a 0%, #1f1505 100%)",f00",
        "glow": "rgba(255, 170, 0, 0.3)",ear-gradient(180deg, #3a2a0a 0%, #1f1505 100%)",
    },70, 0, 0.3)",
    "IBM Blue": {
        "name": "IBM Blue",
        "bg": "#000033",
        "bg2": "#000022",
        "border": "#3399ff",
        "text": "#3399ff",
        "text2": "#99ccff",
        "accent": "#ffffff",
        "warning": "#ffaa00",  "accent": "#ffffff",
        "error": "#ff6666",g": "#ffaa00",
        "success": "#66ff66",",
        "header_bg": "linear-gradient(180deg, #0a1a3a 0%, #050d1f 100%)",f66",
        "glow": "rgba(51, 153, 255, 0.3)",ear-gradient(180deg, #0a1a3a 0%, #050d1f 100%)",
    },3, 255, 0.3)",
    "Matrix": {
        "name": "Matrix",
        "bg": "#000000",
        "bg2": "#001100",
        "border": "#00ff00",
        "text": "#00ff00",
        "text2": "#88ff88",
        "accent": "#ffffff",
        "warning": "#ffff00",  "accent": "#ffffff",
        "error": "#ff0000", "#ffff00",
        "success": "#00ff00",
        "header_bg": "linear-gradient(180deg, #002200 0%, #001100 100%)",f00",
        "glow": "rgba(0, 255, 0, 0.5)",ear-gradient(180deg, #002200 0%, #001100 100%)",
    },, 0, 0.5)",
    "Cyberpunk": {
        "name": "Cyberpunk",
        "bg": "#0d0221",
        "bg2": "#1a0533",
        "border": "#ff00ff",
        "text": "#ff00ff",
        "text2": "#ff99ff",
        "accent": "#00ffff",
        "warning": "#ffff00",  "accent": "#00ffff",
        "error": "#ff3333",0",
        "success": "#00ff00",
        "header_bg": "linear-gradient(180deg, #2d0a4e 0%, #1a0533 100%)",
        "glow": "rgba(255, 0, 255, 0.4)",0%)",
    },
    "Super Mario World": {
        "name": "Super Mario World",
        "bg": "#5c94fc",           # Céu azul do Mario
        "bg2": "#4a7acc",          # Azul mais escuro para contrasteio
        "border": "#e52521",       # Vermelho do Marios escuro para contraste
        "text": "#ffffff",         # Brancolho do Mario
        "text2": "#1a1a1a",        # Preto para legibilidade
        "accent": "#43b047",       # Verde dos canos/Luigie
        "warning": "#fbd000",      # Amarelo estrelai
        "error": "#e52521",        # Vermelho  "warning": "#fbd000",      # Amarelo estrela
        "success": "#43b047",      # Verde       "error": "#e52521",        # Vermelho
        "header_bg": "linear-gradient(180deg, #5c94fc 0%, #3878d8 100%)",        "success": "#43b047",      # Verde
        "glow": "rgba(251, 208, 0, 0.5)",  # Brilho dourado        "header_bg": "linear-gradient(180deg, #5c94fc 0%, #3878d8 100%)",
        "is_light": True,          # Flag para tema claro1, 208, 0, 0.5)",  # Brilho dourado
    },para tema claro
}


def get_current_theme():
    """Retorna o tema atual selecionado"""
    theme_name = st.session_state.get("terminal_theme", "COBOL Verde")ado"""
    return THEMES.get(theme_name, THEMES["COBOL Verde"])    theme_name = st.session_state.get("terminal_theme", "COBOL Verde")
    return THEMES.get(theme_name, THEMES["COBOL Verde"])

def _theme_config_path() -> Path:
    return ROOT / ".last_theme.json":
heme.json"

def _load_saved_theme() -> str | None:
    try:
        p = _theme_config_path()
        if not p.exists():ig_path()
            return Nonets():
        data = json.loads(p.read_text(encoding="utf-8") or "{}")return None
        name = data.get("terminal_theme")json.loads(p.read_text(encoding="utf-8") or "{}")
        if name and name in THEMES:        name = data.get("terminal_theme")
            return name        if name and name in THEMES:
    except Exception:
        passpt Exception:
    return None


def _save_theme(name: str) -> None:
    try:def _save_theme(name: str) -> None:
        p = _theme_config_path()    try:
        p.write_text(json.dumps({"terminal_theme": name}), encoding="utf-8")
    except Exception:    p.write_text(json.dumps({"terminal_theme": name}), encoding="utf-8")
        pass


# Ensure session state has the saved theme on first run of a session
try:ion state has the saved theme on first run of a session
    if "terminal_theme" not in st.session_state:
        saved = _load_saved_theme()theme" not in st.session_state:
        if saved:saved = _load_saved_theme()
            st.session_state["terminal_theme"] = saved        if saved:
        else:            st.session_state["terminal_theme"] = saved
            st.session_state.setdefault("terminal_theme", "COBOL Verde")
except Exception:
    pass


def inject_global_css():
    """Injeta CSS global para estilizar toda a página no tema terminal"""
    theme = get_current_theme()
    is_light_theme = theme.get("is_light", False)
is_light_theme = theme.get("is_light", False)
    # Button text colors computed for contrast against theme colors
    btn_text = _contrast_text_for_bg(theme.get("border"), light="#ffffff", dark="#000000")
    btn_hover_text = _contrast_text_for_bg(theme.get("accent"), light="#ffffff", dark="#000000")ffffff", dark="#000000")
    btn_primary_text = _contrast_text_for_bg(theme.get("success"), light="#ffffff", dark="#000000")ight="#ffffff", dark="#000000")
    btn_primary_text = _contrast_text_for_bg(theme.get("success"), light="#ffffff", dark="#000000")
    # Cores de texto para widgets em temas claros
    input_text_color = "#1a1a1a" if is_light_theme else theme["text"]os
    input_bg_color = "#ffffff" if is_light_theme else theme["bg2"]f is_light_theme else theme["text"]
    label_color = "#1a1a1a" if is_light_theme else theme["text2"]ffff" if is_light_theme else theme["bg2"]
    1a" if is_light_theme else theme["text2"]
    # Desativar efeito CRT para temas claros
    crt_effect = "" if is_light_theme else f'''ito CRT para temas claros
        /* CRT scan line effect */if is_light_theme else f'''
        .stApp::before {{ effect */
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            background: repeating-linear-gradient(e;
                0deg,ckground: repeating-linear-gradient(
                rgba(0, 0, 0, 0.1),
                rgba(0, 0, 0, 0.1) 1px,      rgba(0, 0, 0, 0.1),
                transparent 1px,        rgba(0, 0, 0, 0.1) 1px,
                transparent 2px
            );px
            z-index: 9999;
        }}
        
        /* Flicker animation for authentic CRT feel */
        @keyframes flicker {{/* Flicker animation for authentic CRT feel */
            0% {{ opacity: 0.97; }}s flicker {{
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.98; }}  50% {{ opacity: 1; }}
        }}     100% {{ opacity: 0.98; }}
            }}
        .stApp {{
            animation: flicker 0.15s infinite;
        }}    animation: flicker 0.15s infinite;
    '''
    
    # Optional: apply a SMW sprite/background to the main Streamlit UI.    
    smw_bg_css = ""
    try:
        if theme.get("name") == "Super Mario World":
            bg_data_uri = None

            # Keep a stable background during the session; changes on hard refresh.
            chosen = st.session_state.get("_smw_main_bg")kground during the session; changes on hard refresh.
            if not chosen:t("_smw_main_bg")
                # Pick from themes/smw/manifest.json when present.
                mf = ROOT / "themes" / "smw" / "manifest.json"
                items = Noneemes" / "smw" / "manifest.json"
                if mf.exists():
                    import json as _json
                    data = _json.loads(mf.read_text(encoding="utf-8")) _json
                    items = (data.get("backgrounds") or {}).get("items")ead_text(encoding="utf-8"))
                candidates = []ms")
                if isinstance(items, dict):
                    candidates = [k for k in items.keys() if isinstance(k, str) and k.strip()]
                if not candidates: = [k for k in items.keys() if isinstance(k, str) and k.strip()]
                    # fallback: scan folder
                    bg_dir = ROOT / "themes" / "smw" / "backgrounds"
                    if bg_dir.exists():rounds"
                        candidates = [p.stem for p in bg_dir.iterdir() if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]                    if bg_dir.exists():
                if candidates:file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
                    import random as _random
                    chosen = _random.choice(sorted(candidates))
                    st.session_state["_smw_main_bg"] = chosenosen = _random.choice(sorted(candidates))

            # IMPORTANT: do not fetch the background from the local API server.
            # If the API server is stopped or slow, the browser keeps the tab in a from the local API server.
            # perpetual "loading" state. Instead embed the selected image as a data URI.ed or slow, the browser keeps the tab in a
            if chosen:al "loading" state. Instead embed the selected image as a data URI.
                cached = st.session_state.get("_smw_main_bg_data_uri")
                cached_name = st.session_state.get("_smw_main_bg_data_uri_name")")
                if cached and cached_name == chosen:ata_uri_name")
                    bg_data_uri = cached
                else:ed
                    bg_file = None
                    bg_dir = ROOT / "themes" / "smw" / "backgrounds"e
                    for ext in (".png", ".jpg", ".jpeg", ".webp"):"backgrounds"
                        p = bg_dir / f"{chosen}{ext}"
                        if p.exists():ext}"
                            bg_file = p
                            break
                    if not bg_file and bg_dir.exists():                            break
                        # In case chosen already includes an extension or is a full filename.():
                        p = bg_dir / str(chosen) includes an extension or is a full filename.
                        if p.exists() and p.is_file():
                            bg_file = p                        if p.exists() and p.is_file():

                    if bg_file and bg_file.exists():
                        import base64 as _base64
                        import mimetypes as _mimetypes

                        mime = _mimetypes.guess_type(str(bg_file))[0] or "image/png"
                        b64 = _base64.b64encode(bg_file.read_bytes()).decode("ascii")e = _mimetypes.guess_type(str(bg_file))[0] or "image/png"
                        bg_data_uri = f"data:{mime};base64,{b64}"scii")
                        st.session_state["_smw_main_bg_data_uri"] = bg_data_uriri = f"data:{mime};base64,{b64}"
                        st.session_state["_smw_main_bg_data_uri_name"] = chosent.session_state["_smw_main_bg_data_uri"] = bg_data_uri
ate["_smw_main_bg_data_uri_name"] = chosen
            if bg_data_uri:
                # Apply to the whole app. Add a subtle overlay for readability.
                smw_bg_css = f'''d a subtle overlay for readability.
                .stApp {{
                    background-image:{
                      linear-gradient(
                        180deg,
                        rgba(0,0,0,0.25) 0%,
                        rgba(0,0,0,0.35) 100%
                      ),
                      url("{bg_data_uri}") !important;    ),
                    background-size: cover !important;
                    background-position: center !important;r !important;
                    background-repeat: no-repeat !important;
                    background-attachment: fixed !important;  background-repeat: no-repeat !important;
                }}
                /* Let the background image show through */
                .main .block-container {{
                    background-color: transparent !important;ain .block-container {{
                }}important;
                /* Make containers readable over the background */
                .stApp [data-testid="stAppViewContainer"] > .main {{ Make containers readable over the background */
                    background: rgba(0,0,0,0.18) !important;App [data-testid="stAppViewContainer"] > .main {{
                }}ackground: rgba(0,0,0,0.18) !important;
                section[data-testid="stSidebar"] {{
                    background: rgba(0,0,0,0.25) !important;                section[data-testid="stSidebar"] {{
                }}      background: rgba(0,0,0,0.25) !important;
                '''     }}
    except Exception:
        smw_bg_css = ""

    css = f'''
    <style>
        /* =====================================================
           Escala fluida global (fonte + espaçamento)=========
           Mantém a UI proporcional em qualquer resolução.mento)
           ===================================================== */ resolução.
        :root {{================= */
            /* VSCode-like default sizing: smaller, still responsive */
            --kc-font: clamp(12px, 0.55vw + 7px, 16px);  /* VSCode-like default sizing: smaller, still responsive */
            --kc-s-1: clamp(6px, 0.55vw, 10px);            --kc-font: clamp(12px, 0.55vw + 7px, 16px);
            --kc-s-2: clamp(10px, 0.9vw, 16px);c-s-1: clamp(6px, 0.55vw, 10px);
            --kc-s-3: clamp(14px, 1.2vw, 22px);w, 16px);
            --kc-gap: clamp(10px, 1.2vw, 18px);  --kc-s-3: clamp(14px, 1.2vw, 22px);
        }}            --kc-gap: clamp(10px, 1.2vw, 18px);

        html {{
            font-size: var(--kc-font);
        }}

        /* ===== ANTI-FLICKER GLOBAL ===== */
        /* Previne flash branco durante transições */ ===== ANTI-FLICKER GLOBAL ===== */
        iframe {{/* Previne flash branco durante transições */
            background: {theme["bg"]} !important;
            transition: none !important;background: {theme["bg"]} !important;
            border: none !important;
        }}  border: none !important;
        }}
        /* Desabilita transições que causam flash */
        * {{ões que causam flash */
            transition: none !important;
        }}rtant;
        
        /* Previne reflow durante atualizações */
        .element-container {{s */
            contain: layout style;
            will-change: contents;  contain: layout style;
        }}    will-change: contents;
        
        [data-testid="stElementContainer"] {{
            contain: layout style;
        }}
        
        /* Fix para iframes de components.html - FORÇA fundo escuro */
        iframe[title="streamlit_components.v1.components.html"] {{/* Fix para iframes de components.html - FORÇA fundo escuro */
            background-color: {theme["bg"]} !important;ts.v1.components.html"] {{
            opacity: 1 !important;ortant;
            visibility: visible !important;
        }}  visibility: visible !important;
        }}
        /* Previne flash em fragments */
        [data-testid="stVerticalBlock"] > div {{e flash em fragments */
            background-color: transparent !important;
        }}
        
        /* Reset e base */
        .stApp {{
            background-color: {theme["bg"]} !important;
            font-family: 'Courier New', 'Lucida Console', monospace !important;
        }}onospace !important;
        
        /* Main container */
        .main .block-container {{
            background-color: {theme["bg"]} !important;
            border: 2px solid {theme["border"]} !important;  background-color: {theme["bg"]} !important;
            border-radius: 8px !important;            border: 2px solid {theme["border"]} !important;
            box-shadow: 0 0 30px {theme["glow"]}, inset 0 0 50px rgba(0,0,0,0.5) !important;
            padding: var(--kc-s-3) !important;rgba(0,0,0,0.5) !important;
            margin: var(--kc-s-2) !important;
        }} !important;

        /* Force the main block to use the full viewport width so dashboard
           columns can expand responsively across resolutions. */ the full viewport width so dashboard
        .stApp [data-testid="stAppViewContainer"] > .main .block-container,ely across resolutions. */
        .stApp .block-container { .main .block-container,
            max-width: 100% !important;
            width: 100% !important;   max-width: 100% !important;
            margin-left: 0 !important;            width: 100% !important;
            margin-right: 0 !important;
            padding-left: var(--kc-s-3) !important;
            padding-right: var(--kc-s-3) !important;
        }-right: var(--kc-s-3) !important;

        /* Let columns be flexible and avoid fixed calc widths imposed by
           some Streamlit builds; this helps `st.columns([1, 999])` behaveand avoid fixed calc widths imposed by
           as expected and fill the available frame. */  some Streamlit builds; this helps `st.columns([1, 999])` behave
        .stColumn {   as expected and fill the available frame. */
            min-width: 0 !important;
            flex: 1 1 0% !important;nt;
            width: auto !important;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{        /* Headers */
            color: {theme["text"]} !important;
            font-family: 'Courier New', monospace !important;
            text-shadow: 0 0 10px {theme["glow"]} !important;
        }}    text-shadow: 0 0 10px {theme["glow"]} !important;

        h1 {{ font-size: clamp(1.35rem, 1.8vw, 2.1rem) !important; }}
        h2 {{ font-size: clamp(1.10rem, 1.4vw, 1.55rem) !important; }}; }}
        h3 {{ font-size: clamp(1.00rem, 1.2vw, 1.35rem) !important; }}h2 {{ font-size: clamp(1.10rem, 1.4vw, 1.55rem) !important; }}
        00rem, 1.2vw, 1.35rem) !important; }}
        h1::before {{ content: ">>> "; color: {theme["accent"]}; }}
        h2::before {{ content: ">> "; color: {theme["accent"]}; }}theme["accent"]}; }}
        h3::before {{ content: "> "; color: {theme["accent"]}; }}}; }}
        ::before {{ content: "> "; color: {theme["accent"]}; }}
        /* Paragraphs and text */
        p, span, label, .stMarkdown {{ and text */
            color: {theme["text2"]} !important;{{
            font-family: 'Courier New', monospace !important;
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {theme["bg2"]} !important;
            border-right: 2px solid {theme["border"]} !important;  background-color: {theme["bg2"]} !important;
        }}    border-right: 2px solid {theme["border"]} !important;
        
        [data-testid="stSidebar"] * {{
            color: {theme["text2"]} !important;
        }};
        
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,="stSidebar"] h1,
        [data-testid="stSidebar"] h3 {{
            color: {theme["text"]} !important;
        }}tant;
        
        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div {{,
            background-color: {input_bg_color} !important;
            color: {input_text_color} !important;!important;
            border: 2px solid {theme["border"]} !important;  color: {input_text_color} !important;
            font-family: 'Courier New', monospace !important;    border: 2px solid {theme["border"]} !important;
            border-radius: 4px !important;ce !important;
            font-size: 0.95rem !important;
            padding: 0.55rem 0.6rem !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {{v > input:focus,
            box-shadow: 0 0 10px {theme["glow"]} !important;v > div > input:focus {{
            border-color: {theme["accent"]} !important;0px {theme["glow"]} !important;
        }}theme["accent"]} !important;
        
        /* Labels dos inputs */
        .stTextInput label,
        .stNumberInput label,
        .stSelectbox label,tNumberInput label,
        .stCheckbox label,.stSelectbox label,
        .stRadio label {{abel,
            color: {label_color} !important;
            font-weight: bold !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: {theme["border"]} !important;
            color: {btn_text} !important;important;
            border: 2px solid {theme["border"]} !important;
            font-family: 'Courier New', monospace !important;} !important;
            font-weight: bold !important;nospace !important;
            text-transform: uppercase !important;
            text-decoration: none;mportant;
            font-size: clamp(0.78rem, 0.95vw, 0.95rem); ease !important;
            padding: 0.55em 0.85em !important;!important;
            min-height: 2.75em !important;.85em !important;
            line-height: 1.1 !important;  min-height: 2.75em !important;
            white-space: nowrap;            font-size: 0.92em !important;
            text-align: center;
            overflow: hidden;ap;
        }}

        /* Keep button labels readable (avoid vertical stacking) */
        .stButton > button p,
        .stButton > button span {{ertical stacking) */
            white-space: nowrap !important;
            word-break: keep-all !important;tButton > button span {{
            overflow: hidden !important;            white-space: nowrap !important;
            text-overflow: ellipsis !important;
            margin: 0 !important;t;
        }}mportant;

        /* Extra help for the bot table buttons (LOG/REL/Kill) */
        [class*="st-key-log_"] button,
        [class*="st-key-rep_"] button,LOG/REL/Kill) */
        [class*="st-key-kill_"] button,
        [class*="st-key-log_stopped_"] button,
        [class*="st-key-rep_stopped_"] button,
        [class*="st-key-kill_stopped_"] button {{lass*="st-key-log_stopped_"] button,
            min-width: 5.2em !important;        [class*="st-key-rep_stopped_"] button,
            padding: 0.50em 0.70em !important;
            font-size: 0.90em !important;
        }}

        /* Reduce excessive gaps between Streamlit columns on some builds */
        .main [data-testid="stHorizontalBlock"] {{
            column-gap: var(--kc-gap) !important;lumns on some builds */
            row-gap: var(--kc-gap) !important;talBlock"] {{
        }}p) !important;
rtant;
        /* Progress bar: keep it inside its column */
        [data-testid="stProgress"] {{
            width: 100% !important;side its column */
            overflow: hidden !important;
        }}  width: 100% !important;
        [data-testid="stProgress"] > div {{
            width: 100% !important;
            overflow: hidden !important;ata-testid="stProgress"] > div {{
        }}    width: 100% !important;
        [data-baseweb="progress-bar"] {{tant;
            max-width: 100% !important;
        }}
        
        .stButton > button:hover {{
            background-color: {theme["accent"]} !important;
            border-color: {theme["accent"]} !important;.stButton > button:hover {{
            color: {btn_hover_text} !important;: {theme["accent"]} !important;
            box-shadow: 0 0 20px {theme["glow"]} !important;important;
        }}
        ant;
        /* Primary button */
        .stButton > button[kind="primary"] {{
            background-color: {theme["success"]} !important;/* Primary button */
            border-color: {theme["success"]} !important;
            color: {btn_primary_text} !important;;
        }};
        t;
        .stButton > button[kind="primary"]:hover {{
            background-color: {theme["accent"]} !important;
            border-color: {theme["accent"]} !important;button[kind="primary"]:hover {{
            color: {btn_hover_text} !important;und-color: {theme["accent"]} !important;
        }}
        
        /* Alerts */
        .stAlert {{
            background-color: {theme["bg2"]} !important;/* Alerts */
            border: 1px solid {theme["border"]} !important;
            font-family: 'Courier New', monospace !important;
        }}
          font-family: 'Courier New', monospace !important;
        [data-testid="stAlertContainer"] {{}}
            background-color: {theme["bg2"]} !important;
            border-left: 4px solid {theme["success"]} !important;
        }}ortant;
          border-left: 4px solid {theme["success"]} !important;
        /* Success alert */}}
        .stAlert [data-testid="stAlertContentSuccess"] {{
            color: {theme["success"]} !important;
        }}ess"] {{
          color: {theme["success"]} !important;
        /* Warning alert */}}
        .stAlert [data-testid="stAlertContentWarning"] {{
            color: {theme["warning"]} !important;
        }}rning"] {{
          color: {theme["warning"]} !important;
        /* Error alert */}}
        .stAlert [data-testid="stAlertContentError"] {{
            color: {theme["error"]} !important;ror alert */
        }}
        
        /* Dividers */
        hr {{
            border-color: {theme["border"]} !important;/
            box-shadow: 0 0 5px {theme["glow"]} !important;
        }}
        
        /* Metrics */
        [data-testid="stMetric"] {{
            background-color: {theme["bg2"]} !important; Metrics */
            border: 1px solid {theme["border"]} !important;[data-testid="stMetric"] {{
            padding: var(--kc-s-2) !important;2"]} !important;
            border-radius: 4px !important;!important;
        }}
          border-radius: 4px !important;
        [data-testid="stMetricValue"] {{}}
            color: {theme["accent"]} !important;
            font-family: 'Courier New', monospace !important;
        }}  color: {theme["accent"]} !important;
            font-family: 'Courier New', monospace !important;
        [data-testid="stMetricLabel"] {{
            color: {theme["text2"]} !important;
        }}
          color: {theme["text2"]} !important;
        /* Selectbox dropdown */}}
        [data-baseweb="select"] {{
            background-color: {input_bg_color} !important;
        }}
        
        [data-baseweb="select"] > div {{
            background-color: {input_bg_color} !important;
            color: {input_text_color} !important;> div {{
            border: 2px solid {theme["border"]} !important;
        }}
          border: 2px solid {theme["border"]} !important;
        [data-baseweb="menu"] {{}}
            background-color: {input_bg_color} !important;
            border: 2px solid {theme["border"]} !important;
        }}
          border: 2px solid {theme["border"]} !important;
        [data-baseweb="menu"] li {{}}
            color: {input_text_color} !important;
            background-color: {input_bg_color} !important;
        }}!important;
          background-color: {input_bg_color} !important;
        [data-baseweb="menu"] li:hover {{}}
            background-color: {theme["border"]} !important;
            color: #ffffff !important;
        }} !important;
        f !important;
        /* Caption text */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {theme["text2"]} !important;*/
            opacity: 0.8;, [data-testid="stCaptionContainer"] {{
        }}
        
        /* Info boxes */
        .stInfo {{
            background-color: {theme["bg2"]} !important;/
            border-left: 4px solid {theme["accent"]} !important;
        }}
        ent"]} !important;
        /* Text area */
        .stTextArea textarea {{
            background-color: {theme["bg2"]} !important; Text area */
            color: {theme["text"]} !important;.stTextArea textarea {{
            border: 1px solid {theme["border"]} !important;-color: {theme["bg2"]} !important;
            font-family: 'Courier New', monospace !important;important;
        }}nt;
        ace !important;
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {theme["bg2"]} !important;/* Expander */
            color: {theme["text"]} !important;Header {{
            border: 1px solid {theme["border"]} !important;lor: {theme["bg2"]} !important;
        }}
        "border"]} !important;
        /* Radio buttons */
        .stRadio > div {{
            background-color: transparent !important;/* Radio buttons */
            padding: 10px !important;
            border-radius: 4px !important;mportant;
        }}  padding: 10px !important;
            border-radius: 4px !important;
        .stRadio label {{
            color: {label_color} !important;
        }}tRadio label {{
            color: {label_color} !important;
        .stRadio label span {{
            color: {label_color} !important;
        }}
          color: {label_color} !important;
        /* Checkbox */}}
        .stCheckbox label {{
            color: {label_color} !important;
        }}tCheckbox label {{
            color: {label_color} !important;
        .stCheckbox label span {{
            color: {label_color} !important;
        }}
          color: {label_color} !important;
        /* Checkbox box */}}
        .stCheckbox [data-testid="stCheckbox"] {{
            accent-color: {theme["border"]} !important;
        }}
          accent-color: {theme["border"]} !important;
        /* Progress bar */}}
        .stProgress > div > div {{
            background-color: {theme["border"]} !important;
        }}iv > div {{
        olor: {theme["border"]} !important;
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}  width: 8px;
            height: 8px;
        ::-webkit-scrollbar-track {{
            background: {theme["bg"]} !important;
        }}ck {{
          background: {theme["bg"]} !important;
        ::-webkit-scrollbar-thumb {{}}
            background: {theme["border"]} !important;
            border-radius: 4px;
        }}  background: {theme["border"]} !important;
            border-radius: 4px;
        ::-webkit-scrollbar-thumb:hover {{
            background: {theme["accent"]} !important;
        }}
        
        {crt_effect}
        
        /* FORCE ALL BACKGROUNDS TO DARK */{crt_effect}
        div, section, header, footer, main, aside, article {{
            background-color: transparent !important;
        }}cle {{
          background-color: transparent !important;
        /* Streamlit specific white backgrounds */}}
        [data-testid="stAppViewContainer"] {{
            background-color: {theme["bg"]} !important;
        }}ata-testid="stAppViewContainer"] {{
            background-color: {theme["bg"]} !important;
        [data-testid="stHeader"] {{
            background-color: {theme["bg"]} !important;
        }}ata-testid="stHeader"] {{
            background-color: {theme["bg"]} !important;
        [data-testid="stToolbar"] {{
            background-color: {theme["bg"]} !important;
        }}ata-testid="stToolbar"] {{
            background-color: {theme["bg"]} !important;
        [data-testid="stDecoration"] {{
            background-color: {theme["bg"]} !important;
        }}ata-testid="stDecoration"] {{
            background-color: {theme["bg"]} !important;
        [data-testid="stBottomBlockContainer"] {{
            background-color: {theme["bg"]} !important;
        }}
          background-color: {theme["bg"]} !important;
        /* Main area */}}
        .main {{
            background-color: {theme["bg"]} !important;rea */
        }}
          background-color: {theme["bg"]} !important;
        /* All iframes and embeds */}}
        iframe {{
            background-color: {theme["bg"]} !important; */
        }}
        
        /* Form elements */
        [data-testid="stForm"] {{
            background-color: {theme["bg2"]} !important;
            border: 1px solid {theme["border"]} !important;
        }}
        
        /* Popover and modals */
        [data-baseweb="popover"] {{
            background-color: {theme["bg2"]} !important; and modals */
            border: 1px solid {theme["border"]} !important;
        }};
          border: 1px solid {theme["border"]} !important;
        /* Tabs */}}
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {theme["bg"]} !important;
        }}
          background-color: {theme["bg"]} !important;
        .stTabs [data-baseweb="tab"] {{}}
            background-color: {theme["bg2"]} !important;
            color: {theme["text"]} !important;
        }}  background-color: {theme["bg2"]} !important;
            color: {theme["text"]} !important;
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {theme["border"]} !important;
        }}"]:hover {{
        nt;
        /* Data editor / table */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{ble */
            background-color: {theme["bg2"]} !important;="stDataFrame"],
        }}
          background-color: {theme["bg2"]} !important;
        /* Column config */}}
        .stColumn {{
            background-color: transparent !important;
        }}
          background-color: transparent !important;
        /* Element container */}}
        [data-testid="stElementContainer"] {{
            background-color: transparent !important;
        }}
          background-color: transparent !important;
        /* Vertical block */}}
        [data-testid="stVerticalBlock"] {{
            background-color: transparent !important;
        }}
          background-color: transparent !important;
        /* Horizontal block */}}
        [data-testid="stHorizontalBlock"] {{
            background-color: transparent !important;ck */
        }}
          background-color: transparent !important;
        /* Widget label */}}
        .stWidgetLabel {{
            color: {theme["text2"]} !important;
        }}
        
        /* Toast notifications */
        [data-testid="stToast"] {{
            background-color: {theme["bg2"]} !important;/* Toast notifications */
            border: 1px solid {theme["border"]} !important;"stToast"] {{
            color: {theme["text"]} !important;d-color: {theme["bg2"]} !important;
        }}rtant;
          color: {theme["text"]} !important;
        /* Spinner */}}
        .stSpinner {{
            background-color: transparent !important;
        }}
        ent !important;
        /* Number input buttons */
        .stNumberInput button {{
            background-color: {theme["border"]} !important;/* Number input buttons */
            color: #ffffff !important;
            border-color: {theme["border"]} !important;
        }}
          border-color: {theme["border"]} !important;
        .stNumberInput button:hover {{}}
            background-color: {theme["accent"]} !important;
            border-color: {theme["accent"]} !important;
        }}nt"]} !important;
        
        /* Select all white/light backgrounds */
        [style*="background-color: white"],
        [style*="background-color: #fff"],
        [style*="background-color: rgb(255, 255, 255)"],tyle*="background-color: white"],
        [style*="background: white"],[style*="background-color: #fff"],
        [style*="background: #fff"] {{: rgb(255, 255, 255)"],
            background-color: {theme["bg"]} !important;nd: white"],
        }}
          background-color: {theme["bg"]} !important;
        /* Base web components */}}
        [data-baseweb] {{
            background-color: transparent !important;
        }}
          background-color: transparent !important;
        /* Input containers */}}
        [data-baseweb="input"] {{
            background-color: {input_bg_color} !important;
        }}ata-baseweb="input"] {{
            background-color: {input_bg_color} !important;
        [data-baseweb="input"] input {{
            color: {input_text_color} !important;
        }}
          color: {input_text_color} !important;
        [data-baseweb="base-input"] {{        }}
            background-color: {input_bg_color} !important;
            border: 2px solid {theme["border"]} !important;put"] {{
        }}
heme["border"]} !important;
        /* Extra override: remove gaps between dashboard and the outer frame */
        .stMainBlockContainer,
        .stApp [data-testid="stAppViewContainer"] > .main,between dashboard and the outer frame */
        .main .block-container {
            margin: 0 !important;"] > .main,
            padding: 0 !important;main .block-container {
            max-width: 100% !important;
            width: 100% !important;: 0 !important;
            background: transparent !important;nt;
        }
        /* Make columns truly flexible and remove side paddings */portant;
        .stColumn {
            min-width: 0 !important;* Make columns truly flexible and remove side paddings */
            flex: 1 1 0% !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
        /* Remove extra padding on the main app view wrapper */   padding-right: 0 !important;
        .stApp > div[role="main"] > div {
            padding-left: 0 !important; */
            padding-right: 0 !important;        .stApp > div[role="main"] > div {
        }left: 0 !important;
        /* Reset any explicit top-padding added elsewhere */padding-right: 0 !important;
        .stMainBlockContainer { padding-top: 0 !important; } }
ded elsewhere */
        {smw_bg_css}        .stMainBlockContainer { padding-top: 0 !important; }
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)
    '''

def render_theme_selector(ui=None, key_suffix=""):
    """Renderiza seletor de tema.
def render_theme_selector(ui=None, key_suffix=""):
    A sidebar é escondida globalmente; por padrão este seletor renderiza no
    container atual. Se `ui` for um container (ex.: coluna), renderiza dentro dele.
    """seletor renderiza no

    # By default, avoid rendering inline when called without a container.
    # This prevents accidental duplicate renderings if older code paths
    # call this function without an explicit container.ring inline when called without a container.
    if ui is None and not st.session_state.get("_allow_inline_theme_selector", False):s
        returnhis function without an explicit container.
heme_selector", False):
    def render_bot_control():
        # Defensive: require login per session before rendering any UI
        try:
            if not bool(st.session_state.get("logado", False)):require login per session before rendering any UI
                # Bypass login for dev environment for testing
                if os.environ.get('APP_ENV') == 'dev':
                    st.session_state["logado"] = Truen for dev environment for testing
                else:iron.get('APP_ENV') == 'dev':
                    st.title("🔐 Login obrigatório")    st.session_state["logado"] = True
                    st.warning("Você precisa estar autenticado para acessar o dashboard.")
                    st.stop()
        except Exception:g("Você precisa estar autenticado para acessar o dashboard.")
            try:st.stop()
                if ui_logger:
                    ui_logger.exception("Erro ao verificar autenticação no render_bot_control")
            except Exception:                if ui_logger:
                passverificar autenticação no render_bot_control")
            st.error("Erro ao verificar autenticação. Acesso negado.")except Exception:
            st.stop()
autenticação. Acesso negado.")
        # --- NOVO LAYOUT DASHBOARD PRINCIPAL ---p()
        try:
            import dashboard
            dashboard.render_dashboard()
            return dashboard
        except Exception as e:render_dashboard()
            st.error(f"Erro ao renderizar dashboard: {e}")turn
            st.stop()        except Exception as e:
    if ui is None:
        _render_body()    st.stop()
        returne:

    # If ui is a container (supports context manager), render within it.
    try:
        with ui:iner (supports context manager), render within it.
            _render_body()    try:
    except TypeError:        with ui:
        # If ui isn't a context manager, just render in the current container.
        _render_body()
 manager, just render in the current container.
    _render_body()
def render_bot_window(bot_id: str, controller):
    """Renderiza janela flutuante com gauge e terminal de um bot específico"""
    theme = get_current_theme()
    
    # Header da janela
    st.markdown(f'''
    <div style="text-align: center; padding: 15px; background: {theme['header_bg']}; er da janela
                border: 2px solid {theme['border']}; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="color: {theme['accent']}; margin: 0;">🪟 Bot Monitor - {bot_id[:12]}</h2><div style="text-align: center; padding: 15px; background: {theme['header_bg']}; 
        <p style="color: {theme['text2']}; margin: 5px 0 0 0; font-size: 12px;">Janela Flutuante</p>2px solid {theme['border']}; border-radius: 8px; margin-bottom: 20px;">
    </div> margin: 0;">🪟 Bot Monitor - {bot_id[:12]}</h2>
    ''', unsafe_allow_html=True)le="color: {theme['text2']}; margin: 5px 0 0 0; font-size: 12px;">Janela Flutuante</p>
    
    # Botões de controlee_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader("📊 Monitor em Tempo Real"), col3 = st.columns([2, 1, 1])
    with col2:
        auto_refresh = st.checkbox("🔄 Auto", value=True, key="window_auto_refresh",📊 Monitor em Tempo Real")
                                   help="Atualiza automaticamente a cada 5s")    with col2:
    with col3:lue=True, key="window_auto_refresh",
        if st.button("🔃 Refresh", key="window_refresh", width='stretch'):
            st.rerun()
("🔃 Refresh", key="window_refresh", width='stretch'):
    # Auto-refresh para janela (não-bloqueante):
    # NÃO usar sleep+rerun aqui, pois isso impede o resto do layout de renderizar.
    # Em vez disso, agenda um reload do browser após 5s.# Auto-refresh para janela (não-bloqueante):
    if auto_refresh:sleep+rerun aqui, pois isso impede o resto do layout de renderizar.
                # The gauge uses internal polling; avoid full-page reload to reduce flicker.o browser após 5s.
                passif auto_refresh:
     internal polling; avoid full-page reload to reduce flicker.
    # Cache keypass
    cache_key = f"logs_cache_{bot_id}"
    key
    # Fragment para renderizaçãoid}"
    @st.fragment
    def render_bot_content():ão
        try:
            db = DatabaseManager()ntent():
            logs = db.get_bot_logs(bot_id, limit=30)try:
        except Exception as e:eManager()
            st.error(f"Erro ao conectar banco de dados: {e}")
            logs = []
            st.error(f"Erro ao conectar banco de dados: {e}")
        # Atualiza cache = []
        logs_hash = hashlib.md5(str(logs).encode()).hexdigest() if logs else ""
        st.session_state[cache_key] = logs_hash# Atualiza cache
        b.md5(str(logs).encode()).hexdigest() if logs else ""
        # Targeton_state[cache_key] = logs_hash
        target_pct = st.session_state.get("target_profit_pct", 2.0)
        
        # Renderizar gaugect = st.session_state.get("target_profit_pct", 2.0)
        if logs:
            # Best-effort: detect DRY flag from sessions table
            is_dry_db = False
            try:Y flag from sessions table
                conn2 = db.get_connection()= False
                cur2 = conn2.cursor()
                cur2.execute("SELECT dry_run FROM bot_sessions WHERE id = ? LIMIT 1", (str(bot_id),))t_connection()
                rr = cur2.fetchone()cursor()
                if rr:ECT dry_run FROM bot_sessions WHERE id = ? LIMIT 1", (str(bot_id),))
                    is_dry_db = int(rr[0] or 0) == 1
                conn2.close()        if rr:
            except Exception: = int(rr[0] or 0) == 1
                is_dry_db = False2.close()
            render_cobol_gauge_static(logs, bot_id, target_pct, is_dry_db)
                is_dry_db = False
        # Renderizar terminaler_cobol_gauge_static(logs, bot_id, target_pct, is_dry_db)
        st.divider()
        is_mario_theme = theme.get("name") == "Super Mario World"
        
        if logs:= "Super Mario World"
            log_html_items = []
            for log in reversed(logs):
                level = log.get('level', 'INFO')
                msg = log.get('message', '')
                el', 'INFO')
                txt = (level + " " + msg).upper()
                if any(w in txt for w in ['ERROR', 'ERRO', '❌', 'EXCEPTION']):
                    log_class = "smw-log-error" msg).upper()
                    mario_icon = "☠"
                elif any(w in txt for w in ['PROFIT', 'LUCRO', 'SUCCESS', '✅', 'TARGET', 'GANHO']):
                    log_class = "smw-log-success"
                    mario_icon = "★"):
                elif any(w in txt for w in ['WARNING', 'AVISO', '⚠', 'WARN']):s"
                    log_class = "smw-log-warning"
                    mario_icon = "?"
                elif any(w in txt for w in ['TRADE', 'ORDER', 'BUY', 'SELL', 'COMPRA', 'VENDA']):ng"
                    log_class = "smw-log-trade"
                    mario_icon = "◆"any(w in txt for w in ['TRADE', 'ORDER', 'BUY', 'SELL', 'COMPRA', 'VENDA']):
                elif any(w in txt for w in ['INFO', 'BOT', 'INICIADO', 'CONECTADO']):"
                    log_class = "smw-log-info"
                    mario_icon = "●"elif any(w in txt for w in ['INFO', 'BOT', 'INICIADO', 'CONECTADO']):
                else:log_class = "smw-log-info"
                    log_class = "smw-log-info"
                    mario_icon = "▸"
                = "smw-log-info"
                try:
                    import json as json_lib
                    data = json_lib.loads(msg)
                    parts = []
                    if data.get('event'): parts.append(data['event'].upper())
                    if data.get('price'): parts.append(f"${float(data['price']):,.2f}")
                    if data.get('cycle'): parts.append(f"Cycle:{data['cycle']}")data.get('event'): parts.append(data['event'].upper())
                    if data.get('executed'): parts.append(f"Exec:{data['executed']}")): parts.append(f"${float(data['price']):,.2f}")
                    if data.get('message'): parts.append(data['message'])    if data.get('cycle'): parts.append(f"Cycle:{data['cycle']}")
                except:pend(f"Exec:{data['executed']}")
                    parts = [msg]    if data.get('message'): parts.append(data['message'])
                = " | ".join(parts) if parts else msg
                safe_msg = html.escape(" | ".join(parts))
                
                if is_mario_theme:
                    log_html_items.append(f'''
                        <div class="smw-log-line {log_class}">
                            <span class="smw-log-icon">{mario_icon}</span>rio_theme:
                            <span class="smw-log-level">[{level}]</span>{safe_msg}og_html_items.append(f'''
                        </div>ne {log_class}">
                    ''')
                else:
                    log_html_items.append(f'''
                        <div style="padding: 6px 10px; margin: 3px 0; border-radius: 4px; 
                                    font-size: 13px; line-height: 1.5; background: #0a0a0a; 
                                    border-left: 3px solid #333; color: #cccccc;">html_items.append(f'''
                            <span style="font-weight: bold; margin-right: 8px;">[{level}]</span>{safe_msg}            <div style="padding: 6px 10px; margin: 3px 0; border-radius: 4px; 
                        </div>ine-height: 1.5; background: #0a0a0a; 
                    '''): 3px solid #333; color: #cccccc;">
                            <span style="font-weight: bold; margin-right: 8px;">[{level}]</span>{safe_msg}
            log_html_content = "".join(log_html_items)
            now_str = time.strftime("%H:%M:%S")
                 
            if is_mario_theme:html_items)
                terminal_html = f'''time("%H:%M:%S")
<style>
    /* === SMW CSS (versão compacta) === */
    @keyframes smw-coin-spin {{
        0% {{ transform: scaleX(1); }}>
        50% {{ transform: scaleX(0.3); }}
        100% {{ transform: scaleX(1); }}-coin-spin {{
    }}leX(1); }}
    .smw-message-box {{ font-family: 'Press Start 2P', 'Courier New', monospace; }}.3); }}
    .smw-border {{
        background: #000000;
        border: 4px solid #fbd000;ox {{ font-family: 'Press Start 2P', 'Courier New', monospace; }}
        box-shadow: 0 0 0 2px #000000, 0 0 0 4px #a85800, 6px 6px 0 rgba(0,0,0,0.5);
    }}0;
    .smw-header {{
        background: linear-gradient(180deg, #0068f8 0%, #003080 100%);0 0 2px #000000, 0 0 0 4px #a85800, 6px 6px 0 rgba(0,0,0,0.5);
        padding: 8px 12px;
        border-bottom: 3px solid #fbd000;mw-header {{
        display: flex;
        justify-content: space-between;12px;
    }}
    .smw-header-title {{ color: #f8f8f8; font-size: 9px; text-shadow: 2px 2px #000000; }}
    .smw-text-area {{pace-between;
        background: linear-gradient(180deg, #0000a8 0%, #000080 50%, #000060 100%);
        padding: 12px;mw-header-title {{ color: #f8f8f8; font-size: 9px; text-shadow: 2px 2px #000000; }}
        max-height: 400px;{
        overflow-y: auto;r-gradient(180deg, #0000a8 0%, #000080 50%, #000060 100%);
    }}
    .smw-log-line {{px;
        padding: 5px 8px;
        margin: 4px 0;
        font-size: 9px;
        line-height: 1.6;x;
        border-left: 3px solid transparent;
        background: rgba(0,0,0,0.3);  font-size: 9px;
        color: #f8f8f8;
        text-shadow: 1px 1px #000000;
    }}
    .smw-log-error {{ color: #f85858; border-left-color: #f85858; background: rgba(248,88,88,0.15); }}
    .smw-log-success {{ color: #58f858; border-left-color: #58f858; background: rgba(88,248,88,0.15); }}
    .smw-log-warning {{ color: #f8d830; border-left-color: #f8d830; background: rgba(248,216,48,0.15); }}
    .smw-log-trade {{ color: #58d8f8; border-left-color: #58d8f8; background: rgba(88,216,248,0.15); }}rgba(248,88,88,0.15); }}
    .smw-log-info {{ color: #f8f8f8; border-left-color: #a8a8a8; }}ss {{ color: #58f858; border-left-color: #58f858; background: rgba(88,248,88,0.15); }}
    .smw-log-icon {{ margin-right: 8px; font-size: 10px; }}
    .smw-log-level {{ color: #f8d830; font-weight: bold; margin-right: 6px; }}r: #58d8f8; border-left-color: #58d8f8; background: rgba(88,216,248,0.15); }}
    .smw-footer {{order-left-color: #a8a8a8; }}
        background: linear-gradient(180deg, #58d858 0%, #38a838 20%, #285828 40%, #804020 60%, #583010 100%);argin-right: 8px; font-size: 10px; }}
        padding: 6px 12px;ont-weight: bold; margin-right: 6px; }}
        border-top: 3px solid #fbd000;
        display: flex;ear-gradient(180deg, #58d858 0%, #38a838 20%, #285828 40%, #804020 60%, #583010 100%);
        justify-content: space-between;
        font-size: 8px;  border-top: 3px solid #f8d830;
        color: #f8f8f8;
        text-shadow: 1px 1px #000000;justify-content: space-between;
    }}        font-size: 8px;
    .smw-live-coin {{ color: #f8d830; animation: smw-coin-spin 1s infinite; }}
</style> #000000;

<div class="smw-message-box">; }}
    <div class="smw-border">
        <div class="smw-header">
            <span class="smw-header-title">▸ MESSAGE ▸ {bot_id[:8]}</span>
            <span style="font-size: 8px;">-border">
                <span class="smw-live-coin">●</span>lass="smw-header">
                <span style="color: #f8f8f8;">LIVE ★ {now_str}</span>GE ▸ {bot_id[:8]}</span>
            </span>size: 8px;">
        </div>  <span class="smw-live-coin">●</span>
        <div class="smw-text-area" id="logScroll">or: #f8f8f8;">LIVE ★ {now_str}</span>
            {log_html_content}
        </div>
        <div class="smw-footer">"logScroll">
            <span>★×{len(logs):03d}</span>og_html_content}
            <span style="color: #f8d830;">◀ WINDOW MODE ▶</span>div>
            <span>YOSHI'S HOUSE</span>  <div class="smw-footer">
        </div>    <span>★×{len(logs):03d}</span>
    </div>E ▶</span>
</div>
<script>/div>
    var logDiv = document.getElementById('logScroll'); </div>
    if (logDiv) logDiv.scrollTop = logDiv.scrollHeight;
</script>
''' logDiv = document.getElementById('logScroll');
            else:scrollTop = logDiv.scrollHeight;
                terminal_html = f'''
<style>
    @keyframes blink {{      else:
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.3; }}
    }}
    .live-indicator {{ animation: blink 1s infinite; color: #4ade80; font-weight: bold; }}
</style>
<div style="font-family: 'Courier New', monospace;">
    <div style="background: #0a0a0a; border: 2px solid {theme["border"]}; border-radius: 8px;  font-weight: bold; }}
                box-shadow: 0 0 20px {theme["glow"]}; overflow: hidden;">
        <div style="background: #111; padding: 10px 15px; border-bottom: 1px solid {theme["border"]}; pace;">
                    display: flex; justify-content: space-between;">kground: #0a0a0a; border: 2px solid {theme["border"]}; border-radius: 8px; 
            <span style="color: {theme["text"]}; font-size: 13px; font-weight: bold;">["glow"]}; overflow: hidden;">
                ◉ WINDOW MODE — {bot_id[:12]}border-bottom: 1px solid {theme["border"]}; 
            </span>een;">
            <span style="font-size: 11px;">tyle="color: {theme["text"]}; font-size: 13px; font-weight: bold;">
                <span class="live-indicator">● LIVE</span>  ◉ WINDOW MODE — {bot_id[:12]}
                <span style="color: #888;"> | {now_str}</span>
            </span>size: 11px;">
        </div>  <span class="live-indicator">● LIVE</span>
        <div style="max-height: 400px; overflow-y: auto; padding: 10px;" id="logScroll">
            {log_html_content}
        </div>
        <div style="background: #111; padding: 8px 15px; border-top: 1px solid #222; 0px;" id="logScroll">
                    font-size: 10px; color: #666; display: flex; justify-content: space-between;">og_html_content}
            <span>{len(logs)} logs</span>div>
            <span style="color: #4ade80;">🪟 Floating Window</span>  <div style="background: #111; padding: 8px 15px; border-top: 1px solid #222; 
        </div>            font-size: 10px; color: #666; display: flex; justify-content: space-between;">
    </div>
</div>indow</span>
<script>/div>
    var logDiv = document.getElementById('logScroll'); </div>
    if (logDiv) logDiv.scrollTop = logDiv.scrollHeight;
</script>
'''oll');
            render_html_smooth(terminal_html, height=500, key=f"window_logs_{bot_id}")logDiv) logDiv.scrollTop = logDiv.scrollHeight;
        else:
            st.info("Aguardando logs do bot...")
                render_html_smooth(terminal_html, height=500, key=f"window_logs_{bot_id}")
        # Eternal runs
        render_eternal_runs_history(bot_id)ardando logs do bot...")
            
    # Chamar fragment        # Eternal runs
    render_bot_content()

amar fragment
def render_eternal_runs_history(bot_id: str):
    """Renderiza histórico de ciclos do Eternal Mode"""
    try:
        db = DatabaseManager()story(bot_id: str):
        runs = db.get_eternal_runs(bot_id, limit=15)histórico de ciclos do Eternal Mode"""
        summary = db.get_eternal_runs_summary(bot_id)
    except Exception as e:    db = DatabaseManager()
        runs = []t=15)
        summary = {}_summary(bot_id)
    
    # Ocultar completamente se não há registros    runs = []
    has_runs = runs and len(runs) > 0
    has_summary = summary and summary.get('total_runs', 0) > 0
    # Ocultar completamente se não há registros
    if not has_runs and not has_summary:s) > 0
        return  # Nada a exibir - oculta a seção completamentehas_summary = summary and summary.get('total_runs', 0) > 0
    
    theme = get_current_theme()
        return  # Nada a exibir - oculta a seção completamente
    st.divider()
    st.subheader("🔄 Eternal Mode — Histórico de Ciclos")
    
    # Resumo geralivider()
    if summary and summary.get('total_runs', 0) > 0:🔄 Eternal Mode — Histórico de Ciclos")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:ummary and summary.get('total_runs', 0) > 0:
            total_runs = summary.get('total_runs', 0), col3, col4 = st.columns(4)
            st.metric("Total Ciclos", total_runs)
        
        with col2:
            total_profit = summary.get('total_profit_usdt', 0) or 0    st.metric("Total Ciclos", total_runs)
            color = "normal" if total_profit >= 0 else "inverse"
            st.metric("Lucro Total", f"${total_profit:.2f}", delta_color=color)
        t_usdt', 0) or 0
        with col3:    color = "normal" if total_profit >= 0 else "inverse"
            avg_pct = summary.get('avg_profit_pct', 0) or 0ric("Lucro Total", f"${total_profit:.2f}", delta_color=color)
            st.metric("Média %", f"{avg_pct:.2f}%")
        
        with col4:
            profitable = summary.get('profitable_runs', 0) or 0
            total = summary.get('completed_runs', 0) or 1    
            win_rate = (profitable / total * 100) if total > 0 else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")profitable = summary.get('profitable_runs', 0) or 0
    or 1
    # Tabela de ciclos (profitable / total * 100) if total > 0 else 0
    if runs:in Rate", f"{win_rate:.1f}%")
        # Construir HTML da tabela no estilo terminal
        rows_html = ""
        for run in runs:
            run_num = run.get('run_number', '?')
            status = run.get('status', 'running')
            profit_pct = run.get('profit_pct', 0) or 0
            profit_usdt = run.get('profit_usdt', 0) or 0
            targets_hit = run.get('targets_hit', 0)ng')
            total_targets = run.get('total_targets', 0)profit_pct = run.get('profit_pct', 0) or 0
            entry = run.get('entry_price', 0) or 0_usdt', 0) or 0
            exit_p = run.get('exit_price', 0)targets_hit', 0)
            al_targets', 0)
            # Cores baseadas no resultadoy_price', 0) or 0
            if status == 'running':ice', 0)
                status_color = "#fbbf24"
                status_icon = "⏳"o
                profit_color = "#888"':
            elif profit_pct > 0:
                status_color = "#4ade80"tatus_icon = "⏳"
                status_icon = "✅"
                profit_color = "#4ade80"
            else:
                status_color = "#ff6b6b"    status_icon = "✅"
                status_icon = "❌"
                profit_color = "#ff6b6b"else:
            = "#ff6b6b"
            exit_str = f"${exit_p:.2f}" if exit_p else "—"
            
            rows_html += f'''
            <tr style="border-bottom: 1px solid {theme["border"]}30;">
                <td style="padding: 8px; color: {theme["text"]}; font-weight: bold;">#{run_num}</td>
                <td style="padding: 8px; color: {status_color};">{status_icon} {status.upper()}</td>
                <td style="padding: 8px; color: {theme["text2"]};">${entry:.2f}</td>
                <td style="padding: 8px; color: {theme["text2"]};">{exit_str}</td>
                <td style="padding: 8px; color: {profit_color}; font-weight: bold;">{profit_pct:+.2f}%</td>td style="padding: 8px; color: {status_color};">{status_icon} {status.upper()}</td>
                <td style="padding: 8px; color: {profit_color}; font-weight: bold;">${profit_usdt:+.2f}</td> <td style="padding: 8px; color: {theme["text2"]};">${entry:.2f}</td>
                <td style="padding: 8px; color: {theme["text2"]};">{targets_hit}/{total_targets}</td>        <td style="padding: 8px; color: {theme["text2"]};">{exit_str}</td>
            </tr>="padding: 8px; color: {profit_color}; font-weight: bold;">{profit_pct:+.2f}%</td>
            '''rofit_usdt:+.2f}</td>
        it}/{total_targets}</td>
        table_html = f'''
        <div style="font-family: 'Courier New', monospace; background: {theme["bg2"]}; 
                    border: 2px solid {theme["border"]}; border-radius: 8px; 
                    box-shadow: 0 0 15px {theme["glow"]}; overflow: hidden; margin-top: 10px;">
            <div style="background: #111; padding: 10px 15px; border-bottom: 1px solid {theme["border"]};">t-family: 'Courier New', monospace; background: {theme["bg2"]}; 
                <span style="color: {theme["text"]}; font-size: 14px; font-weight: bold;">  border: 2px solid {theme["border"]}; border-radius: 8px; 
                    📊 ETERNAL RUNS LOGflow: hidden; margin-top: 10px;">
                </span>theme["border"]};">
            </div>="color: {theme["text"]}; font-size: 14px; font-weight: bold;">
            <div style="max-height: 300px; overflow-y: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead>
                        <tr style="background: #0a0a0a; border-bottom: 2px solid {theme["border"]};">
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">CICLO</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">STATUS</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">ENTRY</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">EXIT</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">PROFIT %</th>th style="padding: 10px; color: {theme["accent"]}; text-align: left;">STATUS</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">PROFIT $</th><th style="padding: 10px; color: {theme["accent"]}; text-align: left;">ENTRY</th>
                            <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">TARGETS</th> <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">EXIT</th>
                        </tr>le="padding: 10px; color: {theme["accent"]}; text-align: left;">PROFIT %</th>
                    </thead><th style="padding: 10px; color: {theme["accent"]}; text-align: left;">PROFIT $</th>
                    <tbody>    <th style="padding: 10px; color: {theme["accent"]}; text-align: left;">TARGETS</th>
                        {rows_html}      </tr>
                    </tbody>      </thead>
                </table>         <tbody>
            </div>                {rows_html}
        </div>
        '''                </table>
                    </div>
        render_html_smooth(table_html, height=350, key=f"eternal_table_{bot_id}")
 '''

def render_cobol_gauge_static(logs: list, bot_id: str, target_pct: float = 2.0, is_dry: bool = False): key=f"eternal_table_{bot_id}")
    """
    Renderiza gauge estilo terminal COBOL/mainframe inline (versão estática).
    Usa dados dos logs já carregados, sem polling.s: list, bot_id: str, target_pct: float = 2.0, is_dry: bool = False):
    """"""
    import json as json_libtilo terminal COBOL/mainframe inline (versão estática).
    from datetime import datetimegados, sem polling.
    
    # Obter tema atualimport json as json_lib
    theme = get_current_theme()
    is_mario_theme = theme.get("name") == "Super Mario World"
    
    def _is_dry_from_logs(logs_list: list) -> bool:
        try:
            for l in logs_list:
                # logs may include a dry_run field or mention 'dry' in message(logs_list: list) -> bool:
                if isinstance(l, dict) and (str(l.get('dry_run') or '').strip() in ('1','True','true','true') or 'dry' in str(l.get('message','')).lower()):
                    return True logs_list:
        except Exception:                # logs may include a dry_run field or mention 'dry' in message
            pass') or '').strip() in ('1','True','true','true') or 'dry' in str(l.get('message','')).lower()):
        return False
        except Exception:
    # Merge detection: honor explicit param or infer from logs
    is_dry = bool(is_dry) or _is_dry_from_logs(logs)

    # Try live price firstrge detection: honor explicit param or infer from logs
    price_source = "logs" bool(is_dry) or _is_dry_from_logs(logs)
    live_price = None
    try:t
        try:
            import api as kucoin_api
        except Exception:
            import api as kucoin_api  # type: ignore
        # default symbol if not present in logsrt api as kucoin_api
        sym = None
        if logs and isinstance(logs, list) and len(logs) > 0:ype: ignore
            try:ot present in logs
                maybe = json_lib.loads(logs[0].get('message','') or '{}')
                sym = maybe.get('symbol') isinstance(logs, list) and len(logs) > 0:
            except Exception:
                sym = None'message','') or '{}')
        if not sym:
            sym = 'BTC-USDT'
        live_price = kucoin_api.get_price_fast(sym) None
        if live_price and float(live_price) > 0:
            price_source = 'live'            sym = 'BTC-USDT'
    except Exception:api.get_price_fast(sym)
        live_price = Nonend float(live_price) > 0:
rce = 'live'
    # Extrair dados dos logs
    current_price = 0.0price = None
    entry_price = 0.0
    symbol = "BTC-USDT"dos dos logs
    cycle = 0
    executed = "0/0"0
    mode = "---"symbol = "BTC-USDT"
    last_event = "AGUARDANDO"
    profit_pct = 0.0 = "0/0"
    
    for log in logs: "AGUARDANDO"
        try:
            msg = log.get('message', '')
            try:
                data = json_lib.loads(msg)
                if 'price' in data and price_source != 'live':
                    current_price = float(data['price'])
                if 'entry_price' in data:
                    entry_price = float(data['entry_price'])and price_source != 'live':
                if 'symbol' in data:['price'])
                    symbol = data['symbol']ta:
                if 'cycle' in data:ntry_price'])
                    cycle = int(data['cycle'])a:
                if 'executed' in data:
                    executed = data['executed']
                if 'mode' in data:
                    last_event = data['mode'].upper()'executed' in data:
            except:executed = data['executed']
                pass if 'mode' in data:
        except:    mode = data['mode'].upper()
            pass            if 'event' in data:
      last_event = data['event'].upper().replace('_', ' ')
    # Calcular P&L
    if entry_price > 0 and current_price > 0:
        profit_pct = ((current_price - entry_price) / entry_price) * 100    except:
    
    # Calcular progresso do gauge (0-100%)
    progress = min(100, max(0, (profit_pct / target_pct) * 100)) if target_pct > 0 else 0# Calcular P&L
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")    profit_pct = ((current_price - entry_price) / entry_price) * 100
    
    # Renderizar tema Mario ou padrão, passando is_dry para watermarkso do gauge (0-100%)
    if is_mario_theme:t > 0 else 0
        render_mario_gauge(bot_id, symbol, mode, entry_price, current_price, 
                          profit_pct, target_pct, progress, cycle, executed, 
                          last_event, now, price_source, theme, is_dry)
    else:
        render_terminal_gauge(bot_id, symbol, mode, entry_price, current_price,
                             profit_pct, target_pct, progress, cycle, executed,e, 
                             last_event, now, price_source, theme, is_dry)                          profit_pct, target_pct, progress, cycle, executed, 
                          last_event, now, price_source, theme, is_dry)

def render_mario_gauge(bot_id, symbol, mode, entry_price, current_price, price,
                       profit_pct, target_pct, progress, cycle, executed,
                       last_event, now, price_source, theme, is_dry: bool = False):
    """Renderiza gauge no estilo Super Mario World - com sprites originais do SNES"""
    
    # Barra de progresso com blocos do Marioauge(bot_id, symbol, mode, entry_price, current_price, 
    bar_width = 20t, progress, cycle, executed,
    filled = int(bar_width * progress / 100)                   last_event, now, price_source, theme, is_dry: bool = False):
    o World - com sprites originais do SNES"""
    # Blocos de progresso (pixel art style)
    blocks_filled = "🟨" * filled   # Blocos coletados
    blocks_empty = "⬜" * (bar_width - filled)  # Blocos restantesbar_width = 20
    00)
    # Status baseado nos power-ups do SMW
    if profit_pct >= target_pct:o (pixel art style)
        status = "GOAL!"d   # Blocos coletados
        status_color = "#fbd000"(bar_width - filled)  # Blocos restantes
        mario_char = "🏆"
    elif profit_pct > 2:er-ups do SMW
        status = "POWER UP!"
        status_color = "#fbd000"
        mario_char = "🪶"#fbd000"
    elif profit_pct > 0:
        status = "SUPER!"
        status_color = "#43b047"P!"
        mario_char = "🍄"fbd000"
    elif profit_pct < -3:
        status = "GAME OVER"
        status_color = "#e52521"
        mario_char = "💀"#43b047"
    elif profit_pct < 0:
        status = "CAUTION!"
        status_color = "#ffaa00"ER"
        mario_char = "⚠️"tatus_color = "#e52521"
    else:
        status = "PLAYING"
        status_color = "#ffffff"!"
        mario_char = "🎮"    status_color = "#ffaa00"
    
    # Cor do rótulo indicando origem do preço
    price_label_color = "#43b047" if str(price_source).lower() == "live" else "#fbd000"        status = "PLAYING"

    # Sprites CSS Pixel Art do Super Mario World (16x16 pixels escalados)
    # Usando box-shadow para criar pixel art autêntico
    ndicando origem do preço
    gauge_html = f'''bel_color = "#43b047" if str(price_source).lower() == "live" else "#fbd000"
<div style="
    font-family: 'Press Start 2P', 'Courier New', monospace;xel Art do Super Mario World (16x16 pixels escalados)
    font-size: 10px;
    background: linear-gradient(180deg, #5c94fc 0%, #5c94fc 60%, #43b047 90%, #8b4513 100%);
    border: 4px solid #e52521;
    box-shadow: 0 0 0 4px #fbd000, 0 8px 20px rgba(0,0,0,0.5);
    padding: 0;ss Start 2P', 'Courier New', monospace;
    max-width: 540px;;
    color: #ffffff;gradient(180deg, #5c94fc 0%, #5c94fc 60%, #43b047 90%, #8b4513 100%);
    border-radius: 0px;id #e52521;
    margin: 10px 0;px #fbd000, 0 8px 20px rgba(0,0,0,0.5);
    position: relative;
    overflow: hidden;
    image-rendering: pixelated;  color: #ffffff;
">radius: 0px;
    <style>
        /* ========== SPRITES PIXEL ART SUPER MARIO WORLD - SNES AUTHENTIC ========== */
        /* Referência: sprites originais 16x16 do SNES (1990) */flow: hidden;
        
        /* Small Mario correndo - sprite autêntico SMW */
        .smw-mario {{
            width: 24px; height: 32px;ART SUPER MARIO WORLD - SNES AUTHENTIC ========== */
            background: transparent;originais 16x16 do SNES (1990) */
            position: absolute;
            image-rendering: pixelated;autêntico SMW */
            image-rendering: crisp-edges;
            animation: mario-run 6s linear infinite;  width: 24px; height: 32px;
        }}parent;
        .smw-mario::before {{solute;
            content: '';xelated;
            position: absolute;dges;
            width: 1px; height: 1px;linear infinite;
            background: transparent;
            box-shadow:
                /* === SMALL MARIO SMW (12x16 base) === */
                /* Chapéu vermelho - topo */
                3px 0 #d82800, 4px 0 #d82800, 5px 0 #d82800, 6px 0 #d82800, 7px 0 #d82800,
                2px 1px #d82800, 3px 1px #d82800, 4px 1px #d82800, 5px 1px #d82800, 6px 1px #d82800, 7px 1px #d82800, 8px 1px #d82800, 9px 1px #d82800,t;
                /* Cabelo/rosto */
                2px 2px #6b4423, 3px 2px #6b4423, 4px 2px #6b4423, 5px 2px #fccca8, 6px 2px #fccca8, 7px 2px #fccca8, 8px 2px #000000,
                1px 3px #6b4423, 2px 3px #fccca8, 3px 3px #6b4423, 4px 3px #fccca8, 5px 3px #fccca8, 6px 3px #fccca8, 7px 3px #fccca8, 8px 3px #000000, 9px 3px #000000,
                1px 4px #6b4423, 2px 4px #fccca8, 3px 4px #6b4423, 4px 4px #fccca8, 5px 4px #fccca8, 6px 4px #fccca8, 7px 4px #fccca8, 8px 4px #fccca8, 9px 4px #000000,
                1px 5px #6b4423, 2px 5px #6b4423, 3px 5px #fccca8, 4px 5px #fccca8, 5px 5px #fccca8, 6px 5px #fccca8, 7px 5px #000000, 8px 5px #000000, 9px 5px #000000, 7px 1px #d82800, 8px 1px #d82800, 9px 1px #d82800,
                3px 6px #fccca8, 4px 6px #fccca8, 5px 6px #fccca8, 6px 6px #fccca8, 7px 6px #fccca8,
                /* Corpo - camisa vermelha */ 8px 2px #000000,
                2px 7px #d82800, 3px 7px #d82800, 4px 7px #0068f8, 5px 7px #d82800, 6px 7px #d82800, 7px 7px #d82800, 9px 3px #000000,
                1px 8px #d82800, 2px 8px #d82800, 3px 8px #d82800, 4px 8px #0068f8, 5px 8px #d82800, 6px 8px #0068f8, 7px 8px #d82800, 8px 8px #d82800, 9px 4px #000000,
                1px 9px #d82800, 2px 9px #d82800, 3px 9px #d82800, 4px 9px #0068f8, 5px 9px #0068f8, 6px 9px #0068f8, 7px 9px #0068f8, 8px 9px #d82800,
                0px 10px #fccca8, 1px 10px #fccca8, 2px 10px #d82800, 3px 10px #0068f8, 4px 10px #fcb8a8, 5px 10px #0068f8, 6px 10px #fcb8a8, 7px 10px #0068f8, 8px 10px #fccca8, 9px 10px #fccca8,
                0px 11px #fccca8, 1px 11px #fccca8, 2px 11px #fccca8, 3px 11px #0068f8, 4px 11px #0068f8, 5px 11px #0068f8, 6px 11px #0068f8, 7px 11px #0068f8, 8px 11px #fccca8, 9px 11px #fccca8,
                0px 12px #fccca8, 1px 12px #fccca8, 2px 12px #0068f8, 3px 12px #0068f8, 4px 12px #0068f8, 5px 12px #0068f8, 6px 12px #0068f8, 7px 12px #0068f8, 8px 12px #fccca8, 9px 12px #fccca8,px 7px #d82800, 4px 7px #0068f8, 5px 7px #d82800, 6px 7px #d82800, 7px 7px #d82800,
                /* Macacão azul */px #d82800, 8px 8px #d82800,
                2px 13px #0068f8, 3px 13px #0068f8, 4px 13px #0068f8, 6px 13px #0068f8, 7px 13px #0068f8, 8px 13px #0068f8,px #0068f8, 8px 9px #d82800,
                1px 14px #6b4423, 2px 14px #6b4423, 3px 14px #6b4423, 7px 14px #6b4423, 8px 14px #6b4423, 9px 14px #6b4423,6px 10px #fcb8a8, 7px 10px #0068f8, 8px 10px #fccca8, 9px 10px #fccca8,
                0px 15px #6b4423, 1px 15px #6b4423, 2px 15px #6b4423, 8px 15px #6b4423, 9px 15px #6b4423, 10px 15px #6b4423;, 1px 11px #fccca8, 2px 11px #fccca8, 3px 11px #0068f8, 4px 11px #0068f8, 5px 11px #0068f8, 6px 11px #0068f8, 7px 11px #0068f8, 8px 11px #fccca8, 9px 11px #fccca8,
            transform: scale(2);      0px 12px #fccca8, 1px 12px #fccca8, 2px 12px #0068f8, 3px 12px #0068f8, 4px 12px #0068f8, 5px 12px #0068f8, 6px 12px #0068f8, 7px 12px #0068f8, 8px 12px #fccca8, 9px 12px #fccca8,
        }}        /* Macacão azul */
        f8, 4px 13px #0068f8, 6px 13px #0068f8, 7px 13px #0068f8, 8px 13px #0068f8,
        /* Yoshi verde - sprite autêntico SMW */4px #6b4423, 2px 14px #6b4423, 3px 14px #6b4423, 7px 14px #6b4423, 8px 14px #6b4423, 9px 14px #6b4423,
        .smw-yoshi {{15px #6b4423, 2px 15px #6b4423, 8px 15px #6b4423, 9px 15px #6b4423, 10px 15px #6b4423;
            width: 28px; height: 32px;;
            position: absolute;
            animation: yoshi-bounce 0.8s ease-in-out infinite;
        }}te autêntico SMW */
        .smw-yoshi::before {{
            content: '';: 32px;
            position: absolute;
            width: 1px; height: 1px;0.8s ease-in-out infinite;
            background: transparent;
            box-shadow:
                /* === YOSHI SMW (14x16 base) === */
                /* Cabeça verde - focinho grande */
                0px 2px #2c9f2c, 1px 2px #2c9f2c, 2px 2px #2c9f2c, 3px 2px #2c9f2c,
                0px 3px #2c9f2c, 1px 3px #58d858, 2px 3px #58d858, 3px 3px #2c9f2c, 4px 3px #2c9f2c,
                0px 4px #2c9f2c, 1px 4px #58d858, 2px 4px #58d858, 3px 4px #58d858, 4px 4px #2c9f2c, 5px 4px #2c9f2c, 6px 4px #2c9f2c,
                0px 5px #2c9f2c, 1px 5px #2c9f2c, 2px 5px #58d858, 3px 5px #2c9f2c, 4px 5px #ffffff, 5px 5px #ffffff, 6px 5px #2c9f2c, 7px 5px #2c9f2c,
                1px 6px #2c9f2c, 2px 6px #2c9f2c, 3px 6px #2c9f2c, 4px 6px #ffffff, 5px 6px #000000, 6px 6px #2c9f2c, 7px 6px #d82800, 8px 6px #d82800,inho grande */
                /* Crista vermelha */ 2px 2px #2c9f2c, 3px 2px #2c9f2c,
                7px 3px #d82800, 8px 3px #d82800, 3px 3px #2c9f2c, 4px 3px #2c9f2c,
                7px 4px #d82800, 8px 4px #d82800, 9px 4px #d82800, 2px 4px #58d858, 3px 4px #58d858, 4px 4px #2c9f2c, 5px 4px #2c9f2c, 6px 4px #2c9f2c,
                8px 5px #d82800, 9px 5px #d82800,9f2c, 1px 5px #2c9f2c, 2px 5px #58d858, 3px 5px #2c9f2c, 4px 5px #ffffff, 5px 5px #ffffff, 6px 5px #2c9f2c, 7px 5px #2c9f2c,
                /* Corpo */ 7px 6px #d82800, 8px 6px #d82800,
                2px 7px #2c9f2c, 3px 7px #2c9f2c, 4px 7px #2c9f2c, 5px 7px #2c9f2c, 6px 7px #2c9f2c, 7px 7px #d82800,
                3px 8px #2c9f2c, 4px 8px #58d858, 5px 8px #58d858, 6px 8px #2c9f2c,
                2px 9px #2c9f2c, 3px 9px #58d858, 4px 9px #ffffff, 5px 9px #ffffff, 6px 9px #58d858, 7px 9px #2c9f2c,
                2px 10px #2c9f2c, 3px 10px #58d858, 4px 10px #ffffff, 5px 10px #ffffff, 6px 10px #58d858, 7px 10px #2c9f2c,
                3px 11px #2c9f2c, 4px 11px #58d858, 5px 11px #58d858, 6px 11px #2c9f2c,
                /* Pés laranja */
                1px 12px #e86818, 2px 12px #e86818, 3px 12px #2c9f2c, 4px 12px #2c9f2c, 5px 12px #e86818, 6px 12px #e86818,
                0px 13px #e86818, 1px 13px #e86818, 2px 13px #e86818, 5px 13px #e86818, 6px 13px #e86818, 7px 13px #e86818, 3px 9px #58d858, 4px 9px #ffffff, 5px 9px #ffffff, 6px 9px #58d858, 7px 9px #2c9f2c,
                0px 14px #e86818, 1px 14px #e86818, 2px 14px #e86818, 6px 14px #e86818, 7px 14px #e86818, 8px 14px #e86818;      2px 10px #2c9f2c, 3px 10px #58d858, 4px 10px #ffffff, 5px 10px #ffffff, 6px 10px #58d858, 7px 10px #2c9f2c,
            transform: scale(2);        3px 11px #2c9f2c, 4px 11px #58d858, 5px 11px #58d858, 6px 11px #2c9f2c,
        }}
        2px #e86818, 2px 12px #e86818, 3px 12px #2c9f2c, 4px 12px #2c9f2c, 5px 12px #e86818, 6px 12px #e86818,
        /* Koopa Troopa verde - sprite autêntico SMW */13px #e86818, 2px 13px #e86818, 5px 13px #e86818, 6px 13px #e86818, 7px 13px #e86818;
        .smw-koopa {{;
            width: 20px; height: 28px;
            position: absolute;
            animation: koopa-walk 4s linear infinite; - sprite autêntico SMW */
        }}
        .smw-koopa::before {{: 28px;
            content: '';
            position: absolute; linear infinite;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === KOOPA TROOPA SMW === */
                /* Cabeça verde */
                3px 0px #2c9f2c, 4px 0px #2c9f2c, 5px 0px #2c9f2c,
                2px 1px #2c9f2c, 3px 1px #58d858, 4px 1px #58d858, 5px 1px #58d858, 6px 1px #58d858, 7px 1px #2c9f2c,
                /* Crista vermelha */ SMW === */
                7px 3px #d82800, 8px 3px #d82800,
                7px 4px #d82800, 8px 4px #d82800, 9px 4px #d82800,
                8px 5px #d82800, 9px 5px #d82800,
                /* Corpo */
                2px 7px #2c9f2c, 3px 7px #2c9f2c, 4px 7px #2c9f2c, 5px 7px #2c9f2c, 6px 7px #2c9f2c, 7px 7px #d82800,3px 3px #2c9f2c, 4px 3px #2c9f2c, 5px 3px #2c9f2c,
                3px 8px #2c9f2c, 4px 8px #58d858, 5px 8px #58d858, 6px 8px #2c9f2c,
                2px 9px #2c9f2c, 3px 9px #58d858, 4px 9px #ffffff, 5px 9px #ffffff, 6px 9px #58d858, 7px 9px #2c9f2c, 7px 4px #f8d830,
                2px 10px #2c9f2c, 3px 10px #58d858, 4px 10px #ffffff, 5px 10px #ffffff, 6px 10px #58d858, 7px 10px #2c9f2c, 1px 5px #f8f898, 2px 5px #58d858, 3px 5px #2c9f2c, 4px 5px #2c9f2c, 5px 5px #2c9f2c, 6px 5px #58d858, 7px 5px #f8d830, 8px 5px #f8d830,
                3px 11px #2c9f2c, 4px 11px #58d858, 5px 11px #58d858, 6px 11px #2c9f2c,      0px 6px #f8d830, 1px 6px #f8f898, 2px 6px #58d858, 3px 6px #58d858, 4px 6px #2c9f2c, 5px 6px #58d858, 6px 6px #58d858, 7px 6px #f8d830, 8px 6px #f8d830,
                /* Pés laranja */        1px 7px #f8d830, 2px 7px #f8d830, 3px 7px #2c9f2c, 4px 7px #2c9f2c, 5px 7px #2c9f2c, 6px 7px #f8d830, 7px 7px #f8d830,
                1px 12px #e86818, 2px 12px #e86818, 3px 12px #2c9f2c, 4px 12px #2c9f2c, 5px 12px #e86818, 6px 12px #e86818,
                0px 13px #e86818, 1px 13px #e86818, 2px 13px #e86818, 5px 13px #e86818, 6px 13px #e86818, 7px 13px #e86818,x #e86818, 2px 8px #e86818, 3px 8px #e86818, 5px 8px #e86818, 6px 8px #e86818, 7px 8px #e86818,
                0px 14px #e86818, 1px 14px #e86818, 2px 14px #e86818, 6px 14px #e86818, 7px 14px #e86818, 8px 14px #e86818;px #e86818, 2px 9px #e86818, 6px 9px #e86818, 7px 9px #e86818, 8px 9px #e86818;
            transform: scale(2);;
        }}
        
        /* Galoomba (Goomba do SMW) - sprite autêntico */ SMW) - sprite autêntico */
        .smw-goomba {{
            width: 20px; height: 20px;: 20px;
            position: absolute;
            animation: goomba-walk 5s linear infinite reverse;s linear infinite reverse;
        }}
        .smw-goomba::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === GALOOMBA SMW (redondo, não o goomba clássico) === */
                /* Cabeça verde */a05820, 4px 0px #a05820, 5px 0px #a05820,
                3px 0px #a05820, 4px 0px #a05820, 5px 0px #a05820, 6px 1px #a05820,
                2px 1px #a05820, 3px 1px #d89050, 4px 1px #d89050, 5px 1px #d89050, 6px 1px #a05820, 5px 2px #d89050, 6px 2px #ffffff, 7px 2px #000000,
                1px 2px #a05820, 2px 2px #d89050, 3px 2px #d89050, 4px 2px #d89050, 5px 2px #d89050, 6px 2px #a05820, 7px 2px #d82800, 8px 2px #d82800, 2px 3px #d89050, 3px 3px #d89050, 4px 3px #d89050, 5px 3px #d89050, 6px 3px #d89050, 7px 3px #a05820,
                1px 3px #a05820, 2px 3px #d89050, 3px 3px #d89050, 4px 3px #d89050, 5px 3px #d89050, 6px 3px #d89050, 7px 3px #a05820, 8px 3px #d82800, 9px 3px #d82800,      1px 4px #a05820, 2px 4px #a05820, 3px 4px #d89050, 4px 4px #d89050, 5px 4px #d89050, 6px 4px #a05820, 7px 4px #a05820,
                2px 4px #a05820, 3px 4px #d89050, 4px 4px #d89050, 5px 4px #d89050, 6px 4px #d89050, 7px 4px #a05820, 8px 4px #d82800, 9px 4px #d82800,        2px 5px #a05820, 3px 5px #a05820, 4px 5px #a05820, 5px 5px #a05820, 6px 5px #a05820,
                2px 5px #a05820, 3px 5px #d89050, 4px 5px #d89050, 5px 5px #d89050, 6px 5px #a05820, 7px 5px #d82800, 8px 5px #d82800, 9px 5px #d82800,
                2px 6px #a05820, 3px 6px #d89050, 4px 6px #d89050, 5px 6px #a05820, 6px 6px #d82800, 7px 6px #d82800, 8px 6px #d82800, 9px 6px #d82800,px #282828, 2px 6px #282828, 6px 6px #282828, 7px 6px #282828,
                3px 7px #d89050, 4px 7px #d89050, 5px 7px #a05820, 6px 7px #d82800, 7px 7px #d82800, 8px 7px #d82800,px #282828, 6px 7px #282828, 7px 7px #282828;
                3px 8px #d89050, 4px 8px #d89050, 5px 8px #a05820, 6px 8px #d82800, 7px 8px #d82800, 8px 8px #d82800,;
                4px 9px #d89050, 5px 9px #d89050, 6px 9px #a05820, 7px 9px #d82800, 8px 9px #d82800, 9px 9px #d82800;
            transform: scale(2);
        }}utêntico SMW */
        
        /* ? Block - sprite autêntico SMW */: 24px;
        .smw-block {{
            width: 24px; height: 24px;5s ease-in-out infinite;
            position: absolute;
            animation: block-bump 0.5s ease-in-out infinite;
        }}
        .smw-block::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === ? BLOCK SMW (16x16) === */
                /* Borda preta */
                1px 0px #000000, 2px 0px #000000, 3px 0px #000000, 4px 0px #000000, 5px 0px #000000, 6px 0px #000000, 7px 0px #000000, 8px 0px #000000, 9px 0px #000000, 10px 0px #000000, 11px 0px #000000, 12px 0px #000000, 13px 0px #000000, 14px 0px #000000, 15px 0px #000000,
                0px 1px #000000, 11px 1px #000000,
                /* Interior amarelo */
                1px 1px #f8d830, 2px 1px #f8d830, 3px 1px #f8d830, 4px 1px #f8d830, 5px 1px #f8d830, 6px 1px #f8d830, 7px 1px #f8d830, 8px 1px #f8d830, 9px 1px #f8d830, 10px 1px #f8d830,
                0px 2px #000000, 1px 2px #f8f898, 2px 2px #f8d830, 3px 2px #f8d830, 4px 2px #f8d830, 5px 2px #f8d830, 6px 2px #f8d830, 7px 2px #f8d830, 8px 2px #f8d830, 9px 2px #f8d830, 10px 2px #a85800, 11px 2px #000000,x 4px #f8d830, 3px 4px #000000, 4px 4px #f8d830, 5px 4px #f8d830, 6px 4px #000000, 7px 4px #f8d830, 8px 4px #000000, 9px 4px #f8d830, 10px 4px #a85800, 11px 4px #000000,
                0px 3px #000000, 1px 3px #f8f898, 2px 3px #f8d830, 3px 3px #f8d830, 4px 3px #000000, 5px 3px #000000, 6px 3px #f8d830, 7px 3px #000000, 8px 3px #f8d830, 9px 3px #f8d830, 10px 3px #a85800, 11px 3px #000000,a85800, 11px 5px #000000,
                0px 4px #000000, 1px 4px #f8f898, 2px 4px #f8d830, 3px 4px #000000, 4px 4px #f8d830, 5px 4px #f8d830, 6px 4px #000000, 7px 4px #f8d830, 8px 4px #000000, 9px 4px #f8d830, 10px 4px #a85800, 11px 4px #000000, 1px 6px #f8f898, 2px 6px #f8d830, 3px 6px #f8d830, 4px 6px #f8d830, 5px 6px #f8d830, 6px 6px #000000, 7px 6px #f8d830, 8px 6px #f8d830, 9px 6px #f8d830, 10px 6px #a85800, 11px 6px #000000,
                0px 5px #000000, 1px 5px #f8f898, 2px 5px #f8d830, 3px 5px #f8d830, 4px 5px #f8d830, 5px 5px #f8d830, 6px 5px #000000, 7px 5px #f8d830, 8px 5px #f8d830, 9px 5px #f8d830, 10px 5px #a85800, 11px 5px #000000,      0px 7px #000000, 1px 7px #f8f898, 2px 7px #f8d830, 3px 7px #f8d830, 4px 7px #f8d830, 5px 7px #f8d830, 6px 7px #000000, 7px 7px #000000, 8px 7px #f8d830, 9px 7px #f8d830, 10px 7px #a85800, 11px 7px #000000,
                0px 6px #000000, 1px 6px #f8f898, 2px 6px #f8d830, 3px 6px #f8d830, 4px 6px #f8d830, 5px 6px #f8d830, 6px 6px #000000, 7px 6px #f8d830, 8px 6px #f8d830, 9px 6px #f8d830, 10px 6px #a85800, 11px 6px #000000,        0px 8px #000000, 1px 8px #f8f898, 2px 8px #f8d830, 3px 8px #f8d830, 4px 8px #f8d830, 5px 8px #f8d830, 6px 8px #f8d830, 7px 8px #f8d830, 8px 8px #f8d830, 9px 8px #f8d830, 10px 8px #a85800, 11px 8px #000000,
                0px 7px #000000, 1px 7px #f8f898, 2px 7px #f8d830, 3px 7px #f8d830, 4px 7px #f8d830, 5px 7px #f8d830, 6px 7px #000000, 7px 7px #000000, 8px 7px #f8d830, 9px 7px #f8d830, 10px 7px #a85800, 11px 7px #000000,px 9px #a85800, 3px 9px #a85800, 4px 9px #a85800, 5px 9px #a85800, 6px 9px #a85800, 7px 9px #a85800, 8px 9px #a85800, 9px 9px #a85800, 10px 9px #a85800, 11px 9px #000000,
                0px 8px #000000, 1px 8px #f8f898, 2px 8px #f8d830, 3px 8px #f8d830, 4px 8px #f8d830, 5px 8px #f8d830, 6px 8px #f8d830, 7px 8px #f8d830, 8px 8px #f8d830, 9px 8px #f8d830, 10px 8px #a85800, 11px 8px #000000, #000000, 11px 10px #000000,
                0px 9px #000000, 1px 9px #f8d830, 2px 9px #a85800, 3px 9px #a85800, 4px 9px #a85800, 5px 9px #a85800, 6px 9px #a85800, 7px 9px #a85800, 8px 9px #a85800, 9px 9px #a85800, 10px 9px #a85800, 11px 9px #000000,10px #000000, 3px 10px #000000, 4px 10px #000000, 5px 10px #000000, 6px 10px #000000, 7px 10px #000000, 8px 10px #000000, 9px 10px #000000, 10px 10px #000000;
                0px 10px #000000, 11px 10px #000000,;
                1px 10px #000000, 2px 10px #000000, 3px 10px #000000, 4px 10px #000000, 5px 10px #000000, 6px 10px #000000, 7px 10px #000000, 8px 10px #000000, 9px 10px #000000, 10px 10px #000000;
            transform: scale(2);
        }}m - sprite autêntico SMW */
        
        /* Super Mushroom - sprite autêntico SMW */x;
        .smw-mushroom {{
            width: 20px; height: 24px;
            position: absolute;
        }}
        .smw-mushroom::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow: com manchas brancas */
                /* === SUPER MUSHROOM SMW === */
                /* Topo vermelho com manchas brancas */ 7px 1px #d82800, 8px 1px #d82800,
                3px 0px #d82800, 4px 0px #d82800, 5px 0px #d82800, 6px 0px #d82800, 7px 0px #d82800, 6px 2px #ffffff, 7px 2px #ffffff, 8px 2px #d82800, 9px 2px #d82800,
                2px 1px #d82800, 3px 1px #ffffff, 4px 1px #d82800, 5px 1px #d82800, 6px 1px #ffffff, 7px 1px #d82800, 8px 1px #d82800, 4px 3px #d82800, 5px 3px #d82800, 6px 3px #d82800, 7px 3px #d82800, 8px 3px #d82800, 9px 3px #d82800,
                1px 2px #d82800, 2px 2px #ffffff, 3px 2px #ffffff, 4px 2px #d82800, 5px 2px #d82800, 6px 2px #ffffff, 7px 2px #ffffff, 8px 2px #d82800, 9px 2px #d82800, 3px 4px #d82800, 4px 4px #d82800, 5px 4px #d82800, 6px 4px #d82800, 7px 4px #d82800, 8px 4px #d82800,
                1px 3px #d82800, 2px 3px #d82800, 3px 3px #d82800, 4px 3px #d82800, 5px 3px #d82800, 6px 3px #d82800, 7px 3px #d82800, 8px 3px #d82800, 9px 3px #d82800,      /* Caule bege */
                2px 4px #d82800, 3px 4px #d82800, 4px 4px #d82800, 5px 4px #d82800, 6px 4px #d82800, 7px 4px #d82800, 8px 4px #d82800,        3px 5px #fccca8, 4px 5px #fccca8, 5px 5px #fccca8, 6px 5px #fccca8, 7px 5px #fccca8,
                /* Caule bege */f, 5px 6px #fccca8, 6px 6px #ffffff, 7px 6px #fccca8,
                3px 5px #fccca8, 4px 5px #fccca8, 5px 5px #fccca8, 6px 5px #fccca8, 7px 5px #fccca8,7px #fccca8, 4px 7px #fccca8, 5px 7px #000000, 6px 7px #fccca8, 7px 7px #fccca8,
                3px 6px #fccca8, 4px 6px #ffffff, 5px 6px #fccca8, 6px 6px #ffffff, 7px 6px #fccca8,px #fccca8, 6px 8px #fccca8;
                3px 7px #fccca8, 4px 7px #fccca8, 5px 7px #000000, 6px 7px #fccca8, 7px 7px #fccca8,;
                4px 8px #fccca8, 5px 8px #fccca8, 6px 8px #fccca8;
            transform: scale(2);
        }}te autêntico SMW */
        
        /* Super Star - sprite autêntico SMW */: 24px;
        .smw-star {{
            width: 20px; height: 24px;s linear infinite;
            position: absolute;
            animation: star-spin 1.5s linear infinite;
        }}
        .smw-star::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === SUPER STAR SMW === */
                4px 0px #f8d830, 5px 0px #f8d830, 6px 2px #000000, 7px 2px #f8d830,
                3px 1px #f8d830, 4px 1px #f8f898, 5px 1px #f8f898, 6px 1px #f8d830, 2px 3px #f8d830, 3px 3px #f8d830, 4px 3px #f8d830, 5px 3px #f8d830, 6px 3px #f8d830, 7px 3px #f8d830, 8px 3px #f8d830,
                2px 2px #f8d830, 3px 2px #f8f898, 4px 2px #000000, 5px 2px #f8f898, 6px 2px #000000, 7px 2px #f8d830,      0px 4px #f8d830, 1px 4px #f8d830, 2px 4px #f8d830, 3px 4px #f8d830, 4px 4px #f8d830, 5px 4px #f8d830, 6px 4px #f8d830, 7px 4px #f8d830, 8px 4px #f8d830, 9px 4px #f8d830,
                1px 3px #f8d830, 2px 3px #f8d830, 3px 3px #f8d830, 4px 3px #f8d830, 5px 3px #f8d830, 6px 3px #f8d830, 7px 3px #f8d830, 8px 3px #f8d830,        1px 5px #f8d830, 2px 5px #f8d830, 3px 5px #f8d830, 4px 5px #f8d830, 5px 5px #f8d830, 6px 5px #f8d830, 7px 5px #f8d830, 8px 5px #f8d830,
                0px 4px #f8d830, 1px 4px #f8d830, 2px 4px #f8d830, 3px 4px #f8d830, 4px 4px #f8d830, 5px 4px #f8d830, 6px 4px #f8d830, 7px 4px #f8d830, 8px 4px #f8d830, 9px 4px #f8d830,#f8d830, 4px 6px #f8d830, 5px 6px #f8d830, 6px 6px #f8d830, 7px 6px #f8d830,
                1px 5px #f8d830, 2px 5px #f8d830, 3px 5px #f8d830, 4px 5px #f8d830, 5px 5px #f8d830, 6px 5px #f8d830, 7px 5px #f8d830, 8px 5px #f8d830,7px #f8d830, 3px 7px #f8d830, 6px 7px #f8d830, 7px 7px #f8d830,
                2px 6px #f8d830, 3px 6px #f8d830, 4px 6px #f8d830, 5px 6px #f8d830, 6px 6px #f8d830, 7px 6px #f8d830,px #f8d830, 7px 8px #f8d830, 8px 8px #f8d830;
                2px 7px #f8d830, 3px 7px #f8d830, 6px 7px #f8d830, 7px 7px #f8d830,;
                1px 8px #f8d830, 2px 8px #f8d830, 7px 8px #f8d830, 8px 8px #f8d830;
            transform: scale(2);
        }}êntico SMW */
        
        /* Coin - sprite autêntico SMW */: 20px;
        .smw-coin {{
            width: 12px; height: 20px;infinite;
            position: absolute;
            animation: coin-spin 1s infinite;
        }}
        .smw-coin::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === COIN SMW === */
                2px 0px #f8d830, 3px 0px #f8d830, 1px 2px #f8f898, 2px 2px #f8f898, 3px 2px #f8d830, 4px 2px #f8d830, 5px 2px #a85800,
                1px 1px #f8d830, 2px 1px #f8f898, 3px 1px #f8f898, 4px 1px #f8d830,      0px 3px #f8d830, 1px 3px #f8f898, 2px 3px #f8d830, 3px 3px #f8d830, 4px 3px #a85800, 5px 3px #a85800,
                0px 2px #f8d830, 1px 2px #f8f898, 2px 2px #f8f898, 3px 2px #f8d830, 4px 2px #f8d830, 5px 2px #a85800,        0px 4px #f8d830, 1px 4px #f8f898, 2px 4px #f8d830, 3px 4px #f8d830, 4px 4px #a85800, 5px 4px #a85800,
                0px 3px #f8d830, 1px 3px #f8f898, 2px 3px #f8d830, 3px 3px #f8d830, 4px 3px #a85800, 5px 3px #a85800,98, 2px 5px #f8d830, 3px 5px #f8d830, 4px 5px #a85800, 5px 5px #a85800,
                0px 4px #f8d830, 1px 4px #f8f898, 2px 4px #f8d830, 3px 4px #f8d830, 4px 4px #a85800, 5px 4px #a85800,6px #f8d830, 1px 6px #f8d830, 2px 6px #f8d830, 3px 6px #a85800, 4px 6px #a85800, 5px 6px #a85800,
                0px 5px #f8d830, 1px 5px #f8f898, 2px 5px #f8d830, 3px 5px #f8d830, 4px 5px #a85800, 5px 5px #a85800,px #a85800, 3px 7px #a85800, 4px 7px #a85800;
                0px 6px #f8d830, 1px 6px #f8d830, 2px 6px #f8d830, 3px 6px #a85800, 4px 6px #a85800, 5px 6px #a85800,;
                1px 7px #f8d830, 2px 7px #a85800, 3px 7px #a85800, 4px 7px #a85800;
            transform: scale(2);
        }}prite autêntico SMW */
        
        /* Warp Pipe - sprite autêntico SMW */x;
        .smw-pipe {{
            width: 40px; height: 40px;
            position: absolute;
        }}
        .smw-pipe::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:14px 0px #003800, 15px 0px #003800,
                /* === WARP PIPE SMW (borda do topo) === */14px 1px #003800, 15px 1px #003800,
                0px 0px #003800, 1px 0px #003800, 2px 0px #003800, 3px 0px #003800, 4px 0px #003800, 5px 0px #003800, 6px 0px #003800, 7px 0px #003800, 8px 0px #003800, 9px 0px #003800, 10px 0px #003800, 11px 0px #003800, 12px 0px #003800, 13px 0px #003800, 14px 0px #003800, 15px 0px #003800,14px 2px #003800, 15px 2px #003800,
                0px 1px #003800, 1px 1px #003800, 2px 1px #003800, 3px 1px #003800, 4px 1px #003800, 5px 1px #003800, 6px 1px #003800, 7px 1px #003800, 8px 1px #003800, 9px 1px #003800, 10px 1px #003800, 11px 1px #003800, 12px 1px #003800, 13px 1px #003800, 14px 1px #003800, 15px 1px #003800,14px 3px #003800, 15px 3px #003800,
                0px 2px #003800, 1px 2px #003800, 2px 2px #003800, 3px 2px #003800, 4px 2px #003800, 5px 2px #003800, 6px 2px #003800, 7px 2px #003800, 8px 2px #003800, 9px 2px #003800, 10px 2px #003800, 11px 2px #003800, 12px 2px #003800, 13px 2px #003800, 14px 2px #003800, 15px 2px #003800, */
                0px 3px #003800, 1px 3px #003800, 2px 3px #003800, 3px 3px #003800, 4px 3px #003800, 5px 3px #003800, 6px 3px #003800, 7px 3px #003800, 8px 3px #003800, 9px 3px #003800, 10px 3px #003800, 11px 3px #003800, 12px 3px #003800, 13px 3px #003800, 14px 3px #003800, 15px 3px #003800,      1px 4px #003800, 2px 4px #58d858, 3px 4px #58d858, 4px 4px #2c9f2c, 5px 4px #2c9f2c, 6px 4px #2c9f2c, 7px 4px #2c9f2c, 8px 4px #2c9f2c, 9px 4px #2c9f2c, 10px 4px #2c9f2c, 11px 4px #2c9f2c, 12px 4px #003800, 13px 4px #003800, 14px 4px #003800,
                /* Corpo do cano */        1px 5px #003800, 2px 5px #58d858, 3px 5px #58d858, 4px 5px #2c9f2c, 5px 5px #2c9f2c, 6px 5px #2c9f2c, 7px 5px #2c9f2c, 8px 5px #2c9f2c, 9px 5px #2c9f2c, 10px 5px #2c9f2c, 11px 5px #2c9f2c, 12px 5px #003800, 13px 5px #003800, 14px 5px #003800,
                1px 4px #003800, 2px 4px #58d858, 3px 4px #58d858, 4px 4px #2c9f2c, 5px 4px #2c9f2c, 6px 4px #2c9f2c, 7px 4px #2c9f2c, 8px 4px #2c9f2c, 9px 4px #2c9f2c, 10px 4px #2c9f2c, 11px 4px #2c9f2c, 12px 4px #003800, 13px 4px #003800, 14px 4px #003800,3px 6px #58d858, 4px 6px #2c9f2c, 5px 6px #2c9f2c, 6px 6px #2c9f2c, 7px 6px #2c9f2c, 8px 6px #2c9f2c, 9px 6px #2c9f2c, 10px 6px #2c9f2c, 11px 6px #2c9f2c, 12px 6px #003800, 13px 6px #003800, 14px 6px #003800,
                1px 5px #003800, 2px 5px #58d858, 3px 5px #58d858, 4px 5px #2c9f2c, 5px 5px #2c9f2c, 6px 5px #2c9f2c, 7px 5px #2c9f2c, 8px 5px #2c9f2c, 9px 5px #2c9f2c, 10px 5px #2c9f2c, 11px 5px #2c9f2c, 12px 5px #003800, 13px 5px #003800, 14px 5px #003800,px #003800, 2px 7px #58d858, 3px 7px #58d858, 4px 7px #2c9f2c, 5px 7px #2c9f2c, 6px 7px #2c9f2c, 7px 7px #2c9f2c, 8px 7px #2c9f2c, 9px 7px #2c9f2c, 10px 7px #2c9f2c, 11px 7px #2c9f2c, 12px 7px #003800, 13px 7px #003800, 14px 7px #003800,
                1px 6px #003800, 2px 6px #58d858, 3px 6px #58d858, 4px 6px #2c9f2c, 5px 6px #2c9f2c, 6px 6px #2c9f2c, 7px 6px #2c9f2c, 8px 6px #2c9f2c, 9px 6px #2c9f2c, 10px 6px #2c9f2c, 11px 6px #2c9f2c, 12px 6px #003800, 13px 6px #003800, 14px 6px #003800,px #003800, 3px 8px #003800, 4px 8px #003800, 5px 8px #003800, 6px 8px #003800, 7px 8px #003800, 8px 8px #003800, 9px 8px #003800, 10px 8px #003800, 11px 8px #003800, 12px 8px #003800, 13px 8px #003800, 14px 8px #003800;
                1px 7px #003800, 2px 7px #58d858, 3px 7px #58d858, 4px 7px #2c9f2c, 5px 7px #2c9f2c, 6px 7px #2c9f2c, 7px 7px #2c9f2c, 8px 7px #2c9f2c, 9px 7px #2c9f2c, 10px 7px #2c9f2c, 11px 7px #2c9f2c, 12px 7px #003800, 13px 7px #003800, 14px 7px #003800,;
                1px 8px #003800, 2px 8px #003800, 3px 8px #003800, 4px 8px #003800, 5px 8px #003800, 6px 8px #003800, 7px 8px #003800, 8px 8px #003800, 9px 8px #003800, 10px 8px #003800, 11px 8px #003800, 12px 8px #003800, 13px 8px #003800, 14px 8px #003800;
            transform: scale(2);
        }}- sprite autêntico */
        
        /* Cloud (nuvem SMW) - sprite autêntico */: 24px;
        .smw-cloud {{
            width: 40px; height: 24px;s ease-in-out infinite;
            position: absolute;
            animation: cloud-float 6s ease-in-out infinite;
        }}
        .smw-cloud::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow: 5px 0px #f8f8f8, 6px 0px #f8f8f8, 7px 0px #f8f8f8,
                /* === NUVEM SMW === */      2px 1px #f8f8f8, 3px 1px #f8f8f8, 4px 1px #f8f8f8, 5px 1px #f8f8f8, 6px 1px #f8f8f8, 7px 1px #f8f8f8, 8px 1px #f8f8f8, 9px 1px #f8f8f8, 10px 1px #f8f8f8, 11px 1px #f8f8f8,
                4px 0px #f8f8f8, 5px 0px #f8f8f8, 6px 0px #f8f8f8, 7px 0px #f8f8f8,        1px 2px #f8f8f8, 2px 2px #f8f8f8, 3px 2px #f8f8f8, 4px 2px #f8f8f8, 5px 2px #f8f8f8, 6px 2px #f8f8f8, 7px 2px #f8f8f8, 8px 2px #f8f8f8, 9px 2px #f8f8f8, 10px 2px #f8f8f8, 11px 2px #f8f8f8, 12px 2px #f8f8f8, 13px 2px #f8f8f8,
                2px 1px #f8f8f8, 3px 1px #f8f8f8, 4px 1px #f8f8f8, 5px 1px #f8f8f8, 6px 1px #f8f8f8, 7px 1px #f8f8f8, 8px 1px #f8f8f8, 9px 1px #f8f8f8, 10px 1px #f8f8f8, 11px 1px #f8f8f8,x 3px #f8f8f8, 4px 3px #f8f8f8, 5px 3px #f8f8f8, 6px 3px #f8f8f8, 7px 3px #f8f8f8, 8px 3px #f8f8f8, 9px 3px #f8f8f8, 10px 3px #f8f8f8, 11px 3px #f8f8f8, 12px 3px #f8f8f8, 13px 3px #f8f8f8, 14px 3px #f8f8f8,
                1px 2px #f8f8f8, 2px 2px #f8f8f8, 3px 2px #f8f8f8, 4px 2px #f8f8f8, 5px 2px #f8f8f8, 6px 2px #f8f8f8, 7px 2px #f8f8f8, 8px 2px #f8f8f8, 9px 2px #f8f8f8, 10px 2px #f8f8f8, 11px 2px #f8f8f8, 12px 2px #f8f8f8, 13px 2px #f8f8f8, #d8d8d8, 1px 4px #f8f8f8, 2px 4px #f8f8f8, 3px 4px #f8f8f8, 4px 4px #f8f8f8, 5px 4px #f8f8f8, 6px 4px #f8f8f8, 7px 4px #f8f8f8, 8px 4px #f8f8f8, 9px 4px #f8f8f8, 10px 4px #f8f8f8, 11px 4px #f8f8f8, 12px 4px #f8f8f8, 13px 4px #f8f8f8, 14px 4px #d8d8d8,
                0px 3px #f8f8f8, 1px 3px #f8f8f8, 2px 3px #f8f8f8, 3px 3px #f8f8f8, 4px 3px #f8f8f8, 5px 3px #f8f8f8, 6px 3px #f8f8f8, 7px 3px #f8f8f8, 8px 3px #f8f8f8, 9px 3px #f8f8f8, 10px 3px #f8f8f8, 11px 3px #f8f8f8, 12px 3px #f8f8f8, 13px 3px #f8f8f8, 14px 3px #f8f8f8,px #d8d8d8, 3px 5px #f8f8f8, 4px 5px #f8f8f8, 5px 5px #f8f8f8, 6px 5px #f8f8f8, 7px 5px #f8f8f8, 8px 5px #f8f8f8, 9px 5px #f8f8f8, 10px 5px #f8f8f8, 11px 5px #f8f8f8, 12px 5px #d8d8d8, 13px 5px #d8d8d8;
                0px 4px #d8d8d8, 1px 4px #f8f8f8, 2px 4px #f8f8f8, 3px 4px #f8f8f8, 4px 4px #f8f8f8, 5px 4px #f8f8f8, 6px 4px #f8f8f8, 7px 4px #f8f8f8, 8px 4px #f8f8f8, 9px 4px #f8f8f8, 10px 4px #f8f8f8, 11px 4px #f8f8f8, 12px 4px #f8f8f8, 13px 4px #f8f8f8, 14px 4px #d8d8d8,;
                1px 5px #d8d8d8, 2px 5px #d8d8d8, 3px 5px #f8f8f8, 4px 5px #f8f8f8, 5px 5px #f8f8f8, 6px 5px #f8f8f8, 7px 5px #f8f8f8, 8px 5px #f8f8f8, 9px 5px #f8f8f8, 10px 5px #d8d8d8, 11px 5px #d8d8d8;
            transform: scale(2);
        }}a carnívora) - sprite autêntico SMW */
        
        /* Piranha Plant saindo do Pipe */: 36px;
        .smw-piranha {{
            width: 24px; height: 36px;2.5s ease-in-out infinite;
            position: absolute;
            animation: piranha-peek 2.5s ease-in-out infinite;
        }}
        .smw-piranha::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:
                /* === PIRANHA PLANT SMW === */
                /* Dentes superiores */,
                1px 0px #f8f8f8, 5px 0px #f8f8f8, 9px 0px #f8f8f8,/
                0px 1px #38a818, 1px 1px #f8f8f8, 2px 1px #38a818, 4px 1px #38a818, 5px 1px #f8f8f8, 6px 1px #38a818, 8px 1px #38a818, 9px 1px #f8f8f8, 10px 1px #38a818, 7px 2px #d82800, 8px 2px #d82800, 9px 2px #d82800, 10px 2px #d82800,
                /* Boca aberta vermelha */ 7px 3px #800000, 8px 3px #800000, 9px 3px #800000, 10px 3px #d82800,
                0px 2px #d82800, 1px 2px #d82800, 2px 2px #d82800, 3px 2px #d82800, 4px 2px #d82800, 5px 2px #d82800, 6px 2px #d82800, 7px 2px #d82800, 8px 2px #d82800, 9px 2px #d82800, 10px 2px #d82800,res */
                0px 3px #d82800, 1px 3px #800000, 2px 3px #800000, 3px 3px #800000, 4px 3px #800000, 5px 3px #800000, 6px 3px #800000, 7px 3px #800000, 8px 3px #800000, 9px 3px #800000, 10px 3px #d82800, 4px 4px #d82800, 5px 4px #f8f8f8, 6px 4px #d82800, 8px 4px #d82800, 9px 4px #f8f8f8, 10px 4px #d82800,
                /* Dentes inferiores */ 4px 5px #38a818, 5px 5px #38a818, 6px 5px #38a818, 7px 5px #38a818, 8px 5px #38a818, 9px 5px #38a818,
                0px 4px #d82800, 1px 4px #f8f8f8, 2px 4px #d82800, 4px 4px #d82800, 5px 4px #f8f8f8, 6px 4px #d82800, 8px 4px #d82800, 9px 4px #f8f8f8, 10px 4px #d82800,
                1px 5px #38a818, 2px 5px #38a818, 3px 5px #38a818, 4px 5px #38a818, 5px 5px #38a818, 6px 5px #38a818, 7px 5px #38a818, 8px 5px #38a818, 9px 5px #38a818,x 6px #d82800, 6px 6px #f8f8f8, 7px 6px #d82800, 8px 6px #d82800,
                /* Cabeça com bolinhas */ 3px 7px #d82800, 4px 7px #d82800, 5px 7px #d82800, 6px 7px #d82800, 7px 7px #d82800, 8px 7px #d82800,
                2px 6px #d82800, 3px 6px #f8f8f8, 4px 6px #d82800, 5px 6px #d82800, 6px 6px #f8f8f8, 7px 6px #d82800, 8px 6px #d82800,      /* Caule verde */
                2px 7px #d82800, 3px 7px #d82800, 4px 7px #d82800, 5px 7px #d82800, 6px 7px #d82800, 7px 7px #d82800, 8px 7px #d82800,        4px 8px #38a818, 5px 8px #58d858, 6px 8px #38a818,
                /* Caule verde */
                4px 8px #38a818, 5px 8px #58d858, 6px 8px #38a818,px #38a818, 5px 10px #58d858, 6px 10px #38a818,
                4px 9px #38a818, 5px 9px #38a818, 6px 9px #38a818,11px #38a818, 6px 11px #38a818;
                4px 10px #38a818, 5px 10px #58d858, 6px 10px #38a818,;
                4px 11px #38a818, 5px 11px #38a818, 6px 11px #38a818;
            transform: scale(2);
        }}il gigante) - sprite autêntico SMW */
        
        /* Cloud (nuvem SMW) - sprite autêntico */: 32px;
        .smw-cloud {{
            width: 40px; height: 24px; linear infinite;
            position: absolute;
            animation: cloud-float 6s ease-in-out infinite;
        }}
        .smw-cloud::before {{
            content: '';
            position: absolute;
            width: 1px; height: 1px;
            background: transparent;
            box-shadow:/
                /* === NUVEM SMW === */
                4px 0px #f8f8f8, 5px 0px #f8f8f8, 6px 0px #f8f8f8, 7px 0px #f8f8f8,
                2px 1px #f8f8f8, 3px 1px #f8f8f8, 4px 1px #f8f8f8, 5px 1px #f8f8f8, 6px 1px #f8f8f8, 7px 1px #f8f8f8, 8px 1px #f8f8f8, 9px 1px #f8f8f8, 10px 1px #f8f8f8, 11px 1px #f8f8f8,/
                1px 2px #f8f8f8, 2px 2px #f8f8f8, 3px 2px #f8f8f8, 4px 2px #f8f8f8, 5px 2px #f8f8f8, 6px 2px #f8f8f8, 7px 2px #f8f8f8, 8px 2px #f8f8f8, 9px 2px #f8f8f8, 10px 2px #f8f8f8, 11px 2px #f8f8f8, 12px 2px #f8f8f8, 13px 2px #f8f8f8,
                0px 3px #f8f8f8, 1px 3px #f8f8f8, 2px 3px #f8f8f8, 3px 3px #f8f8f8, 4px 3px #f8f8f8, 5px 3px #f8f8f8, 6px 3px #f8f8f8, 7px 3px #f8f8f8, 8px 3px #f8f8f8, 9px 3px #f8f8f8, 10px 3px #f8f8f8, 11px 3px #f8f8f8, 12px 3px #f8f8f8, 13px 3px #f8f8f8, 14px 3px #f8f8f8,
                0px 4px #d8d8d8, 1px 4px #f8f8f8, 2px 4px #f8f8f8, 3px 4px #f8f8f8, 4px 4px #f8f8f8, 5px 4px #f8f8f8, 6px 4px #f8f8f8, 7px 4px #f8f8f8, 8px 4px #f8f8f8, 9px 4px #f8f8f8, 10px 4px #f8f8f8, 11px 4px #f8f8f8, 12px 4px #f8f8f8, 13px 4px #f8f8f8, 14px 4px #d8d8d8,
                1px 5px #d8d8d8, 2px 5px #d8d8d8, 3px 5px #f8f8f8, 4px 5px #f8f8f8, 5px 5px #f8f8f8, 6px 5px #f8f8f8, 7px 5px #f8f8f8, 8px 5px #f8f8f8, 9px 5px #f8f8f8, 10px 5px #d8d8d8, 11px 5px #d8d8d8; 4px 9px #282828, 4px 10px #282828,
            transform: scale(2); 5px 1px #505050, 5px 2px #787878, 5px 3px #000000, 5px 4px #f8f8f8, 5px 5px #a8a8a8, 5px 6px #787878, 5px 7px #505050, 5px 8px #282828, 5px 9px #282828, 5px 10px #282828, 5px 11px #282828,
        }}      /* Corpo traseiro */
                6px 0px #282828, 6px 1px #505050, 6px 2px #787878, 6px 3px #a8a8a8, 6px 4px #a8a8a8, 6px 5px #787878, 6px 6px #505050, 6px 7px #282828, 6px 8px #e86818, 6px 9px #e86818, 6px 10px #282828, 6px 11px #282828,
        /* Lakitu na nuvem - sprite autêntico SMW */x 2px #505050, 7px 3px #787878, 7px 4px #787878, 7px 5px #505050, 7px 6px #282828, 7px 7px #e86818, 7px 8px #f8a848, 7px 9px #e86818, 7px 10px #282828, 7px 11px #282828,
        .smw-lakitu {{x #282828, 8px 2px #282828, 8px 3px #505050, 8px 4px #505050, 8px 5px #282828, 8px 6px #e86818, 8px 7px #f8a848, 8px 8px #f8a848, 8px 9px #e86818, 8px 10px #282828,
            width: 36px; height: 40px;px #282828, 9px 4px #282828, 9px 5px #e86818, 9px 6px #f8a848, 9px 7px #f8a848, 9px 8px #e86818, 9px 9px #282828;
            position: absolute;;
            animation: lakitu-float 6s ease-in-out infinite;
        }}
        .smw-lakitu::before {{prite autêntico SMW */
            content: '';
            position: absolute;: 40px;
            width: 1px; height: 1px;
            background: transparent;6s ease-in-out infinite;
            box-shadow:
                /* === LAKITU SMW === */
                /* Cabelo/casco */
                4px 0px #38a818, 5px 0px #58d858, 6px 0px #38a818,
                3px 1px #38a818, 4px 1px #58d858, 5px 1px #58d858, 6px 1px #58d858, 7px 1px #38a818,
                /* Cabeça */sparent;
                3px 2px #f8d878, 4px 2px #f8d878, 5px 2px #f8d878, 6px 2px #f8d878, 7px 2px #f8d878,
                2px 3px #f8d878, 3px 3px #f8d878, 4px 3px #000000, 5px 3px #f8d878, 6px 3px #000000, 7px 3px #f8d878, 8px 3px #f8d878,
                2px 4px #f8d878, 3px 4px #f8d878, 4px 4px #f8d878, 5px 4px #f8d878, 6px 4px #f8d878, 7px 4px #f8d878, 8px 4px #f8d878,
                3px 5px #f8d878, 4px 5px #d82800, 5px 5px #d82800, 6px 5px #d82800, 7px 5px #f8d878,
                /* Óculos/mãos */4px 1px #58d858, 5px 1px #58d858, 6px 1px #58d858, 7px 1px #38a818,
                1px 6px #f8d878, 2px 6px #f8d878, 8px 6px #f8d878, 9px 6px #f8d878,
                /* === NUVEM DE LAKITU === */878, 5px 2px #f8d878, 6px 2px #f8d878, 7px 2px #f8d878,
                3px 7px #f8f8f8, 4px 7px #f8f8f8, 5px 7px #f8f8f8, 6px 7px #f8f8f8, 7px 7px #f8f8f8, 7px 3px #f8d878, 8px 3px #f8d878,
                2px 8px #f8f8f8, 3px 8px #f8f8f8, 4px 8px #f8f8f8, 5px 8px #f8f8f8, 6px 8px #f8f8f8, 7px 8px #f8f8f8, 8px 8px #f8f8f8,
                1px 9px #f8f8f8, 2px 9px #f8f8f8, 3px 9px #f8f8f8, 4px 9px #f8f8f8, 5px 9px #f8f8f8, 6px 9px #f8f8f8, 7px 9px #f8f8f8, 8px 9px #f8f8f8, 9px 9px #f8f8f8,
                2px 10px #d8d8d8, 3px 10px #f8f8f8, 4px 10px #f8f8f8, 5px 10px #f8f8f8, 6px 10px #f8f8f8, 7px 10px #f8f8f8, 8px 10px #d8d8d8;
            transform: scale(2); 2px 6px #f8d878, 8px 6px #f8d878, 9px 6px #f8d878,
        }}      /* === NUVEM DE LAKITU === */
                3px 7px #f8f8f8, 4px 7px #f8f8f8, 5px 7px #f8f8f8, 6px 7px #f8f8f8, 7px 7px #f8f8f8,
        /* Animações */ #f8f8f8, 3px 8px #f8f8f8, 4px 8px #f8f8f8, 5px 8px #f8f8f8, 6px 8px #f8f8f8, 7px 8px #f8f8f8, 8px 8px #f8f8f8,
        @keyframes mario-run {{, 2px 9px #f8f8f8, 3px 9px #f8f8f8, 4px 9px #f8f8f8, 5px 9px #f8f8f8, 6px 9px #f8f8f8, 7px 9px #f8f8f8, 8px 9px #f8f8f8, 9px 9px #f8f8f8,
            0% {{ left: -40px; }} 3px 10px #f8f8f8, 4px 10px #f8f8f8, 5px 10px #f8f8f8, 6px 10px #f8f8f8, 7px 10px #f8f8f8, 8px 10px #d8d8d8;
            100% {{ left: calc(100% + 40px); }}
        }}
        @keyframes yoshi-bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-12px); }}
        }}  0% {{ left: -40px; }}
        @keyframes koopa-walk {{00% + 40px); }}
            0%, 100% {{ transform: translateX(0); }}
            50% {{ transform: translateX(-15px); }}
        }}  0%, 100% {{ transform: translateY(0); }}
        @keyframes goomba-walk {{nslateY(-12px); }}
            0% {{ left: -30px; }}
            100% {{ left: calc(100% + 30px); }}
        }}  0%, 100% {{ transform: translateX(0); }}
        @keyframes block-bump {{anslateX(-15px); }}
            0%, 70%, 100% {{ transform: translateY(0); }}
            35% {{ transform: translateY(-10px); }}
        }}  0% {{ left: -30px; }}
        @keyframes star-spin {{100% + 30px); }}
            0% {{ transform: rotate(0deg) scale(1); filter: brightness(1); }}
            50% {{ transform: rotate(180deg) scale(1.2); filter: brightness(1.5); }}
            100% {{ transform: rotate(360deg) scale(1); filter: brightness(1); }}
        }}  35% {{ transform: translateY(-10px); }}
        @keyframes coin-spin {{
            0%, 100% {{ transform: scaleX(1); }}
            50% {{ transform: scaleX(0.2); }}le(1); filter: brightness(1); }}
        }}  50% {{ transform: rotate(180deg) scale(1.2); filter: brightness(1.5); }}
        @keyframes cloud-float {{tate(360deg) scale(1); filter: brightness(1); }}
            0%, 100% {{ transform: translateX(0) translateY(0); }}
            25% {{ transform: translateX(20px) translateY(-5px); }}
            50% {{ transform: translateX(40px) translateY(0); }}  0%, 100% {{ transform: scaleX(1); }}
            75% {{ transform: translateX(20px) translateY(5px); }}eX(0.2); }}
        }}
        @keyframes piranha-peek {{
            0%, 60%, 100% {{ transform: translateY(15px); opacity: 0.5; }}  0%, 100% {{ transform: translateX(0); }}
            70%, 90% {{ transform: translateY(0); opacity: 1; }}anslateX(20px); }}
        }}
        @keyframes banzai-fly {{
            0% {{ left: calc(100% + 30px); }}  0%, 60%, 100% {{ transform: translateY(15px); opacity: 0.5; }}
            100% {{ left: -50px; }} translateY(0); opacity: 1; }}
        }}
        @keyframes lakitu-float {{
            0%, 100% {{ transform: translateX(0) translateY(0); }}
            25% {{ transform: translateX(20px) translateY(-5px); }}
            50% {{ transform: translateX(40px) translateY(0); }}
            75% {{ transform: translateX(20px) translateY(5px); }}frames lakitu-float {{
        }}        0%, 100% {{ transform: translateX(0) translateY(0); }}
    </style> translateX(20px) translateY(-5px); }}
    }}
    <!-- Nuvens pixel art -->
    <div class="smw-cloud" style="top: 15px; left: 8%;"></div>
    <div class="smw-cloud" style="top: 25px; right: 12%; animation-delay: 2s;"></div></style>
    <div class="smw-cloud" style="top: 8px; right: 35%; transform: scale(0.7); animation-delay: 1s;"></div>
    
    <!-- Mario correndo --><div class="smw-cloud" style="top: 15px; left: 8%;"></div>
    <div class="smw-mario" style="bottom: 58px; z-index: 10;"></div>w-cloud" style="top: 25px; right: 12%; animation-delay: 2s;"></div>
    imation-delay: 1s;"></div>
    <!-- Yoshi -->
    <div class="smw-yoshi" style="bottom: 56px; right: 60px; z-index: 10;"></div>->
    
    <!-- Koopa Troopa -->
    <div class="smw-koopa" style="bottom: 56px; right: 25%; z-index: 8;"></div>
    : 10;"></div>
    <!-- Goomba (Galoomba) -->
    <div class="smw-goomba" style="bottom: 56px; z-index: 7;"></div>a -->
    dex: 8;"></div>
    <!-- ? Block -->
    <div class="smw-block" style="top: 70px; right: 15%;"></div><!-- Goomba (Galoomba) -->
    <div class="smw-block" style="top: 70px; left: 20%; animation-delay: 0.3s;"></div>mba" style="bottom: 56px; z-index: 7;"></div>
    
    <!-- Super Star --><!-- ? Block -->
    <div class="smw-star" style="top: 95px; left: 45%;"></div>w-block" style="top: 70px; right: 15%;"></div>
    ion-delay: 0.3s;"></div>
    <!-- Coins -->
    <div class="smw-coin" style="top: 85px; left: 12%;"></div>
    <div class="smw-coin" style="top: 105px; right: 22%; animation-delay: 0.3s;"></div><div class="smw-star" style="top: 95px; left: 45%;"></div>
    <div class="smw-coin" style="top: 115px; left: 35%; animation-delay: 0.6s;"></div>
    
    <!-- Pipe --><div class="smw-coin" style="top: 85px; left: 12%;"></div>
    <div class="smw-pipe" style="bottom: 48px; left: 30%;"></div>px; right: 22%; animation-delay: 0.3s;"></div>
    lay: 0.6s;"></div>
    <!-- Piranha Plant saindo do Pipe -->
    <div class="smw-piranha" style="bottom: 70px; left: 32%;"></div>
    
    <!-- Super Mushroom (decorativo) -->
    <div class="smw-mushroom" style="bottom: 58px; left: 65%;"></div>o Pipe -->
    v>
    <!-- Banzai Bill voando -->
    <div class="smw-banzai" style="top: 140px; z-index: 5;"></div>orativo) -->
    /div>
    <!-- Lakitu na nuvem -->
    <div class="smw-lakitu" style="top: 30px; left: 50%;"></div>
    smw-banzai" style="top: 140px; z-index: 5;"></div>
    <!-- Header - Estilo HUD do Super Mario World -->
    <div style="
        background: linear-gradient(180deg, #e52521 0%, #b01e1e 100%); style="top: 30px; left: 50%;"></div>
        border-bottom: 4px solid #fbd000;
        padding: 10px 15px;D do Super Mario World -->
        text-align: center;
        position: relative;  background: linear-gradient(180deg, #e52521 0%, #b01e1e 100%);
        z-index: 10;
    ">
        <div class="smw-yoshi" style="width: 14px; height: 18px; position: relative; display: inline-block; margin-right: 8px; animation: none;"></div>
        <span style="color: #fbd000; font-weight: bold; text-shadow: 2px 2px #000;"> DINOSAUR LAND TRADING </span>
        <div class="smw-yoshi" style="width: 14px; height: 18px; position: relative; display: inline-block; margin-left: 8px; animation: none; transform: scaleX(-1);"></div>
        <div style="font-size: 8px; color: rgba(255,255,255,0.7); margin-top: 2px;">
            ★ YOSHI'S ISLAND ★ DONUT PLAINS ★ VANILLA DOME ★iv class="smw-yoshi" style="width: 14px; height: 18px; position: relative; display: inline-block; margin-right: 8px; animation: none;"></div>
        </div>    <span style="color: #fbd000; font-weight: bold; text-shadow: 2px 2px #000;"> DINOSAUR LAND TRADING </span>
    </div>style="width: 14px; height: 18px; position: relative; display: inline-block; margin-left: 8px; animation: none; transform: scaleX(-1);"></div>
     margin-top: 2px;">
    <!-- Conteúdo principal -->    ★ YOSHI'S ISLAND ★ DONUT PLAINS ★ VANILLA DOME ★
    <div style="padding: 15px; position: relative; z-index: 10;">
        
        <!-- Info boxes estilo HUD do SMW original -->
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <div style="background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">
                <div style="font-size: 9px; color: #fbd000;">MARIO</div>
                <div style="font-size: 12px; font-weight: bold; color: #ffffff;">{symbol[:3]}</div>
            </div>rgin-bottom: 10px;">
            <div style="background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">r;">
                <div style="font-size: 9px; color: #fbd000;">★×</div>iv style="font-size: 9px; color: #fbd000;">MARIO</div>
                <div style="font-size: 12px; font-weight: bold; color: #ffffff; animation: coin-spin 1s infinite;">{cycle}</div>
            </div>
            <div style="background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">adding: 5px 10px; text-align: center;">
                <div style="font-size: 9px; color: #fbd000;">WORLD</div>iv style="font-size: 9px; color: #fbd000;">★×</div>
                <div style="font-size: 12px; font-weight: bold; color: #ffffff;">{mode}</div>
            </div>
            <div style="background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">
                <div style="font-size: 9px; color: #fbd000;">TIME</div>iv style="font-size: 9px; color: #fbd000;">WORLD</div>
                <div style="font-size: 12px; font-weight: bold; color: #ffffff;">{now.split()[1][:5] if ' ' in now else now[:5]}</div>  <div style="font-size: 12px; font-weight: bold; color: #ffffff;">{mode}</div>
            </div>    </div>
        </div>"background: #000000; border: 3px solid #fbd000; border-radius: 0px; padding: 5px 10px; text-align: center;">
         style="font-size: 9px; color: #fbd000;">TIME</div>
        <!-- Preços -->2px; font-weight: bold; color: #ffffff;">{now.split()[1][:5] if ' ' in now else now[:5]}</div>
        <div style="
            background: rgba(0,0,0,0.6);
            border: 3px solid #43b047;
            border-radius: 8px;
            padding: 10px;iv style="
            margin-bottom: 10px;
        ">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="color: #fbd000;">🏠 ENTRY:</span>g: 10px;
                <span style="font-weight: bold;">${entry_price:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #fbd000;">📍 CURRENT:</span>pan style="color: #fbd000;">🏠 ENTRY:</span>
                <span style="font-weight: bold; color: #43b047;">${current_price:,.2f}</span>  <span style="font-weight: bold;">${entry_price:,.2f}</span>
            </div>    </div>
        </div>"display: flex; justify-content: space-between;">
        n style="color: #fbd000;">📍 CURRENT:</span>
        <!-- Status -->nt-weight: bold; color: #43b047;">${current_price:,.2f}</span>
        <div style="
            text-align: center;
            font-size: 14px;
            font-weight: bold;
            color: {status_color};
            text-shadow: 2px 2px #000;
            margin-bottom: 10px;  font-size: 14px;
            animation: mario-jump 0.5s infinite;
        ">lor: {status_color};
            {mario_char} {status}    text-shadow: 2px 2px #000;
        </div>
        n: mario-jump 0.5s infinite;
        <!-- Profit com Power Meter estilo SMW -->
        <div style="}
            text-align: center;div>
            margin-bottom: 10px;
        ">
            <span style="font-size: 9px; color: #fbd000;">POWER:</span>
            <span style="font-size: 18px; font-weight: bold; color: {status_color}; text-shadow: 2px 2px #000;">ign: center;
                {profit_pct:+.2f}%rgin-bottom: 10px;
            </span>">
        </div>
        yle="font-size: 18px; font-weight: bold; color: {status_color}; text-shadow: 2px 2px #000;">
        <!-- Barra de progresso - Giant Gate (portão de fim de fase) -->
        <div style="
            background: rgba(0,0,0,0.7);
            border: 3px solid #8b4513;
            border-radius: 0px;- Giant Gate (portão de fim de fase) -->
            padding: 8px;iv style="
            margin-bottom: 10px;
        ">
            <div style="font-size: 9px; color: #fbd000; margin-bottom: 5px; text-align: center;">-radius: 0px;
                🚩 GIANT GATE — TARGET {target_pct:.1f}%;
            </div>
            <div style="
                font-size: 14px;9px; color: #fbd000; margin-bottom: 5px; text-align: center;">
                letter-spacing: -1px;ARGET {target_pct:.1f}%
                text-align: center;div>
                line-height: 1.2;
            ">nt-size: 14px;
                {blocks_filled}{blocks_empty}
            </div>
            <div style="text-align: center; margin-top: 5px; font-size: 10px;">ne-height: 1.2;
                <span style="color: #43b047;">★</span> {progress:.0f}/100 BONUS STARS <span style="color: #43b047;">★</span>
            </div>        {blocks_filled}{blocks_empty}
        </div>
        le="text-align: center; margin-top: 5px; font-size: 10px;">
        <!-- Info estilo SMW com Dragon Coins e Secret Exit -->e="color: #43b047;">★</span> {progress:.0f}/100 BONUS STARS <span style="color: #43b047;">★</span>
        <div style="
            display: flex;
            justify-content: center;
            gap: 8px;-- Info estilo SMW com Dragon Coins e Secret Exit -->
            font-size: 10px;
        ">
            <div style="background: #000000; border: 2px solid #fbd000; border-radius: 0px; padding: 4px 8px; display: flex; align-items: center; gap: 4px;">
                <div class="smw-coin" style="position: relative; width: 10px; height: 14px; animation: none;"></div>px;
                <span>×{executed}</span>
            </div>
            <div style="background: #e52521; border: 2px solid #fbd000; border-radius: 0px; padding: 4px 8px;">tyle="background: #000000; border: 2px solid #fbd000; border-radius: 0px; padding: 4px 8px; display: flex; align-items: center; gap: 4px;">
                🔑 {last_event[:12]}  <div class="smw-coin" style="position: relative; width: 10px; height: 14px; animation: none;"></div>
            </div>        <span>×{executed}</span>
        </div>  </div>
                <div style="background: #e52521; border: 2px solid #fbd000; border-radius: 0px; padding: 4px 8px;">
    </div>
    v>
    <!-- Footer - Chão do Dinosaur Land (grama + terra com pixel texture) -->
    <div style="
        background: linear-gradient(180deg, #43b047 0%, #2d8a35 30%, #8b4513 70%, #5a3010 100%);
        border-top: 3px solid #fbd000;
        padding: 8px;do Dinosaur Land (grama + terra com pixel texture) -->
        text-align: center;
        font-size: 9px;gradient(180deg, #43b047 0%, #2d8a35 30%, #8b4513 70%, #5a3010 100%);
        color: #ffffff;  border-top: 3px solid #fbd000;
        position: relative;
    ">
        <div style="display: flex; justify-content: center; align-items: center; gap: 12px;">
            <span style="display: flex; align-items: center; gap: 4px;">
                <div class="smw-mushroom" style="position: relative; width: 12px; height: 12px; transform: scale(0.8);"></div>elative;
                <span>1-UP</span>
            </span>
            <span style="color: #fbd000;">{now}</span>
            <span style="color: {price_label_color}; font-weight: bold;">PRICE: {price_source.upper()}</span>
            <span style="display: flex; align-items: center; gap: 4px;">
                <div class="smw-star" style="position: relative; width: 12px; height: 12px; transform: scale(0.7); animation: none;"></div>
                <span>ONLINE</span>pan style="color: #fbd000;">{now}</span>
            </span>pan style="color: {price_label_color}; font-weight: bold;">PRICE: {price_source.upper()}</span>
        </div> align-items: center; gap: 4px;">
        </div>
        <!-- Watermark for DRY runs -->          <span>ONLINE</span>
        {'<div style="position:absolute; top:40%; left:50%; transform:translate(-50%,-50%) rotate(-20deg); font-size:48px; color: rgba(255,255,255,0.12); font-weight:900; pointer-events:none; z-index:9999;">DRY RUN</div>' if is_dry else ''}         </span>
</div>
'''        </div>
    render_html_smooth(gauge_html, height=520, key=f"mario_gauge_{bot_id}")        <!-- Watermark for DRY runs -->
        {'<div style="position:absolute; top:40%; left:50%; transform:translate(-50%,-50%) rotate(-20deg); font-size:48px; color: rgba(255,255,255,0.12); font-weight:900; pointer-events:none; z-index:9999;">DRY RUN</div>' if is_dry else ''}


def render_terminal_gauge(bot_id, symbol, mode, entry_price, current_price,
                          profit_pct, target_pct, progress, cycle, executed,
                          last_event, now, price_source, theme, is_dry: bool = False):
    """Renderiza gauge no estilo terminal COBOL padrão"""
    de, entry_price, current_price,
    bar_width = 40rogress, cycle, executed,
    filled = int(bar_width * progress / 100)                      last_event, now, price_source, theme, is_dry: bool = False):
    bar = "█" * filled + "░" * (bar_width - filled)o estilo terminal COBOL padrão"""
    
    # Cor baseada no P&L
    if profit_pct >= target_pct:ess / 100)
        pnl_color = theme["success"] "░" * (bar_width - filled)
        status = "TARGET ATINGIDO"
    elif profit_pct > 0:
        pnl_color = theme["text"]et_pct:
        status = "EM LUCRO""]
    elif profit_pct < -1:INGIDO"
        pnl_color = theme["error"]profit_pct > 0:
        status = "PREJUIZO"
    else:O"
        pnl_color = theme["warning"]elif profit_pct < -1:
        status = "NEUTRO"
    
    # Escolhe cor do rótulo de origem de preço    else:
    price_label_color = theme.get("success") if str(price_source).lower() == "live" else theme.get("accent")heme["warning"]
us = "NEUTRO"
    gauge_html = f'''
<div style=" rótulo de origem de preço
    font-family: 'Courier New', 'Lucida Console', monospace;get("success") if str(price_source).lower() == "live" else theme.get("accent")
    font-size: 13px;
    background: {theme["bg"]};
    border: 2px solid {theme["border"]};
    box-shadow: 0 0 20px {theme["glow"]}, inset 0 0 30px rgba(0,0,0,0.8);rier New', 'Lucida Console', monospace;
    padding: 0;
    max-width: 500px;"bg"]};
    color: {theme["text"]};id {theme["border"]};
    border-radius: 4px;  box-shadow: 0 0 20px {theme["glow"]}, inset 0 0 30px rgba(0,0,0,0.8);
    margin: 10px 0;
">
    <div style="
        background: {theme["header_bg"]};
        border-bottom: 1px solid {theme["border"]};
        padding: 8px 12px;
        text-align: center;
    ">
        <span style="color: {theme["warning"]};">╔═══════════════════════════════════════════════╗</span><br>
        <span style="color: {theme["accent"]};">║</span>
        <span style="color: #ffffff; font-weight: bold;"> ◉ KUCOIN TRADING TERMINAL v2.0 ◉ </span>
        <span style="color: {theme["accent"]};">║</span><br>
        <span style="color: {theme["warning"]};">╚═══════════════════════════════════════════════╝</span>    <span style="color: {theme["warning"]};">╔═══════════════════════════════════════════════╗</span><br>
    </div>
    
    <div style="padding: 12px; background: {theme["bg2"]};">
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">┌──────────────────────────────────────────────┐</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ BOT: <span style="color: #ffffff;">{bot_id[:16]:<16}</span>                       │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ SYM: <span style="color: {theme["accent"]};">{symbol:<12}</span> MODE: <span style="color: {theme["warning"]};">{mode:<6}</span>         │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ ENTRY.....: <span style="color: #ffffff;">${{entry_price:>12,.2f}}</span>                │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ CURRENT...: <span style="color: {theme["accent"]}; font-weight: bold;">${{current_price:>12,.2f}}</span>                │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre><6}</span>         │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ P&amp;L STATUS: <span style="color: {pnl_color}; font-weight: bold;">{status:<16}</span>              │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ PROFIT: <span style="color: {pnl_color}; font-weight: bold;">{profit_pct:>+10.4f}%</span>                      │</pre>ce:>12,.2f}</span>                │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ TARGET: <span style="color: {theme["warning"]};">{target_pct:>10.2f}%</span>                      │</pre>ont-weight: bold;">${current_price:>12,.2f}</span>                │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ PROGRESS TO TARGET:                          │</pre>      │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ <span style="color: {pnl_color};">{bar}</span>   │</pre> bold;">{profit_pct:>+10.4f}%</span>                      │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ <span style="color: #ffffff;">{progress:>6.1f}%</span> COMPLETE                          │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ CYCLE: <span class="highlight">${{String(cycle).padStart(6, ' ')}}</span>  EXEC: <span class="value">${{executed.padEnd(8, ' ')}}</span>          │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ EVENT: <span style="color: {theme["warning"]};">${{lastEvent.substring(0,20).padEnd(20, ' ')}}</span>              │</pre><pre style="margin:0; font-family: inherit; color: {theme["text2"]};">│ <span style="color: {pnl_color};">{bar}</span>   │</pre>
        <pre style="margin:0; font-family: inherit; color: {theme["accent"]};">└──────────────────────────────────────────────┘</pre>in:0; font-family: inherit; color: {theme["text2"]};">│ <span style="color: #ffffff;">{progress:>6.1f}%</span> COMPLETE                          │</pre>
        ; font-family: inherit; color: {theme["accent"]};">├──────────────────────────────────────────────┤</pre>
            <div style=" font-family: inherit; color: {theme["text2"]};">│ CYCLE: <span style="color: {theme["accent"]};">{cycle:>6}</span>  EXEC: <span style="color: #ffffff;">{executed:<8}</span>          │</pre>
            margin-top: 8px;or: {theme["text2"]};">│ EVENT: <span style="color: {theme["warning"]};">{last_event[:20]:<20}</span>              │</pre>
            padding-top: 8px;0; font-family: inherit; color: {theme["accent"]};">└──────────────────────────────────────────────┘</pre>
            border-top: 1px dashed {theme["border"]}44;
            color: #666666;
            font-size: 10px;  margin-top: 8px;
            text-align: center;
        ">
            <span style="color: {theme["text"]};">●</span> ONLINE | 
            <span style="color: #aaaaaa;">${{now}}</span> |
            <span style="color: {theme["text"]};">◄</span> AUTO-REFRESH 2sxt-align: center;
        </div>
    </div>      <span style="color: {theme["text"]};">●</span> ONLINE | 
</div>         <span style="color: #aaaaaa;">{now}</span> |
'''lor: {price_label_color}; font-weight:bold;">PRICE: {price_source.upper()}</span> |
    # Renderiza sem flicker> REFRESH MANUAL
    render_html_smooth(gauge_html, height=420, key=f"terminal_gauge_{bot_id}")


def render_cobol_gauge(logs: list, bot_id: str, target_pct: float = 2.0, api_port: int = 8765, is_dry: bool = False):
    """    # Renderiza sem flicker
    Renderiza gauge estilo terminal COBOL/mainframe inline com polling realtime.    # Append watermark for DRY runs into same key wrapper
    Visual retro com bordas ASCII, usa tema selecionado.
    """ # Inject a small badge overlay by appending an absolutely positioned div
    from datetime import datetimeion:absolute; top:8px; right:8px; background: rgba(255,255,255,0.08); padding:6px 8px; color:#ffd; border-radius:6px; font-weight:700; z-index:9999;">DRY RUN</div>\n</div>\n</div>\n\n')
    minal_gauge_{bot_id}")
    # Obter tema atual
    theme = get_current_theme()
    render_cobol_gauge(logs: list, bot_id: str, target_pct: float = 2.0, api_port: int = 8765, is_dry: bool = False):
    gauge_html = f'''
<!DOCTYPE html>inal COBOL/mainframe inline com polling realtime.
<html>Visual retro com bordas ASCII, usa tema selecionado.
<head>
    <meta charset="UTF-8">me import datetime
    <style>
        * {{Obter tema atual
            box-sizing: border-box;eme()
            margin: 0;
            padding: 0;ml = f'''
        }}
        
        body {{
            background: {theme["bg"]};charset="UTF-8">
            font-family: 'Courier New', 'Lucida Console', monospace;
            padding: 0;
            margin: 0;
        }}
          padding: 0;
        .gauge-container {{
            background: {theme["bg"]};
            border: 2px solid {theme["border"]};
            box-shadow: 0 0 20px {theme["glow"]}, inset 0 0 30px rgba(0,0,0,0.8);
            max-width: 520px;
            color: {theme["text"]};
            border-radius: 4px;
        }}  background: {theme["bg"]};
        .gauge-header {{solid {theme["border"]};
            background: {theme["header_bg"]};"]}, inset 0 0 30px rgba(0,0,0,0.8);
            border-bottom: 1px solid {theme["border"]};
            padding: 8px 12px;t"]};
            text-align: center;
        }}
        .gauge-content {{
            padding: 12px;heme["header_bg"]};
            background: {theme["bg2"]};heme["border"]};
        }}  padding: 8px 12px;
        pre {{xt-align: center;
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.3;e["bg2"]};
        }}
        .border-char {{ color: {theme["accent"]}; }}
        .label {{ color: {theme["text2"]}; }}
        .value {{ color: #ffffff; }}w', monospace;
        .highlight {{ color: {theme["accent"]}; font-weight: bold; }}
        .profit-positive {{ color: {theme["success"]}; font-weight: bold; }}
        .profit-negative {{ color: {theme["error"]}; font-weight: bold; }}
        .profit-neutral {{ color: {theme["warning"]}; }}
        .gauge-footer {{ {theme["text2"]}; }}
            margin-top: 8px;ffff; }}
            padding-top: 8px;{theme["accent"]}; font-weight: bold; }}
            border-top: 1px dashed {theme["border"]}44;font-weight: bold; }}
            color: #666666; color: {theme["error"]}; font-weight: bold; }}
            font-size: 10px;olor: {theme["warning"]}; }}
            text-align: center;
        }}  margin-top: 8px;
    </style>padding-top: 8px;
</head>     border-top: 1px dashed {theme["border"]}44;
<body>      color: #666666;
    <div class="gauge-container">
        <div class="gauge-header">
            <span style="color: {theme["warning"]};">╔═══════════════════════════════════════════════╗</span><br>
            <span style="color: {theme["accent"]};">║</span>
            <span style="color: #ffffff; font-weight: bold;"> ◉ KUCOIN TRADING TERMINAL v2.0 ◉ </span>
            <span style="color: {theme["accent"]};">║</span><br>
            <span style="color: {theme["warning"]};">╚═══════════════════════════════════════════════╝</span>
        </div>lass="gauge-header">
            <span style="color: {theme["warning"]};">╔═══════════════════════════════════════════════╗</span><br>
        {('<div style="position:absolute; top:40%; left:50%; transform:translate(-50%,-50%) rotate(-20deg); font-size:48px; color: rgba(255,255,255,0.12); font-weight:900; pointer-events:none; z-index:9999;">DRY RUN</div>') if is_dry else ''}
        <div class="gauge-content" id="gaugeContent"> bold;"> ◉ KUCOIN TRADING TERMINAL v2.0 ◉ </span>
            <pre class="border-char">┌──────────────────────────────────────────────┐</pre>
            <pre class="label">│ <span id="loading">Carregando dados...</span></pre>═════════════════╝</span>
            <pre class="border-char">└──────────────────────────────────────────────┘</pre>
        </div>
    </div>'<div style="position:absolute; top:40%; left:50%; transform:translate(-50%,-50%) rotate(-20deg); font-size:48px; color: rgba(255,255,255,0.12); font-weight:900; pointer-events:none; z-index:9999;">DRY RUN</div>') if is_dry else ''}
        <div class="gauge-content" id="gaugeContent">
    <script><pre class="border-char">┌──────────────────────────────────────────────┐</pre>
        const botId = "{bot_id}";<span id="loading">Carregando dados...</span></pre>
        const targetPct = {target_pct};─────────────────────────────────────────────┘</pre>
        const apiUrl = window.location.protocol + "//" + window.location.hostname + ":{api_port}/api/logs?bot=" + encodeURIComponent(botId) + "&limit=15";
        v>
        function parseNumber(val) {{
            const n = parseFloat(val);
            return isNaN(n) ? 0 : n;
        }}nst targetPct = {target_pct};
        const apiUrl = window.location.protocol + "//" + window.location.hostname + ":{api_port}/api/logs?bot=" + encodeURIComponent(botId) + "&limit=15";
        function formatPrice(p) {{
            return "$" + p.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}  const n = parseFloat(val);
            return isNaN(n) ? 0 : n;
        function makeBar(progress, width) {{
            const filled = Math.floor(width * progress / 100);
            return "█".repeat(filled) + "░".repeat(width - filled);
        }}  return "$" + p.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}
        function renderGauge(data) {{
            let currentPrice = 0, entryPrice = 0, symbol = "BTC-USDT", cycle = 0;
            let executed = "0/0", mode = "---", lastEvent = "AGUARDANDO";
            return "█".repeat(filled) + "░".repeat(width - filled);
            // Parse logs mais recentes
            for (const log of data) {{
                try {{rGauge(data) {{
                    const parsed = JSON.parse(log.message || "{{}}");, cycle = 0;
                    if (parsed.price) currentPrice = parseNumber(parsed.price);
                    if (parsed.entry_price) entryPrice = parseNumber(parsed.entry_price);
                    if (parsed.symbol) symbol = parsed.symbol;
                    if (parsed.cycle) cycle = parseInt(parsed.cycle) || 0;
                    if (parsed.executed) executed = parsed.executed;
                    if (parsed.mode) lastEvent = parsed.mode.toUpperCase().replace(/_/g, " ");
                }} catch(e) {{}}
            }}ntry_price) entryPrice = parseNumber(parsed.entry_price);
                  if (parsed.symbol) symbol = parsed.symbol;
            // Calcular P&L        if (parsed.cycle) cycle = parseInt(parsed.cycle) || 0;
            let profitPct = 0;sed.executed) executed = parsed.executed;
            if (entryPrice > 0 && currentPrice > 0) {{.mode) mode = parsed.mode.toUpperCase();
                profitPct = ((currentPrice - entryPrice) / entryPrice) * 100;ed.event.toUpperCase().replace(/_/g, " ");
            }}
            
            // Progress para o target
            const progress = Math.min(100, Math.max(0, targetPct > 0 ? (profitPct / targetPct) * 100 : 0));
            const bar = makeBar(progress, 40);
             > 0) {{
            // Cores e status    profitPct = ((currentPrice - entryPrice) / entryPrice) * 100;
            let pnlClass = "profit-neutral";
            let status = "NEUTRO";
            if (profitPct >= targetPct) {{get
                pnlClass = "profit-positive"; Math.max(0, targetPct > 0 ? (profitPct / targetPct) * 100 : 0));
                status = "TARGET ATINGIDO";;
            }} else if (profitPct > 0) {{
                pnlClass = "highlight";
                status = "EM LUCRO";ral";
            }} else if (profitPct < -1) {{
                pnlClass = "profit-negative";
                status = "PREJUIZO";
            }}NGIDO";
             else if (profitPct > 0) {{
            const now = new Date().toLocaleString('pt-BR');    pnlClass = "highlight";
            const botIdShort = botId.substring(0, 16).padEnd(16, ' ');
            
            document.getElementById("gaugeContent").innerHTML = `    pnlClass = "profit-negative";
<pre class="border-char">┌──────────────────────────────────────────────┐</pre>
<pre class="label">│ BOT: <span class="value">${{botIdShort}}</span>                       │</pre>
<pre class="label">│ SYM: <span class="highlight">${{symbol.padEnd(12, ' ')}}</span> MODE: <span style="color: {theme["warning"]};">${{mode.padEnd(6, ' ')}}</span>         │</pre>
<pre class="border-char">├──────────────────────────────────────────────┤</pre>
<pre class="label">│ ENTRY.....: <span class="value">${{formatPrice(entryPrice).padStart(12, ' ')}}</span>                │</pre>
<pre class="label">│ CURRENT...: <span class="highlight">${{formatPrice(currentPrice).padStart(12, ' ')}}</span>                │</pre>
<pre class="border-char">├──────────────────────────────────────────────┤</pre>
<pre class="label">│ P&amp;L STATUS: <span class="${{pnlClass}}">${{status.padEnd(16, ' ')}}</span>              │</pre>
<pre class="label">│ PROFIT: <span class="${{pnlClass}}">${{profitPct >= 0 ? '+' : ''}}${{profitPct.toFixed(4).padStart(9, ' ')}}%</span>                      │</pre>
<pre class="label">│ TARGET: <span style="color: {theme["warning"]};">${{targetPct.toFixed(2).padStart(10, ' ')}}%</span>                      │</pre>      │</pre>
<pre class="border-char">├──────────────────────────────────────────────┤</pre>
<pre class="label">│ PROGRESS TO TARGET:                          │</pre>.padStart(12, ' ')}}</span>                │</pre>
<pre class="label">│ <span class="${{pnlClass}}">${{bar}}</span>   │</pre>urrentPrice).padStart(12, ' ')}}</span>                │</pre>
<pre class="label">│ <span class="value">${{progress.toFixed(1).padStart(6, ' ')}}%</span> COMPLETE                          │</pre>/pre>
<pre class="border-char">├──────────────────────────────────────────────┤</pre>
<pre class="label">│ CYCLE: <span class="highlight">${{String(cycle).padStart(6, ' ')}}</span>  EXEC: <span class="value">${{executed.padEnd(8, ' ')}}</span>          │</pre>' : ''}}${{profitPct.toFixed(4).padStart(9, ' ')}}%</span>                      │</pre>
<pre class="label">│ EVENT: <span style="color: {theme["warning"]};">${{lastEvent.substring(0,20).padEnd(20, ' ')}}</span>              │</pre>
<pre class="border-char">└──────────────────────────────────────────────┘</pre>
        
            <div style=" class="${{pnlClass}}">${{bar}}</span>   │</pre>
            margin-top: 8px;(1).padStart(6, ' ')}}%</span> COMPLETE                          │</pre>
            padding-top: 8px;─────────────────────┤</pre>
            border-top: 1px dashed {theme["border"]}44;e).padStart(6, ' ')}}</span>  EXEC: <span class="value">${{executed.padEnd(8, ' ')}}</span>          │</pre>
            color: #666666;lass="label">│ EVENT: <span style="color: {theme["warning"]};">${{lastEvent.substring(0,20).padEnd(20, ' ')}}</span>              │</pre>
            font-size: 10px;rder-char">└──────────────────────────────────────────────┘</pre>
            text-align: center;="gauge-footer">
        ">n style="color: {theme["text"]};">●</span> ONLINE | 
            <span style="color: {theme["text"]};">●</span> ONLINE | </span> |
            <span style="color: #aaaaaa;">${{now}}</span> |olor: {theme["text"]};">◄</span> AUTO-REFRESH 2s
            <span style="color: {theme["text"]};">◄</span> AUTO-REFRESH 2s
        </div>
    </div>
</div>
'''hAndRender() {{
    # Renderiza sem flicker
    render_html_smooth(gauge_html, height=400, key=f"cobol_gauge_{bot_id}")  const resp = await fetch(apiUrl, {{ cache: "no-store" }});
      if (!resp.ok) return;
        const data = await resp.json();
def render_realtime_terminal(bot_id: str, api_port: int = 8765, height: int = 400, poll_ms: int = 2000):ge(data);
    """{{
    Terminal de logs em tempo real com polling da API. error:", e);
    Estilo combina com tema selecionado e mantém boa legibilidade.}
    """ }}
    theme = get_current_theme() 
         // Inicia polling
    html_content = f'''
<!DOCTYPE html>
<html>    </script>
<head></body>
    <meta charset="UTF-8">
    <style>
        * {{
            box-sizing: border-box;bot_id}")
            margin: 0;
            padding: 0;
        }}render_realtime_terminal(bot_id: str, api_port: int = 8765, height: int = 400, poll_ms: int = 2000):
        
        body {{ logs em tempo real com polling da API.
            background: {theme["bg"]};tilo combina com tema selecionado e mantém boa legibilidade.
            font-family: 'Courier New', 'Lucida Console', monospace;"
            padding: 0;eme()
            margin: 0;
        }}tent = f'''
        
        .terminal {{
            background: {theme["bg2"]};
            border: 2px solid {theme["border"]};charset="UTF-8">
            border-radius: 8px;le>
            overflow: hidden;
            height: {height}px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 0 20px {theme["glow"]}, inset 0 0 30px rgba(0,0,0,0.5);
        }}
        body {{
        .header {{nd: {theme["bg"]};
            background: {theme["header_bg"]}; 'Lucida Console', monospace;
            padding: 10px 15px;
            border-bottom: 1px solid {theme["border"]};
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;"]};
        }}
          border-radius: 8px;
        .header-title {{    overflow: hidden;
            color: {theme["text"]};: {height}px;
            font-size: 13px;
            font-weight: bold;umn;
        }} 0 0 30px rgba(0,0,0,0.5);
        
        .header-status {{
            display: flex;
            align-items: center;eme["header_bg"]};
            gap: 8px;  padding: 10px 15px;
            font-size: 11px;    border-bottom: 1px solid {theme["border"]};
        }}x;
        between;
        .status-dot {{ter;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {theme["success"]};
            animation: pulse 2s infinite;"text"]};
        }}
        ht: bold;
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}.header-status {{
        }}lex;
        : center;
        .status-text {{
            color: {theme["text2"]};
        }}
        
        .content {{tatus-dot {{
            flex: 1;    width: 8px;
            overflow-y: auto;
            padding: 12px;
            font-size: 13px;cess"]};
            line-height: 1.6;  animation: pulse 2s infinite;
        }}}}
        
        .log-line {{
            padding: 6px 10px;  0%, 100% {{ opacity: 1; }}
            margin: 3px 0;    50% {{ opacity: 0.5; }}
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            word-wrap: break-word;
            white-space: pre-wrap;"text2"]};
        }}
        
        .log-info {{ontent {{
            background: {theme["bg"]};    flex: 1;
            color: {theme["text2"]};-y: auto;
            border-left: 3px solid {theme["accent"]};
        }}x;
        
        .log-success {{
            background: {theme["bg"]};
            color: {theme["success"]};
            border-left: 3px solid {theme["success"]};  padding: 6px 10px;
            font-weight: bold;    margin: 3px 0;
        }}adius: 4px;
        , monospace;
        .log-warning {{
            background: {theme["bg"]};
            color: {theme["warning"]};
            border-left: 3px solid {theme["warning"]};
        }}
        
        .log-error {{
            background: {theme["bg"]};
            color: {theme["error"]};
            border-left: 3px solid {theme["error"]};
            font-weight: bold;.log-success {{
        }} {theme["bg"]};
        
        .log-trade {{eme["success"]};
            background: {theme["bg"]};
            color: {theme["accent"]};
            border-left: 3px solid {theme["text"]};
        }}{{
        
        .log-neutral {{};
            background: {theme["bg"]};};
            color: {theme["text2"]};
            border-left: 3px solid {theme["border"]}44;
        }}.log-error {{
        d: {theme["bg"]};
        .log-level {{
            font-weight: bold;heme["error"]};
            margin-right: 8px;
        }}
        
        .log-time {{
            color: {theme["text2"]}88;
            font-size: 11px;;
            margin-right: 8px;
        }}
        
        .empty-state {{{{
            text-align: center;["bg"]};
            color: {theme["text2"]};t2"]};
            padding: 40px;  border-left: 3px solid {theme["border"]}44;
            opacity: 0.7;}}
        }}
        
        .footer {{d;
            background: {theme["bg"]};
            padding: 8px 15px;
            border-top: 1px solid {theme["border"]}44;
            font-size: 10px;
            color: {theme["text2"]}88;2"]}88;
            display: flex;
            justify-content: space-between;8px;
            flex-shrink: 0;
        }}
        .empty-state {{
        /* Scrollbar */lign: center;
        .content::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .content::-webkit-scrollbar-track {{
            background: {theme["bg"]};
        }}
        px;
        .content::-webkit-scrollbar-thumb {{  border-top: 1px solid {theme["border"]}44;
            background: {theme["border"]};    font-size: 10px;
            border-radius: 4px;me["text2"]}88;
        }}
        tent: space-between;
        .content::-webkit-scrollbar-thumb:hover {{  flex-shrink: 0;
            background: {theme["accent"]};}}
        }}
    </style>
</head>ontent::-webkit-scrollbar {{
<body>    width: 8px;
    <div class="terminal">
        <div class="header">
            <span class="header-title">◉ LOG TERMINAL — {bot_id[:12]}...</span>lbar-track {{
            <div class="header-status">  background: {theme["bg"]};
                <div class="status-dot"></div>}}
                <span class="status-text">POLLING</span>
            </div>{{
        </div>  background: {theme["border"]};
        border-radius: 4px;
        <div class="content" id="logContent"> }}
            <div class="empty-state">Conectando ao servidor de logs...</div>  
        </div>scrollbar-thumb:hover {{
        me["accent"]};
        <div class="footer">
            <span id="logCount">0 logs</span>
            <span id="lastUpdate">--:--:--</span>
        </div>
    </div>rminal">
    lass="header">
    <script>    <span class="header-title">◉ LOG TERMINAL — {bot_id[:12]}...</span>
        const botId = "{bot_id}";
        const apiUrl = window.location.protocol + "//" + window.location.hostname + ":{api_port}/api/logs?bot=" + encodeURIComponent(botId) + "&limit=30";
        const container = document.getElementById("logContent");  <span class="status-text">POLLING</span>
        const logCountEl = document.getElementById("logCount");    </div>
        const lastUpdateEl = document.getElementById("lastUpdate");
        let lastHash = "";
        
        function getLogClass(level, message) {{iv class="empty-state">Conectando ao servidor de logs...</div>
            const upper = (level + " " + message).toUpperCase();div>
                
            if (upper.includes("ERROR") || upper.includes("ERRO") || upper.includes("EXCEPTION") || upper.includes("❌")) {{ class="footer">
                return "log-error"; logs</span>
            }}
            if (upper.includes("PROFIT") || upper.includes("LUCRO") || upper.includes("GANHO") || upper.includes("TARGET") || upper.includes("✅") || upper.includes("SUCCESS")) {{
                return "log-success";
            }}
            if (upper.includes("WARNING") || upper.includes("AVISO") || upper.includes("⚠️") || upper.includes("WARN")) {{
                return "log-warning";const botId = "{bot_id}";
            }} + "//" + window.location.hostname + ":{api_port}/api/logs?bot=" + encodeURIComponent(botId) + "&limit=30";
            if (upper.includes("TRADE") || upper.includes("ORDER") || upper.includes("BUY") || upper.includes("SELL") || upper.includes("COMPRA") || upper.includes("VENDA")) {{
                return "log-trade";t logCountEl = document.getElementById("logCount");
            }}
            if (upper.includes("INFO") || upper.includes("CONECTADO") || upper.includes("INICIADO") || upper.includes("BOT")) {{
                return "log-info";
            }}
            return "log-neutral";" + message).toUpperCase();
        }}
        ) || upper.includes("❌")) {{
        function formatMessage(msg) {{
            // Tenta parsear JSON para exibir de forma mais legível
            try {{
                const data = JSON.parse(msg);";
                // Formata campos importantes
                let parts = [];
                if (data.event) parts.push("EVENT: " + data.event);g";
                if (data.price) parts.push("PRICE: $" + parseFloat(data.price).toLocaleString('en-US', {{minimumFractionDigits: 2}}));
                if (data.cycle) parts.push("CYCLE: " + data.cycle);RADE") || upper.includes("ORDER") || upper.includes("BUY") || upper.includes("SELL") || upper.includes("COMPRA") || upper.includes("VENDA")) {{
                if (data.executed) parts.push("EXEC: " + data.executed);      return "log-trade";
                if (data.message) parts.push(data.message);    }}
                if (data.symbol) parts.push("SYM: " + data.symbol); || upper.includes("INICIADO") || upper.includes("BOT")) {{
                if (data.mode) parts.push("MODE: " + data.mode);
                if (data.entry_price) parts.push("ENTRY: $" + parseFloat(data.entry_price).toLocaleString('en-US', {{minimumFractionDigits: 2}}));
                
                return parts.length > 0 ? parts.join(" | ") : msg;
            }} catch (e) {{
                return msg;
            }}
        }}
        
        function renderLogs(logs) {{
            const hash = JSON.stringify(logs);
            if (hash === lastHash) return;t);
            lastHash = hash;
            if (data.cycle) parts.push("CYCLE: " + data.cycle);
            container.innerHTML = "";uted);
            ssage) parts.push(data.message);
            if (!logs || logs.length === 0) {{mbol) parts.push("SYM: " + data.symbol);
                container.innerHTML = '<div class="empty-state">Aguardando logs do bot...</div>';  if (data.mode) parts.push("MODE: " + data.mode);
                logCountEl.textContent = "0 logs";      if (data.entry_price) parts.push("ENTRY: $" + parseFloat(data.entry_price).toLocaleString('en-US', {{minimumFractionDigits: 2}}));
                return;        
            }}> 0 ? parts.join(" | ") : msg;
            
            logs.forEach(log => {{
                const div = document.createElement("div");
                const logClass = getLogClass(log.level || "INFO", log.message || "");
                div.className = "log-line " + logClass;
                tion renderLogs(logs) {{
                const level = log.level || "INFO";
                const message = formatMessage(log.message || "");
                
                div.innerHTML = '<span class="log-level">[' + level + ']</span>' + message;
                container.appendChild(div);ntainer.innerHTML = "";
            }});
            th === 0) {{
            container.scrollTop = container.scrollHeight;tate">Aguardando logs do bot...</div>';
            logCountEl.textContent = logs.length + " logs";
            
            const now = new Date();
            lastUpdateEl.textContent = now.toLocaleTimeString('pt-BR');
        }}
        const div = document.createElement("div");
        async function fetchLogs() {{
            try {{ + logClass;
                const response = await fetch(apiUrl, {{ cache: "no-store" }});
                if (!response.ok) {{    const level = log.level || "INFO";
                    console.error("API error:", response.status); || "");
                    return;
                }}    div.innerHTML = '<span class="log-level">[' + level + ']</span>' + message;
                const logs = await response.json();ld(div);
                renderLogs(logs);
            }} catch (error) {{  
                console.error("Fetch error:", error);    container.scrollTop = container.scrollHeight;
            }}logs.length + " logs";
        }}
        
        // Inicia polling = now.toLocaleTimeString('pt-BR');
        fetchLogs();
        setInterval(fetchLogs, {poll_ms});
    </script>tion fetchLogs() {{
</body>
</html>await fetch(apiUrl, {{ cache: "no-store" }});
'''k) {{
    nse.status);
    render_html_smooth(html_content, height=height + 20, key=f"realtime_terminal_{bot_id}")      return;
      }}
        const logs = await response.json();
def colorize_logs_html(log_text: str) -> str:s(logs);
    """Gera HTML com texto colorido em fundo preto. Boa legibilidade.""" (error) {{
    theme = get_current_theme():", error);
    lines = log_text.split("\n")}
    html_lines = [] }}
 
    # Fundo sempre escuro para boa legibilidade     // Inicia polling
    bg = "#0a0a0a"    fetchLogs();

    for line in lines:    </script>
        if not line.strip():</body>
            html_lines.append("<div style='height:4px'>&nbsp;</div>")
            continue

        safe = html.escape(line)ent, height=height + 20, key=f"realtime_terminal_{bot_id}")
        upper_line = line.upper()

        # Defaults - texto claro
        fg = "#cccccc"om texto colorido em fundo preto. Boa legibilidade."""
        weight = "400"    theme = get_current_theme()
        border_color = "#333333"plit("\n")

        if any(word in upper_line for word in ['ERROR', 'ERRO', 'EXCEPTION', 'TRACEBACK', '❌']):
            fg, weight, border_color = "#ff6b6b", "700", "#ff6b6b"  # Vermelho claroscuro para boa legibilidade
        elif any(word in upper_line for word in ['LOSS', 'PREJUÍZO', 'STOP LOSS', '❌ LOSS']):    bg = "#0a0a0a"
            fg, weight, border_color = "#ff6b6b", "700", "#ff6b6b"  # Vermelho claro
        elif any(word in upper_line for word in ['PROFIT', 'LUCRO', 'GANHO', 'TARGET', '✅', 'SUCCESS']):
            fg, weight, border_color = "#4ade80", "700", "#4ade80"  # Verde claro        if not line.strip():
        elif any(word in upper_line for word in ['WARNING', 'AVISO', '⚠️', 'WARN']):div style='height:4px'>&nbsp;</div>")
            fg, weight, border_color = "#fbbf24", "600", "#fbbf24"  # Amarelo
        elif any(word in upper_line for word in ['TRADE', 'ORDER', 'BUY', 'SELL', 'ORDEM', 'COMPRA', 'VENDA']):
            fg, weight, border_color = "#60a5fa", "600", "#60a5fa"  # Azul claro
        elif any(word in upper_line for word in ['INFO', 'CONECTADO', 'INICIADO', 'BOT', 'INICIANDO']):        upper_line = line.upper()
            fg, weight, border_color = "#22d3ee", "500", "#22d3ee"  # Cyan

        style = (
            f"background:{bg}; color:{fg}; padding:6px 10px; margin:3px 0; "
            f"border-radius:4px; font-family:'Courier New',monospace; font-size:13px; "
            f"font-weight:{weight}; white-space:pre-wrap; border-left: 3px solid {border_color};"
        )ACK', '❌']):
        html_lines.append(f"<div style=\"{style}\">{safe}</div>")o claro

    return "".join(html_lines)laro
:
e claro
def render_bot_control():        elif any(word in upper_line for word in ['WARNING', 'AVISO', '⚠️', 'WARN']):
    # Defensive: require login per session before rendering any UIeight, border_color = "#fbbf24", "600", "#fbbf24"  # Amarelo
    if not bool(st.session_state.get("logado", False)):ELL', 'ORDEM', 'COMPRA', 'VENDA']):
        # Auto-login if a local .login_status file exists (developer convenience)
        try:DO']):
            if os.path.exists(LOGIN_FILE):   fg, weight, border_color = "#22d3ee", "500", "#22d3ee"  # Cyan
                st.session_state["logado"] = True
            elif os.environ.get('APP_ENV') == 'dev':        style = (
                st.session_state["logado"] = True color:{fg}; padding:6px 10px; margin:3px 0; "
            else:            f"border-radius:4px; font-family:'Courier New',monospace; font-size:13px; "
                st.title("🔐 Login obrigatório")            f"font-weight:{weight}; white-space:pre-wrap; border-left: 3px solid {border_color};"
                st.warning("Você precisa estar autenticado para acessar o dashboard.")
                st.stop()
        except Exception:
            st.title("🔐 Login obrigatório")
            st.warning("Você precisa estar autenticado para acessar o dashboard.")
            st.stop()
    # Chama o renderizador principal da UI (igual ao repositório oficial)
    _render_full_ui()ndering any UI
lse)):
gin if a local .login_status file exists (developer convenience)
def _render_full_ui(controller=None):
    try:
        if ui_logger:n_state["logado"] = True
            ui_logger.debug("_render_full_ui: entrada")on.get('APP_ENV') == 'dev':
    except Exception: True
        pass
    # =====================================================tle("🔐 Login obrigatório")
    # PAGE CONFIG & TEMA GLOBAL dashboard.")
    # =====================================================op()
    # st.set_page_config(page_title="KuCoin Trading Bot", layout="wide")  # Removido para evitar duplicação        except Exception:
            st.title("🔐 Login obrigatório")
    # Injetar CSS do tema terminalestar autenticado para acessar o dashboard.")
    try:    st.stop()
        inject_global_css()zador principal da UI (igual ao repositório oficial)
    except Exception:
        pass

    # Remover coluna lateral (sidebar) globalmente
    # _hide_sidebar_everywhere()

    # ╔════════════════════════════════════════════════════════════════════════╗
    # ║  ⚠️ CRÍTICO: Session State Initialization                              ║    except Exception:
    # ║  - SEMPRE usar "if X not in st.session_state" antes de atribuir        ║
    # ║  - Se um widget usa key="X", NÃO definir value= no widget              ║===================================================
    # ║  - Violação causa: "widget created with default value but also had     ║OBAL
    # ║    its value set via Session State API" → pode travar a UI             ║======================================
    # ╚════════════════════════════════════════════════════════════════════════╝_page_config(page_title="KuCoin Trading Bot", layout="wide")  # Removido para evitar duplicação
    try:
        if not isinstance(st.session_state.get("active_bots", None), list):
            st.session_state["active_bots"] = []
        if "selected_bot" not in st.session_state:        inject_global_css()
            st.session_state["selected_bot"] = None
        if "controller" not in st.session_state:
            st.session_state["controller"] = None
        if "bot_running" not in st.session_state:
            st.session_state["bot_running"] = False
        if "_api_port" not in st.session_state:
            st.session_state["_api_port"] = None
        if "_equity_snapshot_started" not in st.session_state: ⚠️ CRÍTICO: Session State Initialization                              ║
            st.session_state["_equity_snapshot_started"] = False    ║
        if "target_profit_pct" not in st.session_state: value= no widget              ║
            st.session_state["target_profit_pct"] = 2.0  # ⚠️ sidebar_controller.py widget NÃO deve ter value=fault value but also had     ║
        if "monitor_bg_pack" not in st.session_state:ode travar a UI             ║
            st.session_state["monitor_bg_pack"] = None═══════════════════════════════╝
        if "monitor_bg" not in st.session_state:
            st.session_state["monitor_bg"] = Nonective_bots", None), list):
    except Exception:
        # If Streamlit session-state API is unavailable, continue silently.te:
        passone
    # Ensure a usable controller object is present in session state.
    try:
        if controller is None:
            try:
                controller = get_global_controller()
            except Exception:
                controller = Nonesession_state:
        # store controller into session state for other places that expect itarted"] = False
        try:ofit_pct" not in st.session_state:
            st.session_state["controller"] = controlleroller.py widget NÃO deve ter value=
        except Exception:monitor_bg_pack" not in st.session_state:
            pass
    except Exception:if "monitor_bg" not in st.session_state:
        passmonitor_bg"] = None
tion:
    # Ensure the local API server is started once (non-blocking) so /report and /monitor links work.ble, continue silently.
    try:
        if not st.session_state.get("_api_server_start_attempted"):object is present in session state.
            st.session_state["_api_server_start_attempted"] = True
            if "start_api_server" in globals() and st.session_state.get("_api_port") is None:ontroller is None:
                import threading
r = get_global_controller()
                def _start_api():pt Exception:
                    try:oller = None
                        # prefer default 8765 but allow automatic port selectionore controller into session state for other places that expect it
                        p = start_api_server(8765)        try:
                        if p:
                            try:except Exception:
                                st.session_state["_api_port"] = int(p)
                            except Exception:
                                pass
                    except Exception:
                        pass    # Ensure the local API server is started once (non-blocking) so /report and /monitor links work.

                try:n_state.get("_api_server_start_attempted"):
                    threading.Thread(target=_start_api, name="start-api-server", daemon=True).start()
                except Exception: st.session_state.get("_api_port") is None:
                    # best-effort synchronous fallback (rare)ing
                    try:
                        p = start_api_server(8765)
                        if p:
                            st.session_state["_api_port"] = int(p)ault 8765 but allow automatic port selection
                    except Exception:_server(8765)
                        pass:
            try:                            try:
                if ui_logger:            st.session_state["_api_port"] = int(p)
                    ui_logger.debug("_render_full_ui: agendado start_api_server, _api_port=%s", st.session_state.get("_api_port"))
            except Exception:ass
                pass
    except Exception:pass
        pass
    # ----------------------------------------------------------------
t-api-server", daemon=True).start()
    # =====================================================
    # QUERY STRINGffort synchronous fallback (rare)
    # =====================================================    try:
    q = st.query_paramstart_api_server(8765)
    # query params may be returned as list or single string depending on Streamlit version
    def _qs_get(key, default=None):t.session_state["_api_port"] = int(p)
        v = q.get(key, None)except Exception:
        if v is None:   pass
            return defaulttry:
        # if it's a list, take first element; otherwise return as-is
        try:                    ui_logger.debug("_render_full_ui: agendado start_api_server, _api_port=%s", st.session_state.get("_api_port"))
            if isinstance(v, (list, tuple)):
                return v[0]ss
        except Exception:
            pass
        return v

    def _qs_truthy(v) -> bool:===============================
        try:
            s = str(v).strip().lower()=================================
        except Exception:
            return Falseparams may be returned as list or single string depending on Streamlit version
        return s in ("1", "true", "yes", "y", "on")
)
    # =====================================================
    # VIEW MODE (no new tabs): view=dashboard|monitor|reportrn default
    # Also supports legacy params report=1 and window=1.s a list, take first element; otherwise return as-is
    # =====================================================        try:
    raw_view = _qs_get("view", None)list, tuple)):
    try:    return v[0]
        view = str(raw_view or "").strip().lower()
    except Exception:
        view = ""

    is_report_mode = _qs_truthy(_qs_get("report", None))    def _qs_truthy(v) -> bool:
    is_window_mode = _qs_truthy(_qs_get("window", None))

    if not view:
        if is_report_mode:
            view = "report"es", "y", "on")
        elif is_window_mode:
            view = "monitor"=========
        else:ew tabs): view=dashboard|monitor|report
            view = "dashboard"ts legacy params report=1 and window=1.
    # =====================================================
    # Header estilo terminal (somente no modo principal)
    theme = get_current_theme()
    # If the user picked SMW theme, default the monitor background pack.        view = str(raw_view or "").strip().lower()
    # Important: must run before sidebar widgets are created.tion:
    _maybe_apply_smw_monitor_pack(theme)

    # Build theme query-string for the dedicated /monitor window.thy(_qs_get("report", None))
    theme_qs = (thy(_qs_get("window", None))
        f"&t_bg={urllib.parse.quote(theme.get('bg', ''))}"
        f"&t_bg2={urllib.parse.quote(theme.get('bg2', ''))}"
        f"&t_border={urllib.parse.quote(theme.get('border', ''))}"        if is_report_mode:
        f"&t_accent={urllib.parse.quote(theme.get('accent', ''))}"
        f"&t_text={urllib.parse.quote(theme.get('text', ''))}"
        f"&t_text2={urllib.parse.quote(theme.get('text2', ''))}"
        f"&t_muted={urllib.parse.quote('#8b949e')}"
        f"&t_warning={urllib.parse.quote(theme.get('warning', ''))}"
        f"&t_error={urllib.parse.quote(theme.get('error', ''))}"
        f"&t_success={urllib.parse.quote(theme.get('success', ''))}"
        f"&t_header_bg={urllib.parse.quote(theme.get('header_bg', ''))}"current_theme()
        f"&t_is_light={'1' if theme.get('is_light', False) else '0'}"ckground pack.
    ).

    # Optional background selection for the monitor window (served by /themes/*)
    mon_pack = st.session_state.get("monitor_bg_pack")ow.
    mon_bg = st.session_state.get("monitor_bg")
    try: ''))}"
        if theme.get("name") == "Super Mario World" and not mon_pack:
            mon_pack = "smw"}"
        if theme.get("name") == "Super Mario World" and not mon_bg:
            mon_bg = "random"
    except Exception:
        pass   f"&t_muted={urllib.parse.quote('#8b949e')}"
    if mon_pack:        f"&t_warning={urllib.parse.quote(theme.get('warning', ''))}"
        theme_qs += f"&bg_pack={urllib.parse.quote(str(mon_pack))}"
    if mon_bg:ccess', ''))}"
        theme_qs += f"&bg={urllib.parse.quote(str(mon_bg))}"e.get('header_bg', ''))}"
f"&t_is_light={'1' if theme.get('is_light', False) else '0'}"
    # Selected bot resolution (query param wins)
    query_bot = _qs_get("bot", None) or _qs_get("bot_id", None)
    if query_bot:by /themes/*)
        st.session_state.selected_bot = query_botte.get("monitor_bg_pack")
        if query_bot not in st.session_state.active_bots:on_state.get("monitor_bg")
            st.session_state.active_bots.append(query_bot)
.get("name") == "Super Mario World" and not mon_pack:
    selected_bot = st.session_state.get("selected_bot")
me.get("name") == "Super Mario World" and not mon_bg:
    # Top navigation bar on all pages
    render_top_nav_bar(theme, view, selected_bot=selected_bot)    except Exception:

    # Fullscreen pages: also reduce padding
    if view in ("monitor", "report"):+= f"&bg_pack={urllib.parse.quote(str(mon_pack))}"
        _hide_sidebar_for_fullscreen_pages()
)}"
    # Route views
    if view == "report":    # Selected bot resolution (query param wins)
        # Prefer dedicated HTML report (/report) embedded in-app", None)
        api_port = st.session_state.get("_api_port")    if query_bot:
        if api_port: = query_bot
            theme_query = str(theme_qs).lstrip('&')
                        st.session_state.active_bots.append(query_bot)
            # ⚠️ CRÍTICO: Detectar ambiente para URL correta do iframe
            # Em produção (Fly.io), FLY_APP_NAME está definido - usar URL relativaet("selected_bot")
            # Localmente, usar localhost:api_port
            is_production = bool(os.environ.get("FLY_APP_NAME"))    # Top navigation bar on all pages
            v_bar(theme, view, selected_bot=selected_bot)
            if is_production:
                # Em produção: iframe carrega do mesmo domínio (URLs relativas funcionam)
                report_url = f"/report?{theme_query}" if theme_query else "/report"
            else:r_for_fullscreen_pages()
                # Local: usar localhost com porta da API
                report_url = f"http://127.0.0.1:{int(api_port)}/report?{theme_query}" if theme_query else f"http://127.0.0.1:{int(api_port)}/report"views

            # Provide a safe return URL for the HTML window to navigate back.
            try:t")
                try:
                    st_port = int(st.get_option("server.port"))theme_query = str(theme_qs).lstrip('&')
                except Exception:
                    st_port = 8501
                if is_production:
                    home_url = "/?view=dashboard"almente, usar localhost:api_port
                else:_NAME"))
                    home_url = f"http://127.0.0.1:{st_port}/?view=dashboard"
                home_val = urllib.parse.quote(home_url, safe='')            if is_production:
            except Exception:s funcionam)
                home_val = ''report_url = f"/report?{theme_query}" if theme_query else "/report"
            report_url += ("&" if "?" in report_url else "?") + f"home={home_val or ''}"

            if selected_bot:tp://127.0.0.1:{int(api_port)}/report?{theme_query}" if theme_query else f"http://127.0.0.1:{int(api_port)}/report"
                report_url += f"&bot={urllib.parse.quote(str(selected_bot))}"
            components.iframe(report_url, height=900, scrolling=True)rn URL for the HTML window to navigate back.
        else:
            # Fallback to Streamlit report mode (same tab)
            render_trade_report_page()
        st.stop()
 8501
    if view == "monitor":ion:
        render_monitor_dashboard(theme, preselected_bot=selected_bot)
        st.stop()                else:
 = f"http://127.0.0.1:{st_port}/?view=dashboard"
    # Dashboard header (compact, readable)
    theme = get_current_theme()
    st.markdown(f'''   home_val = ''
    <div style="text-align: center; padding: 10px; margin-bottom: 20px;">?") + f"home={home_val or ''}"
        <pre style="color: {theme["border"]}; font-family: 'Courier New', monospace; font-size: 10px; line-height: 1.2; white-space: pre;">
╔══════════════════════════════════════════════════════════════════════════════╗lected_bot:
║  ██╗  ██╗██╗   ██╗ ██████╗ ██████╗ ██╗███╗   ██╗    ██████╗ ██████╗  ██████╗ ║                report_url += f"&bot={urllib.parse.quote(str(selected_bot))}"
║  ██║ ██╔╝██║   ██║██╔════╝██╔═══██╗██║████╗  ██║    ██╔══██╗██╔══██╗██╔═══██╗║rame(report_url, height=900, scrolling=True)
║  █████╔╝ ██║   ██║██║     ██║   ██║██║██╔██╗ ██║    ██████╔╝██████╔╝██║   ██║║
║  ██╔═██╗ ██║   ██║██║     ██║   ██║██║██║╚██╗██║    ██╔═══╝ ██╔══██╗██║   ██║║lback to Streamlit report mode (same tab)
║  ██║  ██╗╚██████╔╝╚██████╗╚██████╔╝██║██║ ╚████║    ██║     ██║  ██║╚██████╔╝║            render_trade_report_page()
║  ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝╚═╝ ╚════╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ║
║                      T R A D I N G   T E R M I N A L                         ║
╚══════════════════════════════════════════════════════════════════════════════╝tor":
        </pre>
    </div>
    ''', unsafe_allow_html=True)
    st.info("👋 Bem-vindo ao KuCoin PRO! Inicie um bot usando os controles à esquerda para começar. Se nenhum bot estiver ativo, esta tela ficará vazia. Para dúvidas, consulte a documentação.")

    # Se a página for aberta com ?start=1 e parâmetros, iniciar o bot aqui
    q = st.query_params
    start_param = _qs_get("start", None)ace; font-size: 10px; line-height: 1.2; white-space: pre;">
    if start_param and not st.session_state.get("_started_from_qs", False):
        try:
            s_symbol = _qs_get("symbol", "BTC-USDT")
            s_entry = float(_qs_get("entry", "88000"))   ██║██║     ██║   ██║██║██╔██╗ ██║    ██████╔╝██████╔╝██║   ██║║
            s_mode = _qs_get("mode", "sell") ██║   ██║██║     ██║   ██║██║██║╚██╗██║    ██╔═══╝ ██╔══██╗██║   ██║║
            s_targets = _qs_get("targets", "2:0.3,5:0.4")███╔╝██║██║ ╚████║    ██║     ██║  ██║╚██████╔╝║
            s_interval = float(_qs_get("interval", "5"))
            s_size_raw = _qs_get("size", "")║                      T R A D I N G   T E R M I N A L                         ║
            s_size = None if s_size_raw in ("", "0", "0.0", "None") else float(s_size_raw)═════╝
            s_funds_raw = _qs_get("funds", "")
            s_funds = None if s_funds_raw in ("", "0", "0.0", "None") else float(s_funds_raw)
            s_dry = _qs_get("dry", "0").lower() in ("1", "true", "yes")
"👋 Bem-vindo ao KuCoin PRO! Inicie um bot usando os controles à esquerda para começar. Se nenhum bot estiver ativo, esta tela ficará vazia. Para dúvidas, consulte a documentação.")
            bot_id_started = st.session_state.controller.start_bot(
                s_symbol, s_entry, s_mode, s_targets,, iniciar o bot aqui
                s_interval, s_size, s_funds, s_dry,
            )
d_from_qs", False):
            # Adiciona à lista de bots ativos
            if bot_id_started not in st.session_state.active_bots:
                st.session_state.active_bots.append(bot_id_started)88000"))
            st.session_state.selected_bot = bot_id_started

            # Mark as done before touching query params to avoid loops.            s_interval = float(_qs_get("interval", "5"))
            st.session_state["_started_from_qs"] = True
"0.0", "None") else float(s_size_raw)
            # substitui a query para exibir ?bot=... evitando reinícios
            _merge_query_params({"bot": bot_id_started, "start": None})_funds = None if s_funds_raw in ("", "0", "0.0", "None") else float(s_funds_raw)
            # st.rerun()  # Removido para evitar reload desnecessário            s_dry = _qs_get("dry", "0").lower() in ("1", "true", "yes")
        except Exception as e:
            # Avoid infinite retries if something goes wrong.(
            st.session_state["_started_from_qs"] = True
            st.error(f"Erro iniciando bot via query: {e}")
            )
    # =====================================================
    # HIDRATAR BOTS ATIVOS (persistência + processos vivos)
    # =====================================================            if bot_id_started not in st.session_state.active_bots:
    # Bugfix: processos que continuam rodando após reload/F5 (ou iniciados fora
    # desta sessão Streamlit) não apareciam porque a UI dependia apenas ded_started
    # st.session_state.active_bots + registry em memória.
    db_sessions_by_id: dict[str, dict] = {}s.
    ps_pids_by_id: dict[str, int] = {}_started_from_qs"] = True

    # 1) DB (bot_sessions) — fonte canônica quando disponívelitando reinícios
    try:
        db_sync = DatabaseManager()            _merge_query_params({"bot": bot_id_started, "start": None})
        for sess in db_sync.get_active_bots() or []:necessário
            bot_id = sess.get("id") or sess.get("bot_id")
            if not bot_id:g.
                continue
            db_sessions_by_id[str(bot_id)] = sess

        # Marcar sessões 'running' cujo PID não existe mais================
        for bot_id, sess in list(db_sessions_by_id.items()):ia + processos vivos)
            try:    # =====================================================
                if str(sess.get("status") or "").lower() != "running":(ou iniciados fora
                    continuesta sessão Streamlit) não apareciam porque a UI dependia apenas de
                pid = sess.get("pid")+ registry em memória.
                if _pid_alive(pid):
                    continue
                bot_id = str(sess.get("id") or "").strip()
                if not bot_id:s) — fonte canônica quando disponível
                    continue
                try:        db_sync = DatabaseManager()
                    db_sync.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
                    sess["status"] = "stopped"
                    sess["end_ts"] = time.time()
                except Exception:inue
                    pass
            except Exception:
                continue 'running' cujo PID não existe mais
items()):
        # 2) ps scan — cobre casos onde o DB falhou em registrar (cached)id_alive(sess.get("pid")):
        out = _ps_scan_cached()    try:
        for line in out[1:]:                    db_sync.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
            line = line.strip()
            if not line:            pass
                continueid.pop(bot_id, None)
            try:
                pid_s, args_s = line.split(None, 1)
                pid_i = int(pid_s)
            except Exception: casos onde o DB falhou em registrar (cached)
                continue
            if "bot_core.py" not in args_s:
                continue
            try:()
                argv = shlex.split(args_s)
            except Exception:
                argv = args_s.split()
            if "--bot-id" in argv:pid_s, args_s = line.split(None, 1)
                try:
                    idx = argv.index("--bot-id")
                    bot_id = argv[idx + 1]
                except Exception:n args_s:
                    bot_id = Noneinue
                if bot_id:
                    ps_pids_by_id[str(bot_id)] = pid_i
    except Exception:
        passit()
in argv:
    # Merge em st.session_state.active_bots preservando ordem e removendo mortos
    discovered_ids: list[str] = []dx = argv.index("--bot-id")
    for bot_id, sess in db_sessions_by_id.items():        bot_id = argv[idx + 1]
        if _pid_alive(sess.get("pid")):                except Exception:
            discovered_ids.append(bot_id)
    for bot_id, pid in ps_pids_by_id.items():
        if _pid_alive(pid) and bot_id not in discovered_ids:id_i
            discovered_ids.append(bot_id)

    controller_alive: list[str] = []
    try:m e removendo mortos
        for bot_id, proc in getattr(controller, "processes", {}).items():
            try:    for bot_id, sess in db_sessions_by_id.items():
                if proc is not None and proc.poll() is None:)):
                    controller_alive.append(str(bot_id))    discovered_ids.append(bot_id)
            except Exception:
                continuealive(pid) and bot_id not in discovered_ids:
    except Exception:
        pass
r] = []
    alive_set = set(discovered_ids) | set(controller_alive)
roc in getattr(controller, "processes", {}).items():
    merged_active: list[str] = []try:
    for b in (list(st.session_state.active_bots) + discovered_ids):                if proc is not None and proc.poll() is None:
        if not b:
            continue            except Exception:
        if b not in merged_active:
            merged_active.append(b)
    # Remove stale entries that have no live PID/process backing.
    st.session_state.active_bots = [b for b in merged_active if b in alive_set]
) | set(controller_alive)
    # =====================================================
    # DASHBOARD LAYOUT (boas práticas: cards + hierarquia)
    # =====================================================
    sidebar_controller = SidebarController()        if not b:
    # Sidebar controls
    try:
        sidebar_controller.render_balances(st.sidebar)
        st.sidebar.divider() PID/process backing.
        sidebar_controller.render_inputs(st.sidebar)ctive_bots = [b for b in merged_active if b in alive_set]
    except Exception as e:
        st.error(f"Erro no sidebar: {e}")=====
 práticas: cards + hierarquia)
    # Prepare theme and semaphore snapshot for rendering in the main layout=======
    try:idebarController()
        theme = get_current_theme()
    except Exception:    try:
        theme = {}
st.sidebar.divider()
    try:nputs(st.sidebar)
        symbol_for_ai = st.session_state.get("symbol")as e:
        if not symbol_for_ai and st.session_state.get("selected_bot"):"Erro no sidebar: {e}")
            try:
                sess = db_sessions_by_id.get(str(st.session_state.get("selected_bot")))epare theme and semaphore snapshot for rendering in the main layout
                symbol_for_ai = sess.get("symbol") if sess else None
            except Exception:
                symbol_for_ai = Nonetion:

        snapshot = _get_strategy_snapshot_cached(str(symbol_for_ai)) if symbol_for_ai else None
    except Exception:
        snapshot = Nonetate.get("symbol")
        if not symbol_for_ai and st.session_state.get("selected_bot"):
    # adjust columns so the right column fills all remaining space responsively
    # use a very large relative ratio for the right column so it expands to fill the frame= db_sessions_by_id.get(str(st.session_state.get("selected_bot")))
    # PAINEL DE CONTROLE (empilhado acima dos bots ativos)for_ai = sess.get("symbol") if sess else None
    # Theme selector: render inside Streamlit sidebar menu (expander)            except Exception:
    try:
        exp = st.sidebar.expander("🎨 Tema do Terminal", expanded=False)
        render_theme_selector(ui=exp, key_suffix="_dashboard")l_for_ai)) if symbol_for_ai else None
    except Exception:
        try:snapshot = None
            render_theme_selector(ui=st.sidebar, key_suffix="_sidebar")
        except Exception:pace responsively
            passe relative ratio for the right column so it expands to fill the frame
 DE CONTROLE (empilhado acima dos bots ativos)
    st.subheader("🚀 Bot Control")
    col1, col2 = st.columns(2)
    with col1:.sidebar.expander("🎨 Tema do Terminal", expanded=False)
        start_real = st.button("▶️ START (REAL)", type="primary", key="start_real")        render_theme_selector(ui=exp, key_suffix="_dashboard")
    with col2:
        kill_bot = st.button("🛑 KILL BOT", type="secondary", key="kill_bot")
    start_dry = st.button("🧪 START (DRY-RUN)", key="start_dry")nder_theme_selector(ui=st.sidebar, key_suffix="_sidebar")
    num_bots = st.session_state.get("num_bots", 1)
ss
    # STATUS + RESTANTE DO DASHBOARD
    with _safe_container(border=True):
        st.subheader("📋 Status")
        selected_bot_txt = st.session_state.get("selected_bot")    with col1:
        api_port_txt = st.session_state.get("_api_port")TART (REAL)", type="primary", key="start_real")
        st.caption(
            f"Bot selecionado: {str(selected_bot_txt)[:12] + '…' if selected_bot_txt else '(nenhum)'} | "KILL BOT", type="secondary", key="kill_bot")
            f"API local: {api_port_txt if api_port_txt else '(indisponível)'}")
        )

        # Semáforo de estratégia (restaurado ao centro do dashboard)
        try:
            if snapshot:t.subheader("📋 Status")
                components.html(render_strategy_semaphore(snapshot, theme), height=95)        selected_bot_txt = st.session_state.get("selected_bot")
        except Exception:
            passaption(
onado: {str(selected_bot_txt)[:12] + '…' if selected_bot_txt else '(nenhum)'} | "
    with _safe_container(border=True):
        st.subheader("📰 Lançamentos de Carteiras (RSS)")
        if render_wallet_releases_widget is None:
            st.caption("RSS indisponível (módulo não carregou).")        # Semáforo de estratégia (restaurado ao centro do dashboard)
        else:
            # Compact + scrollable + autorefresh (real-time-ish)
            render_wallet_releases_widget(emaphore(snapshot, theme), height=95)
                theme,
                height_px=210,ass
                limit=18,
                refresh_ms=30000,
                key="dash_wallet_rss",📰 Lançamentos de Carteiras (RSS)")
            )ses_widget is None:
SS indisponível (módulo não carregou).")
    # --- Sincroniza lista de bots ativos com DB e processos vivos ---
    try:utorefresh (real-time-ish)
        db_sync = DatabaseManager()ender_wallet_releases_widget(
        db_bots = db_sync.get_active_bots() or []                theme,
        active_bots = []
        for sess in db_bots:        limit=18,
            pid = sess.get('pid')
            if pid:
                try:
                    os.kill(int(pid), 0)
                    active_bots.append(sess.get('id'))s ativos com DB e processos vivos ---
                except Exception:
                    # Se o processo não está vivo, marca como paradotabaseManager()
                    db_sync.update_bot_session(sess.get('id'), {"status": "stopped", "end_ts": time.time()})s() or []
        st.session_state.active_bots = active_bots
    except Exception:
        pass

    # Fallback: if DB shows nothing active, attempt to discover running bots via
    # controller in-memory registry and live subprocess table (best-effort).s.kill(int(pid), 0)
    try:        active_bots.append(sess.get('id'))
        if not st.session_state.active_bots:                except Exception:
            ctrl = st.session_state.get('controller') or (controller if 'controller' in globals() else None) or get_global_controller()
            discovered = []topped", "end_ts": time.time()})
            # 1) Check controller.processes (Popen objects)st.session_state.active_bots = active_bots
            try:
                for bid, proc in getattr(ctrl, 'processes', {}).items():
                    try:
                        if proc is not None and proc.poll() is None:over running bots via
                            discovered.append(str(bid)) in-memory registry and live subprocess table (best-effort).
                    except Exception:
                        continuen_state.active_bots:
            except Exception: if 'controller' in globals() else None) or get_global_controller()
                pass
cesses (Popen objects)
            # 2) Check registry (may have pid or proc)
            try: in getattr(ctrl, 'processes', {}).items():
                if hasattr(ctrl, 'registry') and ctrl.registry is not None:try:
                    for bid in ctrl.registry.list_active_bots().keys():                        if proc is not None and proc.poll() is None:
                        if bid not in discovered:)
                            discovered.append(bid)    except Exception:
            except Exception:
                pass

            # 3) ps scan as a last resort (look for bot_core.py) — use cached scanner
            try:ry (may have pid or proc)
                out = _ps_scan_cached()
                for line in out[1:]:                if hasattr(ctrl, 'registry') and ctrl.registry is not None:
                    if 'bot_core.py' in line:
                        try:        if bid not in discovered:
                            pid_s, args_s = line.strip().split(None, 1)append(bid)
                            argv = shlex.split(args_s)
                            if '--bot-id' in argv:
                                idx = argv.index('--bot-id')
                                bot_id = argv[idx+1]cached scanner
                                if bot_id and bot_id not in discovered:
                                    discovered.append(bot_id)
                        except Exception:
                            continue
            except Exception:
                passt(None, 1)
split(args_s)
            if discovered:t-id' in argv:
                # Merge discovered into session state preserving order   idx = argv.index('--bot-id')
                for b in discovered:            bot_id = argv[idx+1]
                    if b not in st.session_state.active_bots:                                if bot_id and bot_id not in discovered:
                        st.session_state.active_bots.append(b)          discovered.append(bot_id)
    except Exception:
        pass

    with _safe_container(border=True):
        active_bots = st.session_state.active_bots
        if active_bots:if discovered:
            st.subheader(f"🤖 Bots Ativos ({len(active_bots)})")                # Merge discovered into session state preserving order

            # Selection + one-shot hard kill (-9) for chosen botsctive_bots:
            kill_sel_key = "_kill_sel_bots" st.session_state.active_bots.append(b)
            if kill_sel_key not in st.session_state:
                st.session_state[kill_sel_key] = {}        pass

            top_cols = st.columns([3.2, 1.0])
            with top_cols[0]:
                st.caption("Marque os bots e use o botão à direita para SIGKILL (-9).")
            with top_cols[1]:            st.subheader(f"🤖 Bots Ativos ({len(active_bots)})")
                selected_now = [
                    b-shot hard kill (-9) for chosen bots
                    for b in list(active_bots)
                    if bool(st.session_state.get(f"sel_kill_{b}", False))ot in st.session_state:
                ][kill_sel_key] = {}
                try:
                    clicked_kill_selected = st.button(
                        f"🛑 Kill -9 ({len(selected_now)})",
                        key="kill_selected_3",t.caption("Marque os bots e use o botão à direita para SIGKILL (-9).")
                        type="secondary",_cols[1]:
                        use_container_width=True,
                        disabled=(len(selected_now) == 0),
                    )
                except TypeError:ate.get(f"sel_kill_{b}", False))
                    clicked_kill_selected = st.button(
                        f"🛑 Kill -9 ({len(selected_now)})",
                        key="kill_selected_3",licked_kill_selected = st.button(
                        type="secondary", -9 ({len(selected_now)})",
                        use_container_width=True,
                    )
ue,
            if clicked_kill_selected:ected_now) == 0),
                selected = [
                    bt TypeError:
                    for b in list(active_bots)                    clicked_kill_selected = st.button(
                    if bool(st.session_state.get(f"sel_kill_{b}", False))({len(selected_now)})",
                ]"kill_selected_3",
                if not selected:   type="secondary",
                    st.warning("Nenhum bot selecionado para Kill -9.")ue,
                else:
                    killed_any = False
                    killed_ids: list[str] = []cted:
                    for bot_id in selected:
                        killed = False
ve_bots)
                        # Busca detalhes completos do botet(f"sel_kill_{b}", False))
                        sess = db_sessions_by_id.get(str(bot_id))
                        bot_info = controller.registry.get_bot_info(bot_id)
                    st.warning("Nenhum bot selecionado para Kill -9.")
                        pid = None
                        try:
                            pid = (
                                (sess.get("pid") if sess else None)                    for bot_id in selected:
                                or (bot_info.get("pid") if bot_info else None)alse
                                or ps_pids_by_id.get(str(bot_id))
                            )alhes completos do bot
                        except Exception:
                            pid = None

                        # Ask controller to stop first (best-effort) None
                        try:
                            controller.stop_bot(str(bot_id))
                        except Exception:                                (sess.get("pid") if sess else None)
                            passelse None)
    or ps_pids_by_id.get(str(bot_id))
                        # Force SIGKILL by PID if available
                        if pid is not None:
                            try:= None
                                killed = _kill_pid_sigkill_only(int(pid))
                            except Exception as e:t-effort)
                                st.error(f"Erro ao dar Kill -9 em {str(bot_id)[:8]} (PID {pid}): {e}")
                                killed = Falseroller.stop_bot(str(bot_id))
                        else:
                            st.warning(f"PID não encontrado para bot {str(bot_id)[:8]}")

                            try: if available
                                DatabaseManager().update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})d is not None:
                            except Exception:
                                pass                                killed = _kill_pid_sigkill_only(int(pid))
pt Exception as e:
                            try:
                                DatabaseManager().release_bot_quota(str(bot_id))e
                            except Exception:
                                pass                            st.warning(f"PID não encontrado para bot {str(bot_id)[:8]}")

                            try:
                                if bot_id in st.session_state.active_bots:er().update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
                                    st.session_state.active_bots = [b for b in st.session_state.active_bots if b != bot_id]xception:
                                if st.session_state.get("selected_bot") == bot_id:                                pass
                                    st.session_state.selected_bot = None
                            except Exception:
                                pass

                            # Clear selection checkbox state for removed bot
                            try:
                                st.session_state[f"sel_kill_{bot_id}"] = False
                            except Exception:                                if bot_id in st.session_state.active_bots:
                                passin st.session_state.active_bots if b != bot_id]
if st.session_state.get("selected_bot") == bot_id:
                            if killed:
                                killed_any = True
                                killed_ids.append(str(bot_id))

                        if killed_any:lection checkbox state for removed bot
                            st.success(f"Kill -9 aplicado em {len(killed_ids)} bot(s).")
                            # st.rerun()  # Removido para evitar reload desnecessárioot_id}"] = False
                            except Exception:
            header_cols = st.columns([2.0, 1.8, 1.0, 3.5, 0.8, 1.5])
            header_cols[0].markdown("**🆔 Bot ID**")
            header_cols[1].markdown("**📊 Símbolo**")
            header_cols[2].markdown("**⚙️ Modo**")                                killed_any = True
            header_cols[3].markdown("**📝 Último Evento**")
            header_cols[4].markdown("**✅ Sel.**")
            header_cols[5].markdown("**📜 Log**")
plicado em {len(killed_ids)} bot(s).")
            db_for_logs = DatabaseManager()vitar reload desnecessário
            target_pct_global = st.session_state.get("target_profit_pct", 2.0)
.0, 3.5, 0.8, 1.5])
            for bot_id in list(active_bots):            header_cols[0].markdown("**🆔 Bot ID**")
                # Busca detalhes completos do botímbolo**")
                sess = db_sessions_by_id.get(str(bot_id))
                bot_info = controller.registry.get_bot_info(bot_id)            header_cols[3].markdown("**📝 Último Evento**")
                symbol = (bot_info.get('symbol') if bot_info else None) or (sess.get('symbol') if sess else None) or 'N/A'.**")
                mode = (bot_info.get('mode') if bot_info else None) or (sess.get('mode') if sess else None) or 'N/A'

                # Buscar último evento dos logs
                last_event = "Sem eventos"
                try:
                    logs = db_for_logs.get_bot_logs(bot_id, limit=1)            for bot_id in list(active_bots):
                    if logs:ot
                        last_log = logs[0]et(str(bot_id))
                        msg = last_log.get('message', '')info = controller.registry.get_bot_info(bot_id)
                        ts = last_log.get('timestamp', '')ne) or (sess.get('symbol') if sess else None) or 'N/A'
                        # Tentar extrair event do JSON, senão usar mensagem truncadainfo.get('mode') if bot_info else None) or (sess.get('mode') if sess else None) or 'N/A'
                        try:
                            import json as _json
                            data = _json.loads(msg)
                            if 'event' in data:
                                msg = data['event'].upper().replace('_', ' ')b_for_logs.get_bot_logs(bot_id, limit=1)
                            elif len(msg) > 40:
                                msg = msg[:40] + "..."
                        except Exception:sage', '')
                            if len(msg) > 40:
                                msg = msg[:40] + "..."do JSON, senão usar mensagem truncada
                        # Converter timestamp float para string se necessário
                        if isinstance(ts, (int, float)):s _json
                            try:s(msg)
                                from datetime import datetime
                                ts = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                            except Exception:
                                ts = str(ts)msg = msg[:40] + "..."
                        ts_short = str(ts)[:19] if ts else ''
                        last_event = f"{ts_short} - {msg}" if ts_short else msg
                except Exception:] + "..."
                    passp float para string se necessário

                # Compute progress toward target profit based on recent logs (cached)
                cache_key = f"progress_{bot_id}"rom datetime import datetime
                if cache_key not in st.session_state or st.session_state.get(f"{cache_key}_time", 0) < time.time() - 5:  # Cache for 5 seconds        ts = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    progress_value = 0.0                            except Exception:
                    profit_pct_value = 0.0
                    try:if ts else ''
                        logs = db_for_progress.get_bot_logs(bot_id, limit=30)
                        current_price = 0.0
                        entry_price = 0.0
                        for log in logs:
                            msg = (log.get('message') or "")(cached)
                            try:_id}"
                                import json as _jsonssion_state or st.session_state.get(f"{cache_key}_time", 0) < time.time() - 5:  # Cache for 5 seconds
                                data = _json.loads(msg)
                                if 'price' in data and data['price'] is not None:
                                    current_price = float(data['price']);
                                if 'entry_price' in data and data['entry_price'] is not None:ot_logs(bot_id, limit=30)
                                    entry_price = float(data['entry_price']);
                            } catch (e) {
                                console.error("JSON parse error:", e);
                            }

                        if entry_price > 0 && current_price > 0 {s _json
                            profit_pct_value = ((current_price - entry_price) / entry_price) * 100;json.loads(msg)
                        }                                if 'price' in data and data['price'] is not None:
                        if target_pct_global && float(target_pct_global) > 0 {rice'])
                            progress_value = min(1.0, max(0.0, (profit_pct_value / float(target_pct_global))));
                        }
                    } catch (e) {
                        console.error("Error computing progress:", e);nue
                    }
                    st.session_state[cache_key] = (progress_value, profit_pct_value);
                    st.session_state[f"{cache_key}_time"] = time.time();price) / entry_price) * 100
                } else {   if target_pct_global and float(target_pct_global) > 0:
                    progress_value, profit_pct_value = st.session_state[cache_key]; float(target_pct_global))))
                }                    except Exception:

                # Determine if this session/bot is a dry-run to adjust visualsst.session_state[cache_key] = (progress_value, profit_pct_value)
                try:[f"{cache_key}_time"] = time.time()
                    dry_flag = false;
                    try {
                        dry_flag = bool(int((sess.get("dry_run") if sess is not None else None) || 0) == 1);
                    } catch (e) {ion/bot is a dry-run to adjust visuals
                        console.error("Error determining dry_run flag:", e);
                        dry_flag = false;
                    }
                    try {ol(int((sess.get("dry_run") if sess is not None else None) or 0) == 1)
                        if (!dry_flag && bot_info) {
                            dry_flag = bool(int((bot_info.get("dry_run") if bot_info is not None else None) || 0) == 1);                        dry_flag = False
                        }
                    } catch (e) {
                        console.error("Error determining dry_run flag from bot_info:", e);    dry_flag = bool(int((bot_info.get("dry_run") if bot_info is not None else None) or 0) == 1)
                        dry_flag = false;
                    }str(bot_id)[:12])
                } catch (e) {
                    dry_flag = false;
                }or dry)

                row = st.columns([2.0, 1.8, 1.0, 3.5, 0.8, 1.5]);
                // Render bot id with a colored badge depending on dry-run status
                try {e-block;padding:6px 8px;border-radius:6px;'
                    if (dry_flag) {                            f'background:rgba(255,255,255,0.02);color:{mode_color};font-weight:700;' 
                        badge_html = (mode).upper()}</div>'
                            f'<div style="background:#0b1220;color:#f8f8f2;padding:6px;border-radius:6px;'
                            f'border-left:4px solid #f59e0b;font-family:monospace;font-weight:700">{str(bot_id)[:12]}… 'html=True)
                            f'<span style="color:#ffd166;font-size:0.85em;margin-left:8px;font-weight:600">DRY</span></div>'pt Exception:
                        );
                    } else {
                        badge_html = (ório (HTML) in a NEW TAB.
                            f'<div style="background:#071329;color:#c9d1d9;padding:6px;border-radius:6px;' (works in VS Code/remote too).
                            f'border-left:4px solid #22c55e;font-family:monospace;font-weight:700">{str(bot_id)[:12]}…</div>'et("_api_port")
                        );
                    }ot api_port and 'start_api_server' in globals():
                    row[0].markdown(badge_html, unsafe_allow_html=True);tart_api_server(8765)
                } catch (e) {
                    row[0].write(str(bot_id)[:12]);                                st.session_state["_api_port"] = int(p)
                }

                row[1].write(symbol);    pass
                // Mode rendered as a colored badge (green for real, amber for dry):
                try {
                    mode_color = "#f59e0b" if dry_flag else "#22c55e";
                    mode_html = (
                        f'<div style="display:inline-block;padding:6px 8px;border-radius:6px;'
                        f'background:rgba(255,255,255,0.02);color:{mode_color};font-weight:700;'
                        f'font-family:monospace">{str(mode).upper()}</div>'y_flag:
                    );
                    row[2].markdown(mode_html, unsafe_allow_html=True);
                } catch (e) {
                    row[2].write(str(mode).upper());   f'<span style="color:#ffd166;font-size:0.85em;margin-left:8px;font-weight:600">DRY</span></div>'
                }

                // Coluna 3: Último Evento
                row[3].caption(last_event);                            f'<div style="background:#071329;color:#c9d1d9;padding:6px;border-radius:6px;'
-left:4px solid #22c55e;font-family:monospace;font-weight:700">{str(bot_id)[:12]}…</div>'
                // Selection checkbox
                with row[4]:row[0].markdown(badge_html, unsafe_allow_html=True)
                    st.checkbox(
                        "Selecionar",str(bot_id)[:12])
                        key=f"sel_kill_{bot_id}",
                        label_visibility="collapsed",
                    );or dry)

                // Coluna 5: Link para Log
                api_port = st.session_state.get("_api_port");
                try {e-block;padding:6px 8px;border-radius:6px;'
                    if (!api_port && 'start_api_server' in globals()) {                        f'background:rgba(255,255,255,0.02);color:{mode_color};font-weight:700;'
                        p = start_api_server(8765);ospace">{str(mode).upper()}</div>'
                        if (p) {
                            st.session_state["_api_port"] = int(p);                    row[2].markdown(mode_html, unsafe_allow_html=True)
                            api_port = int(p);
                        }rite(str(mode).upper())
                    }
                } catch (e) {ento
                    console.error("Error starting API server:", e);
                }
ection checkbox
                with row[5]:                with row[4]:
                    if (api_port) {
                        // ╔═══════════════════════════════════════════════════════════════════════════════╗
                        // ║  🔒 HOMOLOGADO: URLs dinâmicas + Botões Log/Report em sessões encerradas      ║    key=f"sel_kill_{bot_id}",
                        // ║  Data: 2026-01-02 | Sessão: fix-link-button-target-blank                      ║
                        // ╚═══════════════════════════════════════════════════════════════════════════════╝
                        is_production = bool(os.environ.get("FLY_APP_NAME"));
                        base = "" if is_production else f"http://127.0.0.1:{int(api_port)}";
                        try {et("_api_port")
                            st_port = int(st.get_option("server.port"));
                        } catch (e) {ot api_port and 'start_api_server' in globals():
                            st_port = 8501;                        p = start_api_server(8765)
                        }:
                        home_url = "/?view=dashboard" if is_production : f"http://127.0.0.1:{st_port}/?view=dashboard";ession_state["_api_port"] = int(p)
                        home_val = urllib.parse.quote(home_url, safe='');

                        log_url = (
                            `${{base}}/monitor?${{theme_query}}&home=${{home_val}}&bot=${{encodeURIComponent(str(bot_id))}}`
                            : `${{base}}/monitor?home=${{home_val}}&bot=${{encodeURIComponent(str(bot_id))}}`
                        );
                        rep_url = (══════════════════════════════════════════════════════════════════════════════╗
                            `${{base}}/report?${{theme_query}}&home=${{home_val}}&bot=${{encodeURIComponent(str(bot_id))}}`URLs dinâmicas                     ║
                            : `${{base}}/report?home=${{home_val}}&bot=${{encodeURIComponent(str(bot_id))}}`1-02 | Sessão: fix-link-button-target-blank                      ║
                        );════════════════════════════════════════════════════════════════╝

                        c_log.markdown(.1:{int(api_port)}"
                            f'''
                            <a href="{log_url}" target="_blank" rel="noopener noreferrer"    st_port = int(st.get_option("server.port"))
                               style="display:inline-flex;align-items:center;justify-content:center;ption:
                                      width:100%;padding:0.25rem 0.5rem;border-radius:0.5rem;
                                      min-height:2rem;text-decoration:none;font-size:0.85rem;=dashboard" if is_production else f"http://127.0.0.1:{st_port}/?view=dashboard"
                                      background-color:rgb(19,23,32);color:rgb(250,250,250);
                                      border:1px solid rgba(250,250,250,0.2);">heme_query = str(theme_qs).lstrip('&')
                                    📜 LOG
                            </a>log_url = (
                            ''',id))}"
                            unsafe_allow_html=True,
                        );
                        c_rep.markdown(
                            f'''OLOGADO
                            <a href="{rep_url}" target="_blank" rel="noopener noreferrer"
                               style="display:inline-flex;align-items:center;justify-content:center;═════════════════╗
                                      width:100%;padding:0.25rem 0.5rem;border-radius:0.5rem;      ║
                                      min-height:2rem;text-decoration:none;font-size:0.85rem;            ║
                                      background-color:rgb(19,23,32);color:rgb(250,250,250);═════════════════════════════╝
                                      border:1px solid rgba(250,250,250,0.2);">
                                    📑 REL.
                            </a>log_url}" target="_blank" rel="noopener noreferrer"
                            ''',tyle="display:inline-flex;align-items:center;justify-content:center;
                            unsafe_allow_html=True,      width:100%;padding:0.25rem 0.75rem;border-radius:0.5rem;
                        );5rem;text-decoration:none;
                        // 🔒 FIM HOMOLOGADO             background-color:rgb(19,23,32);color:rgb(250,250,250);
r:1px solid rgba(250,250,250,0.2);font-weight:400;">
                    } else {       📜 Log
                        st.caption("off");
                    }        ''',
                try {
                    pct_color = "#f59e0b" if dry_flag else "#22c55e";
                    row[5].markdown(
                        `<div style='color:${{pct_color}};font-weight:700'>${{profit_pct_value:+.2f}}% / alvo ${{float(target_pct_global):.2f}}%</div>`,
                        unsafe_allow_html=True,   st.caption("off")
                    );
                } catch (e) {
                    row[5].caption(f"{profit_pct_value:+.2f}% / alvo {float(target_pct_global):.2f}%");       row[5].markdown(
                } / alvo {float(target_pct_global):.2f}%</div>",
            }                        unsafe_allow_html=True,

    # =====================================================
    # TRATAMENTO DOS BOTÕESit_pct_value:+.2f}% / alvo {float(target_pct_global):.2f}%")
    # =====================================================
    if start_real or start_dry:nfo("🚦 Nenhum bot ativo. Use os controles à esquerda para iniciar um novo bot.")
        try:
            if not st.session_state.get("controller"):        with _safe_container(border=True):
                st.error("Controller não disponível. Tente recarregar a página.")ões com end_ts dentro do dia atual)
                return
            
            # Obter parâmetros do session_state
            symbol = st.session_state.get("symbol", "BTC-USDT")                import datetime as _dt
            entry = st.session_state.get("entry", 0.0)
            mode = st.session_state.get("mode", "sell")
            targets = st.session_state.get("targets", "1:0.3,3:0.5,5:0.2")ar, now.month, now.day)
            interval = st.session_state.get("interval", 5.0)tart_day.timestamp())
            size = st.session_state.get("size", 0.0006)= start_ts + 86400.0
            funds = st.session_state.get("funds", 20.0)
            reserve_pct = st.session_state.get("reserve_pct", 50.0)nager()
            eternal_mode = st.session_state.get("eternal_mode", False)
            num_bots = st.session_state.get("num_bots", 1)r()
            
            # Iniciar múltiplos bots se num_bots > 1
            started_bots = [];d, status, pid, symbol, mode, entry_price, start_ts, end_ts, dry_run
            for (let i = 0; i < num_bots; i++) {{ bot_sessions
                try {{us, '') != 'running'
                    // Pequena variação nos parâmetros para bots múltiplos     AND end_ts IS NOT NULL
                    let varied_entry = parseFloat(entry) * (1 + (i * 0.001));  // Variação de 0.1% por bot
                    let varied_size = parseFloat(size) * (1 + (i * 0.01));    // Variação de 1% no size                    ORDER BY COALESCE(end_ts, 0) DESC
                    
                    let bot_id_started = st.session_state.controller.start_bot(
                        symbol, varied_entry, mode, targets,ts, end_ts),
                        parseFloat(interval), varied_size, parseFloat(funds), start_dry,
                        eternal_mode=eternal_mode,r) for r in (cur_today.fetchall() or [])]
                    );
                    trades) para mostrar no progresso
                    started_bots.push(bot_id_started);in stopped_today if s.get("id")]

                    // Adiciona à lista de bots ativos",".join(["?"] * len(bot_ids))
                    if (bot_id_started not in st.session_state.active_bots) {{
                        st.session_state.active_bots.append(bot_id_started);
                    }}CT bot_id,
                     AS trades,
                }} catch (bot_error) {{          COALESCE(SUM(COALESCE(profit,0)),0) AS profit_sum
                    st.warning(`Erro ao iniciar bot ${i+1}: ${bot_error}`);
                    continue;d IN ({placeholders})
                }}
            }}

            if (started_bots.length > 0) {{                    )
                st.session_state.selected_bot = started_bots[0];  // Seleciona o primeirofor r in (cur_today.fetchall() or []):
                st.session_state.bot_running = true;
                // Não bloquear o render: não usar sleep aqui(d.get("bot_id") or "")
                // Navegar para o monitor (mesma aba) após iniciarif bid:
                _merge_query_params({"bot": started_bots[0], "view": "monitor"});rade_agg_today[bid] = d
                let bot_count = started_bots.length;
                st.success(`✅ ${bot_count} bot${bot_count > 1 ? 's' : ''} iniciado${bot_count > 1 ? 's' : ''}! Abrindo Monitor na mesma aba.`);
                // st.rerun()  // Removido para evitar reload desnecessário                    conn_today.close()
            }} else {{
                st.error("Falha ao iniciar todos os bots.");                    pass
            }}
        } catch (e) {{
            st.error(`Erro ao iniciar bots: ${e}`);
        }}
n(stopped_today)})")
    # =====================================================
    # TELA PRINCIPAL7, 1.4, 1.7])
    # =====================================================            header_cols[0].markdown("**🆔 Bot ID**")
    # Aqui só chegamos se NÃO estivermos em modo janelawn("**📊 Símbolo**")

    # Footer com versãor_cols[3].markdown("**📑 Relatório**")
    st.markdown("---")
    st.markdown(            header_cols[5].markdown("**📈 Progresso**")
        f"<div style='text-align: center; color: #666; font-size: 0.8em;'>{get_version()} - AutoCoinBot</div>",
        unsafe_allow_html=True
    )aption("Nenhum bot encerrado hoje.")

    st.markdown(
        f"<div style='text-align: center; color: #666; font-size: 0.8em;'>{get_version()} - AutoCoinBot</div>",
        unsafe_allow_html=True
    )

