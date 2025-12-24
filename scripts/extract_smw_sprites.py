#!/usr/bin/env python3
"""Extract named sprites from SMW enemy sheet using absolute pixel coords.

This implements the exact workflow you shared:
- open the sheet (2192x1936)
- crop rectangles given by tx/ty/width/height
- save each crop as PNG

By default, it reads from the workspace sheet:
  themes/smw/characters/enemies_sheet.png
and writes into:
  scripts/out/smw_sprites_extracted/

It also optionally exports quick animated GIFs for entries that look like strips
(e.g. width divisible by 16 and notes mention frames).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from PIL import Image


SHEET_DEFAULT = Path("themes/smw/characters/enemies_sheet.png")
OUT_DEFAULT = Path("scripts/out/smw_sprites_extracted")


@dataclass(frozen=True)
class SpriteDef:
    name: str
    tx: int
    ty: int
    width: int
    height: int
    notes: str | None = None


SPRITES: list[SpriteDef] = [
    SpriteDef("Goomba", 136, 88, 80, 24, "4 frames de caminhada"),
    SpriteDef("Para_Goomba", 224, 88, 32, 40),
    SpriteDef("Lakitu", 192, 40, 48, 88),
    SpriteDef("Spiny", 248, 56, 24, 24),
    SpriteDef("Bob_omb", 120, 120, 48, 24),
    SpriteDef("Hammer_Brother", 456, 48, 48, 40),
    SpriteDef("Boomerang_Brother", 504, 48, 48, 40),
    SpriteDef("Fire_Brother", 552, 48, 48, 40),
    SpriteDef("Dry_Bones", 456, 128, 64, 40),
    SpriteDef("Bony_Beetle", 520, 128, 32, 24),
    SpriteDef("Sumo_Brother", 896, 48, 48, 48),
    SpriteDef("Monty_Mole", 896, 112, 32, 24),
    SpriteDef("Pokey", 992, 80, 32, 80),
    SpriteDef("Volcano_Lotus", 936, 48, 32, 48),
    SpriteDef("Rex", 1336, 64, 48, 48),
    SpriteDef("Mega_Mole", 1336, 128, 48, 48),
    SpriteDef("Bullet_Bill", 1336, 192, 48, 24),
    SpriteDef("Banzai_Bill", 1776, 48, 96, 96),
    SpriteDef("Dino_Rhino", 1840, 64, 72, 64),
    SpriteDef("Dino_Torch", 1896, 64, 48, 48),
    SpriteDef("Koopa_Troopa_Verde", 896, 400, 32, 48),
    SpriteDef("Koopa_Troopa_Vermelho", 960, 400, 32, 48),
    SpriteDef("Koopa_Troopa_Azul", 1024, 400, 32, 48),
    SpriteDef("Koopa_Troopa_Amarelo", 1088, 400, 32, 48),
    SpriteDef("Para_Koopa", 896, 464, 48, 48),
    SpriteDef("Beach_Koopa", 896, 528, 32, 32),
    SpriteDef("Big_Boo", 16, 752, 48, 48),
    SpriteDef("Boo", 64, 752, 32, 32),
    SpriteDef("Eerie", 96, 752, 32, 32),
    SpriteDef("Podoboo", 192, 784, 32, 48),
    SpriteDef("Thwomp", 896, 752, 48, 64),
    SpriteDef("Thwimp", 896, 832, 24, 24),
    SpriteDef("Grinder", 1776, 752, 32, 32),
    SpriteDef("Ball_n_Chain", 1808, 752, 48, 48),
    SpriteDef("Reznor", 1336, 1456, 72, 72),
    SpriteDef("Blargg", 1400, 1456, 48, 48),
    SpriteDef("Mechakoopa", 48, 1456, 32, 32),
    SpriteDef("Chargin_Chuck", 896, 1104, 96, 64),
    SpriteDef("Wiggler", 1336, 1104, 96, 32),
    SpriteDef("Piranha_Plant", 936, 400, 32, 48),
    SpriteDef("Coin", 1776, 1456, 64, 16, "4 frames de rotação"),
    SpriteDef("Peach_Ending", 16, 1792, 48, 64),
    SpriteDef("Mario_Ending", 64, 1792, 32, 48),
    SpriteDef("Luigi_Ending", 112, 1792, 32, 48),
]


def sanitize_filename(name: str) -> str:
    s = name.strip().replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_\-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "sprite"


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=str(SHEET_DEFAULT))
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args()

    sheet_path = Path(args.sheet)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    im = Image.open(sheet_path).convert("RGBA")
    print(f"Spritesheet carregado: {sheet_path} size={im.size}")

    for s in SPRITES:
        box = (s.tx, s.ty, s.tx + s.width, s.ty + s.height)
        crop = im.crop(box)
        fn = out_dir / f"{sanitize_filename(s.name)}.png"
        crop.save(fn)
        print(f"Salvo: {fn} ({s.width}x{s.height})")

    print(f"\nExtração concluída! Pasta: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
