#!/bin/bash
cd /home/eddie/AutoCoinBot
source venv/bin/activate
export LOCAL_URL='https://autocoinbot.fly.dev'
timeout 120 python3 selenium_validate_all.py
