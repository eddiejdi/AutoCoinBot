#!/usr/bin/env python3
"""Teste simples para verificar PRAGMA/WAL e checkpoint.

Cria `data/test_trades_wal.db`, insere alguns registros e executa `wal_checkpoint`.
"""
from pathlib import Path
import time
import json

from database import DatabaseManager


def main():
    base = Path(__file__).resolve().parent.parent
    db_dir = base / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "test_trades_wal.db"

    # Remove DB antigo para teste limpo
    if db_path.exists():
        print("Removing existing test DB")
        db_path.unlink()

    db = DatabaseManager(db_path=db_path)

    # Inserir alguns trades
    for i in range(5):
        db.insert_trade({
            "id": f"t{i}",
            "timestamp": time.time(),
            "symbol": "BTC-USDT",
            "side": "buy" if i % 2 == 0 else "sell",
            "price": 20000 + i,
            "size": 0.001 * (i + 1),
            "funds": None,
            "profit": None if i % 2 == 0 else 10.0,
            "commission": 0.001,
            "order_id": f"o{i%2}",
            "bot_id": "TEST",
            "strategy": "kucoin_fill",
            "dry_run": True,
            "metadata": {}
        })

    # Atualizar bandit rewards
    db.update_bandit_reward("BTC-USDT", "alpha", 0.1, 1.0)
    db.update_bandit_reward("BTC-USDT", "alpha", 0.2, 0.5)

    # Criar histórico adicional
    for i in range(10):
        db.update_bandit_reward("BTC-USDT", "alpha", 0.1, 0.5 + i)

    # Executar checkpoint WAL
    ok = db.wal_checkpoint("PASSIVE")
    print("wal_checkpoint:", ok)

    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode")
    print("journal_mode:", cur.fetchone())
    cur.execute("PRAGMA wal_autocheckpoint")
    print("wal_autocheckpoint:", cur.fetchone())
    cur.execute("PRAGMA synchronous")
    print("synchronous:", cur.fetchone())
    conn.close()

    print("Files in db dir:")
    for p in sorted(db_path.parent.iterdir()):
        print(" -", p.name)


if __name__ == "__main__":
    main()
