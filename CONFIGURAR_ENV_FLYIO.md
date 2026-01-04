# 🚀 Configurar Variáveis de Ambiente no Fly.io

## ❌ Problema
A aplicação em https://autocoinbot.fly.dev ainda gera URLs absolutas (`http://127.0.0.1:8768/monitor`) porque nenhuma variável de detecção de produção está definida.

## ✅ Solução: Definir APP_ENV

Execute este comando para configurar a variável de ambiente no Fly.io:

```bash
fly secrets set APP_ENV=hom --app autocoinbot
```

Ou se preferir definir como produção:

```bash
fly secrets set APP_ENV=production --app autocoinbot
```

### Verificar variáveis atuais

```bash
fly secrets list --app autocoinbot
```

### Após definir a variável

O Fly.io vai **reiniciar automaticamente** a aplicação. Depois:

1. Aguarde ~30 segundos para o restart completar
2. Acesse: https://autocoinbot.fly.dev/?view=dashboard
3. Clique no botão LOG
4. A URL deve ser: `https://autocoinbot.fly.dev/monitor?...` ✅

---

## 🔍 Debug: Verificar detecção de ambiente

Se ainda não funcionar, você pode verificar quais variáveis estão definidas em produção:

### Via SSH no container

```bash
fly ssh console --app autocoinbot
$ env | grep -E 'FLY|APP_ENV|DYNO|RENDER'
```

### Via script de debug

Adicione temporariamente ao start.sh:

```bash
# No início do start.sh
echo "🔍 DEBUG: Variáveis de ambiente"
env | grep -E 'FLY|APP_ENV|DYNO|RENDER' || echo "Nenhuma encontrada"
python debug_env_detection.py || true
```

Depois veja os logs:

```bash
fly logs --app autocoinbot | grep -A20 "DEBUG: Variáveis"
```

---

## 📋 Checklist

- [ ] Definir `APP_ENV=hom` no Fly.io: `fly secrets set APP_ENV=hom --app autocoinbot`
- [ ] Aguardar restart automático (~30s)
- [ ] Testar em https://autocoinbot.fly.dev/?view=dashboard
- [ ] Clicar botão LOG → URL deve ser relativa `/monitor?...`
- [ ] Se funcionar, fechar issue ✅

---

## 🎯 Resultado Esperado

**Antes** (errado):
```
http://127.0.0.1:8768/monitor?t_bg=...
```

**Depois** (correto):
```
/monitor?t_bg=...
ou
https://autocoinbot.fly.dev/monitor?t_bg=...
```

---

## 💡 Alternativa: Usar fly.toml

Se não quiser usar `fly secrets`, pode adicionar ao `fly.toml`:

```toml
[env]
  APP_ENV = "hom"
  PORT = "8080"
```

Depois fazer deploy:

```bash
fly deploy --app autocoinbot
```

---

**Nota**: A variável `FLY_APP_NAME` deveria ser definida automaticamente pelo Fly.io, mas aparentemente não está. Por isso estamos usando `APP_ENV` como alternativa.
