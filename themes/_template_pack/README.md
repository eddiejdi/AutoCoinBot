# Template pack (user assets)

Coloque seus arquivos aqui para criar um pack de tema.

## Pastas
- `backgrounds/` : imagens de fundo (PNG/JPG/WEBP)
- `characters/`  : sprites/personagens (PNG/WEBP) ou spritesheets
- `ui/`          : ícones/botões/badges (PNG/WEBP/SVG se quiser)
- `tiles/`       : formatos estilo console (opcional)
  - recomendado: `.chr` (tiles 4bpp), `.bin` etc
- `palettes/`    : paletas (opcional)
  - recomendado: `.pal` (BGR555) ou `.json`
- `meta/`        : metadados extras (licença, notas, mapeamentos)

## Como o monitor usa
Hoje o monitor usa fundo via query string:
- `bg_pack=<pack>&bg=<nome_sem_extensao>`

Isso resolve o problema de refresh: o fundo fica “preso” na URL.

Exemplo:
- `/monitor?bot=<id>&bg_pack=_template_pack&bg=meu_fundo_01`

## Checklist
- Nomes em minúsculas com `_` (ex: `donut_plains_1.png`)
- Sem espaços/acento (evita problemas de URL)

