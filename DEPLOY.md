# Deploy automático para Fly.io

Este documento descreve os passos para habilitar deploy automático do repositório no Fly.io usando GitHub Actions.

## Pré-requisitos
- Conta no Fly.io
- `fly.toml` no diretório raiz do repositório (gerado por `flyctl launch`)
- GitHub repository admin access para adicionar secrets

## 1) Criar o token no Fly
1. Acesse: https://fly.io/user/settings/tokens
2. Clique em **Generate token** e copie o valor gerado.

## 2) Adicionar `FLY_API_TOKEN` no GitHub Secrets
- Web: Repo → Settings → Secrets and variables → Actions → New repository secret
  - Name: `FLY_API_TOKEN`
  - Value: (cole o token copiado do Fly)
- gh CLI (exemplo):
```bash
gh auth login
gh secret set FLY_API_TOKEN --body "YOUR_TOKEN" -R eddiejdi/AutoCoinBot
```


3) Workflow de deploy

O workflow já adicionado em `.github/workflows/deploy_fly.yml` agora constrói uma imagem Docker, publica no GitHub Container Registry (GHCR) e, em seguida, faz o deploy no Fly utilizando a imagem publicada.

Fluxo resumido que o workflow realiza:

- Build da imagem usando `docker/build-push-action` e `buildx`.
- Publicação em `ghcr.io/${{ github.repository_owner }}/autocoinbot:${{ github.sha }}`.
- Deploy no Fly com `flyctl deploy --image <IMAGE>`.

Observações importantes:
- O workflow usa `GITHUB_TOKEN` para publicar no GHCR; verifique se as permissões `packages: write` estão disponíveis para o `GITHUB_TOKEN` no repo settings (Configurações → Actions → General → Workflow permissions). Se houver restrições, crie um Personal Access Token com `packages:write` e configure como secret `GHCR_TOKEN`, atualizando o workflow para usá-lo.
- `FLY_API_TOKEN` deve estar configurado como Secret (veja os passos em 2).
- Se preferir que o runner faça o build e envie uma imagem para outro registry (Docker Hub, ECR, etc.), eu posso ajustar o workflow.

## 4) Testar deploy local (opcional)
```bash
flyctl auth login
flyctl deploy --config fly.toml
```

## 5) Troubleshooting
- Verifique que `fly.toml` contém o `app = "<nome-do-app>"` correto.
- Se o build falhar por dependências nativas, tente usar `--remote-only` ou ajustar `Dockerfile` para criar todas as dependências no build.

## 6) Criar PR para as mudanças
- Para eu criar o PR automaticamente preciso de um GitHub Personal Access Token com escopo `repo` (ou você pode usar o `gh` CLI localmente). Se quiser que eu crie o PR aqui, cole o token com segurança na conversa (ou autorize via outro método) e eu criarei o PR.

---
Se quiser, eu posso também atualizar o workflow para empacotar e publicar uma imagem Docker em Container Registry antes do deploy. Diga se prefere essa opção.
