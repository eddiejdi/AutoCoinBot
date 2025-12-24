# kucoin_app/equity.py

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HISTORY_FILE = ROOT / "equity_history.json"


def add_equity_snapshot(balance_usdt: float):
    """Salva snapshot do patrimônio no arquivo JSON."""
    try:
        if HISTORY_FILE.exists():
            data = json.loads(HISTORY_FILE.read_text())
        else:
            data = []

        data.append({
            "ts": int(time.time()),
            "balance": float(balance_usdt)
        })

        HISTORY_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        print("Erro ao salvar equity:", e)


def load_equity_history():
    """Carrega histórico de patrimônio como lista de dicts."""
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text())
        return []
    except:
        return []


def snapshot_equity():
    """Snapshots current account balances as equity."""
    try:
        from .balance import get_account_balances_detail
        from .database import DatabaseManager
        
        result = get_account_balances_detail()
        if len(result) == 3:
            print(f"Erro ao obter saldos: {result[2]}")
            return False
        
        total_usdt, balances_rows = result
        if total_usdt is None:
            print("Total USDT é None")
            return False
        
        print(f"Total USDT: {total_usdt}, Balances: {len(balances_rows)}")
        
        # Prepare balances dict: currency -> usdt_value
        balances = {}
        for row in balances_rows:
            currency = row.get('currency')
            converted = row.get('converted_usdt')
            if currency and converted is not None and converted > 0:
                balances[currency] = converted
        
        print(f"Balances dict: {balances}")
        
        db = DatabaseManager()
        success = db.add_equity_snapshot(total_usdt, balances=balances)
        print(f"Snapshot added: {success}")
        return success
    except Exception as e:
        print(f"Erro ao snapshot equity: {e}")
        import traceback
        traceback.print_exc()
        return False
