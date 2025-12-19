# bot_core.py
import sys
import json
import time
import logging
import os
from pathlib import Path

# ======================================================
# IMPORT DO BOT — NÃO INVENTA MÓDULO
# ======================================================
try:
    from .bot import EnhancedTradeBot
except ImportError:
    try:
        from bot import EnhancedTradeBot
    except ImportError:
        EnhancedTradeBot = None


#from .utils import parse_targets 


def parse_targets(s: str):
    """
    Converte '2:0.3,5:0.4' em [(2.0, 0.3), (5.0, 0.4)]
    Mantido aqui para evitar dependências inexistentes.
    """
    out = []
    if not s:
        return out

    for part in s.split(","):
        if ":" not in part:
            continue
        a, b = part.split(":", 1)
        try:
            out.append((float(a), float(b)))
        except ValueError:
            continue

    return out


# ======================================================
# LOG SETUP — GRAVA EM SQLITE VIA DATABASE.PY
# ======================================================
class DatabaseLogger:
    """Wrapper que permite usar DatabaseManager como um logger Python"""
    def __init__(self, db_manager, bot_id: str):
        self.db = db_manager
        self.bot_id = bot_id
        self.handlers = []  # Fake handlers para compatibilidade
        self.propagate = False
    
    def setLevel(self, level):
        """Noop para compatibilidade"""
        pass
    
    def addHandler(self, handler):
        """Noop para compatibilidade"""
        self.handlers.append(handler)
    
    def info(self, message: str):
        """Grava INFO log"""
        try:
            self.db.add_bot_log(self.bot_id, "INFO", message, {"message": message})
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)
    
    def error(self, message: str):
        """Grava ERROR log"""
        try:
            self.db.add_bot_log(self.bot_id, "ERROR", message, {"message": message})
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)
    
    def warning(self, message: str):
        """Grava WARNING log"""
        try:
            self.db.add_bot_log(self.bot_id, "WARNING", message, {"message": message})
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)
    
    def debug(self, message: str):
        """Grava DEBUG log"""
        try:
            self.db.add_bot_log(self.bot_id, "DEBUG", message, {"message": message})
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)


def init_log(bot_id: str):
    """Inicializa o gerenciador de logs para o bot (usa SQLite)"""
    try:
        from .database import DatabaseManager
    except ImportError:
        from database import DatabaseManager
    db = DatabaseManager()
    return DatabaseLogger(db, bot_id)


def log(db_logger, bot_id: str, event: dict):
    """Grava evento de log em SQLite"""
    event["timestamp"] = time.time()
    event["bot_id"] = bot_id
    
    # Extrai o tipo de evento para usar como nível de log
    level = str(event.pop("event", "INFO")).upper()
    if level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        level = "INFO"
    
    # Message é uma concatenação legível do evento
    message = str(event)
    
    # Grava usando o método apropriado
    getattr(db_logger, level.lower(), db_logger.info)(message)


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KuCoin Trading Bot")

    parser.add_argument("--bot-id", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--entry", type=float, required=True)
    parser.add_argument("--mode", default="mixed", choices=["sell", "buy", "mixed"])
    parser.add_argument("--targets", required=True)
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--size", type=float, default=0.0)
    parser.add_argument("--funds", type=float, default=0.0)
    parser.add_argument("--dry", action="store_true", default=False)
    parser.add_argument("--reserve-pct", type=float, default=50.0, help="% do saldo a reservar")
    parser.add_argument("--target-profit-pct", type=float, default=2.0, help="% de lucro alvo")
    parser.add_argument("--eternal", action="store_true", default=False, help="Eternal mode - reinicia após targets")

    args = parser.parse_args()

    if EnhancedTradeBot is None:
        print("Erro crítico: EnhancedTradeBot não encontrado", file=sys.stderr)
        sys.exit(1)

    logger = init_log(args.bot_id)

    # ========== LOG INICIAL COM BOT_ID E PID ==========
    current_pid = os.getpid()
    logger.info(f"Bot iniciado: ID={args.bot_id}, PID={current_pid}")
    
    targets = parse_targets(args.targets)
    if not targets:
        log(logger, args.bot_id, {
            "event": "error",
            "message": "Nenhum target configurado"
        })
        sys.exit(1)

    log(logger, args.bot_id, {
        "event": "bot_started",
        "symbol": args.symbol,
        "mode": args.mode,
        "dry_run": args.dry,
        "bot_id": args.bot_id,
        "pid": current_pid,
        "reserve_pct": args.reserve_pct,
        "target_profit_pct": args.target_profit_pct,
        "eternal_mode": args.eternal
    })

    bot = EnhancedTradeBot(
        symbol=args.symbol,
        entry_price=args.entry,
        mode=args.mode,
        targets=targets,
        interval=args.interval,
        size=args.size,
        funds=args.funds,
        dry_run=args.dry,
        bot_id=args.bot_id,
        logger=logger,
        eternal_mode=args.eternal,
    )

    bot.run()

