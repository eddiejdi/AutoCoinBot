# bot_registry.py

from typing import Dict, Optional
import subprocess
import time


class BotRegistry:
    def __init__(self):
        self._bots = {}

    def register_bot(self, bot_id: str, config: dict, pid: int):
        self._bots[bot_id] = {
            "config": config,
            "pid": pid,
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
        return info["proc"]

    def is_bot_running(self, bot_id: str) -> bool:
        proc = self.get_process(bot_id)
        return proc is not None and proc.poll() is None

    def list_active_bots(self):
        alive = {}
        for bot_id, info in list(self._bots.items()):
            proc = info["proc"]
            if proc.poll() is None:
                alive[bot_id] = info
            else:
                self._bots.pop(bot_id, None)
        return alive

