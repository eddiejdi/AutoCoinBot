#!/usr/bin/env python3
"""Start a dry-run bot using `current_config.json` (if present).
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from bot_controller import BotController


def main():
    cfg_file = HERE / "current_config.json"
    if not cfg_file.exists():
        print("No current_config.json found; nothing to start.")
        return

    cfg = json.loads(cfg_file.read_text(encoding='utf-8'))
    symbol = cfg.get('symbol')
    entry = cfg.get('entry_price') or cfg.get('entry') or 0
    mode = cfg.get('mode', 'mixed')
    targets = cfg.get('targets')
    if isinstance(targets, list):
        # convert [[2,0.3]] to "2:0.3,5:0.4"
        try:
            targets_s = ",".join([f"{int(t[0])}:{float(t[1])}" for t in targets])
        except Exception:
            targets_s = ""
    else:
        targets_s = str(targets or "")

    interval = cfg.get('interval', 5)
    size = cfg.get('size', 0)
    funds = cfg.get('funds', 0)

    controller = BotController()
    bot_id = controller.start_bot(symbol=symbol, entry=entry, mode=mode, targets=targets_s,
                                  interval=interval, size=size, funds=funds, dry=True)
    print(f"Started dry-run bot {bot_id} from current_config.json")


if __name__ == '__main__':
    main()
