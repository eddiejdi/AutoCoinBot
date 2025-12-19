# bot.py — VERSÃO OTIMIZADA E CORRIGIDA
from __future__ import annotations
import time
import json
import uuid
import threading
import os
import sys
import logging
import logging.handlers
import random
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from datetime import datetime

# Adiciona o diretório do projeto ao sys.path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

try:
    import api
    HAS_API = True
except ImportError as e:
    print(f"[ERRO] Não foi possível importar api: {e}")
    print("[INFO] Rodando em modo SIMULAÇÃO (dry_run forçado)")
    HAS_API = False
    api = None

ROOT = Path(__file__).resolve().parent
HISTORY_JSON = ROOT / "bot_history.json"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ====================== CONFIGURAÇÕES ======================
class BotConfig:
    """Configurações e validações do bot"""
    
    @staticmethod
    def validate_targets(targets: List[Tuple[float, float]]) -> None:
        """Valida se os targets são válidos"""
        if not targets:
            raise ValueError("Pelo menos um target deve ser configurado")
        
        total = sum(portion for _, portion in targets)
        if total > 1.0:
            raise ValueError(f"Soma dos targets ({total:.2f}) excede 1.0")
        
        if total < 0:
            raise ValueError("Soma dos targets não pode ser negativa")
        
        for pct, portion in targets:
            if portion <= 0 or portion > 1:
                raise ValueError(f"Porção inválida: {portion}. Deve estar entre 0 e 1")
    
    @staticmethod
    def validate_stop_loss(stop_loss_pct: Optional[float], mode: str) -> Optional[float]:
        """Normaliza stop loss para sempre ser negativo em modo sell"""
        if stop_loss_pct is None:
            return None
        
        if mode == "sell":
            return -abs(stop_loss_pct)
        else:
            return abs(stop_loss_pct)
    
    @staticmethod
    def validate_funds_or_size(funds: Optional[float], size: Optional[float]) -> None:
        """Valida se pelo menos funds ou size foi definido"""
        if funds is None and size is None:
            raise ValueError("Deve especificar 'funds' ou 'size'")
        
        if funds is not None and funds <= 0:
            raise ValueError(f"Funds deve ser positivo: {funds}")
        
        if size is not None and size <= 0:
            raise ValueError(f"Size deve ser positivo: {size}")

# ====================== LOGGER ======================
def setup_bot_logger(bot_id: str) -> logging.Logger:
    """Logger que imprime JSON puro no STDOUT para ui.py capturar"""
    logger = logging.getLogger(f"bot_{bot_id}")
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            return record.getMessage()
    
    stdout_handler.setFormatter(JSONFormatter())
    logger.addHandler(stdout_handler)
    
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / f"bot_{bot_id}.log",
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"[WARN] Não foi possível criar arquivo de log: {e}", file=sys.stderr, flush=True)
    
    return logger

# ====================== HISTÓRICO ======================
def _append_history(entry: dict):
    """Salva entrada no histórico JSON"""
    hist = []
    if HISTORY_JSON.exists():
        try:
            hist = json.loads(HISTORY_JSON.read_text(encoding="utf-8"))
        except:
            pass
    hist.append(entry)
    try:
        HISTORY_JSON.write_text(json.dumps(hist, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] Salvando histórico: {e}", file=sys.stderr, flush=True)

# ====================== ORDEM ======================
def place_market_order(symbol: str, side: str, funds: Optional[float] = None,
                       size: Optional[float] = None, dry_run: bool = True,
                       logger: Optional[logging.Logger] = None,
                       max_retries: int = 3) -> dict:
    """Executa ordem de mercado com retry"""
    payload = {
        "clientOid": str(uuid.uuid4()),
        "side": side,
        "symbol": symbol,
        "type": "market",
    }
    if funds: 
        payload["funds"] = str(round(funds, 8))
    if size: 
        payload["size"] = str(round(size, 12))

    if dry_run:
        sim = {
            "simulated": True,
            "clientOid": payload["clientOid"],
            "side": side,
            "symbol": symbol,
            "funds": payload.get("funds"),
            "size": payload.get("size"),
            "timestamp": int(time.time() * 1000)
        }
        if logger:
            logger.info(json.dumps({
                "event": "simulated_order", 
                "payload": payload,
                "result": "success"
            }))
        return sim

    # Ordem real com retry
    for attempt in range(max_retries):
        try:
            import requests
            endpoint = "/api/v1/orders"
            url = api._base_url() + endpoint
            body_str = json.dumps(payload, separators=(",", ":"))
            headers = api._build_headers("POST", endpoint, body_str)
            r = requests.post(url, headers=headers, data=body_str, timeout=20)
            r.raise_for_status()
            
            if logger:
                logger.info(json.dumps({
                    "event": "order_success",
                    "attempt": attempt + 1,
                    "response": r.json()
                }))
            
            return r.json()
            
        except Exception as e:
            if logger:
                logger.error(json.dumps({
                    "event": "order_error",
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "error": str(e)
                }))
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return {"error": str(e)}

# ====================== SIMULADOR DE PREÇO ======================
class PriceSimulator:
    """Simula movimento de preço realista"""
    
    def __init__(self, entry_price: float, trend_pct: float = 5.0, 
                 trend_duration: float = 300.0, volatility: float = 0.002):
        self.entry_price = entry_price
        self.trend_pct = trend_pct
        self.trend_duration = trend_duration
        self.volatility = volatility
        self.start_time = time.time()
    
    def get_price(self) -> float:
        """Gera preço com tendência + volatilidade"""
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.trend_duration, 1.0)
        trend = self.entry_price * (1 + (self.trend_pct / 100) * progress)
        noise = random.uniform(-self.volatility, self.volatility)
        simulated = trend * (1 + noise)
        return round(simulated, 2)

# ====================== BOT PRINCIPAL ======================
class EnhancedTradeBot:
    def __init__(
        self,
        symbol,
        entry_price,
        mode,
        targets,
        interval,
        size,
        funds,
        dry_run,
        bot_id=None,
        logger=None,
        eternal_mode=False,  # Novo parâmetro
    ):
        # Validações
        BotConfig.validate_funds_or_size(funds, size)
        targets = sorted(targets or [], key=lambda x: x[0])
        BotConfig.validate_targets(targets)

        # Parâmetros principais
        self.symbol = symbol.upper()
        self.entry_price = float(entry_price)
        self.mode = mode.lower()
        self.targets = targets
        self.interval = float(interval)
        self.check_interval = float(interval)
        self.size = size
        self.funds = funds
        self.dry_run = dry_run or not HAS_API
        self.bot_id = bot_id
        self.eternal_mode = eternal_mode  # Eternal mode flag
        self.eternal_run_number = 0  # Contador de ciclos
        self.eternal_run_id = None  # ID do ciclo atual no banco

        # Parâmetros opcionais
        self.trailing_stop_pct = None
        self.stop_loss_pct = None
        self.verbose = False

        # Estado interno
        self._id = bot_id or str(uuid.uuid4())[:8]
        self._logger = logger or setup_bot_logger(self._id)
        self._stopped = threading.Event()
        self._start_ts = time.time()

        self._last_price = self.entry_price
        self._peak_price = self.entry_price if self.mode == "sell" else None
        self._valley_price = self.entry_price if self.mode == "buy" else None

        self._executed_parts: List[float] = []
        self._initial_remaining = 1.0 - sum(p for _, p in self.targets)
        self._remaining_fraction = self._initial_remaining
        self.executed_trades: List[dict] = []

        # Simulador de preço
        self._price_simulator = None
        if self.dry_run:
            self._price_simulator = PriceSimulator(
                entry_price=self.entry_price,
                trend_pct=5.0,
                trend_duration=300.0,
                volatility=0.002
            )

        # Log inicial
        self._log(
            "bot_initialized",
            symbol=self.symbol,
            entry_price=self.entry_price,
            mode=self.mode,
            targets=self.targets,
            dry_run=self.dry_run,
        )

    def _log(self, event: str, **kwargs):
        """Log estruturado em JSON"""
        log_entry = {
            "bot_id": self._id,
            "event": event,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            **kwargs
        }
        message = json.dumps(log_entry, ensure_ascii=False, default=str)
        self._logger.info(message)
        sys.stdout.flush()

    def _get_current_price(self) -> float:
        """Obtém preço atual (real ou simulado)"""
        if not HAS_API or self.dry_run:
            simulated = self._price_simulator.get_price()
            elapsed = time.time() - self._start_ts
            change_pct = ((simulated / self.entry_price) - 1) * 100
            
            self._log("price_simulated", 
                     price=simulated, 
                     elapsed=round(elapsed, 1),
                     change_pct=round(change_pct, 2))
            return simulated
        
        try:
            ob = api.get_orderbook_price(self.symbol)
            if ob and isinstance(ob, dict):
                price = ob.get("mid_price")
                if price:
                    return float(price)
            return self._last_price
        except Exception as e:
            self._log("price_fetch_error", error=str(e))
            return self._last_price

    def _calculate_portion_size(self, portion: float) -> float:
        """Calcula tamanho da ordem"""
        if self.size: 
            return self.size * portion
        price = self._get_current_price()
        if self.funds and price: 
            return (self.funds * portion) / price
        return 0.0

    def _execute_fraction(self, portion: float, side: str) -> dict:
        """Executa ordem para uma fração"""
        size = self._calculate_portion_size(portion)
        self._log("executing_order", side=side, portion=round(portion, 4), size=round(size, 8))
        
        result = place_market_order(
            self.symbol, side, size=size, 
            dry_run=self.dry_run, logger=self._logger
        )
        return result

    def _record_trade(self, kind: str, price: float, portion: float):
        """Registra trade"""
        profit = 0
        if "sell" in kind and self.size:
            profit = portion * (price - self.entry_price) * self.size
        elif "buy" in kind and self.size:
            profit = portion * (self.entry_price - price) * self.size

        trade = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "kind": kind,
            "price": round(price, 2),
            "portion": round(portion, 4),
            "profit_usdt": round(profit, 2),
            "simulated": self.dry_run
        }
        self.executed_trades.append(trade)
        self._log("trade_executed", **trade)
        
        # Gravar no banco de dados SQLite
        if "buy" in kind:
            side = "buy"
        elif "sell" in kind:
            side = "sell"
        else:
            side = "unknown"
        
        try:
            from .database import DatabaseManager
        except ImportError:
            from database import DatabaseManager
        
        try:
            db = DatabaseManager()
            trade_data = {
                "id": str(time.time()),
                "timestamp": time.time(),
                "symbol": self.symbol,
                "side": side,
                "price": price,
                "size": portion,
                "funds": None,
                "profit": profit,
                "commission": None,
                "order_id": None,
                "bot_id": self.bot_id if hasattr(self, 'bot_id') else None,
                "strategy": kind,
                "dry_run": self.dry_run,
                "metadata": {"kind": kind, "portion": portion}
            }
            db.insert_trade(trade_data)
            
            # Criar sinalizador para o frontend fazer refresh imediato
            try:
                from pathlib import Path
                bot_id = self.bot_id if hasattr(self, 'bot_id') else str(time.time())
                signal_file = Path(__file__).parent / ".trade_signal"
                signal_file.write_text(bot_id)
            except Exception:
                pass
        except Exception as e:
            pass

    def _get_total_remaining(self) -> float:
        """Calcula fração total ainda não executada"""
        total = self._remaining_fraction
        for pct, portion in self.targets:
            if pct not in self._executed_parts:
                total += portion
        return total

    def _should_continue(self) -> bool:
        """Verifica se deve continuar"""
        if self._stopped.is_set():
            return False
        return self._get_total_remaining() > 0.01

    def _get_next_target(self) -> Optional[Dict]:
        """Retorna próximo target"""
        for pct, portion in self.targets:
            if pct not in self._executed_parts:
                target_price = self.entry_price * (1 + pct / 100)
                return {
                    "pct": pct,
                    "portion": portion,
                    "price": target_price,
                    "distance_pct": ((target_price / self._last_price) - 1) * 100
                }
        return None

    def get_status(self) -> dict:
        """Status atual"""
        total_profit = sum(t.get("profit_usdt", 0) for t in self.executed_trades)
        current_pnl_pct = ((self._last_price / self.entry_price) - 1) * 100
        
        return {
            "bot_id": self._id,
            "running": not self._stopped.is_set(),
            "current_price": self._last_price,
            "entry_price": self.entry_price,
            "current_pnl_pct": round(current_pnl_pct, 2),
            "executed_targets": len(self._executed_parts),
            "total_targets": len(self.targets),
            "next_target": self._get_next_target(),
            "peak_price": self._peak_price,
            "total_profit_usdt": round(total_profit, 2),
            "total_remaining": round(self._get_total_remaining(), 4),
            "uptime_seconds": round(time.time() - self._start_ts, 1)
        }

    def run(self):
        """Loop principal - suporta eternal mode"""
        if self.eternal_mode:
            self._run_eternal()
        else:
            self._run_single()
    
    def _get_db(self):
        """Obtém instância do DatabaseManager"""
        try:
            from .database import DatabaseManager
        except ImportError:
            from database import DatabaseManager
        return DatabaseManager()
    
    def _run_eternal(self):
        """Executa em modo eternal - reinicia automaticamente após completar targets"""
        self._log("eternal_mode_started", message="🔄 Eternal Mode ativado!")
        
        while not self._stopped.is_set():
            self.eternal_run_number += 1
            self._log("eternal_run_start", 
                     run_number=self.eternal_run_number,
                     message=f"🚀 Iniciando ciclo #{self.eternal_run_number}")
            
            # Registra início do ciclo no banco
            try:
                db = self._get_db()
                self.eternal_run_id = db.add_eternal_run(
                    bot_id=self._id,
                    run_number=self.eternal_run_number,
                    symbol=self.symbol,
                    entry_price=self.entry_price,
                    total_targets=len(self.targets)
                )
            except Exception as e:
                self._log("eternal_db_error", error=str(e))
                self.eternal_run_id = None
            
            # Reseta estado para novo ciclo
            self._reset_for_new_run()
            
            # Executa um ciclo completo
            self._run_single()
            
            if self._stopped.is_set():
                break
            
            # Calcula resultados do ciclo
            total_profit_usdt = sum(t.get("profit_usdt", 0) for t in self.executed_trades)
            profit_pct = ((self._last_price / self.entry_price) - 1) * 100
            
            # Atualiza ciclo no banco como completo
            if self.eternal_run_id and self.eternal_run_id > 0:
                try:
                    db = self._get_db()
                    db.complete_eternal_run(
                        run_id=self.eternal_run_id,
                        exit_price=self._last_price,
                        profit_pct=profit_pct,
                        profit_usdt=total_profit_usdt,
                        targets_hit=len(self._executed_parts)
                    )
                except Exception as e:
                    self._log("eternal_db_error", error=str(e))
            
            self._log("eternal_run_complete", 
                     run_number=self.eternal_run_number,
                     profit_pct=round(profit_pct, 2),
                     profit_usdt=round(total_profit_usdt, 2),
                     targets_hit=len(self._executed_parts),
                     message=f"✅ Ciclo #{self.eternal_run_number} completo!")
            
            # Atualiza entry_price para o preço atual antes de reiniciar
            self.entry_price = self._last_price
            
            # Pequena pausa antes de reiniciar
            self._log("eternal_restarting", 
                     message=f"⏳ Reiniciando em 5s com entry={self.entry_price:.2f}...")
            time.sleep(5)
        
        self._log("eternal_mode_stopped", 
                 total_runs=self.eternal_run_number,
                 message="🛑 Eternal Mode encerrado")
    
    def _reset_for_new_run(self):
        """Reseta estado interno para novo ciclo"""
        self._start_ts = time.time()
        self._last_price = self.entry_price
        self._peak_price = self.entry_price if self.mode == "sell" else None
        self._valley_price = self.entry_price if self.mode == "buy" else None
        self._executed_parts = []
        self._remaining_fraction = self._initial_remaining
        self.executed_trades = []
        
        # Reseta simulador de preço
        if self._price_simulator:
            self._price_simulator = PriceSimulator(
                entry_price=self.entry_price,
                trend_pct=5.0,
                trend_duration=300.0,
                volatility=0.002
            )
    
    def _run_single(self):
        """Loop principal para um ciclo"""
        self._log("bot_started", message="Iniciando monitoramento...")
        
        try:
            cycle = 0
            while self._should_continue():
                cycle += 1
                price = self._get_current_price()
                
                if price is None:
                    self._log("price_unavailable")
                    time.sleep(self.interval)
                    continue
                
                self._last_price = price
                
                # Atualiza peak/valley
                if self.mode == "sell":
                    if self._peak_price is None or price > self._peak_price:
                        self._peak_price = price
                elif self.mode == "buy":
                    if self._valley_price is None or price < self._valley_price:
                        self._valley_price = price
                
                # Log periódico
                if cycle % 10 == 0:
                    self._log("status_update", **self.get_status())
                
                self._log("price_check", 
                         cycle=cycle,
                         price=round(price, 2),
                         executed=f"{len(self._executed_parts)}/{len(self.targets)}")
                
                # Stop loss
                if self.stop_loss_pct is not None:
                    if self.mode == "sell":
                        threshold = self.entry_price * (1 + self.stop_loss_pct / 100)
                        if price <= threshold:
                            self._log("stop_loss_triggered", price=price)
                            total = self._get_total_remaining()
                            if total > 0.01:
                                self._execute_fraction(total, "sell")
                                self._record_trade("stop_loss", price, total)
                            self._stopped.set()
                            break
                
                # Trailing stop
                if self.trailing_stop_pct is not None:
                    if self.mode == "sell" and self._peak_price:
                        threshold = self._peak_price * (1 - self.trailing_stop_pct / 100)
                        if price <= threshold:
                            self._log("trailing_stop_triggered", price=price)
                            total = self._get_total_remaining()
                            if total > 0.01:
                                self._execute_fraction(total, "sell")
                                self._record_trade("trailing_stop", price, total)
                            self._stopped.set()
                            break
                
                # Targets
                for pct, portion in self.targets:
                    if pct in self._executed_parts:
                        continue
                    
                    target = self.entry_price * (1 + pct / 100)
                    
                    if self.mode == "sell" and price >= target:
                        self._log("target_hit", target_pct=pct, price=price)
                        self._execute_fraction(portion, "sell")
                        self._record_trade(f"target_sell_{pct}%", price, portion)
                        self._executed_parts.append(pct)
                    
                    elif self.mode == "buy" and price <= target:
                        self._log("target_hit", target_pct=pct, price=price)
                        self._execute_fraction(portion, "buy")
                        self._record_trade(f"target_buy_{pct}%", price, portion)
                        self._executed_parts.append(pct)
                
                if not self._should_continue():
                    self._log("completion_check", message="✅ Concluído!")
                    break
                
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            self._log("bot_interrupted")
        except Exception as e:
            self._log("bot_error", error=str(e))
            import traceback
            self._log("traceback", tb=traceback.format_exc())
        finally:
            self._finalize()

    def _finalize(self):
        """Finaliza bot"""
        total_profit = sum(t.get("profit_usdt", 0) for t in self.executed_trades)
        
        self._log("bot_finalized",
                 executed_trades=len(self.executed_trades),
                 total_profit=round(total_profit, 2))
        
        final = {
            "id": self._id,
            "symbol": self.symbol,
            "entry_price": self.entry_price,
            "mode": self.mode,
            "start_ts": self._start_ts,
            "end_ts": time.time(),
            "executed_trades": self.executed_trades,
            "total_profit": total_profit,
            "dry_run": self.dry_run,
        }
        _append_history(final)

    def stop(self):
        """Para o bot"""
        self._stopped.set()
        self._log("stop_requested")

# ====================== UTILITIES ======================
def parse_targets(s: str) -> List[Tuple[float, float]]:
    """Parse '2:0.3,5:0.5' -> [(2.0, 0.3), (5.0, 0.5)]"""
    out = []
    for p in s.split(","):
        if ":" in p:
            try:
                a, b = p.split(":")
                out.append((float(a), float(b)))
            except:
                pass
    return out

# ====================== CLI ======================
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="BTC-USDT")
    p.add_argument("--entry", type=float, default=88000.0)
    p.add_argument("--mode", default="sell", choices=["sell", "buy"])
    p.add_argument("--targets", default="2:0.2,5:0.3,10:0.3")
    p.add_argument("--size", type=float, default=None)
    p.add_argument("--funds", type=float, default=100.0)
    p.add_argument("--interval", type=float, default=5.0)
    p.add_argument("--dry", action="store_true", default=False)
    args = p.parse_args()

    targets = parse_targets(args.targets)
    bot = EnhancedTradeBot(
        symbol=args.symbol,
        entry_price=args.entry,
        mode=args.mode,
        targets=targets,
        interval=args.interval,
        size=args.size,
        funds=args.funds,
        dry_run=args.dry,
    )
    bot.run()
