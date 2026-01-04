from . import api
import math

def get_account_balances_detail():
    try:
        raw = api.get_accounts_raw()
    except Exception as e:
        return None, [], {'error': str(e)}

    total = 0.0
    rows = []

    for acc in raw:
        currency = acc.get('currency')
        try:
            balance = float(acc.get('balance') or 0)
        except Exception:
            balance = 0.0
        try:
            available = float(acc.get('available') or 0)
        except Exception:
            available = 0.0
        try:
            holds = float(acc.get('holds') or 0)
        except Exception:
            holds = 0.0

        converted = None
        quote_used = None
        converted_error = None

        if currency in ('USDT','USDC'):
            converted = balance
            quote_used = currency

        if balance <= 0:
            rows.append({
                'currency': currency,
                'balance': balance,
                'available': available,
                'holds': holds,
                'converted_usdt': 0.0 if converted is not None else None,
                'quote': quote_used,
                'converted_error': None
            })
            if converted is not None:
                total += float(converted)
            continue

        if converted is None:
            for q in ('USDT','USDC'):
                symbol = f"{currency}-{q}"
                try:
                    price = api.get_orderbook_price(symbol)
                    if price is not None:
                        converted = balance * float(price)
                        quote_used = q
                        break
                except Exception as e:
                    converted_error = f"{symbol}: {e}"
                    continue

        if converted is None:
            for q in ('USDT','USDC'):
                symbol_inv = f"{q}-{currency}"
                try:
                    price_inv = api.get_orderbook_price(symbol_inv)
                    if price_inv:
                        converted = balance * (1.0 / float(price_inv))
                        quote_used = q
                        converted_error = f"converted via inverse {symbol_inv}"
                        break
                except Exception as e:
                    converted_error = (converted_error or '') + f" ; inv {symbol_inv}: {e}"
                    continue

        converted_f = float(converted) if converted is not None else None
        if converted_f is not None and not (isinstance(converted_f, float) and math.isnan(converted_f)):
            total += converted_f

        rows.append({
            'currency': currency,
            'balance': balance,
            'available': available,
            'holds': holds,
            'converted_usdt': round(converted_f, 6) if converted_f is not None else None,
            'quote': quote_used,
            'converted_error': converted_error
        })

    return round(total,6), rows
