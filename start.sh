#!/bin/bash
# start.sh - Script para iniciar todos os serviços
# Usado pelo Fly.io e Docker para deploy em produção

set -e

echo "🚀 Iniciando AutoCoinBot..."

# Iniciar API HTTP em background (porta 8765)
echo "📡 Iniciando API HTTP na porta 8765..."
python start_api_server.py &
API_PID=$!
echo "API PID: $API_PID"

# Aguardar API iniciar
sleep 2

# Verificar se nginx está instalado
if command -v nginx &> /dev/null; then
    echo "🔀 Iniciando nginx como proxy reverso..."
    nginx -c /app/nginx.conf -g "daemon off;" &
    NGINX_PID=$!
    echo "Nginx PID: $NGINX_PID"
    
    # Iniciar Streamlit (nginx vai fazer proxy)
    echo "🎨 Iniciando Streamlit na porta 8501..."
    exec streamlit run streamlit_app.py \
        --server.port=8501 \
        --server.headless=true \
        --server.address=127.0.0.1
else
    # Sem nginx - Streamlit exposto diretamente
    echo "⚠️ Nginx não encontrado - Streamlit exposto diretamente na porta 8501"
    echo "📝 AVISO: Rotas /api, /monitor, /report não estarão disponíveis externamente"
    
    exec streamlit run streamlit_app.py \
        --server.port=8501 \
        --server.headless=true \
        --server.address=0.0.0.0
fi
