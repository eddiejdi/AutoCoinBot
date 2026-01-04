# 🔍 DIAGNÓSTICO: Erro de DATABASE_URL no Fly.io

**Data:** 2026-01-04  
**Status:** 🔴 CRÍTICO - 35.3% dos testes falhando em produção

---

## 📊 Resumo do Problema

### Erro Detectado
```
❌ Erro ao renderizar interface: missing "=" after "trades.db" in connection info string
```

### Impacto nos Testes Selenium (Homologação)

| Página | Testes | Pass/Fail | Taxa |
|--------|--------|-----------|------|
| **Trading** | 7 | 0/7 ❌ | 0% |
| **Dashboard** | 15 | 12/15 | 80% |
| **Learning** | 4 | 3/4 | 75% |
| **Trades** | 5 | 4/5 | 80% |
| **Monitor** | 4 | 3/4 | 75% |
| **Report** | 6 | 6/6 ✅ | 100% |
| **TOTAL** | **34** | **22/34** | **64.7%** |

### Páginas Afetadas

4 páginas contêm o erro de database (confirmado via análise HTML):
- ✅ dashboard_20260104_182604.html
- ✅ learning_20260104_182618.html
- ✅ trades_20260104_182624.html
- ✅ trading_20260104_182610.html

**Report** não apresenta erro e funciona 100% ✅

---

## 🔎 Análise Técnica

### Código de Erro
O erro ocorre em `autocoinbot/streamlit_app.py:144`:
```python
try:
    ui_mod.render_bot_control()
except Exception as e:
    st.error(f"❌ Erro ao renderizar interface: {e}")
```

A exceção é lançada quando `DatabaseManager()` tenta conectar usando `psycopg.connect()`.

### Erro do psycopg
```python
# autocoinbot/database.py:314
def get_connection(self):
    return psycopg.connect(self.db_dsn, row_factory=dict_row)
```

O erro "missing '=' after 'trades.db'" é característico de **connection string malformada**.

### Formato Correto vs Incorreto

✅ **CORRETO:**
```
postgresql://username:password@host:port/database
```

❌ **INCORRETO (provável no Fly.io):**
```
postgresql://username:password@host:port trades.db
                                        ↑ espaço em vez de '/'
```

Ou:

❌ **INCORRETO (possibilidade 2):**
```
postgresql://username:password@host:port/database&sslmode=require
                                                  ↑ falta '?'
```

---

## 🛠️ Passos para Correção

### 1. Verificar DATABASE_URL Atual

Usando o endpoint de diagnóstico recém-criado:

```bash
# Local
curl http://localhost:8765/api/debug/database_url

# Produção (após deploy)
curl https://autocoinbot.fly.dev/api/debug/database_url
```

**Resposta esperada:**
```json
{
  "url_safe": "postgresql://user:***@host:5432/dbname",
  "length": 68,
  "has_space": false,
  "has_equals": false,
  "format_errors": []
}
```

### 2. Acessar Secrets do Fly.io

**Opção A: Via CLI (requer flyctl instalado)**
```bash
flyctl secrets list --app autocoinbot
```

**Opção B: Via Dashboard**
1. Acesse https://fly.io/dashboard
2. Selecione app "autocoinbot"
3. Vá para "Secrets"
4. Visualize DATABASE_URL

### 3. Corrigir String de Conexão

Se o formato estiver incorreto, corrigir usando um dos métodos:

**Via CLI:**
```bash
flyctl secrets set DATABASE_URL="postgresql://user:pass@host:port/dbname" --app autocoinbot
```

**Via Dashboard:**
1. Editar secret DATABASE_URL
2. Garantir formato: `postgresql://[user]:[password]@[host]:[port]/[database]`
3. Exemplos válidos:
   - `postgresql://postgres:senha123@db.example.com:5432/autocoinbot`
   - `postgresql://user:pass@host:5432/db?sslmode=require`

**⚠️ IMPORTANTE:** Se usar query parameters (como `sslmode`), o formato é:
```
postgresql://user:pass@host:port/database?param1=value1&param2=value2
                                          ↑ '?' antes dos params
```

### 4. Re-deploy

```bash
flyctl deploy --app autocoinbot
```

Ou via GitHub Actions (se configurado).

### 5. Re-validar com Selenium

```bash
export APP_ENV=hom
timeout 120 python3 tests/selenium/test_all_pages.py
```

**Expectativa pós-fix:**
- Trading: 0/7 → 7/7 ✅ (+7 testes)
- Dashboard: 12/15 → 15/15 ✅ (+3 testes)
- Learning: 3/4 → 4/4 ✅ (+1 teste)
- Trades: 4/5 → 5/5 ✅ (+1 teste)
- Monitor: 3/4 → 4/4 ✅ (+1 teste)
- **TOTAL: 22/34 → 34/34 (100%)** ✅

---

## 📁 Arquivos Relacionados

### Código Fonte
- `autocoinbot/database.py:43` - Lê DATABASE_URL do ambiente
- `autocoinbot/database.py:305-314` - DatabaseManager.__init__ e get_connection
- `autocoinbot/streamlit_app.py:144` - Captura e exibe erro
- `autocoinbot/terminal_component.py:795-882` - Endpoint de diagnóstico (NOVO)

### Testes
- `tests/selenium/test_all_pages.py` - Suite completa
- `tests/selenium/pages/trading_page.py` - Página mais afetada (0/7)

### Documentação
- `.github/copilot-instructions.md` - Instruções do projeto
- `AGENTE_TREINAMENTO.md` - Manual do desenvolvedor
- `test/selenium/screenshots/` - Capturas de tela dos testes

---

## 🎯 Checklist de Correção

- [ ] 1. Deploy da versão com endpoint de diagnóstico (commit 2792070)
- [ ] 2. Consultar `/api/debug/database_url` em produção
- [ ] 3. Identificar formato exato do erro
- [ ] 4. Acessar Fly.io secrets
- [ ] 5. Corrigir DATABASE_URL com formato correto
- [ ] 6. Re-deploy da aplicação
- [ ] 7. Aguardar deploy completar (~2-5 min)
- [ ] 8. Testar conexão manualmente: `curl https://autocoinbot.fly.dev/api/bot?bot=test`
- [ ] 9. Re-executar Selenium homologação
- [ ] 10. Verificar 34/34 testes passando ✅
- [ ] 11. Remover endpoint `/api/debug/database_url` (segurança)
- [ ] 12. Commit final e documentar lição aprendida

---

## 🔒 Segurança

### ⚠️ ATENÇÃO
O endpoint `/api/debug/database_url` **mascara a senha** mas ainda expõe:
- Usuário do banco
- Host e porta
- Nome do banco

**Remover após diagnóstico!**

```bash
git revert 2792070
# ou
git checkout main
# remover manualmente o bloco do endpoint
git commit -m "chore: remove diagnostic endpoint"
git push
```

---

## 📚 Referências

### Documentos do Projeto
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - Seção "Lições Aprendidas"
- [AGENTE_TREINAMENTO.md](AGENTE_TREINAMENTO.md) - Troubleshooting
- [FIX_PRODUCAO_URLS_DINAMICAS.md](FIX_PRODUCAO_URLS_DINAMICAS.md) - Problemas similares

### PostgreSQL Connection String
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [psycopg Connection Parameters](https://www.psycopg.org/psycopg3/docs/api/connections.html)

### Fly.io
- [Fly.io Secrets Management](https://fly.io/docs/reference/secrets/)
- [Fly.io Environment Variables](https://fly.io/docs/reference/configuration/#the-env-variables-section)

---

## 📝 Histórico

| Data | Commit | Descrição |
|------|--------|-----------|
| 2026-01-04 | 20f0d3a | Fix Selenium xpaths - 100% local |
| 2026-01-04 | 2792070 | Add diagnostic endpoint |

---

**Próxima Ação:** Deploy commit 2792070 e acessar endpoint de diagnóstico para confirmar formato da DATABASE_URL.
