# market.py — VERSÃO FINAL 100% INQUEBRÁVEL
try:
    # Preferred when running as a package (kucoin_app.market)
    from . import api
except Exception:
    # Fallback when running as a loose script/module
    import api  # type: ignore
import pandas as pd
import time
import math


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1 / max(1, period), adjust=False).mean()
    roll_down = down.ewm(alpha=1 / max(1, period), adjust=False).mean().replace(0, 1e-9)
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))


def analyze_market_regime_5m(
    symbol: str,
    min_candles: int = 120,
    lookback_hours: int = 24,
    ktype: str = "5min",
) -> dict:
    """Analyze 5m market regime to switch strategy (spot).

    Returns a dict with:
      - regime: 'trend' | 'range' | 'breakout_watch' | 'error' | 'no_data'
      - strategy: 'trend_following' | 'mean_reversion' | 'breakout'
      - bias: 'BUY' | 'SELL' | 'WAIT'
      - confidence: 0..1
      - scores: {trend, mean_reversion, breakout} each 0..1
      - metrics: lightweight indicators for debugging/telemetry
    """
    now_s = int(time.time())
    start_s = now_s - int(max(1, lookback_hours) * 3600)

    try:
        candles = api.get_candles_fast(symbol, ktype=ktype, startAt=start_s, endAt=now_s, timeout=2.5)
    except Exception as e:
        return {
            "symbol": symbol,
            "ktype": ktype,
            "regime": "error",
            "strategy": "trend_following",
            "bias": "WAIT",
            "confidence": 0.0,
            "scores": {"trend": 0.0, "mean_reversion": 0.0, "breakout": 0.0},
            "metrics": {"error": str(e)},
        }

    if not candles or len(candles) < min_candles:
        return {
            "symbol": symbol,
            "ktype": ktype,
            "regime": "no_data",
            "strategy": "trend_following",
            "bias": "WAIT",
            "confidence": 0.0,
            "scores": {"trend": 0.0, "mean_reversion": 0.0, "breakout": 0.0},
            "metrics": {"candles": len(candles or [])},
        }

    try:
        df = pd.DataFrame(candles[::-1], columns=["time", "open", "close", "high", "low", "volume", "amount"])
        df["time"] = pd.to_datetime(df["time"].astype(int), unit="s")
        for c in ("open", "close", "high", "low", "volume", "amount"):
            df[c] = df[c].astype(float)
    except Exception as e:
        return {
            "symbol": symbol,
            "ktype": ktype,
            "regime": "error",
            "strategy": "trend_following",
            "bias": "WAIT",
            "confidence": 0.0,
            "scores": {"trend": 0.0, "mean_reversion": 0.0, "breakout": 0.0},
            "metrics": {"error": f"df_parse:{e}"},
        }

    close = df["close"]
    price = float(close.iloc[-1]) if len(close) else 0.0
    if price <= 0:
        return {
            "symbol": symbol,
            "ktype": ktype,
            "regime": "error",
            "strategy": "trend_following",
            "bias": "WAIT",
            "confidence": 0.0,
            "scores": {"trend": 0.0, "mean_reversion": 0.0, "breakout": 0.0},
            "metrics": {"error": "bad_price"},
        }

    # Core indicators
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    sma20 = close.rolling(window=20, min_periods=20).mean()
    std20 = close.rolling(window=20, min_periods=20).std(ddof=0)
    rsi14 = _rsi(close, 14)

    # Trend strength: EMA separation + slope
    ema_sep_pct = (abs(ema20.iloc[-1] - ema50.iloc[-1]) / max(1e-9, price)) * 100.0
    slope_n = 6  # ~30 minutes on 5m
    try:
        ema20_prev = float(ema20.iloc[-1 - slope_n])
    except Exception:
        ema20_prev = float(ema20.iloc[0])
    slope_pct = ((float(ema20.iloc[-1]) - ema20_prev) / max(1e-9, ema20_prev)) * 100.0

    # Range/mean-reversion: z-score vs SMA20 + RSI extremes
    z = 0.0
    if not pd.isna(sma20.iloc[-1]) and not pd.isna(std20.iloc[-1]) and float(std20.iloc[-1]) > 0:
        z = (price - float(sma20.iloc[-1])) / float(std20.iloc[-1])
    rsi = float(rsi14.iloc[-1]) if not pd.isna(rsi14.iloc[-1]) else 50.0

    # Volatility compression (breakout watch): Bollinger bandwidth
    bandwidth = 0.0
    if not pd.isna(sma20.iloc[-1]) and not pd.isna(std20.iloc[-1]) and float(sma20.iloc[-1]) != 0:
        upper = float(sma20.iloc[-1]) + 2.0 * float(std20.iloc[-1])
        lower = float(sma20.iloc[-1]) - 2.0 * float(std20.iloc[-1])
        bandwidth = (upper - lower) / max(1e-9, float(sma20.iloc[-1]))

    # Normalize scores to 0..1 (simple heuristics tuned for 5m spot)
    trend_score = max(0.0, min(1.0, (ema_sep_pct / 0.20)))  # 0.20% separation ~ strong
    trend_score = max(trend_score, max(0.0, min(1.0, abs(slope_pct) / 0.25)))

    meanrev_score = max(0.0, min(1.0, (abs(z) / 2.0)))
    # add RSI component
    if rsi <= 35:
        meanrev_score = max(meanrev_score, min(1.0, (35 - rsi) / 15.0))
    elif rsi >= 65:
        meanrev_score = max(meanrev_score, min(1.0, (rsi - 65) / 15.0))

    breakout_score = 0.0
    # smaller bandwidth => higher compression score
    if bandwidth > 0:
        breakout_score = max(0.0, min(1.0, (0.03 - bandwidth) / 0.02))  # 3%->1% roughly

    # Choose regime/strategy
    # Priority: strong trend > breakout-watch (compression) > range
    if trend_score >= 0.65:
        regime = "trend"
        strategy = "trend_following"
    elif breakout_score >= 0.65:
        regime = "breakout_watch"
        strategy = "breakout"
    else:
        regime = "range"
        strategy = "mean_reversion"

    # Bias direction (spot semantics)
    bias = "WAIT"
    # Trend bias follows slope sign.
    if regime == "trend":
        if slope_pct > 0.03:
            bias = "BUY"
        elif slope_pct < -0.03:
            bias = "SELL"
        else:
            bias = "WAIT"
    elif regime == "range":
        # mean reversion: BUY when oversold, SELL when overbought
        if (rsi <= 35) or (z <= -1.2):
            bias = "BUY"
        elif (rsi >= 65) or (z >= 1.2):
            bias = "SELL"
        else:
            bias = "WAIT"
    else:
        # breakout_watch: wait for direction; small directional hint by slope
        if slope_pct > 0.05:
            bias = "BUY"
        elif slope_pct < -0.05:
            bias = "SELL"
        else:
            bias = "WAIT"

    scores = {
        "trend": float(max(0.0, min(1.0, trend_score))),
        "mean_reversion": float(max(0.0, min(1.0, meanrev_score))),
        "breakout": float(max(0.0, min(1.0, breakout_score))),
    }
    # Confidence: gap between top-1 and top-2 scores
    top = sorted(scores.values(), reverse=True)
    confidence = float(max(0.0, min(1.0, (top[0] - top[1]) if len(top) > 1 else top[0])))

    return {
        "symbol": symbol,
        "ktype": ktype,
        "price": price,
        "regime": regime,
        "strategy": strategy,
        "bias": bias,
        "confidence": confidence,
        "scores": scores,
        "metrics": {
            "ema_sep_pct": float(ema_sep_pct),
            "slope_pct": float(slope_pct),
            "rsi14": float(rsi),
            "z": float(z),
            "bb_bandwidth": float(bandwidth),
            "candles": int(len(df)),
        },
    }

def compute_signal_from_candles(symbol: str, rel_gap=0.00025, slope_window=3, min_candles=40):
    # Preço atual
    price_now = None
    try:
        ob = api.get_orderbook_price_fast(symbol, timeout=2.0)
        if isinstance(ob, dict):
            price_now = ob.get("mid_price")
    except:
        price_now = None

    # Candles
    end = int(time.time())
    start = end - 150 * 3600
    try:
        candles = api.get_candles_fast(symbol, ktype='1hour', startAt=start, endAt=end, timeout=2.5)
    except Exception as e:
        return price_now or 0.0, None, None, "ERRO API", "#ff0000", None, None, "ERROR"

    if not candles or len(candles) < min_candles:
        return price_now or 0.0, None, None, "SEM DADOS", "#888888", None, None, "WAIT"

    try:
        df = pd.DataFrame(candles[::-1], columns=["time","open","close","high","low","volume","amount"])
        df['time'] = pd.to_datetime(df['time'].astype(int), unit='s')
        df[['open','close','high','low','volume','amount']] = df[['open','close','high','low','volume','amount']].astype(float)

        # Indicadores
        df['MA9'] = df['close'].rolling(window=9, min_periods=1).mean()
        df['MA21'] = df['close'].rolling(window=21, min_periods=1).mean()

        delta = df['close'].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.ewm(alpha=1/14, adjust=False).mean()
        roll_down = down.ewm(alpha=1/14, adjust=False).mean().replace(0, 1e-9)
        rs = roll_up / roll_down
        df['RSI'] = 100 - (100 / (1 + rs))

        df['ma_diff'] = df['MA9'] - df['MA21']
        df['ma9_shift'] = df['MA9'].shift(slope_window)
        df['slope'] = df['MA9'] - df['ma9_shift']

        def safe_get(series, idx=-1, default=None):
            try:
                val = series.iloc[idx]
                return None if pd.isna(val) else float(val)
            except:
                return default

        current_rsi = safe_get(df['RSI'])
        ma9 = safe_get(df['MA9'])
        ma21 = safe_get(df['MA21'])
        ma_diff = safe_get(df['ma_diff'])
        prev_ma_diff = safe_get(df['ma_diff'], -2)
        slope = safe_get(df['slope'])
        price_ref = safe_get(df['close']) or price_now or 1.0

        gap_threshold = price_ref * rel_gap

        signal = "AGUARDE"
        color = "#ffaa00"
        emoji = "WAIT"

        # Lógica de sinal simplificada e robusta
        if current_rsi is not None:
            if current_rsi < 30 and ma9 is not None and price_ref < ma9:
                signal, color, emoji = "COMPRA FORTE", "#00ff00", "BUY"
            elif current_rsi < 40 and ma9 is not None and price_ref < ma9:
                signal, color, emoji = "COMPRA", "#00ff88", "BUY"
            elif current_rsi > 70 and ma9 is not None and price_ref > ma9:
                signal, color, emoji = "VENDA FORTE", "#ff0000", "SELL"
            elif current_rsi > 60 and ma9 is not None and price_ref > ma9:
                signal, color, emoji = "VENDA", "#ff4444", "SELL"
            elif ma_diff is not None and prev_ma_diff is not None:
                if prev_ma_diff <= gap_threshold and ma_diff > gap_threshold:
                    signal, color, emoji = "CRUZAMENTO ALTISTA", "#00ff00", "BUY"
                elif prev_ma_diff >= -gap_threshold and ma_diff < -gap_threshold:
                    signal, color, emoji = "CRUZAMENTO BAIXISTA", "#ff0000", "SELL"

        return float(price_now or 0), df, current_rsi, signal, color, ma9, ma21, emoji

    except Exception as e:
        return float(price_now or 0), None, None, "ERRO INTERNO", "#ff0000", None, None, "ERROR"
