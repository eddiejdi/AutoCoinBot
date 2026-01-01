Adendo: Verificação de merges não resolvidos

Objetivo
- Garantir que, sempre que ocorrer um erro em execução ou teste, a primeira ação automatizada e as instruções de diagnóstico incluam uma verificação por marcadores de conflito Git ("<<<<<<<", "=======", ">>>>>>>").

Sugestão de texto a inserir em `.github/copilot-instructions.md`

"Regra rápida de diagnóstico de erros:
1. Ao detectar qualquer erro em testes, execução ou build, primeiro verifique se há conflitos de merge não resolvidos no repositório. Procure por linhas contendo:
   - `<<<<<<<`
   - `=======`
   - `>>>>>>>`
2. Se encontrar algum marcador, resolva os conflitos antes de prosseguir com outras correções — esses marcadores frequentemente causam falhas de build (ex.: `Dockerfile`), erros de parsing e comportamentos inesperados.
3. Ferramentas recomendadas para busca rápida:
   - `grep -RIn "^<<<<<<<\|^=======$\|^>>>>>>>" --exclude-dir=venv --exclude-dir=.git .`
"

Detalhes de implementação
- Podemos (opcional) adicionar um script simples `scripts/check_merge_conflicts.sh` que roda a busca acima e retorna código 1 quando encontrar marcadores.
- Também recomendo incluir esta verificação no checklist inicial de diagnóstico descrito em `copilot-instructions.md`.

Responsável: Copilot (agente automatizado) — revisão humana recomendada antes de mesclar no arquivo principal.
