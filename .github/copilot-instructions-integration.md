Integração: verificação automática de conflitos antes do diagnóstico

Resumo
- Adicionei um script de diagnóstico que executa, na ordem: `scripts/check_merge_conflicts.sh`, verificação de sintaxe Python e testes (`pytest`) quando disponível.

Como usar
- Para executar o diagnóstico manualmente:

```bash
./scripts/run_diagnostics.sh
```

Sugestão de integração
- Incluir a chamada a `./scripts/run_diagnostics.sh` no início de qualquer processo de CI local, pipeline de build ou antes de rodar `pytest` diretamente.
- Exemplo (local):

```bash
# exemplo de uso em um fluxo local de debug
./scripts/run_diagnostics.sh || exit 1
# se passou, prosseguir com ações de correção/execução
```

Notas
- O script falhará imediatamente se encontrar marcadores de conflito `<<<<<<<` / `=======` / `>>>>>>>`.
- Recomendo mesclar esse conteúdo no arquivo principal `.github/copilot-instructions.md` durante revisão humana.
