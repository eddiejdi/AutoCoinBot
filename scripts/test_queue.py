#!/usr/bin/env python3
"""Teste do sistema de fila: enfileira várias INSERTs via `enqueue_sql`.
"""
from pathlib import Path
import time

from database import DatabaseManager


def main():
    base = Path(__file__).resolve().parent.parent
    db_dir = base / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "test_queue.db"

    # remove antigo
    if db_path.exists():
        db_path.unlink()

    db = DatabaseManager(db_path=db_path)

    # Cria algumas tasks de insert em paralelo (enfileiradas)
    tasks = []
    for i in range(20):
        sql = "INSERT INTO bot_learning_history (timestamp, symbol, param_name, param_value, reward) VALUES (?, ?, ?, ?, ?)"
        params = (time.time(), 'BTC-USDT', 'alpha', 0.1, float(i))
        t = db.enqueue_sql(sql, params)
        tasks.append(t)

    # Aguarda resultados
    for t in tasks:
        try:
            res = t.wait(timeout=5)
            print("rowcount:", res)
        except Exception as e:
            print("task error:", e)

    # Verifica contagem
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM bot_learning_history")
    print("count:", cur.fetchone()[0])
    conn.close()


if __name__ == '__main__':
    main()
