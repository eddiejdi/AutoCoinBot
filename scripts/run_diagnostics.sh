#!/usr/bin/env bash
set -euo pipefail

echo "1) Verificando marcadores de conflito de merge..."
./scripts/check_merge_conflicts.sh || { echo "ERRO: marcadores de conflito encontrados. Resolva-os antes de prosseguir."; exit 1; }

echo "2) Verificando sintaxe de arquivos Python (py_compile)..."
python3 -m py_compile $(find . -name "*.py") || { echo "ERRO: falha na verificação de sintaxe."; exit 1; }

echo "3) (Opcional) Rodar testes com pytest se disponível..."
if [ -x "$(command -v pytest)" ]; then
  pytest -q || { echo "ERRO: alguns testes falharam."; exit 1; }
else
  echo "pytest não encontrado no PATH — pulei a etapa de testes." 
fi

echo "Diagnóstico concluído com sucesso."
