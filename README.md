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
Automação de compra e venda de ETF e ativos na KuCoin, com painel de controle via Streamlit.

