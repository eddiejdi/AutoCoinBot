#!/usr/bin/env python3
"""Organize a user-provided sprite/background pack into a predictable structure.

This script is intentionally generic: it does not assume any specific game.
It normalizes filenames, groups files by type (backgrounds/characters/ui),
and writes a manifest mapping original -> new paths.

Usage:
  python3 scripts/organize_sprite_pack.py \
    --src /path/to/source \
    --dst themes/user_sprite_pack \
    --mode copy

Modes:
  copy (default)  - keep originals, copy into dst
  move            - move originals into dst
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


def slugify(name: str) -> str:
    s = name.strip()
    s = s.replace("-", " ")
    s = re.sub(r"\((\d+)\)", "", s)  # drop parentheses counters like (12)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s.lower()


def classify(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        # default images to backgrounds unless filename suggests otherwise
        n = path.stem.lower()
        if any(k in n for k in ("ui", "hud", "button", "icon", "cursor")):
            return "ui"
        if any(k in n for k in ("char", "player", "enemy", "npc", "sprite")):
            return "characters"
        return "backgrounds"
    if ext in {".wav", ".mp3", ".ogg"}:
        return "audio"
    return "misc"


def ensure_unique(dest_dir: Path, base: str, ext: str) -> str:
    cand = f"{base}{ext}"
    i = 2
    while (dest_dir / cand).exists():
        cand = f"{base}_{i}{ext}"
        i += 1
    return cand


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--mode", choices=["copy", "move"], default="copy")
    args = ap.parse_args()

    src = Path(args.src).expanduser().resolve()
    dst = Path(args.dst).expanduser().resolve()

    if not src.exists() or not src.is_dir():
        raise SystemExit(f"Source not found or not a dir: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, str] = {}

    files = [p for p in src.iterdir() if p.is_file()]
    for p in sorted(files, key=lambda x: x.name.lower()):
        bucket = classify(p)
        out_dir = dst / bucket
        out_dir.mkdir(parents=True, exist_ok=True)

        base = slugify(p.stem)
        if not base:
            base = "asset"

        out_name = ensure_unique(out_dir, base, p.suffix.lower())
        out_path = out_dir / out_name

        if args.mode == "move":
            shutil.move(str(p), str(out_path))
        else:
            shutil.copy2(str(p), str(out_path))

        manifest[str(p)] = str(out_path)

    (dst / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    readme = dst / "README.txt"
    if not readme.exists():
        readme.write_text(
            "This folder contains a user-provided asset pack organized by type.\n"
            "If you want the app to load these assets, wire it via the theme loader.\n",
            encoding="utf-8",
        )

    print(f"Organized {len(manifest)} files into {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
