#!/usr/bin/env python3
"""Stop all active bots recorded in the DB and in bot_registry.json.

This script attempts a best-effort graceful termination (SIGTERM), then SIGKILL if needed.
It also updates `bot_sessions` status to 'stopped' in the DB where possible.
"""
import os
import signal
import time
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from database import DatabaseManager


def kill_pid(pid: int):
    try:
        os.kill(pid, signal.SIGTERM)
    except Exception:
        pass
    # wait briefly
    time.sleep(0.3)
    try:
        os.kill(pid, 0)
        # still alive -> SIGKILL
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    except Exception:
        # process not found
        return


def main():
    db = DatabaseManager()
    active = db.get_active_bots() or []
    if not active:
        print("No active bot sessions found in DB.")
    else:
        print(f"Found {len(active)} active sessions; attempting to stop...")
    for sess in active:
        bot_id = sess.get('id') or sess.get('bot_id')
        pid = sess.get('pid')
        try:
            pid_i = int(pid) if pid is not None else None
        except Exception:
            pid_i = None
        if pid_i:
            print(f"Stopping bot {bot_id} (PID {pid_i})...")
            kill_pid(pid_i)
            try:
                db.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
            except Exception:
                pass
            print(f"Stopped {bot_id}")
        else:
            print(f"No PID for bot {bot_id}; marking as stopped in DB")
            try:
                db.update_bot_session(bot_id, {"status": "stopped", "end_ts": time.time()})
            except Exception:
                pass

    # Also try to kill any processes named bot_core.py found in ps that match active ids
    try:
        import subprocess
        r = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True)
        out = (r.stdout or "").splitlines()
        for line in out[1:]:
            if "bot_core.py" in line:
                parts = line.strip().split(None, 1)
                if not parts:
                    continue
                try:
                    pid = int(parts[0])
                except Exception:
                    continue
                # best-effort kill
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.1)
                except Exception:
                    pass
    except Exception:
        pass

    print("Stop attempt complete.")


if __name__ == '__main__':
    main()
