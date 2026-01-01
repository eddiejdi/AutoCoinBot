# api.py - KuCoin API V1 - Versão Otimizada e Expandida
"""
Módulo de integração com KuCoin API V1
Suporta operações de mercado, saldo, histórico e análise de dados
"""

import os
import time
import hmac
import hashlib
import base64
import json
import requests
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from functools import wraps
from datetime import datetime, timedelta
from urllib.parse import urlencode

# ====================== CONFIGURAÇÃO DE LOGGING ======================
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Prefer LOG_DIR but fallback to a user-writable path if not writable (avoids root-owned log files)
def _prepare_log_handler():
    handlers = [logging.StreamHandler()]
    target = LOG_DIR / 'kucoin_api.log'
    try:
        # attempt to create the file if it doesn't exist and set permisssions
        if not target.exists():
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, 'a'):
                    pass
                try:
                    target.chmod(0o644)
                except Exception:
                    pass
            except PermissionError:
                raise
        handlers.insert(0, logging.FileHandler(target))
        return handlers
    except PermissionError:
        # fallback to user home dir logs
        home_logs = Path.home() / '.autocoinbot' / 'logs'
        home_logs.mkdir(parents=True, exist_ok=True)
        fallback = home_logs / 'kucoin_api.log'
        try:
            if not fallback.exists():
                with open(fallback, 'a'):
                    pass
                try:
                    fallback.chmod(0o644)
                except Exception:
                    pass
            handlers.insert(0, logging.FileHandler(fallback))
            print(f"[WARN] no permission to write {target}, using {fallback}")
        except Exception:
            # give up and just use StreamHandler
            pass
        return handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=_prepare_log_handler()
)
logger = logging.getLogger(__name__)

# ====================== LOAD ENVIRONMENT ======================
try:
    from dotenv import load_dotenv
    ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
    if ROOT_ENV.exists():
        load_dotenv(dotenv_path=str(ROOT_ENV))
        logger.info(f"✅ Loaded .env from {ROOT_ENV}")
    else:
        logger.warning("⚠️ No .env file found at project root")
except ImportError:
    logger.warning("⚠️ python-dotenv not installed, using system env vars only")

def _get_secret(key, default=""):
    # First try environment variables (for development)
    env_value = os.getenv(key, None)
    if env_value is not None:
        return env_value

    # Then try streamlit secrets
    try:
        import streamlit as st
        # 1. Busca no root (Streamlit Cloud expande para root)
        if key in st.secrets:
            return st.secrets[key]
        # 2. Busca na seção [secrets] se existir
        if 'secrets' in st.secrets and isinstance(st.secrets['secrets'], dict):
            if key in st.secrets['secrets']:
                return st.secrets['secrets'][key]
        # 3. Busca em outras seções
        for section in st.secrets:
            if isinstance(st.secrets[section], dict) and key in st.secrets[section]:
                return st.secrets[section][key]
        # 4. Se não encontrou, loga as chaves disponíveis para debug
        try:
            available = list(st.secrets.keys())
            logger.debug("[DEBUG] Chave '%s' não encontrada em st.secrets. Disponíveis: %s", key, available)
        except Exception:
            pass
        return default
    except (ImportError, AttributeError):
        return default

# ====================== API CREDENTIALS ======================
# Suporta tanto V1 quanto V2
API_KEY = _get_secret("API_KEYv1", "") or _get_secret("API_KEY", "")
API_SECRET = _get_secret("API_SECRETv1", "") or _get_secret("API_SECRET", "")
API_PASSPHRASE = _get_secret("API_PASSPHRASEv1", "") or _get_secret("API_PASSPHRASE", "")
API_KEY_VERSION = _get_secret("API_KEY_VERSION", "1")  # Default V1
KUCOIN_BASE = _get_secret("KUCOIN_BASE", "https://api.kucoin.com").rstrip("/")

# Other configs
TELEGRAM_BOT_TOKEN = _get_secret("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = _get_secret("TELEGRAM_CHAT_ID", "")
WEBHOOK_HOST = _get_secret("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(_get_secret("WEBHOOK_PORT", "5000"))
WEBHOOK_SANDBOX = int(_get_secret("WEBHOOK_SANDBOX", "0"))
WEBHOOK_DRYRUN = int(_get_secret("WEBHOOK_DRYRUN", "0"))
TRADES_DB = _get_secret("TRADES_DB", "trades.db")

# ====================== RATE LIMITING ======================
_last_request_time = 0
_min_request_interval = 0.1  # 100ms entre requests

def rate_limit():
    """Rate limiting para evitar throttling da API"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _min_request_interval:
        time.sleep(_min_request_interval - elapsed)
    _last_request_time = time.time()

# ====================== RETRY DECORATOR ======================
def retry_on_failure(max_retries: int = 3, backoff: float = 2.0):
    """Decorator para retry com backoff exponencial"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"❌ Failed after {max_retries} attempts: {e}")
                        raise
                    wait_time = backoff ** attempt
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                except Exception as e:
                    logger.error(f"❌ Unexpected error in {func.__name__}: {e}")
                    raise
            return None
        return wrapper
    return decorator

# ====================== HELPER FUNCTIONS ======================
def _base_url() -> str:
    """Retorna URL base da API"""
    return KUCOIN_BASE

def _has_keys() -> bool:
    """Verifica se credenciais estão configuradas"""
    return bool(API_KEY and API_SECRET and API_PASSPHRASE)


def _mask_headers_for_log(h: dict) -> dict:
    """Return a copy of headers with sensitive values masked for safe logging."""
    out = {}
    try:
        for k, v in (h or {}).items():
            if not isinstance(k, str):
                out[k] = v
                continue
            kl = k.upper()
            if kl in ("KC-API-KEY", "KC-API-PASSPHRASE", "KC-API-SIGN"):
                try:
                    s = str(v)
                    out[k] = s[:6] + "..." if len(s) > 6 else "***"
                except Exception:
                    out[k] = "***"
            else:
                out[k] = v
    except Exception:
        return h
    return out

def validate_credentials():
    """Valida credenciais da API"""
    if not _has_keys():
        raise RuntimeError(
            "❌ API credentials not configured. Please set API_KEY, API_SECRET, "
            "and API_PASSPHRASE in .env file or environment variables"
        )

# ====================== TIME SYNC ======================
# Cache do offset de tempo entre servidor e local para evitar chamadas repetidas
_time_offset_ms: int = 0  # offset = server_time - local_time
_time_offset_updated: float = 0.0  # quando foi atualizado
_TIME_OFFSET_TTL: float = 300.0  # atualizar offset a cada 5 minutos
_time_sync_failures: int = 0  # contador de falhas consecutivas


def _sync_time_offset() -> bool:
    """Sincroniza o offset de tempo com o servidor KuCoin.
    
    Retorna True se sincronizou com sucesso, False caso contrário.
    """
    global _time_offset_ms, _time_offset_updated, _time_sync_failures
    
    try:
        rate_limit()
        local_before = int(time.time() * 1000)
        r = requests.get(f"{KUCOIN_BASE}/api/v1/timestamp", timeout=10)
        local_after = int(time.time() * 1000)
        
        if r.status_code == 200:
            server_time = int(r.json().get("data", 0))
            if server_time > 0:
                # Usar média do tempo local para calcular offset
                local_avg = (local_before + local_after) // 2
                _time_offset_ms = server_time - local_avg
                _time_offset_updated = time.time()
                _time_sync_failures = 0
                
                if abs(_time_offset_ms) > 1000:
                    logger.info(f"🕐 Time offset synchronized: {_time_offset_ms}ms")
                return True
    except Exception as e:
        _time_sync_failures += 1
        logger.warning(f"⚠️ Time sync failed (attempt {_time_sync_failures}): {e}")
    
    return False


def _get_synced_timestamp() -> int:
    """Obtém timestamp sincronizado com o servidor.
    
    Usa cache de offset para evitar chamadas repetidas ao servidor.
    Se não conseguir sincronizar, usa tempo local com offset anterior.
    """
    global _time_offset_ms, _time_offset_updated, _time_sync_failures
    
    now = time.time()
    
    # Verificar se precisa re-sincronizar
    needs_sync = (
        _time_offset_updated == 0.0 or  # nunca sincronizou
        (now - _time_offset_updated) > _TIME_OFFSET_TTL or  # TTL expirado
        (_time_sync_failures > 0 and _time_sync_failures < 3)  # retry após falha
    )
    
    if needs_sync:
        _sync_time_offset()
    
    # Retornar tempo local + offset (mesmo que offset seja 0)
    return int(now * 1000) + _time_offset_ms


@retry_on_failure(max_retries=2)
def _server_time() -> int:
    """Obtém timestamp sincronizado em milliseconds.
    
    Usa sistema de cache de offset para melhor performance e resiliência.
    """
    return _get_synced_timestamp()

def _build_headers(method: str, endpoint: str, body_str: str = "", use_server_time: bool = True) -> Dict[str, str]:
    """Constrói headers para endpoints privados (suporta V1 e V2).

    `use_server_time=False` evita chamada ao endpoint de timestamp e usa o relógio local.
    Útil para telas/UI onde preferimos falhar rápido ao invés de bloquear o render.
    """
    validate_credentials()

    ts = str(_server_time() if use_server_time else int(time.time() * 1000))
    method_up = method.upper()
    to_sign = ts + method_up + endpoint + (body_str or "")
    
    signature = base64.b64encode(
        hmac.new(API_SECRET.encode(), to_sign.encode(), hashlib.sha256).digest()
    ).decode()
    
    # V1: passphrase em plain text
    # V2: passphrase encriptada com HMAC-SHA256
    if API_KEY_VERSION == "1":
        passphrase = API_PASSPHRASE
    else:
        passphrase = base64.b64encode(
            hmac.new(API_SECRET.encode(), API_PASSPHRASE.encode(), hashlib.sha256).digest()
        ).decode()

    return {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": ts,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": API_KEY_VERSION,
        "Content-Type": "application/json"
    }




# ====================== PUBLIC ENDPOINTS ======================

@retry_on_failure(max_retries=2)
def get_orderbook_price(symbol: str) -> Optional[Dict[str, Any]]:
    url = f"{KUCOIN_BASE}/api/v1/market/orderbook/level1?symbol={symbol}"

    try:
        rate_limit()
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        logger.warning(f"⚠️ Error fetching orderbook for {symbol}: {e}")
        return None

    # 🔑 VALIDAÇÃO OBRIGATÓRIA DA KUCOIN
    if not isinstance(j, dict) or j.get("code") != "200000":
        logger.error(f"❌ KuCoin API error ({symbol}): {j}")
        return None

    data = j.get("data")
    # KuCoin sometimes returns {code:200000, data:null} for unsupported symbols.
    # This is not an app error; treat it as "no market data".
    if data is None:
        logger.debug(f"No orderbook data for {symbol} (data=null)")
        return None
    if not isinstance(data, dict):
        logger.debug(f"Invalid orderbook payload type for {symbol}: {type(data)}")
        return None

    
    out = {}
    
    # Mid price
    for k in ("price", "last", "lastPrice", "close"):
        if k in data and data[k] is not None:
            try:
                out["mid_price"] = float(data[k])
                break
            except:
                pass
    
    # Best ask
    for ka in ("bestAsk", "best_ask", "ask"):
        if ka in data and data[ka] is not None:
            try:
                out["best_ask"] = float(data[ka])
                break
            except:
                pass
    
    # Best bid
    for kb in ("bestBid", "best_bid", "bid"):
        if kb in data and data[kb] is not None:
            try:
                out["best_bid"] = float(data[kb])
                break
            except:
                pass
    
    # Calcula mid_price se não encontrou
    if "mid_price" not in out and "best_ask" in out and "best_bid" in out:
        out["mid_price"] = (out["best_ask"] + out["best_bid"]) / 2.0
    
    # Timestamp
    for kt in ("timestamp", "time", "ts"):
        if kt in data and data[kt] is not None:
            try:
                out["timestamp"] = int(data[kt])
                break
            except:
                pass
    
    if not out:
        logger.warning(f"⚠️ Could not extract price data for {symbol}")
        return None
    
    logger.debug(f"📊 Orderbook {symbol}: mid={out.get('mid_price')}, "
                f"ask={out.get('best_ask')}, bid={out.get('best_bid')}")
    return out


def get_orderbook_price_fast(symbol: str, timeout: float = 1.5) -> Optional[Dict[str, Any]]:
    """Versão *sem retry* e com timeout baixo (ideal para UI)."""
    url = f"{KUCOIN_BASE}/api/v1/market/orderbook/level1?symbol={symbol}"

    try:
        rate_limit()
        r = requests.get(url, timeout=float(timeout))
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        logger.warning(f"⚠️ Error fetching orderbook (fast) for {symbol}: {e}")
        return None

    if not isinstance(j, dict) or j.get("code") != "200000":
        logger.error(f"❌ KuCoin API error ({symbol}) [fast]: {j}")
        return None

    data = j.get("data")
    # KuCoin sometimes returns {code:200000, data:null} for unsupported symbols.
    if data is None:
        # Keep UI quiet: this is expected for some currencies/pairs.
        return None
    if not isinstance(data, dict):
        return None

    out: Dict[str, Any] = {}

    for k in ("price", "last", "lastPrice", "close"):
        if k in data and data[k] is not None:
            try:
                out["mid_price"] = float(data[k])
                break
            except Exception:
                pass

    for ka in ("bestAsk", "best_ask", "ask"):
        if ka in data and data[ka] is not None:
            try:
                out["best_ask"] = float(data[ka])
                break
            except Exception:
                pass

    for kb in ("bestBid", "best_bid", "bid"):
        if kb in data and data[kb] is not None:
            try:
                out["best_bid"] = float(data[kb])
                break
            except Exception:
                pass

    if "mid_price" not in out and "best_ask" in out and "best_bid" in out:
        out["mid_price"] = (out["best_ask"] + out["best_bid"]) / 2.0

    for kt in ("timestamp", "time", "ts"):
        if kt in data and data[kt] is not None:
            try:
                out["timestamp"] = int(data[kt])
                break
            except Exception:
                pass

    if not out:
        return None
    return out

def get_price(symbol: str) -> Optional[float]:
    """Atalho para obter apenas o preço médio"""
    ob = get_orderbook_price(symbol)
    if ob and isinstance(ob, dict):
        return ob.get("mid_price")
    return None


def get_price_fast(symbol: str, timeout: float = 1.5) -> Optional[float]:
    """Atalho rápido para UI (sem retry, timeout curto)."""
    ob = get_orderbook_price_fast(symbol, timeout=timeout)
    if ob and isinstance(ob, dict):
        return ob.get("mid_price")
    return None

@retry_on_failure(max_retries=3)
def get_candles(symbol: str, ktype: str = "1hour", startAt: int = None, 
                endAt: int = None, timeout: float = 12.0) -> List[Any]:
    """
    Busca candles do endpoint público
    
    Args:
        symbol: Par (ex: BTC-USDT)
        ktype: Tipo de candle (1min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week)
        startAt: Unix timestamp em segundos
        endAt: Unix timestamp em segundos
    
    Returns:
        Lista de candles
    """
    url = f"{KUCOIN_BASE}/api/v1/market/candles?type={ktype}&symbol={symbol}"
    if startAt:
        url += f"&startAt={int(startAt)}"
    if endAt:
        url += f"&endAt={int(endAt)}"
    
    rate_limit()
    r = requests.get(url, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"❌ Error fetching candles: {r.status_code} - {r.text}")
    
    candles = r.json().get("data", [])
    logger.info(f"✅ Fetched {len(candles)} candles for {symbol}")
    return candles

def get_candles_safe(symbol: str, ktype: str = "1hour", startAt: int = None, 
                     endAt: int = None) -> List[List[Any]]:
    """
    Wrapper robusto que retorna candles normalizados
    
    Returns:
        Lista de [timestamp, open, close, high, low, volume, amount]
    """
    try:
        raw = get_candles(symbol, ktype=ktype, startAt=startAt, endAt=endAt)
        normalized = []
        
        for item in raw:
            try:
                if isinstance(item, dict):
                    t = int(item.get("time") or item.get("timestamp") or 0)
                    o = float(item.get("open", 0) or 0)
                    c = float(item.get("close", 0) or 0)
                    h = float(item.get("high", 0) or 0)
                    l = float(item.get("low", 0) or 0)
                    v = float(item.get("volume", 0) or 0)
                    amt = float(item.get("amount", 0) or 0)
                    normalized.append([t, o, c, h, l, v, amt])
                elif isinstance(item, (list, tuple)) and len(item) >= 6:
                    t = int(item[0])
                    o = float(item[1])
                    c = float(item[2])
                    h = float(item[3])
                    l = float(item[4])
                    v = float(item[5])
                    amt = float(item[6]) if len(item) > 6 else 0.0
                    normalized.append([t, o, c, h, l, v, amt])
            except:
                continue
                
        return normalized
    except Exception as e:
        logger.error(f"❌ Error in get_candles_safe: {e}")
        return []


def get_candles_fast(
    symbol: str,
    ktype: str = "1hour",
    startAt: int | None = None,
    endAt: int | None = None,
    timeout: float = 2.5,
) -> List[Any]:
    """Fast, no-retry candles fetch.

    Intended for UI rendering paths where blocking is worse than missing data.
    Returns an empty list on any error.
    """
    url = f"{KUCOIN_BASE}/api/v1/market/candles?type={ktype}&symbol={symbol}"
    if startAt:
        url += f"&startAt={int(startAt)}"
    if endAt:
        url += f"&endAt={int(endAt)}"

    try:
        rate_limit()
        r = requests.get(url, timeout=float(timeout))
        r.raise_for_status()
        j = r.json()
        if not isinstance(j, dict) or j.get("code") != "200000":
            return []
        data = j.get("data")
        return data if isinstance(data, list) else []
    except Exception:
        return []

@retry_on_failure(max_retries=2)
def get_all_symbols() -> List[Dict[str, Any]]:
    """
    Obtém todos os símbolos disponíveis na KuCoin
    
    Returns:
        Lista de símbolos com detalhes
    """
    url = f"{KUCOIN_BASE}/api/v1/symbols"
    
    try:
        rate_limit()
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        symbols = r.json().get("data", [])
        logger.info(f"✅ Fetched {len(symbols)} symbols")
        return symbols
    except Exception as e:
        logger.error(f"❌ Error fetching symbols: {e}")
        return []

def get_trading_pairs(quote_currency: str = "USDT") -> List[str]:
    """
    Retorna pares de trading ativos para uma moeda quote
    
    Args:
        quote_currency: Moeda quote (USDT, BTC, ETH, etc)
    
    Returns:
        Lista de símbolos (ex: ['BTC-USDT', 'ETH-USDT'])
    """
    symbols = get_all_symbols()
    pairs = [
        s["symbol"] for s in symbols 
        if s.get("quoteCurrency") == quote_currency and s.get("enableTrading")
    ]
    logger.info(f"✅ Found {len(pairs)} active {quote_currency} pairs")
    return sorted(pairs)

# ====================== PRIVATE ENDPOINTS ======================

@retry_on_failure(max_retries=2)
def get_fills(
    symbol: str | None = None,
    start_at: int | None = None,
    end_at: int | None = None,
    page_size: int = 100,
    current_page: int = 1,
) -> Dict[str, Any]:
    """Busca execuções (fills) da conta.

    Observação: start_at/end_at são timestamps em MILISSEGUNDOS.
    """
    validate_credentials()

    endpoint = "/api/v1/fills"

    def _normalize_ms_ts(v: int | None) -> int | None:
        if v is None:
            return None
        try:
            vv = int(v)
        except Exception:
            return None
        # If it's in seconds (10 digits-ish), convert to milliseconds.
        # Current epoch ms ~ 1.7e12, seconds ~ 1.7e9.
        if vv > 0 and vv < 10**11:
            vv *= 1000
        return vv

    try:
        page_size_i = int(page_size)
    except Exception:
        page_size_i = 100
    if page_size_i <= 0:
        page_size_i = 100
    # KuCoin constraint: pageSize must be >= 10
    if page_size_i < 10:
        page_size_i = 10

    try:
        current_page_i = int(current_page)
    except Exception:
        current_page_i = 1
    if current_page_i <= 0:
        current_page_i = 1

    params: Dict[str, Any] = {
        "pageSize": page_size_i,
        "currentPage": current_page_i,
    }
    if symbol:
        params["symbol"] = symbol
    start_ms = _normalize_ms_ts(start_at)
    end_ms = _normalize_ms_ts(end_at)

    # KuCoin may reject invalid/too-large ranges. Clamp and sanitize.
    try:
        if start_ms is not None and end_ms is not None:
            if start_ms > end_ms:
                start_ms, end_ms = end_ms, start_ms
            # Common KuCoin constraint: time range must be within last 7 days.
            max_range_ms = 7 * 24 * 60 * 60 * 1000
            now_ms = int(time.time() * 1000)

            # endAt cannot be in the future
            if end_ms > now_ms:
                end_ms = now_ms

            # If endAt is too old (outside the permitted window), move it to now.
            if end_ms < now_ms - max_range_ms:
                end_ms = now_ms

            # Clamp startAt to the permitted window.
            if start_ms < now_ms - max_range_ms:
                start_ms = now_ms - max_range_ms

            # Ensure the range itself is within max_range_ms.
            if end_ms - start_ms > max_range_ms:
                start_ms = end_ms - max_range_ms
    except Exception:
        pass

    if start_ms is not None:
        params["startAt"] = int(start_ms)
    if end_ms is not None:
        params["endAt"] = int(end_ms)

    qs = urlencode(params)
    signed_endpoint = f"{endpoint}?{qs}" if qs else endpoint
    url = f"{KUCOIN_BASE}{signed_endpoint}"

    headers = _build_headers("GET", signed_endpoint)
    rate_limit()
    r = requests.get(url, headers=headers, timeout=12)
    if r.status_code != 200:
        raise RuntimeError(f"❌ API fills error: {r.status_code} - {r.text}")
    j = r.json()
    if not isinstance(j, dict) or j.get("code") != "200000":
        raise RuntimeError(f"❌ KuCoin API error (fills): {j}")
    return j


def get_all_fills(
    symbol: str | None = None,
    start_at: int | None = None,
    end_at: int | None = None,
    page_size: int = 200,
    max_pages: int = 10,
) -> List[Dict[str, Any]]:
    """Paginação simples para coletar múltiplas páginas de fills."""
    items: List[Dict[str, Any]] = []

    try:
        max_pages_i = int(max_pages)
    except Exception:
        max_pages_i = 10
    if max_pages_i <= 0:
        max_pages_i = 10

    for p in range(1, max_pages_i + 1):
        j = get_fills(
            symbol=symbol,
            start_at=start_at,
            end_at=end_at,
            page_size=page_size,
            current_page=p,
        )
        data = (j or {}).get("data")
        page_items = []
        if isinstance(data, dict):
            page_items = data.get("items") or []
        if not isinstance(page_items, list):
            page_items = []

        for it in page_items:
            if isinstance(it, dict):
                items.append(it)

        # condição de parada: página menor que page_size
        if len(page_items) < int(page_size):
            break

    return items

@retry_on_failure(max_retries=3)
def get_accounts_raw() -> List[Dict[str, Any]]:
    """
    Retorna lista de contas da KuCoin
    
    Returns:
        Lista de contas com saldos
    """
    endpoint = "/api/v1/accounts"
    headers = _build_headers("GET", endpoint, "")
    rate_limit()
    try:
        logger.debug("[DEBUG KuCoin get_accounts_raw()] URL: %s", KUCOIN_BASE + endpoint)
        logger.debug("[DEBUG KuCoin get_accounts_raw()] HEADERS: %s", _mask_headers_for_log(headers))
    except Exception:
        pass
    r = requests.get(KUCOIN_BASE + endpoint, headers=headers, timeout=15)
    try:
        logger.debug("[DEBUG KuCoin get_accounts_raw()] STATUS: %s", r.status_code)
        # Log a truncated payload (avoid leaking secrets in unexpected places)
        txt = (r.text or "")
        logger.debug("[DEBUG KuCoin get_accounts_raw()] RAW RESPONSE (truncated %d chars): %s", len(txt), txt[:1024])
    except Exception:
        pass
    if r.status_code != 200:
        raise RuntimeError(f"❌ API accounts error: {r.status_code} - {r.text}")
    logger.info("✅ Successfully fetched accounts")
    data = r.json().get("data", [])
    logger.debug("[DEBUG KuCoin get_accounts_raw()] Retorno: %s", data)
    return data


def get_accounts_raw_fast(timeout: float = 4.0) -> List[Dict[str, Any]]:
    """Versão *sem retry* e com timeout curto (ideal para Streamlit/UI)."""
    endpoint = "/api/v1/accounts"
    headers = _build_headers("GET", endpoint, "", use_server_time=False)
    rate_limit()
    r = requests.get(KUCOIN_BASE + endpoint, headers=headers, timeout=float(timeout))
    if r.status_code != 200:
        raise RuntimeError(f"❌ API accounts error [fast]: {r.status_code} - {r.text}")
    return r.json().get("data", [])

def get_balances(account_type: str = "trade", min_balance: float = 0.0) -> List[Dict[str, Any]]:
    """
    Retorna saldos disponíveis filtrados
    
    Args:
        account_type: Tipo de conta (trade, main, margin)
        min_balance: Saldo mínimo para incluir
    
    Returns:
        Lista de saldos formatados
    """
    try:
        accounts = get_accounts_raw()
        balances = []
        
        for acc in accounts:
            if acc.get("type") != account_type:
                continue
            
            balance = float(acc.get("balance", 0) or 0)
            if balance < min_balance:
                continue
            
            balances.append({
                "currency": acc.get("currency"),
                "balance": balance,
                "available": float(acc.get("available", 0) or 0),
                "holds": float(acc.get("holds", 0) or 0),
                "account_type": acc.get("type"),
                "id": acc.get("id")
            })
        
        logger.info(f"✅ Found {len(balances)} non-zero {account_type} balances")
        return balances
        
    except Exception as e:
        logger.error(f"❌ Error getting balances: {e}")
        raise


def get_balances_fast(account_type: str = "trade", min_balance: float = 0.0, timeout: float = 4.0) -> List[Dict[str, Any]]:
    """Saldos com fail-fast (sem retry), pensado para não travar UI."""
    accounts = get_accounts_raw_fast(timeout=timeout)
    balances: List[Dict[str, Any]] = []
    for acc in accounts:
        if acc.get("type") != account_type:
            continue
        try:
            balance = float(acc.get("balance", 0) or 0)
        except Exception:
            balance = 0.0
        if balance < float(min_balance or 0.0):
            continue
        balances.append(
            {
                "currency": acc.get("currency"),
                "balance": balance,
                "available": float(acc.get("available", 0) or 0),
                "holds": float(acc.get("holds", 0) or 0),
                "account_type": acc.get("type"),
                "id": acc.get("id"),
            }
        )
    logger.info(f"✅ Found {len(balances)} non-zero {account_type} balances [fast]")
    return balances

def get_balance(details: bool = False) -> Any:
    """
    Calcula saldo total convertido para USDT
    
    Args:
        details: Se True, retorna (total_usdt, rows)
        
    Returns:
        float ou tuple: Valor total em USDT ou (total_usdt, detalhes)
    """
    try:
        accounts = get_accounts_raw()
        total_usdt = 0.0
        rows = []
        
        for acc in accounts:
            curr = acc.get("currency")
            balance = float(acc.get("balance", 0) or 0)
            available = float(acc.get("available", 0) or 0)
            holds = float(acc.get("holds", 0) or 0)

            converted = None
            used_pair = None

            if balance > 0:
                if curr in ("USDT", "USDC"):
                    converted = balance
                    used_pair = curr
                    total_usdt += converted
                else:
                    # Tenta pares diretos
                    for quote in ("USDT", "USDC"):
                        symbol = f"{curr}-{quote}"
                        try:
                            ob = get_orderbook_price(symbol)
                            if ob and isinstance(ob, dict):
                                price = ob.get("mid_price")
                                if price:
                                    converted = balance * price
                                    used_pair = symbol
                                    total_usdt += converted
                                    break
                        except:
                            continue
                    
                    # Tenta pares invertidos
                    if converted is None:
                        for quote in ("USDT", "USDC"):
                            symbol = f"{quote}-{curr}"
                            try:
                                ob = get_orderbook_price(symbol)
                                if ob and isinstance(ob, dict):
                                    price = ob.get("mid_price")
                                    if price and price > 0:
                                        converted = balance / price
                                        used_pair = f"{symbol} (inv)"
                                        total_usdt += converted
                                        break
                            except:
                                continue

            rows.append({
                "currency": curr,
                "balance": balance,
                "available": available,
                "holds": holds,
                "converted_usdt": round(converted, 6) if converted else 0.0,
                "used_pair": used_pair,
                "account_type": acc.get("type")
            })

        total_usdt = round(total_usdt, 6)
        logger.info(f"💰 Total balance: ${total_usdt:,.2f} USDT")
        
        if details:
            return total_usdt, rows
        return total_usdt

    except Exception as e:
        logger.error(f"❌ Error getting balance: {e}")
        raise

@retry_on_failure(max_retries=3)
def place_market_order(symbol: str, side: str, funds: float = None, 
                       size: float = None, client_oid: str = None) -> Dict[str, Any]:
    """
    Executa ordem de mercado na KuCoin
    
    Args:
        symbol: Par de trading (ex: BTC-USDT)
        side: "buy" "mixed" "sell"
        funds: Valor em moeda quote (USDT)
        size: Quantidade em moeda base (BTC)
        client_oid: ID customizado (gerado automaticamente se None)
    
    Returns:
        dict: Resposta da API
    """
    validate_credentials()
    
    endpoint = "/api/v1/orders"
    
    if client_oid is None:
        client_oid = f"bot_{int(time.time() * 1e6)}"
    
    payload = {
        "clientOid": client_oid,
        "side": side.lower(),
        "symbol": symbol,
        "type": "market",
    }
    
    if funds is not None:
        payload["funds"] = str(round(float(funds), 8))
    elif size is not None:
        payload["size"] = str(round(float(size), 12))
    else:
        raise ValueError("❌ Must specify either 'funds' or 'size'")
    
    body_str = json.dumps(payload, separators=(",", ":"))
    headers = _build_headers("POST", endpoint, body_str)
    
    logger.info(f"📤 Placing {side.upper()} order: {symbol} - funds={funds}, size={size}")
    
    rate_limit()
    r = requests.post(KUCOIN_BASE + endpoint, headers=headers, 
                     data=body_str, timeout=15)
    
    if r.status_code not in (200, 201):
        error_msg = f"❌ Error placing order: {r.status_code} - {r.text}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    result = r.json()
    
    if result.get("code") != "200000":
        error_msg = f"❌ API error: {result.get('msg', 'Unknown')}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    order_id = result.get("data", {}).get("orderId")
    logger.info(f"✅ Order placed: {side.upper()} {symbol} - OrderID: {order_id}")
    
    return result

@retry_on_failure(max_retries=2)
def get_order_details(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtém detalhes de uma ordem específica
    
    Args:
        order_id: ID da ordem
    
    Returns:
        dict com detalhes da ordem ou None
    """
    validate_credentials()
    
    endpoint = f"/api/v1/orders/{order_id}"
    headers = _build_headers("GET", endpoint, "")
    
    rate_limit()
    r = requests.get(KUCOIN_BASE + endpoint, headers=headers, timeout=10)
    
    if r.status_code != 200:
        logger.warning(f"⚠️ Error fetching order {order_id}: {r.status_code}")
        return None
    
    result = r.json()
    if result.get("code") == "200000":
        return result.get("data")
    
    return None

@retry_on_failure(max_retries=2)
def get_recent_orders(symbol: str = None, status: str = None, 
                     limit: int = 50) -> List[Dict[str, Any]]:
    """
    Obtém ordens recentes
    
    Args:
        symbol: Filtrar por símbolo (opcional)
        status: Filtrar por status (active, done)
        limit: Número máximo de ordens (1-500)
    
    Returns:
        Lista de ordens
    """
    validate_credentials()
    
    endpoint = "/api/v1/orders"
    params = []
    
    if symbol:
        params.append(f"symbol={symbol}")
    if status:
        params.append(f"status={status}")
    if limit:
        params.append(f"pageSize={min(limit, 500)}")
    
    if params:
        endpoint += "?" + "&".join(params)
    
    headers = _build_headers("GET", endpoint, "")
    
    rate_limit()
    r = requests.get(KUCOIN_BASE + endpoint, headers=headers, timeout=15)
    
    if r.status_code != 200:
        logger.error(f"❌ Error fetching orders: {r.status_code}")
        return []
    
    result = r.json()
    if result.get("code") == "200000":
        items = result.get("data", {}).get("items", [])
        logger.info(f"✅ Fetched {len(items)} orders")
        return items
    
    return []

@retry_on_failure(max_retries=2)
def get_account_history(currency: str = None, start_at: int = None, 
                       end_at: int = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Obtém histórico de transações da conta
    
    Args:
        currency: Filtrar por moeda (opcional)
        start_at: Timestamp início em ms
        end_at: Timestamp fim em ms
        limit: Número máximo de registros
    
    Returns:
        Lista de transações
    """
    validate_credentials()
    
    endpoint = "/api/v1/accounts/ledgers"
    params = []
    
    if currency:
        params.append(f"currency={currency}")
    if start_at:
        params.append(f"startAt={start_at}")
    if end_at:
        params.append(f"endAt={end_at}")
    if limit:
        params.append(f"pageSize={min(limit, 500)}")
    
    if params:
        endpoint += "?" + "&".join(params)
    
    headers = _build_headers("GET", endpoint, "")
    
    rate_limit()
    r = requests.get(KUCOIN_BASE + endpoint, headers=headers, timeout=15)
    
    if r.status_code != 200:
        logger.error(f"❌ Error fetching account history: {r.status_code}")
        return []
    
    result = r.json()
    if result.get("code") == "200000":
        items = result.get("data", {}).get("items", [])
        logger.info(f"✅ Fetched {len(items)} account history items")
        return items
    
    return []

# ====================== ANALYTICS ======================

def get_portfolio_summary() -> Dict[str, Any]:
    """
    Retorna resumo completo do portfolio
    
    Returns:
        dict com estatísticas do portfolio
    """
    try:
        total_usdt, rows = get_balance(details=True)
        
        # Filtra apenas com saldo
        non_zero = [r for r in rows if r["balance"] > 0]
        
        # Agrupa por tipo de conta
        by_type = {}
        for row in non_zero:
            acc_type = row.get("account_type", "unknown")
            if acc_type not in by_type:
                by_type[acc_type] = 0.0
            by_type[acc_type] += row.get("converted_usdt", 0.0)
        
        # Moedas com maior valor
        top_holdings = sorted(
            non_zero,
            key=lambda x: x.get("converted_usdt", 0.0),
            reverse=True
        )[:10]
        
        summary = {
            "total_usdt": total_usdt,
            "total_assets": len(non_zero),
            "by_account_type": by_type,
            "top_holdings": [
                {
                    "currency": h["currency"],
                    "balance": h["balance"],
                    "value_usdt": h["converted_usdt"],
                    "percentage": round((h["converted_usdt"] / total_usdt) * 100, 2) if total_usdt > 0 else 0
                }
                for h in top_holdings
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📊 Portfolio summary: ${total_usdt:,.2f} across {len(non_zero)} assets")
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error getting portfolio summary: {e}")
        raise

def get_market_overview(symbols: List[str] = None) -> List[Dict[str, Any]]:
    """
    Obtém overview de múltiplos mercados
    
    Args:
        symbols: Lista de símbolos (default: top USDT pairs)
    
    Returns:
        Lista com dados de mercado
    """
    if symbols is None:
        symbols = ["BTC-USDT", "ETH-USDT", "BNB-USDT", "SOL-USDT", "XRP-USDT"]
    
    overview = []
    
    for symbol in symbols:
        try:
            ob = get_orderbook_price(symbol)
            if ob:
                overview.append({
                    "symbol": symbol,
                    "price": ob.get("mid_price"),
                    "best_ask": ob.get("best_ask"),
                    "best_bid": ob.get("best_bid"),
                    "spread": round(
                        ((ob.get("best_ask", 0) - ob.get("best_bid", 0)) / ob.get("mid_price", 1)) * 100, 
                        3
                    ) if ob.get("mid_price") else None,
                    "timestamp": ob.get("timestamp")
                })
        except Exception as e:
            logger.warning(f"⚠️ Failed to get data for {symbol}: {e}")
            continue
    
    logger.info(f"📈 Market overview: {len(overview)} symbols fetched")
    return overview

# ====================== EXPORT LIST ======================
__all__ = [
    # Config
    'API_KEY', 'API_SECRET', 'API_PASSPHRASE', 'API_KEY_VERSION', 'KUCOIN_BASE',
    
    # Public
    'get_orderbook_price', 'get_price', 'get_candles', 'get_candles_safe',
    'get_all_symbols', 'get_trading_pairs',
    
    # Private
    'get_accounts_raw', 'get_balances', 'get_balance', 
    'place_market_order', 'get_order_details', 'get_recent_orders',
    'get_account_history',
    
    # Analytics
    'get_portfolio_summary', 'get_market_overview',
    
    # Utils
    '_has_keys', '_base_url', 'validate_credentials'
]

# ====================== SELF-TEST ======================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Running API self-test...")
    logger.info("=" * 60)
    
#    try:
#        # Config check
#        logger.info(f"KUCOIN_BASE: {KUCOIN_BASE}")
#        logger.info(f"API_KEY: {'✅ Set' if API_KEY else '❌ Not set'}")
#        logger.info(f"API_SECRET: {'✅ Set' if API_SECRET else '❌ Not set'}")
#        logger.info(f"API_PASS
