#!/usr/bin/env python3
"""Small helper to inspect `trades.db` using DatabaseManager.

Usage examples:
  ./scripts/db_inspect.py logs --bot BOT_ID --limit 50
  ./scripts/db_inspect.py sessions
  ./scripts/db_inspect.py trades --bot BOT_ID --limit 50
  ./scripts/db_inspect.py order --order-id ORDER_ID
  ./scripts/db_inspect.py equity --limit 20
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from database import DatabaseManager


def print_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_logs(args):
    db = DatabaseManager()
    logs = db.get_bot_logs(args.bot, limit=args.limit) if hasattr(db, 'get_bot_logs') else []
    # Fallback: query directly if method not present
    if not logs:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT timestamp, level, message, data FROM bot_logs WHERE bot_id = ? ORDER BY timestamp DESC LIMIT ?", (args.bot, args.limit))
        rows = cur.fetchall()
        logs = [dict(r) for r in rows]
        conn.close()
    print_json(logs)


def cmd_sessions(args):
    db = DatabaseManager()
    sessions = db.get_active_bots()
    print_json(sessions)


def cmd_trades(args):
    db = DatabaseManager()
    rows = db.get_trade_history_grouped(limit=args.limit, bot_id=args.bot) if hasattr(db, 'get_trade_history_grouped') else []
    print_json(rows)


def cmd_order(args):
    db = DatabaseManager()
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trades WHERE order_id = ?", (args.order_id,))
    rows = cur.fetchall()
    conn.close()
    print_json([dict(r) for r in rows])


def cmd_equity(args):
    db = DatabaseManager()
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT timestamp, balance_usdt, btc_price, average_cost FROM equity_snapshots ORDER BY timestamp DESC LIMIT ?", (args.limit,))
    rows = cur.fetchall()
    conn.close()
    print_json([dict(r) for r in rows])


def main():
    p = argparse.ArgumentParser(description="Inspect trades.db")
    sub = p.add_subparsers(dest='cmd')

    a = sub.add_parser('logs', help='Fetch recent logs for a bot')
    a.add_argument('--bot', required=True)
    a.add_argument('--limit', type=int, default=50)

    a = sub.add_parser('sessions', help='List active bot sessions')

    a = sub.add_parser('trades', help='Recent trades (grouped)')
    a.add_argument('--bot', required=False)
    a.add_argument('--limit', type=int, default=50)

    a = sub.add_parser('order', help='Find trades by order id')
    a.add_argument('--order-id', required=True)

    a = sub.add_parser('equity', help='Recent equity snapshots')
    a.add_argument('--limit', type=int, default=50)

    args = p.parse_args()
    if args.cmd == 'logs':
        cmd_logs(args)
    elif args.cmd == 'sessions':
        cmd_sessions(args)
    elif args.cmd == 'trades':
        cmd_trades(args)
    elif args.cmd == 'order':
        cmd_order(args)
    elif args.cmd == 'equity':
        cmd_equity(args)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
