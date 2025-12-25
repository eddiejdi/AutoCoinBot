#!/bin/bash

# Script para controlar a aplicação KuCoin Streamlit
# Suporte a Docker se o container estiver rodando
# Uso: ./control_app.sh start|stop|restart|status

APP_NAME="kucoin_app"
STREAMLIT_CMD="/home/edenilson/Downloads/kucoin_app/.venv_app/bin/python /home/edenilson/Downloads/kucoin_app/.venv_app/bin/streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true"
VENV_PATH="/home/edenilson/Downloads/kucoin_app/.venv_app/bin/activate"
CONTAINER_NAME="deploy-streamlit-1"

# Verificar se Docker está disponível e container existe
use_docker() {
    if command -v docker > /dev/null 2>&1; then
        if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
            return 0
        fi
    fi
    return 1
}

# Função para verificar se está rodando
is_running() {
    if use_docker; then
        if docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
            return 0
        fi
    else
        if pgrep -f "streamlit run streamlit_app.py" > /dev/null; then
            return 0
        fi
    fi
    return 1
}

# Função para iniciar
start() {
    if is_running; then
        echo "Aplicação já está rodando"
        return 1
    fi

    echo "Iniciando $APP_NAME..."

    if use_docker; then
        docker start "$CONTAINER_NAME" > /dev/null 2>&1
        sleep 3
    else
        # Executar streamlit com ambiente virtualenv correto
        export PYTHONHOME="/home/edenilson/Downloads/kucoin_app/.venv_app"
        export PYTHONPATH="/home/edenilson/Downloads/kucoin_app/.venv_app/lib/python3.13/site-packages"
        nohup /home/edenilson/Downloads/kucoin_app/.venv_app/bin/python /home/edenilson/Downloads/kucoin_app/.venv_app/bin/streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > logs/streamlit.log 2>&1 &
        sleep 2
    fi

    if is_running; then
        echo "Aplicação iniciada com sucesso"
        echo "Acesse: http://localhost:8501"
    else
        echo "Erro ao iniciar aplicação"
        return 1
    fi
}

# Função para parar
stop() {
    if ! is_running; then
        echo "Aplicação não está rodando"
        return 1
    fi

    echo "Parando $APP_NAME..."

    if use_docker; then
        docker stop "$CONTAINER_NAME" > /dev/null 2>&1
        sleep 2
    else
        pkill -f "streamlit run streamlit_app.py" 2>/dev/null
        sleep 2
    fi

    if ! is_running; then
        echo "Aplicação parada com sucesso"
    else
        echo "Erro ao parar aplicação"
        return 1
    fi
}

# Função para reiniciar
restart() {
    echo "Reiniciando $APP_NAME..."
    stop
    sleep 2
    start
}

# Função para status
status() {
    if is_running; then
        echo "Aplicação está rodando"
        echo "Acesse: http://localhost:8501"
    else
        echo "Aplicação não está rodando"
    fi
}

# Verificar argumentos
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0