#!/usr/bin/env bash
set -euo pipefail
PUB="/mnt/c/Users/DELL LATITUDE 5480/.ssh/id_rsa_homelab.pub"
USER_HOST="homelab@192.168.15.2"
sshpass -p homelab ssh -o StrictHostKeyChecking=no "$USER_HOST" "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
tr -d '\r' < "$PUB" | sshpass -p homelab ssh -o StrictHostKeyChecking=no "$USER_HOST" "cat > ~/.ssh/authorized_keys"
sshpass -p homelab ssh -o StrictHostKeyChecking=no "$USER_HOST" "chmod 600 ~/.ssh/authorized_keys"
