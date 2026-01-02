#!/usr/bin/env python3
from terminal_component import start_api_server
import time
import urllib.request

p = start_api_server(8765)
print("Port:", p)
time.sleep(0.5)

# Test /monitor
try:
    r = urllib.request.urlopen("http://127.0.0.1:8765/monitor", timeout=2)
    print("/monitor status:", r.status)
except Exception as e:
    print("/monitor error:", e)

# Test /report
try:
    r = urllib.request.urlopen("http://127.0.0.1:8765/report", timeout=2)
    print("/report status:", r.status)
except Exception as e:
    print("/report error:", e)

# Test /api/logs
try:
    r = urllib.request.urlopen("http://127.0.0.1:8765/api/logs?bot=test", timeout=2)
    print("/api/logs status:", r.status)
except Exception as e:
    print("/api/logs error:", e)
