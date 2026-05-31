"""OpenGraph image generator. /api/og/til/<slug>.png returns a 1200×630 PNG
preview card that platforms (X, LinkedIn, Slack) use when someone shares a
TIL link.

Renders the post title, date, and tags on a dark canvas matching the site
aesthetic. Fonts are looked up in a fallback chain so it works on dev (macOS)
and prod (Linux) without bundled assets — and gets prettier if you drop a
Fraunces TTF into `app/fonts/`.
"""

from __future__ import annotations

import io
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.db import get_db
from app.models import TilPost


router = APIRouter(prefix="/og", tags=["og"])

# Aesthetic
W, H = 1200, 630
COLOR_BG = (11, 11, 15)
COLOR_INK_OVERLAY = (22, 23, 31)
COLOR_CREAM = (233, 226, 207)
COLOR_PARCHMENT = (216, 207, 182)
COLOR_MIST = (142, 138, 125)
COLOR_GOLD = (201, 169, 110)
COLOR_EMBER = (234, 88, 12)

# Font fallback search paths. First-match wins.
_FONT_DIR = BASE_DIR / "app" / "fonts"

_DISPLAY_FONT_CANDIDATES = [
    _FONT_DIR / "fraunces.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSerif-Bold.ttf"),
    Path("/Library/Fonts/Georgia.ttf"),
    Path("/System/Library/Fonts/Supplemental/Georgia.ttf"),
    Path("/System/Library/Fonts/SFGeorgian.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
]
_MONO_FONT_CANDIDATES = [
    _FONT_DIR / "jetbrains-mono.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf"),
    Path("/System/Library/Fonts/Menlo.ttc"),
    Path("/Library/Fonts/Menlo.ttc"),
    Path("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"),
]


@lru_cache(maxsize=8)
def _font(kind: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = _DISPLAY_FONT_CANDIDATES if kind == "display" else _MONO_FONT_CANDIDATES
    for p in candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Greedy word-wrap to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    line: list[str] = []
    for word in words:
        trial = " ".join([*line, word])
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            line.append(word)
        else:
            if line:
                lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))
    return lines


def _render(post: TilPost) -> bytes:
    img = Image.new("RGB", (W, H), COLOR_BG)
    d = ImageDraw.Draw(img)

    # Subtle top + bottom edge accent lines
    d.line([(60, 70), (W - 60, 70)], fill=COLOR_GOLD, width=1)
    d.line([(60, H - 70), (W - 60, H - 70)], fill=COLOR_GOLD, width=1)

    # Top-left site mark
    mark = "◆ gokulraam.dev"
    d.text((60, 88), mark, fill=COLOR_GOLD, font=_font("mono", 22))

    # Top-right "№ NNN · TIL" stamp
    numero = f"№ {post.id:03d} · TIL"
    nbbox = d.textbbox((0, 0), numero, font=_font("mono", 22))
    d.text((W - 60 - (nbbox[2] - nbbox[0]), 88), numero, fill=COLOR_MIST, font=_font("mono", 22))

    # Title — wrap to width
    title = post.title
    title_font = _font("display", 76)
    title_lines = _wrap(d, title, title_font, max_width=W - 120)
    # Limit to 3 lines, append ellipsis
    if len(title_lines) > 3:
        title_lines = title_lines[:3]
        title_lines[-1] = title_lines[-1].rstrip() + "…"

    title_y = 200
    line_h = 92
    for i, line in enumerate(title_lines):
        # Slightly different colour on a single italic-look line
        d.text((60, title_y + i * line_h), line, fill=COLOR_CREAM, font=title_font)

    # Bottom row: date · tags
    date_str = post.created_at.strftime("%d %b %Y").lower() if post.created_at else ""
    tags_str = " · ".join(f"#{t}" for t in post.tags.split(",") if t.strip())
    meta_parts = [p for p in (date_str, tags_str) if p]
    meta = "   ·   ".join(meta_parts)
    if meta:
        d.text((60, H - 130), meta, fill=COLOR_MIST, font=_font("mono", 22))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@router.get("/til/{slug}.png")
def og_for_til(slug: str, db: Annotated[Session, Depends(get_db)]) -> Response:
    # strip .png if Astro passes it through (it won't, but defensive)
    if slug.endswith(".png"):
        slug = slug[:-4]
    post = db.scalar(select(TilPost).where(TilPost.slug == slug))
    if not post or post.draft:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")
    png = _render(post)
    return Response(
        content=png,
        media_type="image/png",
        headers={
            # Aggressive cache — share platforms cache OG images forever anyway.
            "Cache-Control": "public, max-age=3600, s-maxage=86400",
        },
    )
