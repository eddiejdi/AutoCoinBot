#!/usr/bin/env python3
"""Limpar bots mortos do banco de dados"""
import time
from database import DatabaseManager

db = DatabaseManager()
sessions = db.get_active_bots()

print(f"Encontrados {len(sessions)} bots com status 'running'")

for sess in sessions:
    bot_id = sess.get('id')
    pid = sess.get('pid')
    print(f"Marcando {bot_id} (PID {pid}) como stopped...")
    db.update_bot_session(bot_id, {'status': 'stopped', 'end_ts': time.time()})

print("✅ Limpeza concluída!")
