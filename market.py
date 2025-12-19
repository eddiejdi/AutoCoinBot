# market.py — VERSÃO FINAL 100% INQUEBRÁVEL
from . import api
import pandas as pd
import time
import math

def compute_signal_from_candles(symbol: str, rel_gap=0.00025, slope_window=3, min_candles=40):
    # Preço atual
    price_now = None
    try:
        price_now = api.get_orderbook_price(symbol)
        if isinstance(price_now, dict):  # proteção contra erro
            price_now = None
    except:
        price_now = None

    # Candles
    end = int(time.time())
    start = end - 150 * 3600
    try:
        candles = api.get_candles(symbol, ktype='1hour', startAt=start, endAt=end)
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
