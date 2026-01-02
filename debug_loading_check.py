#!/usr/bin/env python3
"""Teste rápido da verificação de loading eterno."""
from agent0_scraper import _create_driver, _check_eternal_loading, _wait_page_ready
import time

print("[1] Criando driver...")
driver = _create_driver(headless=True)

print("[2] Acessando localhost:8501...")
driver.get("http://localhost:8501")

print("[3] Verificando loading...")
result = _wait_page_ready(driver, timeout=30, min_wait=3)

print(f"[4] Resultado:")
print(f"    - is_stuck: {result.get('is_stuck', False)}")
print(f"    - wait_time: {result.get('wait_time', 0):.1f}s")
print(f"    - details: {result.get('details', 'N/A')}")

driver.quit()
print("[5] TESTE CONCLUÍDO")
