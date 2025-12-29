#!/usr/bin/env bash
set -euo pipefail

# Busca por marcadores de conflito de merge, excluindo pastas grandes/virtuais
matches=$(grep -RIn --exclude-dir=venv --exclude-dir=.git --exclude-dir=logs --exclude-dir=__pycache__ '^<<<<<<<\|^=======$\|^>>>>>>>' . || true)
if [ -n "$matches" ]; then
  echo "Conflitos encontrados:"
  echo "$matches"
  exit 1
else
  echo "Nenhum marcador de conflito encontrado."
  exit 0
fi
