## Estrutura do código

O núcleo da aplicação está em `autocoinbot/` (ex.: `autocoinbot/streamlit_app.py`, `autocoinbot/bot_core.py`). Existem shims na raiz para compatibilidade, mas prefira importar e executar diretamente do pacote:

```bash
python -m streamlit run autocoinbot/streamlit_app.py --server.port=8501 --server.headless=true
python -m autocoinbot.bot_core --bot-id test1 --symbol BTC-USDT --targets "2:0.3" --dry
```

## Treinamento e diretrizes do agente

Consulte o arquivo [AGENTE_TREINAMENTO.md](./AGENTE_TREINAMENTO.md) para diretrizes, procedimentos de validação e relatórios de treinamento do agente automatizado.

## Start/Stop/Restart com Docker

Para rodar a aplicação via Docker:

```bash
# Build da imagem
docker build -t autocoinbot .

# Start do container
docker run -d --name autocoinbot -p 8501:8501 --env-file .env autocoinbot

# Parar o container
docker stop autocoinbot

# Reiniciar o container
docker restart autocoinbot

# Remover o container (opcional)
docker rm autocoinbot
```

> O parâmetro `--env-file .env` garante que as variáveis do seu .env sejam lidas pelo container.

# Kucoin App (AutoCoinBot)

## Uso obrigatório de ambiente virtual (venv)

Sempre ative a venv antes de rodar qualquer comando:

```bash
source venv/bin/activate
```

Se estiver no Windows, prefira usar o WSL (Ubuntu). Verifique que você está no WSL e com a `venv` ativada antes de executar os scripts. Exemplo de checagens rápidas:

```bash
# confirmar WSL
grep -qi microsoft /proc/version && echo "Estou no WSL" || echo "Não parece ser WSL"

# ativar venv
source venv/bin/activate
echo "VENV: $VIRTUAL_ENV"
```

Para rodar scripts, utilize sempre `python3` (ou o caminho do python da venv):

```bash
python3 agent0_scraper.py --local --check-buttons
```

Para instalar dependências:

```bash
pip install -r requirements.txt
```

Se o comando `python` não existir, use sempre `python3`.

---
Automaçao de compra e venda de ETF e ativos na KuCoin, com painel de controle via Streamlit.
