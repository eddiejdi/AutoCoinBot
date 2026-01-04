# ✅ Checklist de Alterações - AutoCoinBot

## 🔍 Antes de Qualquer Commit

- [ ] Código passa em `python -m py_compile arquivo.py`
- [ ] Variáveis de ambiente não expostas
- [ ] Logs usando `DatabaseLogger`, não `print()`
- [ ] Type hints em funções novas/modificadas

## 📝 Alterações em Bot Core

### bot_core.py ou bot_controller.py
- [ ] CLI args sincronizados em ambos arquivos
- [ ] Testado em dry-run: `python bot_core.py --dry ...`
- [ ] Verificar `bot_sessions` no PostgreSQL
- [ ] Documentar novas flags no README

### bot.py
- [ ] Estratégias testadas com dados históricos
- [ ] Custos de trading considerados (taxas)
- [ ] Logs de debug adicionados
- [ ] Tratamento de erros implementado

## 🗄️ Alterações em Database

### database.py
- [ ] Todos os callers das funções atualizados
- [ ] Schema documentado
- [ ] Migrations criadas (se necessário)
- [ ] Índices verificados/atualizados
- [ ] Rodar `python -m py_compile database.py`

### Tabelas Novas/Modificadas
- [ ] CREATE TABLE statements testados
- [ ] Foreign keys validadas
- [ ] Índices para performance
- [ ] Backup antes de migration em produção

## 🎨 Alterações em UI

### ui.py
- [ ] Sintaxe OK: `python -m py_compile ui.py`
- [ ] Navegação por tabs funcional
- [ ] Validado com scraper: `python agent0_scraper.py --local --test-dashboard`
- [ ] Session state gerenciado corretamente
- [ ] Tema aplicado consistentemente

### sidebar_controller.py
- [ ] Inputs validados
- [ ] Session state sincronizado
- [ ] Valores padrão corretos

### terminal_component.py
- [ ] Shape do JSON preservada
- [ ] Headers CORS mantidos
- [ ] Endpoint testado: `curl http://localhost:8765/api/logs?bot=test`
- [ ] Tratamento de erros 404/500

## 🔌 Alterações em API

### api.py
- [ ] Testado em dry-run primeiro
- [ ] Rate limits respeitados (30 req/3s trading, 10 req/3s data)
- [ ] Retry logic implementado
- [ ] Erros KuCoin tratados (code != "200000")
- [ ] Timeout configurado (default 15s)

### Credenciais
- [ ] Não hardcoded no código
- [ ] `.env` ou `st.secrets` utilizado
- [ ] Validação `_has_keys()` antes de chamadas privadas

## 🧪 Testes

### Unitários
- [ ] `pytest tests/` passa
- [ ] Cobertura de código mantida/aumentada
- [ ] Mocks para APIs externas

### E2E (Selenium)
- [ ] `RUN_SELENIUM=1 ./run_tests.sh` passa
- [ ] Screenshots gerados em caso de erro
- [ ] Testes rodando no WSL (não Windows)

### Scraper
- [ ] `python agent0_scraper.py --local --test-all` passa
- [ ] Relatórios gerados
- [ ] Elementos críticos validados

## 🚀 Deploy

### Docker
- [ ] `docker build -t autocoinbot .` sem erros
- [ ] `.dockerignore` atualizado
- [ ] Variáveis de ambiente via `--env-file`

### Fly.io
- [ ] `fly.toml` atualizado
- [ ] Secrets configurados: `fly secrets set`
- [ ] `fly deploy` testado em staging primeiro

### CI/CD
- [ ] Pre-commit hooks instalados: `pre-commit install`
- [ ] `ggshield` configurado para scan de secrets
- [ ] `GITGUARDIAN_API_KEY` no repositório

## 📚 Documentação

### README e Docs
- [ ] README.md atualizado com novas features
- [ ] AGENTE_TREINAMENTO.md sincronizado
- [ ] Docstrings em funções novas
- [ ] Exemplos de uso adicionados

### Git
- [ ] Commit message segue padrão: `tipo(escopo): descrição`
- [ ] Branch naming: `feature/nome`, `fix/nome`, `docs/nome`
- [ ] PR description clara e completa

## 🔐 Segurança

- [ ] Nenhum secret commitado
- [ ] `.env` no `.gitignore`
- [ ] Inputs do usuário validados/sanitizados
- [ ] SQL injection prevenido (parametrized queries)

## 📊 Performance

- [ ] Queries do DB otimizadas (usar EXPLAIN)
- [ ] Cache implementado onde apropriado
- [ ] Rate limiting respeitado
- [ ] Logs não excessivos em produção

## 🐛 Rollback Plan

- [ ] Saber como reverter mudança
- [ ] Backup do DB antes de migration
- [ ] Versão anterior deployável
- [ ] Documentar breaking changes

---

**Lembrete:** Sempre testar em **dry-run** antes de executar com dinheiro real!
