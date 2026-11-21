"""Holographic 3D motifs, batch C: black holes, how vaccines work, ultraviolet light and the eye.

Every figure is drawn with Pillow primitives only (pure code) and turns slowly so it reads as a solid.
"""

from __future__ import annotations

import math
from typing import Any

from .holo3d import box, columns, floor_grid, pt, view
from .visual_motifs import (BLUE, CX, CY, CYAN, GREEN, GREY, ORANGE, RED, WHITE, YELLOW, _c, _dot, _glow, _globe3d,
                            _label, _proj)
from .visual_motifs_3d import _ellipse_poly, _solid

VIOLET = (190, 120, 255, 230)
SKIN = (235, 170, 120, 235)
DARK = (4, 8, 18, 250)


def _p(x: float, y: float, z: float, yaw: float, tilt: float, cx: float = CX, cy: float = CY, scale: float = 200.0):
    """Point in pixel-sized coordinates (x right, y up, z towards the viewer) to screen (x, y, depth)."""
    return _proj((x / scale, y / scale, z / scale), cx, cy, scale, yaw, tilt)


def _smooth(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- black holes

def black_hole_3d(draw, p, t, fonts, color):
    yaw, tilt = 0.25 * math.sin(t * 0.4), 0.42
    cx, cy = CX, CY
    disk = []
    for i in range(150):
        r = 105 + 150 * ((i * 0.6180339) % 1.0)
        a = math.tau * ((i * 0.381966) % 1.0) + t * (2.4 * (105 / r) ** 1.5)
        x, z = r * math.cos(a), r * math.sin(a)
        sx, sy, d = _p(x, 0, z, yaw, tilt, cx, cy)
        heat = 1 - (r - 105) / 150
        disk.append((d, sx, sy, heat, 2.2 + 2.4 * heat))
    disk.sort()
    for d, sx, sy, heat, size in disk:
        if d <= 0:
            _dot(draw, sx, sy, size, _c((255, int(150 + 90 * heat), int(60 + 120 * heat)), 150 + int(90 * heat)))
    _glow(draw, cx, cy, 64, _c(ORANGE, 90))
    draw.ellipse((cx - 62, cy - 62, cx + 62, cy + 62), fill=DARK, outline=_c(WHITE, 220), width=3)
    draw.arc((cx - 78, cy - 78, cx + 78, cy + 78), 200, 340, fill=_c(YELLOW, 200), width=4)
    for d, sx, sy, heat, size in disk:
        if d > 0:
            _dot(draw, sx, sy, size, _c((255, int(150 + 90 * heat), int(60 + 120 * heat)), 190 + int(60 * heat)))
    for k, off in enumerate((-190, -125, -70)):
        y0 = cy + off - 120
        pts = []
        for i in range(41):
            x = -330 + 660 * i / 40
            pull = math.exp(-((x / 120.0) ** 2))
            y = cy + off + (-off) * (0.55 if off < -100 else 0.85) * pull
            pts.append((cx + x, y))
        end = len(pts) if k < 2 else 23
        draw.line(pts[:end], fill=_c(YELLOW, 140), width=2)
        s = (t * 0.55 + k * 0.3) % 1.0
        i = min(end - 1, int(s * end))
        _dot(draw, pts[i][0], pts[i][1], 6, _c(WHITE, 240))
    _label(draw, (cx, cy + 150), "event horizon: not even light escapes", fonts, WHITE, "mm")


def star_collapse_3d(draw, p, t, fonts, color):
    cx, cy = CX, CY
    yaw = t * 0.3
    k = _smooth((p - 0.3) / 0.35)
    if k < 1.0:
        r = 140 - 105 * k
        shell = 1.0 + 1.3 * k
        _globe3d(draw, cx, cy, 120 * shell, yaw, 0.4, color=_c(ORANGE, 180))
        _solid(draw, cx, cy, r, ORANGE if k < 0.5 else RED, int(235 * (1 - 0.3 * k)))
    for i in range(60):
        a = math.tau * ((i * 0.618) % 1.0)
        z = math.asin(2 * ((i * 0.377) % 1.0) - 1)
        d = 60 + 280 * _smooth((p - 0.45) / 0.5) * (0.5 + 0.5 * ((i * 0.31) % 1.0))
        if p > 0.45:
            sx, sy, dep = _p(d * math.cos(a) * math.cos(z), d * math.sin(z), d * math.sin(a) * math.cos(z), yaw, 0.4, cx, cy)
            _dot(draw, sx, sy, 3, _c(YELLOW, int(230 * (1 - _smooth((p - 0.7) / 0.3) * 0.6))))
    if k > 0.6:
        c = _smooth((k - 0.6) / 0.4)
        draw.ellipse((cx - 44 * c, cy - 44 * c, cx + 44 * c, cy + 44 * c), fill=DARK, outline=_c(CYAN, 230), width=3)
        _ellipse_poly(draw, cx, cy, 90 * c, 20 * c, 0.2, _c(ORANGE, 120))
    stage = "massive star runs out of fuel" if p < 0.35 else ("core collapses, outer layers explode" if p < 0.7 else "a black hole remains")
    _label(draw, (cx, cy + 250), stage, fonts, WHITE, "mm")


def galaxy_core_3d(draw, p, t, fonts, color):
    yaw, tilt = t * 0.22, 0.95
    cx, cy = CX, CY
    for ring in (80, 150, 230, 310):
        pts = [_p(ring * math.cos(u), 0, ring * math.sin(u), yaw, tilt, cx, cy) for u in [math.tau * i / 60 for i in range(61)]]
        for a, b in zip(pts, pts[1:]):
            draw.line((a[0], a[1], b[0], b[1]), fill=_c(CYAN, 55), width=1)
    stars = []
    for i in range(70):
        r = 70 + 250 * ((i * 0.618034) % 1.0) ** 0.8
        a = math.tau * ((i * 0.381966) % 1.0) + t * 1.8 * (80 / r) ** 1.5
        sx, sy, d = _p(r * math.cos(a), 28 * math.sin(i), r * math.sin(a), yaw, tilt, cx, cy)
        stars.append((d, sx, sy, r))
    stars.sort()
    for d, sx, sy, r in stars:
        _dot(draw, sx, sy, 3.5 if d > 0 else 2.2, _c(YELLOW if r < 150 else WHITE, 230 if d > 0 else 110))
    _glow(draw, cx, cy, 30, _c(ORANGE, 110))
    draw.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=DARK, outline=_c(WHITE, 230), width=2)
    _label(draw, (cx, cy + 290), "stars orbit the central black hole", fonts, WHITE, "mm")


# ---------------------------------------------------------------- vaccines

def _fib(n: int):
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        a = i * 2.399963
        yield r * math.cos(a), y, r * math.sin(a)


def _antibody(draw, x, y, size, color):
    draw.line((x, y + size, x, y), fill=color, width=4)
    draw.line((x, y, x - size * 0.8, y - size * 0.8), fill=color, width=4)
    draw.line((x, y, x + size * 0.8, y - size * 0.8), fill=color, width=4)


def antibody_train_3d(draw, p, t, fonts, color):
    yaw, tilt = t * 0.5, 0.4
    vx, vy = CX - 130, CY + 90
    spikes = list(_fib(26))
    pts = []
    for ux, uy, uz in spikes:
        base = _p(ux * 70, uy * 70, uz * 70, yaw, tilt, vx, vy)
        tip = _p(ux * 104, uy * 104, uz * 104, yaw, tilt, vx, vy)
        pts.append((base, tip))
    sx_c, sy_c = CX + 150, CY - 170
    _solid(draw, sx_c, sy_c, 62, BLUE)
    draw.ellipse((sx_c - 22, sy_c - 22, sx_c + 22, sy_c + 22), outline=_c(WHITE, 150), width=2)
    for base, tip in sorted(pts, key=lambda b: b[1][2]):
        if tip[2] <= 0:
            draw.line((base[0], base[1], tip[0], tip[1]), fill=_c(RED, 90), width=2)
    _solid(draw, vx, vy, 66, RED, 200)
    for base, tip in sorted(pts, key=lambda b: b[1][2]):
        if tip[2] > 0:
            draw.line((base[0], base[1], tip[0], tip[1]), fill=_c(RED, 230), width=3)
            _dot(draw, tip[0], tip[1], 5, _c(YELLOW, 235))
    near = [tip for _, tip in pts if tip[2] > 0.15]
    for i, tip in enumerate(near[:10]):
        s = _smooth(p * 1.5 - i * 0.08 - 0.2)
        if s <= 0:
            continue
        x = sx_c + (tip[0] - sx_c) * s
        y = sy_c + (tip[1] - sy_c) * s + 40 * math.sin(math.pi * s) * (1 if i % 2 else -1)
        _antibody(draw, x, y, 12, _c(GREEN, 240))
    _label(draw, (sx_c, sy_c - 86), "immune cell", fonts, BLUE, "mm")
    _label(draw, (vx, vy + 132), "weakened germ", fonts, RED, "mm")
    _label(draw, (CX, 930), "the body learns to make antibodies", fonts, WHITE, "mm")


def immune_memory_3d(draw, p, t, fonts, color):
    ang = view(t)
    floor_grid(draw, ang, half=300, step=75)
    stages = (("READY", 22), ("MULTIPLY", 215), ("ATTACK", 300), ("DWINDLE", 120), ("KEEP WATCH", 36))
    n = len(stages)
    for i, (name, h) in enumerate(stages):
        x = -250 + i * 125
        grow = _smooth(p * 1.25 - i * 0.16)
        hh = 14 + (h - 14) * grow
        col = GREEN if i == n - 1 else (ORANGE if i in (1, 2) else BLUE)
        box(draw, x, 0, 64, 64, hh, ang, col, 225)
        sx, sy = pt(x, hh + 16, 0, ang)
        if grow > 0.2:
            for j in range(3 if i == n - 1 else max(1, int(hh / 60))):
                _dot(draw, sx + (j - 1) * 14, sy - j * 0 - 8, 5, _c(WHITE, 220))
        lx, ly = pt(x, -8, 0, ang)
        _label(draw, (lx, ly + 52), name if i != n - 1 else "KEEP", fonts, WHITE, "mm")
        if i == n - 1:
            _label(draw, (lx, ly + 78), "WATCH", fonts, WHITE, "mm")
    sx, sy = pt(0, 380, 0, ang)
    _label(draw, (sx, sy), "white cells multiply, then a few keep watch", fonts, YELLOW, "mm")


def herd_shield_3d(draw, p, t, fonts, color):
    ang = view(t)
    floor_grid(draw, ang, half=300, step=75)
    cols, rows = 6, 4
    unprotected = {(2, 1), (4, 2), (1, 3)}
    people = [(c, r) for r in range(rows) for c in range(cols)]
    others = [pr for pr in people if pr not in unprotected]
    order = {pr: i for i, pr in enumerate(sorted(others, key=lambda q: (q[0] * 7 + q[1] * 3) % 11))}
    shown = p * len(others) * 1.15
    items = []
    for c, r in people:
        x, z = -250 + c * 100, -150 + r * 100
        items.append((pt(x, 0, z, ang)[1], c, r, x, z))
    for _, c, r, x, z in sorted(items):
        vacc = (c, r) not in unprotected and order[(c, r)] < shown
        weak = (c, r) in unprotected
        col = YELLOW if weak else (BLUE if vacc else GREY)
        box(draw, x, z, 26, 26, 46, ang, col, 230)
        sx, sy = pt(x, 46 + 16, z, ang)
        _solid(draw, sx, sy, 14, col, 235)
        if weak:
            _glow(draw, sx, sy - 40, 5, _c(YELLOW, 230))
    for i in range(7):
        s = (t * 0.25 + i * 0.37) % 1.0
        r = i % rows
        x = -330 + 660 * s
        hit = [c for c in range(cols) if (c, r) not in unprotected and order[(c, r)] < shown and -250 + c * 100 > x - 6]
        if hit and -250 + hit[0] * 100 - x < 20:
            continue
        sx, sy = pt(x, 40, -150 + r * 100, ang)
        _dot(draw, sx, sy, 6, _c(RED, 235))
    sx, sy = pt(0, 300, 0, ang)
    _label(draw, (sx, sy), "protected people shield the rest", fonts, WHITE, "mm")


# ---------------------------------------------------------------- ultraviolet light

def uv_filter_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.2, base=0.35)
    floor_grid(draw, ang, half=280, step=70)
    box(draw, 0, 0, 520, 240, 14, ang, GREEN, 200)
    box(draw, 0, 0, 520, 240, 70, ang, BLUE, 55, y0=300, wire=True)
    bands = ((-190, VIOLET, 0.0, "UVC"), (0, ORANGE, 0.82, "UVB"), (190, YELLOW, 1.0, "UVA"))
    for x, col, thru, name in bands:
        a = pt(x - 60, 620, -40, ang)
        for k in range(3):
            z = -60 + 60 * k
            top = (x - 60 + 0.0 * k, 520, z)
            stop_y = 300 + 70 if thru == 0 else (150 if thru < 1 else 14)
            low = (x + 0, stop_y, z)
            ya, yb = pt(*top, ang), pt(*low, ang)
            draw.line((*ya, *yb), fill=_c(col, 110), width=2)
            s = (t * 0.45 + k * 0.31 + x / 900) % 1.0
            y_at = top[1] + (low[1] - top[1]) * s
            xp = top[0] + (low[0] - top[0]) * s
            sx, sy = pt(xp, y_at, z, ang)
            _dot(draw, sx, sy, 6, _c(col, 240))
            if thru == 0:
                _glow(draw, *pt(x, 370, z, ang), 5, _c(col, 200))
        sx, sy = pt(x, 540, 0, ang)
        _label(draw, (sx, sy - 20), name, fonts, col, "mm")
    sx, sy = pt(0, 500, 0, ang)
    _label(draw, (CX, 1010), "UVC blocked · UVB absorbed · UVA passes", fonts, WHITE, "mm")
    _label(draw, (CX, 970), "the atmosphere filters sunlight", fonts, CYAN, "mm")


def uv_path_3d(draw, p, t, fonts, color):
    gx, gy, R = CX, CY + 520, 360
    _globe3d(draw, gx, gy, R, t * 0.15, 0.1, color=GREEN)
    draw.arc((gx - R - 56, gy - R - 56, gx + R + 56, gy + R + 56), 215, 325, fill=_c(CYAN, 190), width=3)
    draw.arc((gx - R - 28, gy - R - 28, gx + R + 28, gy + R + 28), 215, 325, fill=_c(CYAN, 100), width=2)
    elev = math.radians(22 + 68 * math.sin(math.pi * p))
    dirx, diry = -math.cos(elev), -math.sin(elev)
    px, py = gx, gy - R
    for off in (-34, 0, 34):
        ex, ey = px + off, py
        sx, sy = ex - dirx * 520, ey - diry * 520
        draw.line((sx, sy, ex, ey), fill=_c(YELLOW, 70 + int(150 * math.sin(elev))), width=3 if off == 0 else 2)
        sh = 56 / max(0.25, math.sin(elev))
        ix, iy = ex - dirx * sh, ey - diry * sh
        draw.line((ix, iy, ex, ey), fill=_c(ORANGE, 150), width=5)
    _glow(draw, px - dirx * 520, py - diry * 520, 30, _c(YELLOW, 235))
    draw.line((px, py, px, py - 36), fill=WHITE, width=4)
    _dot(draw, px, py - 46, 9, WHITE)
    _label(draw, (CX, 880), "high sun: short path, strongest UV", fonts, WHITE, "mm")
    _label(draw, (CX, 920), "low sun: long path, more UV absorbed", fonts, CYAN, "mm")


def sun_protection_3d(draw, p, t, fonts, color):
    yaw, tilt = 0.35 * math.sin(t * 0.5), 0.2
    cx, cy = CX, CY + 60
    k = min(1.0, p * 1.4)
    _globe3d(draw, cx, cy - 10, 215, yaw, tilt, color=_c(CYAN, int(255 * (0.25 + 0.75 * k))))
    box(draw, 0, 0, 56, 36, 120, view(t), BLUE, 235, y0=0, cy=cy + 160)
    hx, hy = _p(0, 140, 0, yaw, tilt, cx, cy + 160)[:2]
    _solid(draw, hx, hy, 26, SKIN)
    if k > 0.3:
        _ellipse_poly(draw, hx, hy - 18, 54, 14, 0, _c(ORANGE, 230))
    if k > 0.55:
        draw.line((hx - 20, hy - 2, hx + 20, hy - 2), fill=DARK, width=7)
    for i in range(9):
        s = (t * 0.5 + i * 0.113) % 1.0
        x0, y0 = cx - 330 + 40 * (i % 3), cy - 330
        x1, y1 = cx - 130 + 38 * i / 3 * 0.2, cy - 130 + 12 * (i % 3)
        _dot(draw, x0 + (x1 - x0) * s, y0 + (y1 - y0) * s, 5, _c(YELLOW, 230))
        if s > 0.92:
            _glow(draw, x1, y1, 7, _c(YELLOW, 220))
    chips = ("SHADE", "CLOTHES", "HAT", "SUNGLASSES", "SUNSCREEN SPF 15+")
    for i, name in enumerate(chips):
        on = p * len(chips) * 1.1 > i
        y = 760 + 34 * i
        _dot(draw, 150, y, 8, _c(GREEN if on else GREY, 240 if on else 120))
        _label(draw, (176, y), name, fonts, WHITE if on else GREY, "lm")


# ---------------------------------------------------------------- the eye

def eye_path_3d(draw, p, t, fonts, color):
    yaw, tilt = -0.55 + 0.25 * math.sin(t * 0.45), 0.25
    cx, cy, R = CX - 40, CY, 150
    _globe3d(draw, cx, cy, R, yaw, tilt, color=_c(WHITE, 190))
    ring = [_p(-95, 70 * math.cos(u), 70 * math.sin(u), yaw, tilt, cx, cy) for u in [math.tau * i / 40 for i in range(41)]]
    draw.polygon([(a[0], a[1]) for a in ring], fill=_c(CYAN, 90), outline=_c(CYAN, 230))
    back = [_p(138 * math.cos(a), 138 * math.sin(a) * 0.9, 0, yaw, tilt, cx, cy) for a in [math.radians(d) for d in range(-40, 41, 5)]]
    draw.line([(b[0], b[1]) for b in back], fill=_c(ORANGE, 230), width=6)
    focus = _p(124, 0, 0, yaw, tilt, cx, cy)
    nerve = [_p(150 + 160 * i / 10, -8, 0, yaw, tilt, cx, cy) for i in range(11)]
    draw.line([(n[0], n[1]) for n in nerve], fill=_c(ORANGE, 220), width=8)
    brain = _p(350, -8, 0, yaw, tilt, cx, cy)
    _solid(draw, brain[0], brain[1], 46, BLUE)
    for off in (-52, -26, 0, 26, 52):
        a = _p(-330, off * 1.1, 0, yaw, tilt, cx, cy)
        l = _p(-95, off * 0.9, 0, yaw, tilt, cx, cy)
        draw.line((a[0], a[1], l[0], l[1]), fill=_c(YELLOW, 150), width=2)
        draw.line((l[0], l[1], focus[0], focus[1]), fill=_c(YELLOW, 150), width=2)
        s = (t * 0.4 + off / 300) % 1.0
        if s < 0.5:
            x, y = a[0] + (l[0] - a[0]) * s * 2, a[1] + (l[1] - a[1]) * s * 2
        else:
            x, y = l[0] + (focus[0] - l[0]) * (s - 0.5) * 2, l[1] + (focus[1] - l[1]) * (s - 0.5) * 2
        _dot(draw, x, y, 5, _c(WHITE, 240))
    sig = (t * 0.5) % 1.0
    ni = min(9, int(sig * 10))
    _dot(draw, nerve[ni][0], nerve[ni][1], 7, _c(GREEN, 240))
    _label(draw, (CX, cy + 185), "cornea + lens focus light", fonts, YELLOW, "mm")
    _label(draw, (cx + 20, cy - 190), "retina → optic nerve → brain", fonts, ORANGE, "mm")


vision_counts = columns([
    ("IMPAIRED VISION", 100, ORANGE, "AT LEAST 2.2 BILLION"),
    ("PREVENTABLE OR UNMET", 45.5, YELLOW, "AT LEAST 1 BILLION")], rise=1.3)


def lens_focus_3d(draw, p, t, fonts, color):
    ang = view(t, sway=0.22, base=0.9)
    floor_grid(draw, ang, half=300, step=75)
    fixed = _smooth((p - 0.45) / 0.3)
    lens_x = -20
    for k in range(10):
        a = math.tau * k / 10
        y, z = 90 + 100 * 0 + 70 * math.sin(a) + 0, 70 * math.cos(a)
        start = pt(-300, y, z, ang)
        mid = pt(lens_x, y, z, ang)
        focus_x = 150 + (1 - fixed) * -85 + fixed * 85 - fixed * 0
        focus_x = 230 - 90 * (1 - fixed)
        end = pt(focus_x, 90, 0, ang)
        draw.line((*start, *mid), fill=_c(YELLOW, 140), width=2)
        draw.line((*mid, *end), fill=_c(YELLOW, 140), width=2)
        s = (t * 0.45 + k * 0.1) % 1.0
        if s < 0.5:
            x, y2 = start[0] + (mid[0] - start[0]) * s * 2, start[1] + (mid[1] - start[1]) * s * 2
        else:
            x, y2 = mid[0] + (end[0] - mid[0]) * (s - 0.5) * 2, mid[1] + (end[1] - mid[1]) * (s - 0.5) * 2
        _dot(draw, x, y2, 4, _c(WHITE, 235))
    ring = [pt(lens_x, 90 + 90 * math.sin(u), 90 * math.cos(u), ang) for u in [math.tau * i / 36 for i in range(37)]]
    draw.polygon(ring, fill=_c(CYAN, 70), outline=_c(CYAN, 235))
    if fixed > 0.05:
        g = [pt(-120, 90 + 90 * math.sin(u), 90 * math.cos(u), ang) for u in [math.tau * i / 36 for i in range(37)]]
        draw.line(g + [g[0]], fill=_c(GREEN, int(230 * fixed)), width=4)
    box(draw, 250, 0, 14, 260, 200, ang, ORANGE, 110, y0=0)
    spot = 6 + 70 * (1 - fixed)
    sx, sy = pt(240, 90, 0, ang)
    _ellipse_poly(draw, sx, sy, spot * 0.55, spot, 0, _c(YELLOW if fixed < 0.9 else GREEN, 210))
    _label(draw, (CX, 930), "glasses refocus light on the retina" if fixed > 0.5 else "light focuses short of the retina",
           fonts, GREEN if fixed > 0.5 else RED, "mm")


MOTIFS_3D_C = {name: fn for name, fn in (
    ("black_hole_3d", black_hole_3d), ("star_collapse_3d", star_collapse_3d), ("galaxy_core_3d", galaxy_core_3d),
    ("antibody_train_3d", antibody_train_3d), ("immune_memory_3d", immune_memory_3d), ("herd_shield_3d", herd_shield_3d),
    ("uv_filter_3d", uv_filter_3d), ("uv_path_3d", uv_path_3d), ("sun_protection_3d", sun_protection_3d),
    ("eye_path_3d", eye_path_3d), ("vision_counts", vision_counts), ("lens_focus_3d", lens_focus_3d))}
