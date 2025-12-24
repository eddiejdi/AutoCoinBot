#!/usr/bin/env python3
"""Extract frames from a spritesheet and save as an animated GIF.

This is a small, dependency-light utility meant to validate the same logic
used by classic console-era spritesheets:
- sprites are stored as a grid / strip inside a larger image
- animation is a sequence of rectangular crops

It supports:
- horizontal frame strips (x + i*frame_w)
- transparency via a color key (e.g. SNES common sky blue)
- a fully synthetic `--demo` mode (safe to run anywhere)

Examples
--------
Demo (creates scripts/out/demo.gif):
  python scripts/spritesheet_to_gif.py --demo

Goomba-like strip (4 frames) using your sheet:
  python scripts/spritesheet_to_gif.py \
    --sheet themes/smw/characters/enemies_sheet.png \
    --x 16 --y 0 --frame-w 16 --frame-h 16 --frames 4 \
    --scale 2 --colorkey '#5C94FC' \
    --out scripts/out/goomba.gif

Notes
-----
If you already have alpha transparency in the PNG, you can omit --colorkey.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def parse_hex_color(value: str) -> tuple[int, int, int] | None:
    if not value:
        return None
    s = value.strip()
    if len(s) != 7 or not s.startswith("#"):
        return None
    try:
        r = int(s[1:3], 16)
        g = int(s[3:5], 16)
        b = int(s[5:7], 16)
        return r, g, b
    except ValueError:
        return None


def apply_colorkey_rgba(img: Image.Image, colorkey: tuple[int, int, int]) -> Image.Image:
    """Return a RGBA image with any exact colorkey pixels made transparent."""
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba)
    r, g, b = colorkey
    mask = (arr[:, :, 0] == r) & (arr[:, :, 1] == g) & (arr[:, :, 2] == b)
    arr = arr.copy()
    arr[mask, 3] = 0
    return Image.fromarray(arr, mode="RGBA")


def make_demo_sheet(tile: int = 16, frames: int = 4) -> Image.Image:
    """Build a small synthetic sheet for validating extraction+GIF save."""
    w = tile * frames
    h = tile
    bg = np.zeros((h, w, 4), dtype=np.uint8)
    bg[:, :, :] = (0x5C, 0x94, 0xFC, 255)  # classic SNES-ish sky blue

    for i in range(frames):
        x0 = i * tile
        # simple "walker" blob that shifts left/right
        cx = x0 + tile // 2 + (i % 2) * 2 - 1
        cy = tile // 2
        for y in range(h):
            for x in range(x0, x0 + tile):
                if (x - cx) ** 2 + (y - cy) ** 2 <= 28:
                    bg[y, x, :] = (0xE5, 0x25, 0x21, 255)  # red
        # feet
        bg[tile - 3 : tile - 1, x0 + 3 : x0 + 6, :] = (0x43, 0xB0, 0x47, 255)  # green
        bg[tile - 3 : tile - 1, x0 + 10 : x0 + 13, :] = (0x43, 0xB0, 0x47, 255)

    return Image.fromarray(bg, mode="RGBA")


def extract_strip_frames(sheet: Image.Image, x: int, y: int, frame_w: int, frame_h: int, frames: int) -> list[Image.Image]:
    out: list[Image.Image] = []
    for i in range(frames):
        box = (x + i * frame_w, y, x + (i + 1) * frame_w, y + frame_h)
        out.append(sheet.crop(box))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", type=str, default=None, help="Path to spritesheet image (PNG/WebP/JPG)")
    ap.add_argument("--x", type=int, default=0, help="Top-left X (pixels)")
    ap.add_argument("--y", type=int, default=0, help="Top-left Y (pixels)")
    ap.add_argument("--frame-w", type=int, default=16, help="Frame width (pixels)")
    ap.add_argument("--frame-h", type=int, default=16, help="Frame height (pixels)")
    ap.add_argument("--frames", type=int, default=4, help="Number of frames")
    ap.add_argument("--duration-ms", type=int, default=150, help="Duration per frame in ms")
    ap.add_argument("--scale", type=int, default=2, help="Nearest-neighbor scale")
    ap.add_argument("--colorkey", type=str, default=None, help="Hex color to make transparent, e.g. #5C94FC")
    ap.add_argument("--out", type=str, default="scripts/out/out.gif", help="Output GIF path")
    ap.add_argument("--demo", action="store_true", help="Use a generated synthetic sheet instead of loading a file")
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.demo:
        sheet = make_demo_sheet(tile=max(8, args.frame_w), frames=max(2, args.frames))
    else:
        if not args.sheet:
            raise SystemExit("--sheet is required unless --demo is used")
        sheet_path = Path(args.sheet)
        if not sheet_path.exists():
            raise SystemExit(f"Sheet not found: {sheet_path}")
        sheet = Image.open(sheet_path)

    frames = extract_strip_frames(sheet, args.x, args.y, args.frame_w, args.frame_h, args.frames)

    ck = parse_hex_color(args.colorkey) if args.colorkey else None
    if ck:
        frames = [apply_colorkey_rgba(f, ck) for f in frames]

    if args.scale and args.scale != 1:
        frames = [
            f.resize((f.width * args.scale, f.height * args.scale), resample=Image.Resampling.NEAREST)
            for f in frames
        ]

    # Save as GIF
    frames0 = frames[0]
    frames_rest = frames[1:]
    frames0.save(
        out_path,
        save_all=True,
        append_images=frames_rest,
        duration=max(20, args.duration_ms),
        loop=0,
        disposal=2,
        optimize=False,
    )

    print(f"Wrote: {out_path} ({len(frames)} frames, {args.frame_w}x{args.frame_h} -> scale {args.scale}x)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
