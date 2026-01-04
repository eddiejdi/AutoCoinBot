# Executando o AutoCoinBot (Windows, WSL/Linux, Docker)

Este documento descreve formas recomendadas para levantar a aplicação localmente em Windows, WSL/Linux e Docker.

Resumo rápido:
- Para desenvolvimento rápido em WSL/Linux: use `scripts/start.py --detach` (cria venv, instala deps e inicia Streamlit).
- Para Windows: execute `python scripts/start.py --detach` a partir do PowerShell.
- Para execução em container: use `docker-compose up --build` (arquivo `docker-compose.yml` incluso).

## Pré-requisitos

- Python 3.10+ (para execução sem Docker)
- Docker Desktop (se for usar containers)
- Em WSL: recomenda-se usar a distro Ubuntu com integração Docker Desktop habilitada

## Variáveis sensíveis

Copie `.env.example` para `.env` e preencha suas chaves (API_KEY, API_SECRET, API_PASSPHRASE, etc):

```bash
cp .env.example .env
# editar .env com suas credenciais
```

Ou defina variáveis de ambiente adequadamente no host.

## Opção A — WSL / Linux (rápido para desenvolvimento)

1. Abra seu terminal WSL e vá para a raiz do repositório.
2. Execute o script unificado:

```bash
./scripts/start.py --detach
tail -f streamlit.log
```

O script fará:
- criar `.env` a partir de `.env.example` se faltar
- criar `venv` se necessário
- instalar dependências em `venv`
- iniciar `streamlit_app.py` (porta 8501)

Abra no navegador: `http://localhost:8501`.

## Opção B — Windows (PowerShell)

1. Abra PowerShell no diretório do projeto.
2. Execute:

```powershell
python .\scripts\start.py --detach
Get-Content streamlit.log -Wait
```

Se preferir, existe `scripts/start_windows.ps1` que oferece modo interativo e detach.

## Opção C — Docker (recomendado para parity entre ambientes)

Pré-requisito: Docker Desktop com integração WSL2 habilitada.

Build + start:

```bash
docker compose up --build
```

O `docker-compose.yml` expõe a porta `8501` e monta volumes para logs. O banco de dados PostgreSQL é configurado via variável de ambiente `DATABASE_URL`.

Logs do container:

```bash
docker compose logs -f
```

## Parar a aplicação

- Se rodou via `scripts/start.py`: mate o PID em `streamlit.pid` (ex.: `kill $(cat streamlit.pid)`).
- Se rodou via Docker Compose: `docker compose down`.

## Dicas e resolução de problemas

- Se `docker` não estiver disponível no Windows, habilite WSL2 e a integração com sua distro em Docker Desktop.
- Se o Streamlit ficar preso em "Carregando...", verifique `streamlit.log` e confirme que `ui.py` foi importado sem exceção.
- Se faltar `git` identity para commits no ambiente, configure com:

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu@exemplo.com"
```

## Arquivos úteis

- `scripts/start.py` — script unificado (Windows / POSIX) para setup + start
- `docker-compose.yml` — compose para build+run
- `scripts/start_local.sh`, `scripts/start_windows.ps1` — scripts legacy/fallback

---

Se quiser, eu posso:
- commitar este arquivo (`RUNNING.md`) no repositório (preciso de autorização para configurar `git user` aqui),
- adicionar um `healthcheck` no `docker-compose.yml`, ou
- incluir instruções extras (ex.: start de bots via UI/API).
