#!/bin/bash

echo "===== CORREÇÃO DO AMBIENTE PYTHON PARA KUCOIN_APP ====="

PROJECT_DIR="$HOME/Downloads/kucoin_app"
PROJECT_VENV="$PROJECT_DIR/venv"

echo
echo "[1] Validando diretório do projeto..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERRO: O diretório do projeto não existe:"
    echo "  $PROJECT_DIR"
    exit 1
fi
echo "[OK] Projeto encontrado."

echo
echo "[2] Limpando variáveis perigosas..."
unset PYTHONPATH
unset PYTHONHOME
unset PIP_TARGET
unset PIP_PREFIX
unset PIP_USER

echo "[OK] Variáveis zeradas."

echo
echo "[3] Removendo aliases pip/python..."
unalias pip 2>/dev/null
unalias python 2>/dev/null
echo "[OK] Aliases removidos."

echo
echo "[4] Limpando ~/.bashrc de contaminações..."
sed -i '/google-assistant/d' ~/.bashrc
sed -i '/export PYTHONPATH/d' ~/.bashrc
sed -i '/export PYTHONHOME/d' ~/.bashrc
sed -i '/PIP_TARGET/d' ~/.bashrc
sed -i '/PIP_PREFIX/d' ~/.bashrc

echo "[OK] ~/.bashrc corrigido."

echo
echo "[5] Protegendo o ambiente do Google Assistant..."
if [ -d "/opt/google-assistant/venv" ]; then
    sudo chown -R root:root /opt/google-assistant/venv/
    sudo chmod -R 755 /opt/google-assistant/venv/
    echo "[OK] Diretório protegido."
else
    echo "[INFO] Google Assistant não instalado — ignorado."
fi

echo
echo "[6] Ativando venv do projeto em:"
echo "   $PROJECT_VENV"

if [ ! -d "$PROJECT_VENV" ]; then
    echo "[ERRO] Venv não encontrado, criando..."
    python3 -m venv "$PROJECT_VENV"
fi

# ativa o venv
source "$PROJECT_VENV/bin/activate"

echo "[OK] venv ativado."

echo
echo "[7] Reinstalando bibliotecas corretas (requests/urllib3/six)..."
pip install --upgrade pip setuptools wheel

pip install --force-reinstall \
    "requests>=2.32.0" \
    "urllib3>=2.2.0" \
    six

echo "[OK] Bibliotecas reinstaladas."

echo
echo "[8] Verificando se 'requests' e 'urllib3' estão carregando DO LUGAR CERTO..."
python - <<EOF
import sys, requests, urllib3
print("Python executável:", sys.executable)
print("requests carregado de:", requests.__file__)
print("urllib3 carregado de:", urllib3.__file__)

if "/opt/google-assistant" in requests.__file__ or "/opt/google-assistant" in urllib3.__file__:
    print("ERRO: ainda está usando o Google Assistant!")
else:
    print("OK! Dependências carregadas do venv correto.")
EOF

echo
echo "===== AMBIENTE CORRIGIDO COM SUCESSO ====="

echo
echo "Para rodar o bot:"
echo "  $PROJECT_VENV/bin/python -m kucoin_app.bot --symbol BTC-USDT --entry 88000 --pct 2.5 --size 0.001 --interval 5 --dry"
