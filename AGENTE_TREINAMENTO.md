<<<<<<< HEAD
# Manual de Treinamento para Agente - Aplicação KuCoin Trading Bot
```markdown
# AGENTE_TREINAMENTO — Manual e Diretrizes

## Resumo dos Principais Ajustes e Problemas Identificados

- Bots ativos não aparecem no dashboard:
    - Verificar se a função `get_active_bots` em `database.py` está retornando corretamente e se o frontend (`ui.py`) consome corretamente.
    - Checar se o status dos bots está sendo atualizado no banco (`status` em `bot_sessions`).
    - Validar se o dashboard busca do banco ou apenas da memória (problema comum após reload/F5).

- Gráficos de aprendizado não aparecem:
    - Confirmar existência e população das tabelas `learning_stats` e `learning_history`.
    - Garantir que `DatabaseManager` exponha `get_learning_stats`, `get_learning_history`, `get_learning_symbols`.

- Navegação por URL/tab não funcionava:
    - Implementado suporte a seleção de abas via query string (`?view=aprendizado`, `?view=report`, etc.) no frontend (`ui.py`).

- Frontend quebrado após alterações:
    - Rodar `python -m py_compile ui.py` e checar logs após mudanças.

- Testes Selenium e validação visual:
    - Scripts ajustados para login robusto e validação de elementos.

## Política obrigatória
- Todos os bots, scripts e agentes devem seguir as instruções do responsável pelo projeto.
- Ações automatizadas devem obedecer às orientações neste documento e nos READMEs do repositório.

## Procedimentos obrigatórios de teste e validação
1. Remover `.login_status` antes de validações visuais automatizadas.
2. Executar `python -m py_compile` nos arquivos alterados.
3. Rodar `pytest` quando disponível; em caso de falha por dependências, gravar em `relatorio_testes.txt`.
4. Em falha visual, criar/atualizar `relatorio_validacao_attempt_<N>.md` com URL, screenshot, verificações, stack trace e HTML snapshot.

## Consolidação de relatórios
- Relatórios existentes agregados em `relatorio_validacao.md` e `relatorio_validacao_attempt_*.md`.

## Regras de Colocação de Arquivos (Boas Práticas)
- Documentação: coloque em `docs/` salvo exceções explícitas.
- Scripts/utilitários: `scripts/`.
- Imagens/screenshots: `docs/reports/images/` ou `assets/images/`.
- Dados/configs: `data/` ou `configs/`.
- Relatórios temporários: `docs/reports/` com timestamp + `bot_id`.

## Integração CI
- Adicione `python scripts/check_file_placement.py` ao pipeline para validar colocação de arquivos.

## Observação
- Antes de mover arquivos automaticamente confirme a intenção — movimentos podem exigir ajustes de imports/paths.

## Contato
- Mantenha o proprietário do projeto informado sobre mudanças de comportamento dos agentes.

```
## Como usar este documento
- Atualize este arquivo sempre que adicionar novas regras de operação/automações para agentes.
- Antes de rodar bots de validação automatizada, verifique a seção "Procedimentos obrigatórios".

## Contato
- Mantenha o proprietário do projeto informado sobre qualquer alteração de comportamento do agente.
