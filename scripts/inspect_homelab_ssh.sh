#!/usr/bin/env bash
set -euo pipefail
USER_HOST="homelab@192.168.15.2"
sshpass -p homelab ssh -o StrictHostKeyChecking=no "$USER_HOST" "ls -l ~/.ssh && echo '---' && cat -A ~/.ssh/authorized_keys"
