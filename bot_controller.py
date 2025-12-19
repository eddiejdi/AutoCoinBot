# bot_controller.py
# Responsável por iniciar, parar e monitorar bots
# Compatível com Streamlit + múltiplas abas

import subprocess
import sys
import uuid
import time
from pathlib import Path
from typing import Dict

from .bot_registry import BotRegistry
from .database import DatabaseManager

ROOT = Path(__file__).resolve().parent
BOT_CORE = ROOT / "bot_core.py"


class BotController:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.registry = BotRegistry()

    def start_bot(
                    self,
                    symbol,
                    entry,
                    mode,
                    targets,
                    interval,
                    size,
                    funds,
                    dry,
                    reserve_pct=50.0,
                    target_profit_pct=2.0,
                    eternal_mode=False,
                ):
        bot_id = f"bot_{uuid.uuid4().hex[:8]}"

        cmd = [
            sys.executable,
            "-u",
            str(BOT_CORE),
            "--bot-id", bot_id,
            "--symbol", symbol,
            "--entry", str(entry),
            "--mode", mode,
            "--targets", targets,
            "--interval", str(interval),
            "--size", str(size),
            "--funds", str(funds),
            "--reserve-pct", str(reserve_pct),
            "--target-profit-pct", str(target_profit_pct),
        ]

        if dry:
            cmd.append("--dry")
        
        if eternal_mode:
            cmd.append("--eternal")

        print("[BOT_CONTROLLER]", " ".join(cmd), flush=True)

        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.processes[bot_id] = proc

        # ✅ Registrar no bot_registry (em memória)
        self.registry.register_bot(
            bot_id,
            {
                "symbol": symbol,
                "entry": entry,
                "mode": mode,
                "targets": targets,
                "interval": interval,
                "size": size,
                "funds": funds,
                "dry": dry,
                "reserve_pct": reserve_pct,
                "target_profit_pct": target_profit_pct,
                "eternal_mode": eternal_mode,
            },
            proc.pid,
        )

        # ✅ Registrar no banco de dados (persistência)
        try:
            db = DatabaseManager()
            db.insert_bot_session({
                "id": bot_id,
                "pid": proc.pid,
                "symbol": symbol,
                "mode": mode,
                "entry_price": entry,
                "targets": targets,
                "size": size,
                "funds": funds,
                "start_ts": time.time(),
                "dry_run": dry,
                "reserve_pct": reserve_pct,
                "target_profit_pct": target_profit_pct,
            })
        except Exception as e:
            print(f"[BOT_CONTROLLER] Erro ao registrar sessão no DB: {e}", flush=True)

        print(f"[BOT_CONTROLLER] Bot {bot_id} iniciado com PID {proc.pid} (Reserve: {reserve_pct}%, Lucro: {target_profit_pct}%)", flush=True)

        return bot_id


    def stop_bot(self, bot_id: str):
        proc = self.processes.get(bot_id)
        if proc:
            proc.terminate()
            self.processes.pop(bot_id, None)
            self.registry.unregister_bot(bot_id)

    def is_running(self, bot_id: str) -> bool:
        proc = self.processes.get(bot_id)
        return proc is not None and proc.poll() is None

