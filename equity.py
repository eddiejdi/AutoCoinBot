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

