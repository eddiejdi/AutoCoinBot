# bot_controller.py
# Responsável por iniciar, parar e monitorar bots
# Compatível com Streamlit + múltiplas abas

import subprocess
import sys
import uuid
import time
import threading
import weakref
import re
from pathlib import Path
from typing import Dict

from .bot_registry import BotRegistry
from .database import DatabaseManager

ROOT = Path(__file__).resolve().parent
BOT_CORE = ROOT / "bot_core.py"

_ALL_CONTROLLERS: "weakref.WeakSet[BotController]" = weakref.WeakSet()


class BotController:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.registry = BotRegistry()
        # Modo contínuo: mapeia bot_id atual -> stop_event do grupo
        self._continuous_stop: Dict[str, threading.Event] = {}

        try:
            _ALL_CONTROLLERS.add(self)
        except Exception:
            pass

    @classmethod
    def stop_all_continuous(cls):
        """Best-effort: stop all continuous-mode runner threads in this process."""
        for controller in list(_ALL_CONTROLLERS):
            try:
                cont = getattr(controller, "_continuous_stop", None)
                if isinstance(cont, dict) and cont:
                    for _, ev in list(cont.items()):
                        try:
                            ev.set()
                        except Exception:
                            pass
                    try:
                        cont.clear()
                    except Exception:
                        pass
            except Exception:
                pass

    def _start_one(
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
        continuous_mode=False,
    ):
        """Inicia um único processo de bot e registra no DB."""
        bot_id = f"bot_{uuid.uuid4().hex[:8]}"

        # Normalize targets to avoid accidental newlines/whitespace breaking parsing.
        try:
            targets = re.sub(r"\s+", "", str(targets or ""))
        except Exception:
            targets = str(targets or "")

        cmd = [
            sys.executable,
            "-u",
            str(BOT_CORE),
            "--bot-id", bot_id,
            "--symbol", symbol,
            "--entry", str(entry),
            "--mode", mode,
            # Use = form so values that start with '-' (negative targets) are parsed correctly.
            f"--targets={targets}",
            "--interval", str(interval),
            "--size", str(size),
            "--funds", str(funds),
            "--reserve-pct", str(reserve_pct),
            "--target-profit-pct", str(target_profit_pct),
        ]

        if dry:
            cmd.append("--dry")

        # IMPORTANTE: modo contínuo NÃO usa --eternal interno do bot
        # (ele termina e um novo processo é criado com novo ID)

        print("[BOT_CONTROLLER]", " ".join(cmd), flush=True)

        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            # Start in a new session/process-group so the UI can safely kill the bot tree
            # without affecting the Streamlit server.
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.processes[bot_id] = proc

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
                "eternal_mode": bool(continuous_mode),
            },
            proc.pid,
        )

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

        print(
            f"[BOT_CONTROLLER] Bot {bot_id} iniciado com PID {proc.pid} (Reserve: {reserve_pct}%, Lucro: {target_profit_pct}%)",
            flush=True,
        )
        return bot_id

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
        # Normalize targets early so both normal and eternal modes behave consistently.
        try:
            targets = re.sub(r"\s+", "", str(targets or ""))
        except Exception:
            targets = str(targets or "")

        if eternal_mode:
            stop_event = threading.Event()

            first_bot_id = self._start_one(
                symbol,
                entry,
                mode,
                targets,
                interval,
                size,
                funds,
                dry,
                reserve_pct=reserve_pct,
                target_profit_pct=target_profit_pct,
                continuous_mode=True,
            )
            self._continuous_stop[first_bot_id] = stop_event

            def _runner(current_bot_id: str):
                cfg = {
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
                }
                bot_id = current_bot_id
                # Guard against runaway restarts if the bot process exits immediately.
                restart_times: list[float] = []
                while not stop_event.is_set():
                    proc = self.processes.get(bot_id)
                    if proc is None:
                        break
                    # espera o processo terminar
                    while proc.poll() is None and not stop_event.is_set():
                        time.sleep(1.0)
                    if stop_event.is_set():
                        break

                    # Rate-limit restarts: if we restart too frequently, stop instead of spamming.
                    try:
                        now = time.time()
                        restart_times.append(now)
                        window_s = 60.0
                        max_restarts = 5
                        restart_times = [t for t in restart_times if (now - t) <= window_s]
                        if len(restart_times) > max_restarts:
                            print(
                                f"[BOT_CONTROLLER] Eternal-mode restart limit reached for {current_bot_id}. Stopping to avoid loop.",
                                flush=True,
                            )
                            stop_event.set()
                            break
                    except Exception:
                        pass

                    # Backoff a bit to avoid tight restart loops on immediate failures.
                    try:
                        time.sleep(2.0)
                    except Exception:
                        pass

                    # processo acabou: inicia um novo bot com NOVO ID
                    new_bot_id = self._start_one(
                        cfg["symbol"],
                        cfg["entry"],
                        cfg["mode"],
                        cfg["targets"],
                        cfg["interval"],
                        cfg["size"],
                        cfg["funds"],
                        cfg["dry"],
                        reserve_pct=cfg["reserve_pct"],
                        target_profit_pct=cfg["target_profit_pct"],
                        continuous_mode=True,
                    )

                    # move o controle do grupo para o novo bot_id
                    try:
                        self._continuous_stop.pop(bot_id, None)
                    except Exception:
                        pass
                    self._continuous_stop[new_bot_id] = stop_event
                    bot_id = new_bot_id

            t = threading.Thread(target=_runner, args=(first_bot_id,), daemon=True)
            t.start()

            return first_bot_id

        # modo normal (um único bot)
        return self._start_one(
            symbol,
            entry,
            mode,
            targets,
            interval,
            size,
            funds,
            dry,
            reserve_pct=reserve_pct,
            target_profit_pct=target_profit_pct,
            continuous_mode=False,
        )


    def stop_bot(self, bot_id: str):
        # Se for um bot em modo contínuo, parar o loop também
        try:
            ev = self._continuous_stop.get(bot_id)
            if ev is not None:
                ev.set()
                # remove o mapeamento (o runner também tenta remover)
                self._continuous_stop.pop(bot_id, None)
        except Exception:
            pass

        proc = self.processes.get(bot_id)
        if proc:
            try:
                proc.terminate()
            except Exception:
                pass

            # Best-effort wait; then hard kill.
            try:
                proc.wait(timeout=0.8)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    proc.wait(timeout=0.8)
                except Exception:
                    pass

            self.processes.pop(bot_id, None)
            try:
                self.registry.unregister_bot(bot_id)
            except Exception:
                pass

    def is_running(self, bot_id: str) -> bool:
        proc = self.processes.get(bot_id)
        return proc is not None and proc.poll() is None


# Single controller instance shared within a Python process.
# This avoids per-Streamlit-session controllers that cannot stop bots started elsewhere.
_GLOBAL_CONTROLLER: BotController | None = None


def get_global_controller() -> BotController:
    global _GLOBAL_CONTROLLER
    if _GLOBAL_CONTROLLER is None:
        _GLOBAL_CONTROLLER = BotController()
    return _GLOBAL_CONTROLLER

