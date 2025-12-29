#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .dockerignore ]; then
  echo '.dockerignore not found, computing full repo size (bytes):'
  du -sb . | awk '{print $1}'
  exit 0
fi

echo 'Estimating build context size excluding .dockerignore patterns (approx)...'
bytes=$(tar -c --exclude-from=.dockerignore -C . . 2>/dev/null | wc -c || true)
if [ -z "$bytes" ]; then
  bytes=0
fi
printf "%s\n" "$bytes"
python3 - <<PY
import sys
s=sys.stdin.read().strip()
try:
    b=int(s)
except:
    b=0
units=['B','KiB','MiB','GiB','TiB']
size=b
u=0
while size>=1024 and u<len(units)-1:
    size/=1024.0
    u+=1
print(f'{b} bytes')
print(f'{size:.2f} {units[u]}')
PY
