#!/usr/bin/env python3
"""Quick test to debug button detection."""
import os
os.environ['LOCAL_URL'] = 'http://localhost:8501'
os.environ['APP_ENV'] = 'dev'

import agent0_scraper as s

print("Iniciando validação...")
r, sc = s.validar_tela('http://localhost:8501', s.ELEMENTOS_ESPERADOS, 'test_debug.png', check_buttons=True)

print("\n=== RESULTADOS ===")
print('button_texts:', r.get('button_texts', []))
print('login_preenchido:', r.get('login_preenchido'))
print()
for k, v in r.items():
    if 'button_label' in k:
        print(f'{k}: {v}')

print("\n=== ELEMENTOS PRINCIPAIS ===")
for k in ['h1', 'h2', 'stButton', 'stSidebar', 'stAlert', 'clickable_button_found']:
    print(f'{k}: {r.get(k)}')
