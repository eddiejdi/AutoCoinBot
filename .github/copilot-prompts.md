# Copilot Prompts — AutoCoinBot (curto e resiliente)

Use prompts curtos para reduzir falhas “Response contained no choices”. Evite anexar arquivos grandes desnecessariamente.

Prompts base (substitua <...>)
- Revisão pontual
  - “Revise apenas [ui.py] nas linhas relevantes ao render de monitor. Ignore logs/HTML. Aponte riscos de travar UI (session_state vs value).”
- Diff dirigido
  - “Gere patch para trocar hardcode de 127.0.0.1 por URL relativa no [ui.py] ao embutir iframes, mantendo padrão FLY_APP_NAME.”
- Teste mínimo
  - “Escreva teste simples para validar que `DatabaseManager.get_bot_logs()` retorna `timestamp` float e `message` string.”
- Bug específico
  - “No [terminal_component.py], ajuste `/monitor` para usar window.location.origin no HTML gerado. Foque apenas nessa rota.”
- Refactor seguro
  - “Extraia função utilitária para formatar timestamps (float→string) e use-a na coluna ‘Último Evento’ em [ui.py], sem mexer em blocos 🔒.”
- CI rápido
  - “Liste comandos para rodar testes sem Selenium e checar sintaxe, sem mudar código.”

Quando o chat falhar
- Reduza o escopo (um arquivo/uma função/um trecho de linhas).
- Peça patches incrementais e pequenos.
- Remova anexos grandes; prefira links e referências a arquivos/linhas.

Referência
- Guia TL;DR e troubleshooting: .github/copilot-instructions.md
- Agente padrão: .github/agents.json