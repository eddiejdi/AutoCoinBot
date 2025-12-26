# Kucoin App (AutoCoinBot)

Automação de compra e venda de ETF e ativos na KuCoin, com painel de controle via Streamlit.

## Deploy no Streamlit Community Cloud

### 1. Pré-requisitos
- Conta no [Streamlit Cloud](https://share.streamlit.io/) (login via GitHub)
- Código hospedado em repositório GitHub

### 2. Estrutura esperada
```
kucoin_app/
├── streamlit_app.py         # Arquivo principal
├── ui.py                   # Lógica de interface
├── requirements.txt        # Dependências
├── .streamlit/secrets.toml # (opcional, use painel de segredos no deploy)
├── ...                     # Outros scripts, subpastas, dados
```

### 3. requirements.txt
Inclua todas as dependências Python usadas no projeto (já incluso neste repo).

### 4. Segredos/API Keys
- No painel do Streamlit Cloud, acesse Settings > Secrets e cole o conteúdo do `.streamlit/secrets.toml` (preencha os valores).
- No código, acesse via `st.secrets["NOME"]`.

## 4.b Ambiente local via `.env`
- For local development you can use a `.env` file at the repo root. The project loads variables from `.env` when available (via `python-dotenv` if installed) and will also read Streamlit secrets from `.streamlit/secrets.toml` when deployed.
- To switch which app the validators target, set `APP_ENV` to `dev` (uses `LOCAL_URL`) or `hom` (uses `HOM_URL`). You can also set `LOCAL_URL`, `HOM_URL`, or `APP_URL` directly in `.env` to override.
- A sample file is provided at `.env.example`.

### 5. Deploy
1. Faça push de todo o código para o GitHub.
2. No Streamlit Cloud, clique em "New app", selecione o repositório, branch e arquivo principal (`streamlit_app.py`).
3. Cole os segredos em Settings > Secrets.
4. Clique em Deploy.

### 6. Atualização
- Basta dar push no GitHub para atualizar o app.

### 7. Observações
- O login persistente usa arquivo local e será perdido a cada restart do app (limitação do ambiente).
- O banco SQLite local (`trades.db`) é efêmero. Para produção, use banco externo.
- Todos os scripts e subpastas devem estar no repositório.

### 8. Teste local
Execute:
```
streamlit run streamlit_app.py
```

### Rodando a suíte de testes (recomendado)
- Os testes sempre devem ser executados dentro do ambiente virtual do projeto (`venv`). Use o helper `run_tests.sh` abaixo para criar/ativar o venv, instalar dependências e executar `pytest` com `APP_ENV=dev` por padrão.

Exemplo (rápido):
```bash
./run_tests.sh
# ou para rodar com homologação
APP_ENV=hom ./run_tests.sh
```

Se preferir ativar manualmente o venv:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest python-dotenv selenium
APP_ENV=dev pytest
```

### Running Selenium visual tests

- Selenium visual tests require a local Chrome installation and a matching `chromedriver` available on `PATH` (or use webdriver manager). Install Chrome and download chromedriver matching your Chrome version, then place `chromedriver` on `PATH`.
- To run the visual/Selenium tests use the helper with the `--selenium` flag or set `RUN_SELENIUM=1`:
```bash
./run_tests.sh --selenium
# or
RUN_SELENIUM=1 ./run_tests.sh
```

If you prefer to run only the visual test file directly:
```bash
source venv/bin/activate
pytest tests/test_visual_validation.py -q
```

Note on seeing the browser window:
- By default tests run headless (no visible browser) to be CI-friendly. To show the browser on-screen set `SHOW_BROWSER=1` in your environment and run tests on a machine with an X display (local desktop). Example:
```bash
SHOW_BROWSER=1 ./run_tests.sh --selenium
```
- If running on a headless server, use `xvfb-run` to emulate an X server:
```bash
xvfb-run ./run_tests.sh --selenium
```

Auto-download chromedriver
- If you install `webdriver-manager` in your venv, `agent0_scraper.py` will try to auto-download a matching `chromedriver` at runtime. Install it with:
```bash
pip install webdriver-manager
```
This removes the manual step of placing `chromedriver` on `PATH` on most local setups. The scraper falls back to the system `chromedriver` or Selenium Manager if `webdriver-manager` is not installed.

---

## Contato
Dúvidas ou sugestões: abra uma issue ou envie um pull request.

## Dev helpers

- DB inspector: `scripts/db_inspect.py` — run `./scripts/db_inspect.py logs --bot BOT_ID`.
- Start all registry bots (dry-run): `./scripts/run_all_bots.py` (safe: forces `dry=True`).
