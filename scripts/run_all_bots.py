#!/usr/bin/env python3
"""Start all bots defined in `bot_registry.json` in dry-run mode.

This helper reads `bot_registry.json` (if present) and starts a subprocess
for each bot config using `BotController`. It forces `dry=True` to avoid
placing real orders.

Usage:
  ./scripts/run_all_bots.py
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from bot_controller import BotController


def main():
    reg_file = HERE / "bot_registry.json"
    if not reg_file.exists():
        print("No bot_registry.json found; nothing to start.")
        return

    with open(reg_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    controller = BotController()
    started = []

    for bot_id, entry in (data.items() if isinstance(data, dict) else []):
        conf = entry.get('config') or entry
        symbol = conf.get('symbol')
        entry_price = conf.get('entry') or conf.get('entry_price') or 0
        mode = conf.get('mode', 'mixed')
        targets = conf.get('targets') or conf.get('targets_raw') or ""
        interval = conf.get('interval', 5)
        size = conf.get('size', 0)
        funds = conf.get('funds', 0)

        try:
            print(f"Starting bot from registry: {bot_id} -> {symbol} (dry)")
            new_id = controller.start_bot(symbol=symbol, entry=entry_price, mode=mode,
                                          targets=targets, interval=interval,
                                          size=size, funds=funds, dry=True)
            started.append(new_id)
        except Exception as e:
            print(f"Error starting bot {bot_id}: {e}")

    print(f"Started {len(started)} bots (dry-run): {started}")


if __name__ == '__main__':
    main()
