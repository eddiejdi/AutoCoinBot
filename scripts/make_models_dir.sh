#!/usr/bin/env bash
set -euo pipefail
USER_HOST="homelab@192.168.15.2"
sshpass -p homelab ssh -o StrictHostKeyChecking=no "$USER_HOST" "mkdir -p ~/models && chmod 755 ~/models"
