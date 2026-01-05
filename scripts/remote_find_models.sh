#!/usr/bin/env bash
set -eo pipefail
USER_HOST="homelab@192.168.15.2"
sshpass -p homelab ssh -o StrictHostKeyChecking=no "$USER_HOST" 'echo homelab | sudo -S find / \( -path /proc -o -path /sys -o -path /dev \) -prune -o -type f \( -name "*.gguf" -o -name "*.bin" -o -name "*.pt" -o -name "*.safetensors" \) -print 2>/dev/null'
