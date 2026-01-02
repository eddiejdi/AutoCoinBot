#!/usr/bin/env python3
from database import DatabaseManager
db = DatabaseManager()
active = db.get_active_bots()
print('Active bots in DB:', active)
for bot in active:
    print(f"Bot ID: {bot.get('id')}, Status: {bot.get('status')}, PID: {bot.get('pid')}")