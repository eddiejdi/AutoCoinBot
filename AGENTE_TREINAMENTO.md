<<<<<<< HEAD
# Manual de Treinamento para Agente - Aplicação KuCoin Trading Bot
# Pontos de Ajuste Encontrados (Sessão de Debug 2025)

## Resumo dos Principais Ajustes e Problemas Identificados

- **Bots ativos não aparecem no dashboard:**
    - Verificar se a função `get_active_bots` em `database.py` está retornando corretamente e se o frontend (`ui.py`) está consumindo corretamente.
    - Checar se o status dos bots está sendo atualizado corretamente no banco (campo `status` em `bot_sessions`).
    - Validar se o dashboard está buscando do banco ou apenas da memória (problema comum após reload/F5).

- **Gráficos de aprendizado não aparecem:**
    - Faltavam métodos `get_learning_stats`, `get_learning_history`, `get_learning_symbols` no `DatabaseManager` (`database.py`).
    - Corrigir para garantir que a aba Aprendizado sempre busque dados reais do banco.
    - Validar se as tabelas `learning_stats` e `learning_history` existem e estão populadas.

- **Navegação por URL/tab não funcionava:**
    - Implementado suporte a seleção de abas via query string (`?view=aprendizado`, `?view=report`, etc.) no frontend (`ui.py`).
    - Permite abrir diretamente a aba desejada por link.

- **Frontend quebrado após alterações:**
    - Sempre rodar `python -m py_compile ui.py` e checar logs após mudanças.
    - Validar se todos os componentes obrigatórios estão presentes (ex: botões START/STOP, tabelas, gráficos).

- **Testes Selenium e validação visual:**
    - Scripts Selenium ajustados para login robusto, navegação por abas e validação de elementos.
    - Testes automatizados para garantir que gráficos e bots ativos aparecem corretamente.

- **Outros pontos recorrentes:**
    - Persistência de login pode falhar se `.login_status` não for manipulado corretamente.
    - Problemas de API KuCoin geralmente são credenciais ou rate limit.
    - Sempre reiniciar a aplicação após mudanças críticas.

---

=======
# AGENTE_TREINAMENTO — Diretrizes e Relatórios
>>>>>>> Autooin/main

## Política obrigatória
- Todos os bots, scripts e agentes devem seguir estritamente as instruções do usuário responsável pelo projeto.
- Qualquer ação automatizada deverá obedecer às orientações explícitas presentes neste arquivo e nos READMEs do repositório.
- Em caso de conflito entre comportamento automatizado e instruções do usuário, o agente deve interromper a ação e registrar um relatório detalhado.

## Objetivo do treinamento
- Tornar os agentes (ex.: `agent0_scraper.py`) robustos, auditáveis e previsíveis.
- Garantir que todas as tentativas automáticas de login, testes e deploys registrem evidências (logs, HTML snapshots, relatórios) em caso de erro.

## Procedimentos obrigatórios de teste e validação
1. Antes de executar validações visuais automatizadas, remover o arquivo persistente de login: `.login_status`.
2. Sempre executar `python -m py_compile` nos arquivos alterados.
3. Executar a suite de testes com `pytest` quando disponível; caso falhe por dependências, gravar o erro em `relatorio_testes.txt`.
4. Em caso de falha visual, criar/atualizar `relatorio_validacao_attempt_<N>.md` contendo:
   - URL testada
   - Screenshot (quando possível)
   - Lista de verificações (OK / NÃO ENCONTRADO)
   - Stack trace + HTML snapshot (arquivo `login_error.txt` ou equivalente)

## Consolidação de relatórios
- Os relatórios de validação existentes foram agregados abaixo para referência.

### Relatórios existentes (consolidados)

- `relatorio_validacao.md`

```
# Validação visual do app: http://localhost:8501

- Elemento 'h1': NÃO ENCONTRADO
- Elemento 'stButton': OK
- Elemento 'stDataFrame': NÃO ENCONTRADO
- Elemento 'stAlert': NÃO ENCONTRADO
- Elemento 'stSidebar': OK
- Elemento 'login_preenchido': NÃO ENCONTRADO
```

- `relatorio_validacao_attempt_1.md`

```
# Validação visual do app: http://localhost:8501

- Elemento 'h1': NÃO ENCONTRADO
- Elemento 'stButton': OK
- Elemento 'stDataFrame': NÃO ENCONTRADO
- Elemento 'stAlert': NÃO ENCONTRADO
- Elemento 'stSidebar': OK
- Elemento 'login_preenchido': NÃO ENCONTRADO
```

- `relatorio_validacao_attempt_2.md`

```
# Validação visual do app: http://localhost:8501

- Elemento 'h1': NÃO ENCONTRADO
- Elemento 'stButton': OK
- Elemento 'stDataFrame': NÃO ENCONTRADO
- Elemento 'stAlert': NÃO ENCONTRADO
- Elemento 'stSidebar': OK
- Elemento 'login_preenchido': NÃO ENCONTRADO
```

- `relatorio_validacao_attempt_3.md`

## Regras de Colocação de Arquivos (Boas Práticas)

Sempre que novos arquivos forem criados no repositório, siga estas regras para garantir organização e rastreabilidade:

- **Documentação (`.md`)**: coloque em `docs/` salvo exceções explícitas (ex.: `README.md`, `AGENTE_TREINAMENTO.md`). Relatórios gerados automaticamente devem ir para `docs/reports/`.
- **Scripts e utilitários (`.py`)**: scripts utilitários e pequenas ferramentas devem ficar em `scripts/`. Aplicação principal fica na raiz apenas quando necessário (ex.: `streamlit_app.py`), mas prefira `app/` ou `src/` para novos módulos.
- **Imagens e screenshots (`.png`, `.jpg`)**: mantenha em `docs/reports/images/` ou `assets/images/`.
- **Dados e configurações (`.json`, `.db`)**: coloque em `data/` ou `configs/` conforme a natureza; não deixe arquivos de dados soltos na raiz.
- **Relatórios temporários**: arquivos gerados por validações automáticas devem ser salvos em `docs/reports/` com nomes que incluam timestamp e `bot_id`.

Ferramenta de verificação e correção rápida
----------------------------------------
Incluímos um pequeno utilitário para verificar se há arquivos fora das pastas recomendadas: `scripts/check_file_placement.py`.

Uso recomendado (somente verificação):

```bash
python scripts/check_file_placement.py
```

Para mover automaticamente os arquivos para os destinos sugeridos (use com cautela):

```bash
python scripts/check_file_placement.py --move --yes
```

Integração CI
-------------
Adicione `python scripts/check_file_placement.py` ao pipeline/CI para rejeitar commits que deixem arquivos fora das pastas recomendadas.

Observação
---------
Essas regras são conservadoras — antes de mover arquivos automaticamente confirme a intenção, pois movimentos podem requerer ajustes de imports/paths.


```
# Validação visual do app: http://localhost:8501

- Elemento 'h1': NÃO ENCONTRADO
- Elemento 'stButton': OK
- Elemento 'stDataFrame': NÃO ENCONTRADO
- Elemento 'stAlert': NÃO ENCONTRADO
- Elemento 'stSidebar': OK
- Elemento 'login_preenchido': NÃO ENCONTRADO
```

## Como usar este documento
- Atualize este arquivo sempre que adicionar novas regras de operação/automações para agentes.
- Antes de rodar bots de validação automatizada, verifique a seção "Procedimentos obrigatórios".

## Contato
- Mantenha o proprietário do projeto informado sobre qualquer alteração de comportamento do agente.
