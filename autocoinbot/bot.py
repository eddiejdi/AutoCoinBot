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

try:
    # When bot is imported as kucoin_app.bot
    from .market import analyze_market_regime_5m
except Exception:
    try:
        # When bot is imported as top-level module
        from market import analyze_market_regime_5m  # type: ignore
    except Exception:
        analyze_market_regime_5m = None

try:
    # Optional: public (anonymous) flow signal for spot
    from .public_flow_intel import analyze_public_flow
except Exception:
    try:
        from public_flow_intel import analyze_public_flow  # type: ignore
    except Exception:
        analyze_public_flow = None

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

    # Ordem real com retry (somente para falhas de rede/HTTP).
    # Respostas KuCoin com code != 200000 devem ser tratadas como rejeição (sem retry).
    for attempt in range(max_retries):
        try:
            import requests
            endpoint = "/api/v1/orders"
            url = api._base_url() + endpoint
            body_str = json.dumps(payload, separators=(",", ":"))
            headers = api._build_headers("POST", endpoint, body_str)
            r = requests.post(url, headers=headers, data=body_str, timeout=20)
            r.raise_for_status()

            resp = None
            try:
                resp = r.json()
            except Exception:
                resp = {"error": "invalid_json_response"}

            # KuCoin success contract
            try:
                code = resp.get("code") if isinstance(resp, dict) else None
            except Exception:
                code = None

            if code is not None and str(code) != "200000":
                if logger:
                    logger.error(json.dumps({
                        "event": "order_failed",
                        "attempt": attempt + 1,
                        "payload": payload,
                        "response": resp,
                    }))
                return resp

            if logger:
                logger.info(json.dumps({
                    "event": "order_success",
                    "attempt": attempt + 1,
                    "response": resp
                }))

            return resp
            
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
        interval=None,
        size=None,
        funds=None,
        dry_run=False,
        bot_id=None,
        logger=None,
        eternal_mode=False,  # Novo parâmetro
        # Compatibility with older callers / service scripts
        check_interval=None,
        target_profit_pct: float = 0.0,
    ):
        # Validações
        BotConfig.validate_funds_or_size(funds, size)
        targets = sorted(targets or [], key=lambda x: x[0])
        BotConfig.validate_targets(targets)

        # Parâmetros principais
        self.symbol = symbol.upper()
        self.entry_price = float(entry_price)
        self.mode = str(mode or "sell").lower().strip()
        # Compat: UI/CLI uses "mixed"; older worker uses "both".
        # We keep "mixed" as a first-class mode here.
        if self.mode == "both":
            self.mode = "mixed"

        # Public-flow mode ("copy the market" using anonymous public data)
        # This mode executes chunks based on flow signals, not on price targets.
        self.public_flow_enabled = (self.mode == "flow")
        if interval is None:
            interval = check_interval
        if interval is None:
            interval = 5.0
        self.interval = float(interval)
        self.check_interval = float(interval)
        self._flow_last_eval_ts: float = 0.0
        self._flow_last_trade_ts: float = 0.0
        self.flow_min_confidence: float = 0.35
        self.flow_max_spread_bps: float = 25.0
        self.flow_trade_cooldown_s: float = 20.0
        self.flow_eval_interval_s: float = max(5.0, float(self.interval))
        self._last_flow_signal: Optional[dict] = None
        self.targets = targets
        self.size = size
        self.funds = funds
        self.dry_run = dry_run or not HAS_API
        self.bot_id = bot_id
        self.eternal_mode = eternal_mode  # Eternal mode flag
        self.eternal_run_number = 0  # Contador de ciclos
        self.eternal_run_id = None  # ID do ciclo atual no banco

        # Profit gating / take-profit behavior
        # target_profit_pct comes from UI/controller (defaults to 2.0 there).
        try:
            self.target_profit_pct = float(target_profit_pct or 0.0)
        except Exception:
            self.target_profit_pct = 0.0
        
        # ====== CUSTOS DE TRADING (TAXAS KUCOIN) ======
        # KuCoin cobra ~0.1% por operação (maker/taker padrão)
        # Para operação completa (compra + venda), custo total = ~0.2%
        # Adicionamos margem de segurança para slippage
        self._buy_fee_pct: float = 0.10   # Taxa de compra (%)
        self._sell_fee_pct: float = 0.10  # Taxa de venda (%)
        self._slippage_pct: float = 0.05  # Margem para slippage (%)
        
        # Custo total de uma operação round-trip (compra + venda + slippage)
        self._total_trading_cost_pct: float = self._buy_fee_pct + self._sell_fee_pct + self._slippage_pct
        
        # Buffer para evitar vendas com lucro "zero" após taxas
        # Agora considera o custo real de trading
        self._fee_buffer_pct: float = self._total_trading_cost_pct
        self._min_true_profit_pct: float = max(0.0, float(self.target_profit_pct) + float(self._fee_buffer_pct))
        # Trailing percent used after a take-profit level is reached (aims for higher peaks).
        # Derived from target_profit_pct so users can tune it without new UI fields.
        base_trail = 0.5
        if self.target_profit_pct and self.target_profit_pct > 0:
            base_trail = max(0.2, min(2.0, float(self.target_profit_pct) / 2.0))
        self._take_profit_trailing_pct: float = float(base_trail)
        # Auto-learning fields (selection happens after _id/_logger are initialized).
        self._learn_param_name = "take_profit_trailing_pct"
        self._learn_selected_trailing: Optional[float] = None
        self._learn_selected_params: dict[str, float] = {}
        # When a sell target is reached, we "arm" it and trail from the peak instead of selling immediately.
        self._armed_sell: Optional[dict] = None

        # Parâmetros opcionais
        self.trailing_stop_pct = None
        self.stop_loss_pct = None
        self.verbose = False

        # Auto strategy switching (online)
        # Heuristic: enable by default when starting in mixed mode (most flexible).
        self.auto_strategy_enabled = (self.mode == "mixed")
        self._auto_last_eval_ts: float = 0.0
        self._auto_last_change_ts: float = 0.0
        self._auto_last_snapshot: Optional[dict] = None
        self._auto_effective_mode: str = self.mode

        # Estado interno
        self._id = bot_id or str(uuid.uuid4())[:8]
        self._logger = logger or setup_bot_logger(self._id)
        self._stopped = threading.Event()
        self._start_ts = time.time()

        # Auto-learning: pick trailing from a bandit per symbol (aim: higher exit price/profit).
        # Enable/disable via env var AUTO_LEARN_TRAILING=0
        try:
            enable = str(os.environ.get("AUTO_LEARN_TRAILING", "1")).strip().lower() not in ("0", "false", "no", "off")
        except Exception:
            enable = True
        if enable:
            try:
                db = self._get_db()
                candidates = [0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0]
                chosen = db.choose_bandit_param(self.symbol, self._learn_param_name, candidates=candidates, epsilon=0.25)
                self._take_profit_trailing_pct = float(chosen)
                self._learn_selected_trailing = float(chosen)
                self._learn_selected_params[self._learn_param_name] = float(chosen)
                self._log(
                    "auto_learn_param_chosen",
                    param=self._learn_param_name,
                    value=self._take_profit_trailing_pct,
                    candidates=candidates,
                )
            except Exception as e:
                self._log("auto_learn_param_error", error=str(e))

        # Auto-learning for FLOW mode decision thresholds.
        # Enable/disable via env var AUTO_LEARN_FLOW=0
        if self.public_flow_enabled:
            try:
                enable_flow = str(os.environ.get("AUTO_LEARN_FLOW", "1")).strip().lower() not in (
                    "0",
                    "false",
                    "no",
                    "off",
                )
            except Exception:
                enable_flow = True

            if enable_flow:
                try:
                    db = self._get_db()

                    # Flow thresholds (candidates centered around current defaults).
                    p_min_conf = "flow_min_confidence"
                    c_min_conf = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.55]
                    v_min_conf = db.choose_bandit_param(self.symbol, p_min_conf, candidates=c_min_conf, epsilon=0.25)
                    self.flow_min_confidence = float(v_min_conf)
                    self._learn_selected_params[p_min_conf] = float(v_min_conf)
                    self._log(
                        "auto_learn_param_chosen",
                        param=p_min_conf,
                        value=float(v_min_conf),
                        candidates=c_min_conf,
                    )

                    p_max_spread = "flow_max_spread_bps"
                    c_max_spread = [12.0, 15.0, 20.0, 25.0, 30.0, 40.0, 55.0]
                    v_max_spread = db.choose_bandit_param(self.symbol, p_max_spread, candidates=c_max_spread, epsilon=0.25)
                    self.flow_max_spread_bps = float(v_max_spread)
                    self._learn_selected_params[p_max_spread] = float(v_max_spread)
                    self._log(
                        "auto_learn_param_chosen",
                        param=p_max_spread,
                        value=float(v_max_spread),
                        candidates=c_max_spread,
                    )

                    p_cooldown = "flow_trade_cooldown_s"
                    c_cooldown = [5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0]
                    v_cooldown = db.choose_bandit_param(self.symbol, p_cooldown, candidates=c_cooldown, epsilon=0.25)
                    self.flow_trade_cooldown_s = float(v_cooldown)
                    self._learn_selected_params[p_cooldown] = float(v_cooldown)
                    self._log(
                        "auto_learn_param_chosen",
                        param=p_cooldown,
                        value=float(v_cooldown),
                        candidates=c_cooldown,
                    )
                except Exception as e:
                    self._log("auto_learn_flow_param_error", error=str(e))

        self._last_price = self.entry_price
        self._peak_price = self.entry_price if self.mode == "sell" else None
        self._valley_price = self.entry_price if self.mode == "buy" else None

        self._executed_parts: List[float] = []
        self._initial_remaining = 1.0 - sum(p for _, p in self.targets)
        self._remaining_fraction = self._initial_remaining
        # When an order is rejected due to minimum size constraints, we can carry the
        # intended fraction forward and attempt to execute it together with a later target.
        self._carryover_fraction: float = 0.0
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
            auto_strategy=self.auto_strategy_enabled,
            public_flow=self.public_flow_enabled,
        )
        
        # Log dos custos de trading
        self._log(
            "trading_costs_configured",
            buy_fee_pct=self._buy_fee_pct,
            sell_fee_pct=self._sell_fee_pct,
            slippage_pct=self._slippage_pct,
            total_trading_cost_pct=self._total_trading_cost_pct,
            min_true_profit_pct=self._min_true_profit_pct,
            message=f"Targets ajustados para compensar taxas: +{self._total_trading_cost_pct:.2f}%"
        )

    def _symbol_base_quote(self) -> tuple[str, str]:
        try:
            if "-" in self.symbol:
                base, quote = self.symbol.split("-", 1)
                return base.strip().upper(), quote.strip().upper()
        except Exception:
            pass
        return self.symbol.upper(), ""

    def _get_available_balance_fast(self, currency: str) -> float:
        """Best-effort available balance (trade account).

        Uses a short-timeout private endpoint. If it fails, returns 0.
        """
        if not HAS_API or not api:
            return 0.0
        cur = str(currency or "").upper().strip()
        if not cur:
            return 0.0
        try:
            accounts = api.get_accounts_raw_fast(timeout=3.5)
        except Exception:
            return 0.0
        best = 0.0
        for a in (accounts or []):
            try:
                if str(a.get("type") or "") != "trade":
                    continue
                if str(a.get("currency") or "").upper().strip() != cur:
                    continue
                avail = float(a.get("available") or 0.0)
                if avail > best:
                    best = avail
            except Exception:
                continue
        return float(best)

    def _flow_next_chunk(self) -> tuple[Optional[float], float]:
        """Return next chunk portion for flow mode.

        Priority:
        1) next target portion (by list order)
        2) remaining_fraction + carryover
        """
        for pct, portion in self.targets:
            if pct in self._executed_parts:
                continue
            p = float(portion or 0.0) + float(self._carryover_fraction or 0.0)
            return float(pct), float(p)

        # No more targets; use remaining.
        total = float(self._remaining_fraction or 0.0) + float(self._carryover_fraction or 0.0)
        if total > 0.01:
            return None, float(total)
        return None, 0.0

    def _flow_mark_chunk_done(self, pct: Optional[float], portion_used: float):
        if pct is not None:
            try:
                self._executed_parts.append(float(pct))
            except Exception:
                pass
            self._carryover_fraction = 0.0
            return

        # Remaining bucket consumed
        self._remaining_fraction = 0.0
        self._carryover_fraction = 0.0

    def _maybe_trade_public_flow(self, now_ts: float, price: float):
        if not self.public_flow_enabled:
            return
        if analyze_public_flow is None:
            return

        if (now_ts - float(self._flow_last_eval_ts or 0.0)) < float(self.flow_eval_interval_s or 5.0):
            return
        self._flow_last_eval_ts = now_ts

        # Trade cooldown
        if (now_ts - float(self._flow_last_trade_ts or 0.0)) < float(self.flow_trade_cooldown_s or 0.0):
            return

        sig = None
        try:
            sig = analyze_public_flow(self.symbol)
        except Exception as e:
            self._log("public_flow_error", error=str(e))
            return

        if not sig or not isinstance(sig, dict):
            return

        bias = str(sig.get("bias") or "WAIT").upper().strip()
        conf = float(sig.get("confidence") or 0.0)
        spread_bps = float(sig.get("spread_bps") or 0.0)
        score = float(sig.get("score") or 0.0)

        self._log(
            "public_flow_snapshot",
            bias=bias,
            confidence=round(conf, 4),
            spread_bps=round(spread_bps, 2),
            score=round(score, 4),
            details=sig,
        )

        if spread_bps and spread_bps > float(self.flow_max_spread_bps or 25.0):
            return
        if conf < float(self.flow_min_confidence or 0.0):
            return
        if bias not in ("BUY", "SELL"):
            return

        pct, portion = self._flow_next_chunk()
        if portion <= 0.01:
            return

        # Execute at most one order per evaluation.
        side = "buy" if bias == "BUY" else "sell"

        # Store the last decision context (used to shape learning rewards for flow params).
        # Keep it minimal to avoid bloating logs/DB.
        try:
            self._last_flow_signal = {
                "ts": float(now_ts),
                "bias": str(bias),
                "confidence": float(conf),
                "spread_bps": float(spread_bps),
                "score": float(score),
            }
        except Exception:
            self._last_flow_signal = None

        # Balance guard for SELL in spot.
        if side == "sell":
            base, _quote = self._symbol_base_quote()
            avail_base = self._get_available_balance_fast(base)
            if avail_base <= 0:
                self._log("public_flow_skip_sell_no_balance", base=base)
                return

        res, sz = self._execute_fraction(float(portion), side)
        if self._is_order_ok(res):
            self._flow_last_trade_ts = now_ts
            self._record_trade(
                f"flow_{side}",
                price,
                float(portion),
                order_result=res,
                executed_size=sz,
                side_override=side,
            )
            self._flow_mark_chunk_done(pct, float(portion))
        elif self._is_min_size_rejection(res):
            # Carry forward to combine with the next chunk.
            self._log(
                "public_flow_min_size_carryover",
                bias=bias,
                attempted_portion=round(float(portion), 6),
                response=res,
            )
            self._carryover_fraction = float(portion)
            if pct is not None:
                try:
                    self._executed_parts.append(float(pct))
                except Exception:
                    pass
        else:
            self._log("public_flow_order_failed", bias=bias, response=res)

    def _decide_effective_mode_from_snapshot(self, snap: dict) -> Optional[str]:
        """Map regime snapshot -> effective mode.

        Semântica prática para este bot:
        - bias BUY  => priorizar targets de venda (modo sell)
        - bias SELL => priorizar recompras abaixo (modo buy)
        - bias WAIT => permitir bracket (modo mixed)
        """
        if not snap or not isinstance(snap, dict):
            return None
        bias = str(snap.get("bias") or "").upper().strip()
        conf = float(snap.get("confidence") or 0.0)

        # If low confidence, avoid flipping.
        if conf < 0.15:
            return None

        if bias == "BUY":
            return "sell"
        if bias == "SELL":
            return "buy"
        if bias == "WAIT":
            return "mixed"
        return None

    def _maybe_update_strategy_online(self, now_ts: float, price: float):
        if not self.auto_strategy_enabled:
            return
        if analyze_market_regime_5m is None:
            return

        # Evaluate at most every 30s.
        if (now_ts - float(self._auto_last_eval_ts or 0.0)) < 30.0:
            return
        self._auto_last_eval_ts = now_ts

        snap = None
        try:
            snap = analyze_market_regime_5m(self.symbol)
        except Exception as e:
            self._log("auto_strategy_error", error=str(e))
            return

        self._auto_last_snapshot = snap
        desired = self._decide_effective_mode_from_snapshot(snap)
        if not desired:
            return

        # Debounce mode changes: at least 60s between flips.
        if desired != self._auto_effective_mode and (now_ts - float(self._auto_last_change_ts or 0.0)) < 60.0:
            return

        if desired != self._auto_effective_mode:
            prev = self._auto_effective_mode
            self._auto_effective_mode = desired
            self.mode = desired

            # Keep peak/valley consistent when switching.
            if self.mode in ("sell", "mixed"):
                if self._peak_price is None:
                    self._peak_price = float(price)
            else:
                self._peak_price = None

            if self.mode in ("buy", "mixed"):
                if self._valley_price is None:
                    self._valley_price = float(price)
            else:
                self._valley_price = None

            self._auto_last_change_ts = now_ts
            self._log(
                "auto_strategy_mode_changed",
                prev_mode=prev,
                new_mode=self.mode,
                snapshot=snap,
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

    def _execute_fraction(self, portion: float, side: str) -> tuple[dict, float]:
        """Executa ordem para uma fração.

        Retorna (result, computed_size) para registrar no banco o tamanho real solicitado.
        """
        size = self._calculate_portion_size(portion)
        self._log("executing_order", side=side, portion=round(portion, 4), size=round(size, 8))

        result = place_market_order(
            self.symbol, side, size=size,
            dry_run=self.dry_run, logger=self._logger
        )
        return result, float(size or 0.0)

    def _is_order_ok(self, result: dict | None) -> bool:
        if not result or not isinstance(result, dict):
            return False
        if result.get("simulated") is True:
            return True
        code = result.get("code")
        return (code is None) or (str(code) == "200000")

    def _is_min_size_rejection(self, result: dict | None) -> bool:
        try:
            if not result or not isinstance(result, dict):
                return False
            msg = str(result.get("msg") or "")
            return "below the minimum" in msg.lower()
        except Exception:
            return False

    def _record_trade(
        self,
        kind: str,
        price: float,
        portion: float,
        order_result: dict | None = None,
        executed_size: float | None = None,
        side_override: str | None = None,
    ):
        """Registra trade.

        Importante: BUY não é PnL realizado. PnL (profit) só é registrado para SELL.
        Para fins de aprendizado, stop_loss também gera reward negativo (penalização).
        """

        # Determinar side de forma robusta
        side = (side_override or "").strip().lower()
        if not side:
            if "buy" in kind:
                side = "buy"
            elif "sell" in kind:
                side = "sell"
            else:
                side = "unknown"

        # Flag para identificar eventos que devem gerar penalização no aprendizado
        is_stop_loss = "stop_loss" in kind.lower()
        
        profit = None
        if side == "sell" or is_stop_loss:
            # Prefer executed_size (base qty) when available, because self.size may be unset
            # when the bot was configured with funds instead of size.
            base_qty = None
            try:
                if executed_size is not None:
                    base_qty = float(executed_size)
            except Exception:
                base_qty = None

            if base_qty is None and self.size:
                try:
                    base_qty = float(portion) * float(self.size)
                except Exception:
                    base_qty = None

            if base_qty is not None:
                try:
                    profit = float(base_qty) * (float(price) - float(self.entry_price))
                except Exception:
                    profit = None

        # Update learning after a realized SELL or stop_loss (reward = profit_pct).
        # Stop-loss events geram penalização (profit negativo) para o aprendizado.
        should_update_learning = (
            (side == "sell" or is_stop_loss) and 
            profit is not None and 
            self._learn_selected_params
        )
        if should_update_learning:
            try:
                # profit_pct normalized by entry notional (entry_price * qty)
                base_qty_for_pct = None
                try:
                    if executed_size is not None:
                        base_qty_for_pct = float(executed_size)
                except Exception:
                    base_qty_for_pct = None
                if base_qty_for_pct is None and self.size:
                    base_qty_for_pct = float(portion) * float(self.size)

                denom = float(self.entry_price) * float(base_qty_for_pct or 0.0)
                if denom > 0:
                    profit_pct = (float(profit) / denom) * 100.0
                    
                    # Penalização extra para stop-loss: multiplica o prejuízo por 1.5
                    # Isso faz o bot aprender a evitar configurações que levam a stop-loss
                    if is_stop_loss and profit_pct < 0:
                        profit_pct = profit_pct * 1.5  # penalização 50% extra
                        self._log(
                            "stop_loss_penalty_applied",
                            original_pct=round(float(profit) / denom * 100.0, 4),
                            penalized_pct=round(profit_pct, 4),
                        )
                    
                    db = self._get_db()

                    # Optional shaping for FLOW params: penalize wide spreads to prefer
                    # conditions that support better effective exits/entries.
                    spread_bps = 0.0
                    try:
                        if isinstance(self._last_flow_signal, dict):
                            spread_bps = float(self._last_flow_signal.get("spread_bps") or 0.0)
                    except Exception:
                        spread_bps = 0.0
                    # Convert bps -> percent (100 bps = 1%).
                    flow_reward = float(profit_pct) - (float(spread_bps) / 100.0)

                    # Apply the same realized outcome to every active learned param.
                    for pname, pval in (self._learn_selected_params or {}).items():
                        try:
                            pname_s = str(pname)
                            reward = float(flow_reward) if pname_s.startswith("flow_") else float(profit_pct)
                            db.update_bandit_reward(self.symbol, pname_s, float(pval), float(reward))
                            self._log(
                                "auto_learn_reward",
                                param=pname_s,
                                value=float(pval),
                                reward=round(float(reward), 6),
                                base_reward=round(float(profit_pct), 6),
                                spread_bps=round(float(spread_bps), 2),
                                kind=kind,
                                is_penalty=is_stop_loss,
                            )
                        except Exception:
                            continue

                    # Avoid leaking stale flow context into non-flow exits.
                    if str(kind or "").startswith("flow_"):
                        self._last_flow_signal = None
            except Exception:
                pass

        trade = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "kind": kind,
            "price": round(price, 2),
            "portion": round(portion, 4),
            "profit_usdt": round(float(profit or 0.0), 2),
            "simulated": self.dry_run
        }
        self.executed_trades.append(trade)
        self._log("trade_executed", **trade)
        
        # Gravar no banco de dados SQLite
        try:
            from .database import DatabaseManager
        except ImportError:
            from database import DatabaseManager
        
        try:
            db = DatabaseManager()

            order_id = None
            try:
                if isinstance(order_result, dict):
                    # KuCoin response: {code, data:{orderId}}
                    if isinstance(order_result.get("data"), dict) and order_result["data"].get("orderId"):
                        order_id = order_result["data"].get("orderId")
                    elif order_result.get("orderId"):
                        order_id = order_result.get("orderId")
            except Exception:
                order_id = None

            try:
                size_db = float(executed_size) if executed_size is not None else None
            except Exception:
                size_db = None

            trade_data = {
                "id": str(uuid.uuid4()),
                "timestamp": time.time(),
                "symbol": self.symbol,
                "side": side,
                "price": price,
                # IMPORTANTE: gravar quantidade (qty) e não a fração (portion)
                "size": size_db,
                "funds": (float(self.funds) * float(portion)) if (self.funds is not None and side == "buy") else None,
                "profit": profit,
                "commission": None,
                "order_id": None if self.dry_run else (str(order_id) if order_id else None),
                "bot_id": self.bot_id if hasattr(self, 'bot_id') else None,
                "strategy": kind,
                "dry_run": self.dry_run,
                "metadata": {"kind": kind, "portion": portion, "executed_size": size_db, "order": order_result}
            }
            db.insert_trade_ignore(trade_data)
            
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
        total = self._remaining_fraction + float(self._carryover_fraction or 0.0)
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
        """Retorna próximo target ajustado com custos de trading"""
        for pct, portion in self.targets:
            if pct not in self._executed_parts:
                pct_abs = abs(float(pct))
                
                # ====== CÁLCULO DE TARGET COM TAXAS ======
                # Para VENDA: target nominal + custo de trading = lucro líquido desejado
                # Exemplo: target 2%, custo 0.25% -> preço deve subir 2.25% para lucro líquido de 2%
                # Para COMPRA: target nominal - custo de trading
                
                # Runtime semantics:
                # - sell: upper target ajustado (entry * (1 + (|pct| + fees)/100))
                # - buy:  lower target ajustado (entry * (1 - (|pct| + fees)/100))
                # - mixed: bracket (ambos)
                
                fee_adjustment = self._total_trading_cost_pct
                
                # Para VENDA: precisa subir mais para compensar taxas
                upper_adjusted_pct = pct_abs + fee_adjustment
                upper = self.entry_price * (1 + upper_adjusted_pct / 100)
                upper_nominal = self.entry_price * (1 + pct_abs / 100)  # Sem ajuste (para referência)
                
                # Para COMPRA: precisa cair mais para compensar taxas
                lower_adjusted_pct = pct_abs + fee_adjustment  
                lower = self.entry_price * (1 - lower_adjusted_pct / 100)
                lower_nominal = self.entry_price * (1 - pct_abs / 100)  # Sem ajuste (para referência)

                if self.mode == "sell":
                    target_price = upper
                    distance_pct = ((target_price / self._last_price) - 1) * 100
                    return {
                        "pct": pct, 
                        "portion": portion, 
                        "price": target_price, 
                        "price_nominal": upper_nominal,
                        "distance_pct": distance_pct,
                        "fee_adjustment_pct": fee_adjustment,
                        "net_profit_pct": pct_abs
                    }
                if self.mode == "buy":
                    target_price = lower
                    distance_pct = ((target_price / self._last_price) - 1) * 100
                    return {
                        "pct": pct, 
                        "portion": portion, 
                        "price": target_price,
                        "price_nominal": lower_nominal, 
                        "distance_pct": distance_pct,
                        "fee_adjustment_pct": fee_adjustment,
                        "net_profit_pct": pct_abs
                    }

                # mixed: return both levels + nearest distance
                dist_upper = ((upper / self._last_price) - 1) * 100
                dist_lower = ((lower / self._last_price) - 1) * 100
                nearest = dist_upper if abs(dist_upper) <= abs(dist_lower) else dist_lower
                return {
                    "pct": pct,
                    "portion": portion,
                    "upper": upper,
                    "lower": lower,
                    "upper_nominal": upper_nominal,
                    "lower_nominal": lower_nominal,
                    "distance_pct": nearest,
                    "fee_adjustment_pct": fee_adjustment,
                    "net_profit_pct": pct_abs
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
        self._carryover_fraction = 0.0
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

                # Online strategy switching (regime 5m)
                self._maybe_update_strategy_online(time.time(), price)

                # Public flow trading (spot) — executes chunks on BUY/SELL signals
                if self.public_flow_enabled:
                    self._maybe_trade_public_flow(time.time(), price)
                
                # Atualiza peak/valley
                if self.mode in ("sell", "mixed"):
                    if self._peak_price is None or price > self._peak_price:
                        self._peak_price = price
                if self.mode in ("buy", "mixed"):
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
                                res, sz = self._execute_fraction(total, "sell")
                                self._record_trade("stop_loss", price, total, order_result=res, executed_size=sz, side_override="sell")
                            self._stopped.set()
                            break

                    # In mixed mode we allow both directions. For buy-style protection,
                    # a positive stop_loss_pct means adverse move upwards.
                    if self.mode == "mixed":
                        # SELL protection (same as sell)
                        threshold_sell = self.entry_price * (1 + self.stop_loss_pct / 100)
                        if price <= threshold_sell:
                            self._log("stop_loss_triggered", price=price, side="sell")
                            total = self._get_total_remaining()
                            if total > 0.01:
                                res, sz = self._execute_fraction(total, "sell")
                                self._record_trade("stop_loss", price, total, order_result=res, executed_size=sz, side_override="buy")
                            self._stopped.set()
                            break

                        # BUY protection: adverse move up from entry
                        threshold_buy = self.entry_price * (1 + abs(self.stop_loss_pct) / 100)
                        if price >= threshold_buy:
                            self._log("stop_loss_triggered", price=price, side="buy")
                            total = self._get_total_remaining()
                            if total > 0.01:
                                res, sz = self._execute_fraction(total, "buy")
                                self._record_trade("stop_loss", price, total, order_result=res, executed_size=sz, side_override="buy")
                            self._stopped.set()
                            break
                
                # Trailing stop
                if self.trailing_stop_pct is not None:
                    if self.mode in ("sell", "mixed") and self._peak_price:
                        threshold = self._peak_price * (1 - self.trailing_stop_pct / 100)
                        if price <= threshold:
                            self._log("trailing_stop_triggered", price=price)
                            total = self._get_total_remaining()
                            if total > 0.01:
                                res, sz = self._execute_fraction(total, "sell")
                                self._record_trade("trailing_stop", price, total, order_result=res, executed_size=sz, side_override="sell")
                            self._stopped.set()
                            break

                    if self.mode == "mixed" and self._valley_price:
                        threshold = self._valley_price * (1 + self.trailing_stop_pct / 100)
                        if price >= threshold:
                            self._log("trailing_stop_triggered", price=price, side="buy")
                            total = self._get_total_remaining()
                            if total > 0.01:
                                res, sz = self._execute_fraction(total, "buy")
                                self._record_trade("trailing_stop", price, total, order_result=res, executed_size=sz, side_override="buy")
                            self._stopped.set()
                            break
                
                # Targets (evita disparar múltiplos no mesmo ciclo)
                # In flow mode, we do NOT use price-based targets.
                if self.public_flow_enabled:
                    time.sleep(self.interval)
                    continue

                # If a SELL target is armed, trail from the peak to try to capture a higher exit.
                if self._armed_sell and self.mode in ("sell", "mixed"):
                    try:
                        peak = float(self._armed_sell.get("peak_price") or price)
                        if price > peak:
                            peak = price
                            self._armed_sell["peak_price"] = peak
                        trail = float(self._take_profit_trailing_pct or 0.5)
                        threshold = peak * (1 - trail / 100.0)
                        min_true_price = self.entry_price * (1 + float(self._min_true_profit_pct or 0.0) / 100.0)

                        # Only sell if we're still in "true profit" territory.
                        if price <= threshold and price >= min_true_price:
                            pct = self._armed_sell.get("pct")
                            portion = float(self._armed_sell.get("portion") or 0.0)
                            self._log(
                                "armed_target_trailing_exit",
                                target_pct=pct,
                                price=price,
                                peak_price=peak,
                                trail_pct=trail,
                                threshold=threshold,
                            )
                            res, sz = self._execute_fraction(portion, "sell")
                            if self._is_order_ok(res):
                                self._record_trade(f"target_sell_{pct}%", price, portion, order_result=res, executed_size=sz, side_override="sell")
                                try:
                                    self._executed_parts.append(pct)
                                except Exception:
                                    pass
                                self._armed_sell = None
                                time.sleep(self.interval)
                                continue
                            elif self._is_min_size_rejection(res):
                                self._log(
                                    "armed_target_min_size_carryover",
                                    target_pct=pct,
                                    price=price,
                                    attempted_portion=round(float(portion), 6),
                                    response=res,
                                )
                                self._carryover_fraction = float(portion)
                                try:
                                    self._executed_parts.append(pct)
                                except Exception:
                                    pass
                                self._armed_sell = None
                                time.sleep(self.interval)
                                continue
                            else:
                                self._log("armed_target_order_failed", target_pct=pct, price=price, response=res)
                    except Exception as e:
                        self._log("armed_target_error", error=str(e))

                for pct, portion in self.targets:
                    if pct in self._executed_parts:
                        continue
 
                    pct_f = float(pct)
                    pct_abs = abs(pct_f)
                    
                    # ====== CÁLCULO DE TARGETS COM CUSTOS DE TRADING ======
                    # Ajustar targets para compensar taxas de compra + venda + slippage
                    fee_adjustment = self._total_trading_cost_pct
                    
                    # Para VENDA: preço precisa subir mais para compensar taxas
                    upper_adjusted_pct = pct_abs + fee_adjustment
                    upper = self.entry_price * (1 + upper_adjusted_pct / 100)
                    
                    # Para COMPRA: preço precisa cair mais para compensar taxas  
                    lower_adjusted_pct = pct_abs + fee_adjustment
                    lower = self.entry_price * (1 - lower_adjusted_pct / 100)

                    # Backward compat: if user passes negative pct in buy mode, treat it as lower target.
                    if self.mode == "buy" and pct_f < 0:
                        lower = self.entry_price * (1 + (pct_f - fee_adjustment) / 100)

                    if self.mode == "sell":
                        min_true_price = self.entry_price * (1 + float(self._min_true_profit_pct or 0.0) / 100.0)
                        effective_threshold = max(upper, min_true_price)

                        if price >= effective_threshold:
                            # Arm the target and trail to try for higher peaks.
                            if self._armed_sell is None:
                                effective_portion = float(portion or 0.0) + float(self._carryover_fraction or 0.0)
                                self._carryover_fraction = 0.0
                                self._armed_sell = {
                                    "pct": pct,
                                    "portion": float(effective_portion),
                                    "armed_price": float(price),
                                    "peak_price": float(price),
                                    "threshold": float(effective_threshold),
                                }
                                self._log(
                                    "target_armed",
                                    target_pct=pct,
                                    price=price,
                                    threshold=effective_threshold,
                                    min_true_profit_pct=self._min_true_profit_pct,
                                    trail_pct=self._take_profit_trailing_pct,
                                    side="sell",
                                )
                                break
                    
                    elif self.mode == "buy" and price <= lower:
                        self._log("target_hit", target_pct=pct, price=price, side="buy")
                        effective_portion = float(portion or 0.0) + float(self._carryover_fraction or 0.0)
                        res, sz = self._execute_fraction(effective_portion, "buy")

                        if self._is_order_ok(res):
                            self._record_trade(f"target_buy_{pct}%", price, effective_portion, order_result=res, executed_size=sz)
                            self._executed_parts.append(pct)
                            self._carryover_fraction = 0.0
                            break
                        elif self._is_min_size_rejection(res):
                            self._log(
                                "target_min_size_carryover",
                                target_pct=pct,
                                price=price,
                                attempted_portion=round(effective_portion, 6),
                                carryover_next=round(effective_portion, 6),
                                response=res,
                            )
                            self._carryover_fraction = effective_portion
                            self._executed_parts.append(pct)
                            if effective_portion >= 0.99:
                                self._log("min_size_unrecoverable", message="Order size below minimum even at ~100% portion; stopping.")
                                self._stopped.set()
                                break
                            break
                        else:
                            self._log("target_order_failed", target_pct=pct, price=price, response=res)
                            break

                    elif self.mode == "mixed":
                        # Bracket behavior: whichever side hits first consumes the target.
                        if price >= upper:
                            min_true_price = self.entry_price * (1 + float(self._min_true_profit_pct or 0.0) / 100.0)
                            effective_threshold = max(upper, min_true_price)

                            if price >= effective_threshold:
                                if self._armed_sell is None:
                                    effective_portion = float(portion or 0.0) + float(self._carryover_fraction or 0.0)
                                    self._carryover_fraction = 0.0
                                    self._armed_sell = {
                                        "pct": pct,
                                        "portion": float(effective_portion),
                                        "armed_price": float(price),
                                        "peak_price": float(price),
                                        "threshold": float(effective_threshold),
                                    }
                                    self._log(
                                        "target_armed",
                                        target_pct=pct,
                                        price=price,
                                        threshold=effective_threshold,
                                        min_true_profit_pct=self._min_true_profit_pct,
                                        trail_pct=self._take_profit_trailing_pct,
                                        side="sell",
                                    )
                                    break

                        elif price <= lower:
                            self._log("target_hit", target_pct=pct, price=price, side="buy")
                            effective_portion = float(portion or 0.0) + float(self._carryover_fraction or 0.0)
                            res, sz = self._execute_fraction(effective_portion, "buy")
                            if self._is_order_ok(res):
                                self._record_trade(f"target_buy_{pct}%", price, effective_portion, order_result=res, executed_size=sz)
                                self._executed_parts.append(pct)
                                self._carryover_fraction = 0.0
                                break
                            elif self._is_min_size_rejection(res):
                                self._log(
                                    "target_min_size_carryover",
                                    target_pct=pct,
                                    price=price,
                                    attempted_portion=round(effective_portion, 6),
                                    carryover_next=round(effective_portion, 6),
                                    response=res,
                                )
                                self._carryover_fraction = effective_portion
                                self._executed_parts.append(pct)
                                if effective_portion >= 0.99:
                                    self._log("min_size_unrecoverable", message="Order size below minimum even at ~100% portion; stopping.")
                                    self._stopped.set()
                                    break
                                break
                            else:
                                self._log("target_order_failed", target_pct=pct, price=price, response=res)
                                break
                
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
