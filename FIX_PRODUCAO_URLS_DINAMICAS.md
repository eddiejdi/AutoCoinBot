# 🚀 Fix: URLs Dinâmicas para Produção (Fly.io)

## ❌ Problema Encontrado

O código em `autocoinbot/ui.py` (linha 5320) usava URLs **hardcoded** para `localhost`:

```python
# ❌ ANTES - só funciona local
base = f"http://127.0.0.1:{int(api_port)}"
home_url = f"http://127.0.0.1:{st_port}/?view=dashboard"
```

**Resultado**: Botões LOG/RELATÓRIO **não funcionam em produção** (https://autocoinbot.fly.dev) porque tentam acessar `127.0.0.1` (localhost do navegador, não do servidor).

---

## ✅ Solução Implementada

Criado código **dinâmico** que detecta ambiente:

```python
# ✅ DEPOIS - funciona em ambos ambientes
is_production = bool(os.environ.get("FLY_APP_NAME"))
if is_production:
    # Produção: URLs relativas (nginx faz proxy)
    base = ""
    home_url = "/?view=dashboard"
else:
    # Local: URLs absolutas com porta
    base = f"http://127.0.0.1:{int(api_port)}"
    home_url = f"http://127.0.0.1:{st_port}/?view=dashboard"
```

---

## 🏗️ Arquitetura em Produção

```
Internet → Fly.io (:80/:443)
           ↓
       nginx (:8080) 
           ├─→ /monitor, /report, /api/* → API HTTP (:8765)
           └─→ /* (tudo mais) → Streamlit (:8501)
```

**Com URLs relativas**:
- Botão clicado: `/monitor?bot=abc123`
- Nginx intercepta e faz proxy para `http://127.0.0.1:8765/monitor?bot=abc123`
- Browser recebe resposta de `https://autocoinbot.fly.dev/monitor?bot=abc123`

---

## 📋 Comparação Local vs Produção

| Aspecto | Local (Dev) | Produção (Fly.io) |
|---------|-------------|-------------------|
| **Detecção** | `FLY_APP_NAME` não existe | `FLY_APP_NAME` definido ✅ |
| **URLs Botões** | `http://127.0.0.1:8765/monitor` | `/monitor` (relativa) |
| **URL Home** | `http://127.0.0.1:8506/?view=dashboard` | `/?view=dashboard` |
| **Proxy** | Sem nginx (acesso direto) | nginx (:8080) → Streamlit/API |
| **Portas Expostas** | 8506 (Streamlit), 8765 (API) | 80/443 (nginx) |

---

## 🚀 Deploy para Produção

### Passo 1: Commit e Push

```bash
cd /home/eddie/AutoCoinBot

# Verificar mudanças
git status
git diff autocoinbot/ui.py

# Commit
git add autocoinbot/ui.py
git commit -m "fix(ui): URLs dinâmicas para botões LOG/RELATÓRIO em produção

- Detecta ambiente via FLY_APP_NAME
- Produção: URLs relativas (nginx proxy)
- Local: URLs absolutas com porta
- Corrige botões LOG/RELATÓRIO em https://autocoinbot.fly.dev"

# Push
git push origin main
```

### Passo 2: Deploy no Fly.io

```bash
# Opção 1: Deploy automático (se configurado)
# GitHub Actions pode fazer deploy automaticamente após push

# Opção 2: Deploy manual
fly deploy --app autocoinbot

# Verificar logs
fly logs --app autocoinbot
```

### Passo 3: Validar em Produção

```bash
# Testar endpoints
curl -I https://autocoinbot.fly.dev/_stcore/health
# Esperado: HTTP/2 200

curl -I https://autocoinbot.fly.dev/monitor
# Esperado: HTTP/2 200 (ou 400 se não passar bot=)

curl -I https://autocoinbot.fly.dev/report
# Esperado: HTTP/2 200 (ou 400 se não passar bot=)
```

### Passo 4: Teste Visual

1. Abra: **https://autocoinbot.fly.dev/?view=dashboard**
2. Clique no botão **📜 LOG** (Monitor)
3. Deve abrir: `https://autocoinbot.fly.dev/monitor?bot=...` ✅
4. Clique no botão **📊 RELATÓRIO**
5. Deve abrir: `https://autocoinbot.fly.dev/report?bot=...` ✅

---

## ⚠️ Troubleshooting Produção

### Problema: Botões ainda não funcionam após deploy

**Verificações**:

1. **Deploy completou?**
   ```bash
   fly status --app autocoinbot
   # Status: running ✅
   ```

2. **nginx configurado?**
   ```bash
   fly ssh console --app autocoinbot
   $ cat /app/nginx.conf | grep -A5 "location /monitor"
   # Deve ter proxy_pass http://api;
   ```

3. **API HTTP iniciou?**
   ```bash
   fly ssh console --app autocoinbot
   $ ps aux | grep start_api_server
   # Deve ter processo rodando
   ```

4. **Variável de ambiente FLY_APP_NAME existe?**
   ```bash
   fly ssh console --app autocoinbot
   $ echo $FLY_APP_NAME
   # Deve retornar: autocoinbot
   ```

### Problema: 404 ao clicar botão em produção

**Causa**: nginx não está roteando `/monitor` e `/report`

**Solução**:
```bash
# Verificar nginx.conf tem as rotas
cat nginx.conf | grep -E "location /(monitor|report)"

# Se não tiver, conferir se arquivo foi copiado no build
# Dockerfile deve ter: COPY nginx.conf /app/nginx.conf
```

---

## 📊 Validação Local (Regressão)

Antes de fazer deploy, validar que local **ainda funciona**:

```bash
cd /home/eddie/AutoCoinBot
source venv/bin/activate

# Limpar FLY_APP_NAME (simular local)
unset FLY_APP_NAME

# Iniciar Streamlit
python -m streamlit run streamlit_app.py --server.port=8506

# Testar navegador
# http://localhost:8506/?view=dashboard
# Clicar botões LOG/RELATÓRIO → devem abrir em http://127.0.0.1:8765/...
```

---

## 📚 Arquivos Modificados

| Arquivo | Mudança | Linha |
|---------|---------|-------|
| `autocoinbot/ui.py` | URLs dinâmicas (prod vs local) | 5320-5340 |

---

## 🎯 Próximas Ações

- [ ] Commit e push para `main`
- [ ] Deploy no Fly.io: `fly deploy --app autocoinbot`
- [ ] Validar em produção: https://autocoinbot.fly.dev/?view=dashboard
- [ ] Clicar botões LOG/RELATÓRIO e verificar funcionamento
- [ ] Se funcionar, fechar issue ✅

---

**Gerado em**: 2026-01-04 15:30 BRT  
**Ambiente**: AutoCoinBot local (WSL Ubuntu)  
**Deploy target**: Fly.io (https://autocoinbot.fly.dev)
