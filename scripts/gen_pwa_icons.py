"""One-shot generator for PWA + Apple home-screen icons.

Produces a small set of brand-consistent icons: a charcoal rounded
square with the gold ◆ diamond from the header. Run once and the
PNGs land in frontend/public/.

Usage:
  cd backend && .venv/bin/python ../scripts/gen_pwa_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


# Brand tokens
BG_DARK = (11, 11, 15, 255)      # #0b0b0f — site `void`
DIAMOND = (201, 169, 110, 255)   # #c9a96e — site `gold`

# Icons to produce (size, filename, padding factor 0..1)
TARGETS = [
    (180, "apple-touch-icon.png", 0.18),     # iOS home-screen
    (192, "icon-192.png",         0.18),     # Android / manifest
    (512, "icon-512.png",         0.18),     # Hi-res / splash
    (192, "icon-192-maskable.png", 0.28),    # Adaptive: bigger safe-zone padding
    (512, "icon-512-maskable.png", 0.28),
]

OUT = Path(__file__).resolve().parents[1] / "frontend" / "public"


def rounded_square(size: int, radius: int, fill) -> Image.Image:
    """RGBA image of a rounded square the size of the canvas."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=fill)
    return img


def draw_diamond(canvas: Image.Image, padding_factor: float, fill) -> None:
    """Centered diamond. `padding_factor` is the share of the canvas
    reserved as empty around the glyph (per side). 0.18 ≈ standard;
    0.28 ≈ maskable safe zone."""
    size = canvas.size[0]
    cx = cy = size / 2
    half = (size / 2) * (1 - padding_factor)
    points = [
        (cx, cy - half),
        (cx + half, cy),
        (cx, cy + half),
        (cx - half, cy),
    ]
    ImageDraw.Draw(canvas).polygon(points, fill=fill)


def make(size: int, filename: str, padding_factor: float, maskable: bool) -> None:
    radius = int(size * (0.22 if not maskable else 0))  # maskable = full bleed
    img = rounded_square(size, radius, BG_DARK if not maskable else BG_DARK)
    if maskable:
        # Maskable wants a solid background covering the canvas — the OS
        # masks corners itself, so the rounded corners we draw would be
        # cropped.
        img = Image.new("RGBA", (size, size), BG_DARK)
    draw_diamond(img, padding_factor, DIAMOND)
    out = OUT / filename
    img.save(out, "PNG", optimize=True)
    print(f"  wrote {out.relative_to(OUT.parent.parent)}  ({size}×{size})")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Writing icons under {OUT}")
    for size, filename, pad in TARGETS:
        make(size, filename, pad, maskable="maskable" in filename)


if __name__ == "__main__":
    main()
