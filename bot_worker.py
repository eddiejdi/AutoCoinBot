# bot_core.py — EnhancedTradeBot + logging estruturado + histórico
from __future__ import annotations
import time
import json
import uuid
import threading
import requests
import os
import logging
import logging.handlers
from pathlib import Path
from typing import List, Tuple, Optional, Any
import sys  # <--- [CORREÇÃO] Adicionado para usar sys.stdout

# Import da API KuCoin
try:
    from . import api
except:
    import api  # fallback se rodado fora do pacote

# Caminhos de histórico e logs
ROOT = Path(__file__).resolve().parent
HISTORY_JSON = ROOT / "bot_history.json"
LOG_DIR = ROOT / "logs"


# ============================================================
#  LOGGING ESTRUTURADO
# ============================================================
def setup_bot_logger(bot_id: str, log_dir: Optional[str] = None, level=logging.INFO):
    """
    Configura logger para o bot.
    Grava em console e arquivo rotativo logs/bot_<id>.log.
    """
    name = f"kucoin_bot.{bot_id}"
    logger = logging.getLogger(name)

    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    fmt = "%(asctime)s | %(levelname)s | bot=%(bot_id)s | event=%(event)s | %(message)s"

    # Console
    sh = logging.StreamHandler(sys.stdout) # <--- [CORREÇÃO] FORÇANDO A SAÍDA PARA STDOUT
    sh.setLevel(level)
    sh.setFormatter(logging.Formatter(fmt))

    # Diretório
    log_path = Path(log_dir) if log_dir else LOG_DIR
    log_path.mkdir(parents=True, exist_ok=True)

    # Arquivo rotativo
    fh = logging.handlers.RotatingFileHandler(
        log_path / f"bot_{bot_id}.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(fmt))

    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


# ============================================================
#  FUNÇÕES DE HISTÓRICO
# ============================================================
def _load_history():
    if not HISTORY_JSON.exists():
        return []
    try:
        return json.loads(HISTORY_JSON.read_text())
    except:
        return []


def _append_history(entry: dict):
    hist = _load_history()
    hist.append(entry)
    try:
        HISTORY_JSON.write_text(json.dumps(hist, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Erro ao salvar histórico:", e)


# ============================================================
#  EXECUÇÃO DE ORDENS (SIMULADO OU REAL)
# ============================================================
def place_market_order(symbol: str, side: str,
                       funds: Optional[float] = None,
                       size: Optional[float] = None,
                       dry_run: bool = True,
                       logger: Optional[logging.Logger] = None) -> dict:
    """
    Executa ordem no mercado ou simula se dry_run=True.
    """

    payload = {
        "clientOid": str(uuid.uuid4()),
        "side": side,
        "symbol": symbol,
        "type": "market",
    }

    if funds is not None:
        payload["funds"] = str(funds)
    if size is not None:
        payload["size"] = str(size)

    if dry_run or not getattr(api, "_has_keys", lambda: False)():
        if logger:
            logger.info(json.dumps(payload), extra={"bot_id": "sim", "event": "simulated_order"})
        return {
            "simulated": True,
            "symbol": symbol,
            "side": side,
            "funds": funds,
            "size": size,
            "timestamp": time.time()
        }

    # Modo real
    endpoint = "/api/v1/orders"
    url = api._base_url() + endpoint
    body = json.dumps(payload)
    headers = api._build_headers("POST", endpoint, body)
    r = requests.post(url, headers=headers, data=body, timeout=20)
    r.raise_for_status()
    return r.json()


# ============================================================
#  ENHANCED TRADE BOT
# ============================================================
class EnhancedTradeBot:
    def __init__(self,
                 symbol: str,
                 entry_price: float,
                 mode: str = "sell",
                 targets: Optional[List[Tuple[float, float]]] = None,
                 trailing_stop_pct: Optional[float] = None,
                 stop_loss_pct: Optional[float] = None,
                 size: Optional[float] = None,
                 funds: Optional[float] = None,
                 check_interval: float = 5.0,
                 dry_run: bool = True,
                 verbose: bool = False,
                 log_dir: Optional[str] = None):

        self.symbol = symbol
        self.entry_price = float(entry_price)
        self.mode = mode.lower()
        self.targets = sorted(targets or [], key=lambda x: x[0])
        self.trailing_stop_pct = trailing_stop_pct
        self.stop_loss_pct = stop_loss_pct
        self.size = size
        self.funds = funds
        self.check_interval = float(check_interval)
        self.dry_run = dry_run
        self.verbose = verbose
        self.log_dir = log_dir

        self._id = str(uuid.uuid4())
        self._executed_parts = []
        self._remaining_fraction = 1.0 - sum(p[1] for p in self.targets)

        self._last_price = None
        self._peak_price = None
        self._valley_price = None

        level = logging.DEBUG if verbose else logging.INFO
        self._logger = setup_bot_logger(self._id, log_dir, level)

        self._stopped = threading.Event()

    # ------------------- logging helper --------------------
    def _log(self, level: str, event: str, **payload):
        try:
            text = json.dumps(payload, ensure_ascii=False)
        except:
            text = str(payload)

        extra = {"bot_id": self._id, "event": event}

        if level == "debug":
            self._logger.debug(text, extra=extra)
        elif level == "warning":
            self._logger.warning(text, extra=extra)
        elif level == "error":
            self._logger.error(text, extra=extra)
        else:
            self._logger.info(text, extra=extra)

    # ------------------- preço --------------------
    def _get_price(self):
        try:
            price = api.get_orderbook_price(self.symbol)
            return api._extract_price_from_resp(price)
        except Exception as e:
            self._log("error", "price_error", error=str(e))
            return None

    # ------------------- execução SELL --------------------
    def _execute_sell_fraction(self, fraction):
        if fraction <= 0:
            return None
        if self.size:
            qty = self.size * fraction
            return place_market_order(self.symbol, "sell", size=qty,
                                      dry_run=self.dry_run, logger=self._logger)
        else:
            if self._last_price and self.funds:
                funds_val = self.funds * fraction
                return place_market_order(self.symbol, "sell", funds=funds_val,
                                          dry_run=self.dry_run, logger=self._logger)
            return None

    # ------------------- execução BUY --------------------
    def _execute_buy_fraction(self, fraction):
        if fraction <= 0:
            return None
        if self.size:
            qty = self.size * fraction
            return place_market_order(self.symbol, "buy", size=qty,
                                      dry_run=self.dry_run, logger=self._logger)
        else:
            if self.funds:
                funds_val = self.funds * fraction
                return place_market_order(self.symbol, "buy", funds=funds_val,
                                          dry_run=self.dry_run, logger=self._logger)
            return None

    # ------------------- salvar trade --------------------
    def _record_trade(self, kind, price, res, portion=None):
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "symbol": self.symbol,
            "kind": kind,
            "price": price,
            "portion": portion,
            "result": res,
            "dry_run": self.dry_run,
        }
        _append_history(entry)

        # Determinar side (buy ou sell) baseado no kind
        if "buy" in kind:
            side = "buy"
        elif "sell" in kind:
            side = "sell"
        else:
            side = "unknown"
        
        # Gravar no banco de dados SQLite
        try:
            from .database import DatabaseManager
        except ImportError:
            from database import DatabaseManager
        
        try:
            db = DatabaseManager()
            trade_data = {
                "id": entry["id"],
                "timestamp": entry["timestamp"],
                "symbol": self.symbol,
                "side": side,
                "price": price,
                "size": portion if portion else 0.0,
                "funds": None,
                "profit": None,
                "commission": None,
                "order_id": res.get("orderId") if isinstance(res, dict) else None,
                "bot_id": self._id,
                "strategy": kind,
                "dry_run": self.dry_run,
                "metadata": {"result": res}
            }
            db.insert_trade(trade_data)
            
            # Criar sinalizador para o frontend fazer refresh imediato
            try:
                from pathlib import Path
                signal_file = Path(__file__).parent / ".trade_signal"
                signal_file.write_text(self._id)
            except Exception:
                pass
        except Exception as e:
            self._log("error", f"Erro ao gravar trade no banco: {e}")

        self._log("info", "trade_recorded", kind=kind, price=price, portion=portion)

    # ============================================================
    #  LOOP PRINCIPAL DO BOT
    # ============================================================
    def start(self):
        self._log("info", "bot_started",
                  symbol=self.symbol, entry_price=self.entry_price,
                  mode=self.mode, targets=self.targets,
                  stop_loss_pct=self.stop_loss_pct,
                  trailing_stop_pct=self.trailing_stop_pct,
                  size=self.size, funds=self.funds)

        try:
            while not self._stopped.is_set():

                price = self._get_price()
                if price is None:
                    time.sleep(self.check_interval)
                    continue

                self._last_price = price
                self._log("debug", "price_read", price=price)

                # Inicializa valley e peak
                if self._peak_price is None:
                    self._peak_price = price
                if self._valley_price is None:
                    self._valley_price = price

                # Atualiza máximos/mínimos
                if price > self._peak_price:
                    self._log("debug", "peak_update", old=self._peak_price, new=price)
                    self._peak_price = price

                if price < self._valley_price:
                    self._log("debug", "valley_update", old=self._valley_price, new=price)
                    self._valley_price = price

                # ---------------------- STOP-LOSS ----------------------
                if self.stop_loss_pct is not None:
                    sl_price = self.entry_price * (1 + self.stop_loss_pct / 100)
                    self._log("debug", "stoploss_check", threshold=sl_price, price=price)

                    if (self.mode in ("sell", "both")) and price <= sl_price:
                        res = self._execute_sell_fraction(self._remaining_fraction)
                        self._record_trade("stoploss_sell", price, res)
                        break

                    if (self.mode in ("buy", "both")) and price >= sl_price:
                        res = self._execute_buy_fraction(self._remaining_fraction)
                        self._record_trade("stoploss_buy", price, res)
                        break

                # ---------------------- TRAILING STOP ----------------------
                if self.trailing_stop_pct is not None:

                    # SELL trailing
                    if self.mode in ("sell", "both"):
                        threshold = self._peak_price * (1 - self.trailing_stop_pct / 100)
                        self._log("debug", "trailing_sell_check", threshold=threshold, price=price)

                        if price <= threshold:
                            res = self._execute_sell_fraction(self._remaining_fraction)
                            self._record_trade("trailing_sell", price, res)
                            break

                    # BUY trailing
                    if self.mode in ("buy", "both"):
                        threshold = self._valley_price * (1 + self.trailing_stop_pct / 100)
                        self._log("debug", "trailing_buy_check", threshold=threshold, price=price)

                        if price >= threshold:
                            res = self._execute_buy_fraction(self._remaining_fraction)
                            self._record_trade("trailing_buy", price, res)
                            break

                # ---------------------- TARGETS ----------------------
                for pct, portion in list(self.targets):
                    if pct in self._executed_parts:
                        continue

                    target_price = self.entry_price * (1 + pct / 100)
                    self._log("debug", "target_check", pct=pct, portion=portion,
                              target_price=target_price, price=price)

                    if (self.mode in ("sell", "both")) and price >= target_price:
                        res = self._execute_sell_fraction(portion)
                        self._executed_parts.append(pct)
                        self._remaining_fraction -= portion
                        self._record_trade(f"target_sell_{pct}", price, res, portion)

                    if (self.mode in ("buy", "both")) and price <= target_price:
                        res = self._execute_buy_fraction(portion)
                        self._executed_parts.append(pct)
                        self._remaining_fraction -= portion
                        self._record_trade(f"target_buy_{pct}", price, res, portion)

                # Finalizado?
                if self._remaining_fraction <= 0:
                    self._log("info", "targets_completed")
                    break

                time.sleep(self.check_interval)

        except Exception as e:
            self._log("error", "unhandled_exception", error=str(e))

        self._log("info", "bot_finished",
                  executed=self._executed_parts,
                  remaining_fraction=self._remaining_fraction)

    # ============================================================
    def stop(self):
        self._stopped.set()
        self._log("info", "stop_requested")


# ============================================================
# Função utilitária
# ============================================================
def parse_targets(s: str):
    out = []
    if not s:
        return out
    for part in s.split(","):
        if ":" in part:
            a, b = part.split(":")
            try:
                out.append((float(a), float(b)))
            except:
                pass
    return out

if __name__ == "__main__":
    import argparse
    from bot_core import EnhancedTradeBot, parse_targets  # ajuste import

    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--entry", type=float, required=True)
    parser.add_argument("--mode", default="sell")
    parser.add_argument("--targets", default="")
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--size", type=float, default=0.0)
    parser.add_argument("--funds", type=float, default=0.0)
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--no-dry", dest="dry", action="store_false")
    parser.set_defaults(dry=True)

    args = parser.parse_args()

    targets = parse_targets(args.targets)

    bot = EnhancedTradeBot(
        symbol=args.symbol,
        entry_price=args.entry,
        mode=args.mode,
        targets=targets,
        check_interval=args.interval,
        size=args.size,
        funds=args.funds,
        dry_run=args.dry,
    )
    bot.start()  # ou bot.run(), dependendo da versão
