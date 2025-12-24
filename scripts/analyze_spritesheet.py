#!/usr/bin/env python3
"""Analyze a spritesheet and propose candidate animated strips.

Goal
----
When a sheet is a big collage (like SMW 'Enemy Cast Roll' sheets),
hand-picking x/y is error-prone. This script:
- scans the sheet on a 16x16 grid (configurable)
- measures how much non-background content each tile has
- searches for horizontal strips of N frames (default 4)
- exports:
  - an index image with a coarse grid + coordinate labels
  - a text file with candidate (x,y) starts
  - a few candidate GIFs for quick visual validation

This matches the practical workflow used on SNES-era assets:
frames are placed on a fixed grid, typically multiples of 8 or 16.

Usage
-----
python scripts/analyze_spritesheet.py \
  --sheet themes/smw/characters/enemies_sheet.png \
  --tile 16 --frames 4 --top 12 \
  --colorkey '#5C94FC' \
  --out-dir scripts/out
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def parse_hex_color(value: str) -> tuple[int, int, int] | None:
    if not value:
        return None
    s = value.strip()
    if len(s) != 7 or not s.startswith('#'):
        return None
    try:
        return int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16)
    except ValueError:
        return None


def nonbg_mask(arr_rgb: np.ndarray, colorkey: tuple[int, int, int] | None, tol: int = 0) -> np.ndarray:
    """Return boolean mask where pixel is considered foreground."""
    if arr_rgb.ndim != 3 or arr_rgb.shape[2] < 3:
        raise ValueError('expected RGB array')
    if colorkey is None:
        # treat pure black as bg? no. Assume everything is fg.
        return np.ones(arr_rgb.shape[:2], dtype=bool)

    r, g, b = colorkey
    dr = np.abs(arr_rgb[:, :, 0].astype(np.int16) - r)
    dg = np.abs(arr_rgb[:, :, 1].astype(np.int16) - g)
    db = np.abs(arr_rgb[:, :, 2].astype(np.int16) - b)
    if tol <= 0:
        is_bg = (dr == 0) & (dg == 0) & (db == 0)
    else:
        is_bg = (dr <= tol) & (dg <= tol) & (db <= tol)
    return ~is_bg


@dataclass(frozen=True)
class Candidate:
    x: int
    y: int
    mean: float
    var: float
    counts: tuple[int, ...]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', required=True)
    ap.add_argument('--tile', type=int, default=16)
    ap.add_argument('--frames', type=int, default=4)
    ap.add_argument('--top', type=int, default=12)
    ap.add_argument('--colorkey', type=str, default=None, help='Optional background color (hex) to ignore')
    ap.add_argument('--tol', type=int, default=8, help='color key tolerance (only used if --colorkey is set)')
    ap.add_argument('--min-energy', type=float, default=6.0, help='Minimum per-tile texture energy (stddev on luma)')
    ap.add_argument('--out-dir', type=str, default='scripts/out')
    args = ap.parse_args()

    sheet_path = Path(args.sheet)
    if not sheet_path.exists():
        raise SystemExit(f'not found: {sheet_path}')

    tile = max(1, int(args.tile))
    frames = max(2, int(args.frames))
    topn = max(1, int(args.top))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    im = Image.open(sheet_path).convert('RGB')
    w, h = im.size
    arr = np.asarray(im)

    ck = parse_hex_color(args.colorkey) if args.colorkey else None
    mask = nonbg_mask(arr, ck, tol=max(0, int(args.tol))) if ck else None

    # precompute per-tile metrics
    grid_w = w // tile
    grid_h = h // tile
    counts = np.zeros((grid_h, grid_w), dtype=np.int32)
    energy = np.zeros((grid_h, grid_w), dtype=np.float32)

    for gy in range(grid_h):
        y0 = gy * tile
        y1 = y0 + tile
        for gx in range(grid_w):
            x0 = gx * tile
            x1 = x0 + tile

            block = arr[y0:y1, x0:x1, :3].astype(np.float32)
            # Texture energy proxy: stddev of luma within the tile.
            luma = block[:, :, 0] * 0.299 + block[:, :, 1] * 0.587 + block[:, :, 2] * 0.114
            energy[gy, gx] = float(luma.std())

            if mask is not None:
                counts[gy, gx] = int(mask[y0:y1, x0:x1].sum())
            else:
                # Fallback: approximate foreground by counting pixels away from the tile median color.
                med = np.median(block.reshape(-1, 3), axis=0)
                dist = np.abs(block - med).sum(axis=2)
                counts[gy, gx] = int((dist > 18.0).sum())

    # Search for horizontal strips of length frames
    cands: list[Candidate] = []
    min_mean = max(10, int(tile * tile * 0.05))  # at least some pixels
    min_energy = float(args.min_energy)

    for gy in range(grid_h):
        for gx in range(0, grid_w - frames + 1):
            seg = counts[gy, gx:gx + frames]
            e = energy[gy, gx:gx + frames]
            m = float(seg.mean())
            if m < min_mean:
                continue
            v = float(seg.var())
            # Prefer strips where all frames have non-trivial content and similar density
            if seg.min() < min_mean:
                continue
            if v > (m * 0.35):
                continue
            if float(e.min()) < min_energy:
                continue
            # Keep texture consistency too
            if float(e.var()) > max(1.0, float(e.mean()) * 0.8):
                continue
            cands.append(Candidate(x=gx * tile, y=gy * tile, mean=m, var=v, counts=tuple(int(x) for x in seg)))

    cands.sort(key=lambda c: (-(c.mean), c.var))

    # de-duplicate by spatial proximity
    chosen: list[Candidate] = []
    for c in cands:
        if len(chosen) >= topn:
            break
        too_close = any(abs(c.x - o.x) <= tile * 2 and abs(c.y - o.y) <= tile * 1 for o in chosen)
        if too_close:
            continue
        chosen.append(c)

    # Write candidates text
    txt = out_dir / 'spritesheet_candidates.txt'
    with txt.open('w', encoding='utf-8') as f:
        f.write(f'sheet={sheet_path}\nsize={w}x{h}\ntile={tile} frames={frames} colorkey={args.colorkey} tol={args.tol} min_energy={min_energy}\n\n')
        for i, c in enumerate(chosen, 1):
            f.write(f'#{i}: x={c.x} y={c.y} mean={c.mean:.1f} var={c.var:.1f} counts={list(c.counts)}\n')

    # Create a coarse index image with labels every 64px to reduce clutter
    idx = im.copy()
    draw = ImageDraw.Draw(idx)

    step = 64
    # grid lines
    for x in range(0, w + 1, step):
        draw.line([(x, 0), (x, h)], fill=(0, 0, 0), width=1)
    for y in range(0, h + 1, step):
        draw.line([(0, y), (w, y)], fill=(0, 0, 0), width=1)

    # labels
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for x in range(0, w, step):
        draw.text((x + 2, 2), str(x), fill=(255, 255, 255), font=font)
    for y in range(0, h, step):
        draw.text((2, y + 2), str(y), fill=(255, 255, 255), font=font)

    # highlight chosen candidates
    for i, c in enumerate(chosen, 1):
        x0, y0 = c.x, c.y
        x1 = x0 + frames * tile
        y1 = y0 + tile
        draw.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2)
        draw.text((x0 + 2, y0 + 2), f'C{i}', fill=(255, 255, 0), font=font)

    idx_path = out_dir / 'spritesheet_index.png'
    idx.save(idx_path)

    print(f'Wrote: {txt}')
    print(f'Wrote: {idx_path}')
    print('Top candidates:')
    for i, c in enumerate(chosen, 1):
        print(f'  #{i}: x={c.x} y={c.y} counts={list(c.counts)}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
