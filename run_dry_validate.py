#!/usr/bin/env python3
"""
Start bots in dry-run and validate UI using agent0_scraper until validations pass.
Generates per-bot reports: relatorio_bot_<bot_id>.md and screenshot_<bot_id>.png
"""
import time
import os
from bot_controller import BotController
import agent0_scraper as scraper

DEFAULTS = {
    'symbol': 'BTC-USDT',
    'entry': 0.0,
    'mode': 'sell',
    'targets': '1:0.3,3:0.5,5:0.2',
    'interval': 5.0,
    'size': 0.0006,
    'funds': 20.0,
}

MAX_VALIDATION_ATTEMPTS = 5
WAIT_BETWEEN_VALIDATIONS = 3


def start_and_validate(num_bots: int = 1):
    controller = BotController()
    started = []
    try:
        for i in range(num_bots):
            bot_id = controller.start_bot(
                DEFAULTS['symbol'], DEFAULTS['entry'], DEFAULTS['mode'], DEFAULTS['targets'],
                DEFAULTS['interval'], DEFAULTS['size'], DEFAULTS['funds'], True
            )
            started.append(bot_id)
            print(f"Started dry-run bot {bot_id}")
            time.sleep(0.5)

        # For each bot, validate UI until pass or attempts exhausted
        for bot_id in list(started):
            print(f"Validating UI for bot {bot_id} ...")
            passed = False
            for attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):
                print(f"  validation attempt {attempt}/{MAX_VALIDATION_ATTEMPTS}")
                results, screenshot = scraper.validar_tela(scraper.APP_URL, scraper.ELEMENTOS_ESPERADOS, screenshot_path=f"screenshot_{bot_id}.png")
                report = scraper.gerar_relatorio(results, screenshot, scraper.APP_URL)
                fname = f"relatorio_bot_{bot_id}_attempt_{attempt}.md"
                with open(fname, 'w') as f:
                    f.write(report)
                print(f"  report saved: {fname}")

                # Determine pass: all expected selectors True
                expected = [s for (_, s) in scraper.ELEMENTOS_ESPERADOS]
                ok = all(results.get(sel, False) for sel in expected)
                if ok:
                    print(f"  Validation passed for {bot_id} on attempt {attempt}")
                    with open(f"relatorio_bot_{bot_id}.md", 'w') as f:
                        f.write(report)
                    passed = True
                    break
                else:
                    print(f"  Validation failed for {bot_id} on attempt {attempt}")
                    time.sleep(WAIT_BETWEEN_VALIDATIONS)

            if not passed:
                print(f"Validation failed for bot {bot_id} after {MAX_VALIDATION_ATTEMPTS} attempts")

    finally:
        # cleanup: stop started bots
        for bot_id in list(started):
            try:
                controller.stop_bot(bot_id)
                print(f"Stopped bot {bot_id}")
            except Exception:
                pass


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--num', type=int, default=1, help='Number of dry-run bots to start')
    args = p.parse_args()
    start_and_validate(args.num)
