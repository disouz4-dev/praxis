#!/usr/bin/env python3
"""Builds the app icons (PNG / ICO / ICNS) from the speech-bubble symbol in
assets/praxis.png. Run: python scripts/make_icons.py  (ICNS needs macOS iconutil)."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC = ASSETS / "praxis.png"
BG = (11, 15, 25, 255)          # matches the logo background
CROP = (312, 150, 942, 760)     # bubble + waveform, no wordmark (1254px source)


def build(size: int = 1024) -> Image.Image:
    logo = Image.open(SRC).convert("RGBA").crop(CROP)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # macOS icon grid: ~824px rounded body inside 1024 canvas
    body = int(size * 0.805)
    off = (size - body) // 2
    mask = Image.new("L", (body, body), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, body - 1, body - 1),
                                           radius=int(body * 0.225), fill=255)
    tile = Image.new("RGBA", (body, body), BG)
    sym = int(body * 0.86)
    tile.alpha_composite(logo.resize((sym, sym), Image.LANCZOS),
                         ((body - sym) // 2, (body - sym) // 2 + int(body * 0.02)))
    canvas.paste(tile, (off, off), mask)
    return canvas


def main() -> None:
    icon = build()
    icon.save(ASSETS / "icon.png")
    icon.resize((256, 256), Image.LANCZOS).save(ASSETS / "icon_256.png")
    icon.save(ASSETS / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    if shutil.which("iconutil"):
        with tempfile.TemporaryDirectory() as d:
            iconset = Path(d) / "icon.iconset"
            iconset.mkdir()
            for s in (16, 32, 128, 256, 512):
                icon.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
                icon.resize((s * 2, s * 2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")
            subprocess.run(["iconutil", "-c", "icns", str(iconset),
                            "-o", str(ASSETS / "icon.icns")], check=True)
    print("icons written to", ASSETS, file=sys.stderr)


if __name__ == "__main__":
    main()
