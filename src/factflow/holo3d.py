"""Small 3D toolkit for holographic motifs: isometric prisms, floor grids and column charts.

Everything is drawn with Pillow polygons and lines (pure code). The camera sways slowly so figures
read as solid objects.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .visual_motifs import CX, CYAN, WHITE, YELLOW, _c, _label


def view(t: float, sway: float = 0.28, base: float = 0.55) -> float:
    return base + sway * math.sin(t * 0.55)


def pt(x: float, y: float, z: float, ang: float, cx: float = CX, cy: float = 930) -> tuple[float, float]:
    """x right, y up, z depth. Returns screen coordinates."""
    return cx + x * math.cos(ang) - z * math.sin(ang), cy - y + (x * math.sin(ang) + z * math.cos(ang)) * 0.38


def floor_grid(draw: Any, ang: float, half: float = 280, step: float = 70, color: Any = CYAN, cy: float = 930) -> None:
    n = int(half // step)
    for i in range(-n, n + 1):
        a, b = pt(i * step, 0, -half, ang, cy=cy), pt(i * step, 0, half, ang, cy=cy)
        draw.line((*a, *b), fill=_c(color, 60), width=1)
        a, b = pt(-half, 0, i * step, ang, cy=cy), pt(half, 0, i * step, ang, cy=cy)
        draw.line((*a, *b), fill=_c(color, 60), width=1)


def box(draw: Any, x: float, z: float, w: float, d: float, h: float, ang: float, color: Any, alpha: int = 215,
        y0: float = 0.0, cy: float = 930, wire: bool = True) -> None:
    """Shaded cuboid standing on the floor (or at height y0)."""
    if h <= 0.5:
        h = 0.5
    c = [(x - w / 2, z - d / 2), (x + w / 2, z - d / 2), (x + w / 2, z + d / 2), (x - w / 2, z + d / 2)]
    low = [pt(px, y0, pz, ang, cy=cy) for px, pz in c]
    high = [pt(px, y0 + h, pz, ang, cy=cy) for px, pz in c]
    sides = []
    for i in range(4):
        j = (i + 1) % 4
        quad = [low[i], low[j], high[j], high[i]]
        sides.append((sum(p[1] for p in quad), quad, i))
    for depth, quad, i in sorted(sides, key=lambda s: s[0]):
        shade = 0.55 + 0.18 * (i % 2)
        draw.polygon(quad, fill=_c(tuple(int(ch * shade) for ch in color[:3]), alpha))
    draw.polygon(high, fill=_c(tuple(min(255, int(ch * 1.15 + 20)) for ch in color[:3]), alpha))
    if wire:
        for quad in [high] + [s[1] for s in sides]:
            draw.line(quad + [quad[0]], fill=_c(WHITE, 90), width=1)


def columns(items: list[tuple[str, float, Any, str]], ref: float = 100.0, height: float = 300.0, rise: float = 1.5,
            highlight: Callable[[float], int] | None = None) -> Callable[..., None]:
    """Motif factory: labelled 3D columns that rise with progress. items = (label, value, colour, value text)."""
    def motif(draw: Any, p: float, t: float, fonts: dict[str, Any], color: Any) -> None:
        ang = view(t)
        n = len(items)
        span = 620.0
        step = span / max(1, n)
        width = min(70.0, step * 0.55)
        floor_grid(draw, ang)
        order = sorted(range(n), key=lambda i: pt(-span / 2 + step * (i + 0.5), 0, 0, ang)[1])
        for i in order:
            label, value, col, text = items[i]
            x = -span / 2 + step * (i + 0.5)
            grow = min(1.0, max(0.0, p * rise - 0.12 * i))
            h = height * value / ref * grow
            hot = highlight(p) if highlight else -1
            box(draw, x, 0, width, width, h, ang, col, 245 if hot == i else 215)
            sx, sy = pt(x, h + 22, 0, ang)
            if text:
                _label(draw, (sx, sy), text, fonts, YELLOW, "mm")
            lx, ly = pt(x, -8, 0, ang)
            ly += 36
            for k, line in enumerate(_wrap_label(label)):
                _label(draw, (lx, ly + 22 + k * 22), line, fonts, WHITE, "mm")
    return motif


def _wrap_label(text: str, limit: int = 9) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > limit:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines or [text]
