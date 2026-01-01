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
Automação de compra e venda de ETF e ativos na KuCoin, com painel de controle via Streamlit.

