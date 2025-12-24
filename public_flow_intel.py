"""Public (anonymous) market-flow signal for KuCoin spot.

This is NOT copy-trading a person.
It derives signals from public market data:
- Order book depth imbalance (level2_20)
- Recent trade aggressor imbalance (market histories)

It is designed to be fail-fast and safe to call in a trading loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import time
import requests


def _kucoin_base() -> str:
    try:
        import api  # local module

        return str(getattr(api, "KUCOIN_BASE"))
    except Exception:
        return "https://api.kucoin.com"


@dataclass
class FlowSignal:
    bias: str  # BUY|SELL|WAIT
    confidence: float
    score: float
    spread_bps: float
    depth_imbalance: float
    trade_imbalance: float
    mid: float
    best_bid: float
    best_ask: float
    ts: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "bias": self.bias,
            "confidence": float(self.confidence),
            "score": float(self.score),
            "spread_bps": float(self.spread_bps),
            "depth_imbalance": float(self.depth_imbalance),
            "trade_imbalance": float(self.trade_imbalance),
            "mid": float(self.mid),
            "best_bid": float(self.best_bid),
            "best_ask": float(self.best_ask),
            "ts": float(self.ts),
        }


def _public_get_json(url: str, timeout: float) -> Optional[dict]:
    try:
        r = requests.get(url, timeout=float(timeout), headers={"User-Agent": "kucoin_app/1.0"})
        r.raise_for_status()
        j = r.json()
        if not isinstance(j, dict):
            return None
        if j.get("code") != "200000":
            return None
        return j
    except Exception:
        return None


def _get_level1(symbol: str, timeout: float = 2.0) -> Tuple[float, float, float]:
    base = _kucoin_base()
    j = _public_get_json(f"{base}/api/v1/market/orderbook/level1?symbol={symbol}", timeout=timeout)
    if not j:
        return 0.0, 0.0, 0.0
    data = j.get("data")
    if not isinstance(data, dict):
        return 0.0, 0.0, 0.0

    def _f(key: str) -> float:
        try:
            return float(data.get(key) or 0.0)
        except Exception:
            return 0.0

    best_bid = _f("bestBid") or _f("best_bid")
    best_ask = _f("bestAsk") or _f("best_ask")
    mid = _f("price") or _f("last") or 0.0
    if mid <= 0 and best_bid > 0 and best_ask > 0:
        mid = (best_bid + best_ask) / 2.0
    return mid, best_bid, best_ask


def _get_level2_20(symbol: str, timeout: float = 2.5) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    base = _kucoin_base()
    j = _public_get_json(f"{base}/api/v1/market/orderbook/level2_20?symbol={symbol}", timeout=timeout)
    if not j:
        return [], []
    data = j.get("data")
    if not isinstance(data, dict):
        return [], []

    bids_raw = data.get("bids") or []
    asks_raw = data.get("asks") or []

    def _parse_side(raw: Any) -> List[Tuple[float, float]]:
        out: List[Tuple[float, float]] = []
        if not isinstance(raw, list):
            return out
        for row in raw[:20]:
            try:
                if isinstance(row, (list, tuple)) and len(row) >= 2:
                    p = float(row[0])
                    s = float(row[1])
                    if p > 0 and s > 0:
                        out.append((p, s))
            except Exception:
                continue
        return out

    return _parse_side(bids_raw), _parse_side(asks_raw)


def _get_recent_trades(symbol: str, timeout: float = 2.5) -> List[dict]:
    base = _kucoin_base()
    j = _public_get_json(f"{base}/api/v1/market/histories?symbol={symbol}", timeout=timeout)
    if not j:
        return []
    data = j.get("data")
    if not isinstance(data, list):
        return []
    out: List[dict] = []
    for it in data[:120]:
        if isinstance(it, dict):
            out.append(it)
    return out


def analyze_public_flow(
    symbol: str,
    *,
    timeout_level1: float = 2.0,
    timeout_level2: float = 2.5,
    timeout_trades: float = 2.5,
) -> Optional[dict]:
    """Compute a conservative microstructure signal.

    Returns a dict with keys: bias, confidence, score, spread_bps, depth_imbalance, trade_imbalance, mid, best_bid, best_ask.
    """
    sym = str(symbol or "").upper().strip()
    if not sym:
        return None

    mid, best_bid, best_ask = _get_level1(sym, timeout=timeout_level1)
    if mid <= 0:
        return None

    spread_bps = 0.0
    if best_bid > 0 and best_ask > 0 and mid > 0:
        spread_bps = ((best_ask - best_bid) / mid) * 10000.0

    bids, asks = _get_level2_20(sym, timeout=timeout_level2)
    sum_b = sum(s for _, s in bids) if bids else 0.0
    sum_a = sum(s for _, s in asks) if asks else 0.0
    depth_imb = 0.0
    if (sum_b + sum_a) > 0:
        depth_imb = (sum_b - sum_a) / (sum_b + sum_a)

    trades = _get_recent_trades(sym, timeout=timeout_trades)
    buy_v = 0.0
    sell_v = 0.0
    for t in trades:
        side = str(t.get("side") or "").lower().strip()
        # KuCoin histories uses 'size' (base) and 'price'.
        try:
            size = float(t.get("size") or 0.0)
        except Exception:
            size = 0.0
        if size <= 0:
            continue
        if side == "buy":
            buy_v += size
        elif side == "sell":
            sell_v += size

    trade_imb = 0.0
    if (buy_v + sell_v) > 0:
        trade_imb = (buy_v - sell_v) / (buy_v + sell_v)

    # Combine signals.
    score = 0.55 * depth_imb + 0.45 * trade_imb

    # Penalize wide spreads (low quality fills).
    spread_penalty = 1.0
    if spread_bps > 15:
        spread_penalty = max(0.15, 1.0 - min(0.85, (spread_bps - 15) / 50.0))

    # Penalize low sample sizes.
    sample_penalty = 1.0
    n_trades = len(trades)
    if n_trades < 30:
        sample_penalty *= 0.75
    if (sum_b + sum_a) <= 0:
        sample_penalty *= 0.6

    confidence = min(1.0, abs(score)) * spread_penalty * sample_penalty

    thr = 0.18
    bias = "WAIT"
    if score >= thr:
        bias = "BUY"
    elif score <= -thr:
        bias = "SELL"

    sig = FlowSignal(
        bias=bias,
        confidence=float(confidence),
        score=float(score),
        spread_bps=float(spread_bps),
        depth_imbalance=float(depth_imb),
        trade_imbalance=float(trade_imb),
        mid=float(mid),
        best_bid=float(best_bid or 0.0),
        best_ask=float(best_ask or 0.0),
        ts=float(time.time()),
    )
    return sig.as_dict()
