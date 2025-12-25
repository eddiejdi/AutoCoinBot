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

---

## Contato
Dúvidas ou sugestões: abra uma issue ou envie um pull request.
