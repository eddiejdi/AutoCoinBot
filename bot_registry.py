# bot_registry.py

from typing import Dict, Optional
import subprocess
import time


class BotRegistry:
    def __init__(self):
        # _bots stores entries keyed by bot_id with keys: config, pid, proc (optional), start_time
        self._bots: Dict[str, Dict] = {}

    def register_bot(self, bot_id: str, config: dict, proc_or_pid):
        # Accept either a subprocess.Popen or a pid integer
        proc = None
        pid = None
        try:
            if hasattr(proc_or_pid, "poll"):
                proc = proc_or_pid
                pid = getattr(proc_or_pid, "pid", None)
            else:
                pid = int(proc_or_pid) if proc_or_pid is not None else None
        except Exception:
            pid = proc_or_pid

        self._bots[bot_id] = {
            "config": config,
            "pid": pid,
            "proc": proc,
            "start_time": time.time(),
        }

    def unregister_bot(self, bot_id: str):
        self._bots.pop(bot_id, None)


    def get_bot_info(self, bot_id: str) -> Optional[Dict]:
        return self._bots.get(bot_id)

    def get_process(self, bot_id: str) -> Optional[subprocess.Popen]:
        info = self._bots.get(bot_id)
        if not info:
            return None
        return info.get("proc")

    def is_bot_running(self, bot_id: str) -> bool:
        proc = self.get_process(bot_id)
        return proc is not None and proc.poll() is None

    def list_active_bots(self):
        alive = {}
        for bot_id, info in list(self._bots.items()):
            proc = info.get("proc")
            if proc is not None:
                try:
                    if proc.poll() is None:
                        alive[bot_id] = info
                        continue
                    else:
                        # process finished; remove from registry
                        self._bots.pop(bot_id, None)
                        continue
                except Exception:
                    # fall through to pid-based check
                    pass

            # Fallback: check by pid if no proc object
            pid = info.get("pid")
            if pid is not None:
                try:
                    pid_i = int(pid)
                    if pid_i > 0:
                        try:
                            import os

                            os.kill(pid_i, 0)
                            alive[bot_id] = info
                        except Exception:
                            self._bots.pop(bot_id, None)
                except Exception:
                    # unknown pid value: remove for safety
                    self._bots.pop(bot_id, None)

        return alive

