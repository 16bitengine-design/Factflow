"""Holographic 3D versions of the Earth, Sun and body motifs.

Pure-code wireframe and shaded solids with depth cues; each function keeps the name and the
claims of the 2D motif it replaces, so existing topic specs keep working.
"""

from __future__ import annotations

import math
from typing import Any

from .visual_motifs import (BLUE, CX, CY, CYAN, GREY, ORANGE, RED, WATER, WHITE, YELLOW, _c, _dot, _glow,
                            _globe3d, _label, _orbit3d, _proj, _dipole3d)


def _solid(draw: Any, cx: float, cy: float, r: float, color: Any, alpha: int = 235) -> None:
    """Shaded sphere: stacked discs shifted toward a light at the upper left, plus a highlight."""
    for i in range(14):
        f = 1 - i / 14
        draw.ellipse((cx - r * f - i * 0.18 * r / 14 * 4, cy - r * f - i * 0.18 * r / 14 * 4,
                      cx + r * f - i * 0.18 * r / 14 * 4, cy + r * f - i * 0.18 * r / 14 * 4),
                     fill=_c(tuple(min(255, int(ch * (0.35 + 0.65 * (i / 14)))) for ch in color[:3]), alpha))
    draw.ellipse((cx - r * 0.45, cy - r * 0.55, cx - r * 0.15, cy - r * 0.3), fill=(255, 255, 255, 70))


def _ellipse_poly(draw: Any, cx: float, cy: float, a: float, b: float, ang: float, fill: Any) -> None:
    pts = []
    for i in range(48):
        u = math.tau * i / 48
        x, y = a * math.cos(u), b * math.sin(u)
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    draw.polygon(pts, fill=fill)


def tidal_pull(draw, p, t, fonts, color):
    yaw = t * 0.25
    R = 95
    cy = CY + 30
    angle = math.tau * (0.1 + 0.5 * p)
    mx, my = CX + 250 * math.cos(angle), cy - 60 * math.sin(angle)
    tilt = math.atan2(my - cy, mx - CX)
    _ellipse_poly(draw, CX, cy, R + 34, R - 4, tilt, _c(WATER, 110))  # ocean drawn out toward and away from the Moon
    _globe3d(draw, CX, cy, R, yaw, 0.4)
    _solid(draw, mx, my, 34, GREY)
    _arrow3 = (CX + (R + 40) * math.cos(tilt), cy + (R + 40) * math.sin(tilt))
    draw.line((_arrow3[0], _arrow3[1], mx - 44 * math.cos(tilt), my - 44 * math.sin(tilt)), fill=_c(YELLOW, 220), width=4)
    _glow(draw, 70, 470, 46, _c(YELLOW, 230))
    draw.line((120, 470, CX - R - 50, cy - 30), fill=_c(YELLOW, 70), width=3)
    _label(draw, (CX, 880), "the Moon's and Sun's pull raises the ocean", fonts, WHITE, "mm")


def tide_alignment(draw, p, t, fonts, color):
    k = min(1.0, p * 1.6)
    cy = CY + 20
    _glow(draw, 80, cy, 52, _c(YELLOW, 235))
    ang = (1 - k) * 1.1
    mx, my = 610, cy - 150 * math.sin(ang) * (1 - k) - 0
    mx = CX + 250 * math.cos(ang)
    my = cy - 250 * math.sin(ang)
    _ellipse_poly(draw, CX, cy, 74 + 52 * k, 74, 0, _c(WATER, 120))
    _globe3d(draw, CX, cy, 74, t * 0.3, 0.4)
    _solid(draw, mx, my, 28, GREY)
    draw.line((130, cy, 640, cy), fill=_c(WHITE, 50 + int(120 * k)), width=2)
    _label(draw, (CX, 860), "Sun, Moon and Earth in a line", fonts, WHITE, "mm")


def magnetosphere(draw, p, t, fonts, color):
    cx = CX + 60
    _globe3d(draw, cx, CY, 62, t * 0.4, 0.35)
    _dipole3d(draw, cx, CY, 62, t * 0.4, 0.35)
    rx, ry = 210, 250
    for k in range(3):
        draw.arc((cx - rx - k * 10, CY - ry - k * 10, cx + rx + k * 10, CY + ry + k * 10), 90, 270, fill=_c(CYAN, 180 - 50 * k), width=3)
    for k in range(9):
        yo = (k - 4) * 52
        s = (t * 0.45 + k * 0.11) % 1.0
        hit = cx - rx * math.sqrt(max(0.0, 1 - (yo / ry) ** 2))
        x0 = 30
        if s < 0.5:
            x = x0 + (hit - x0) * (s / 0.5)
            y = CY + yo
        else:
            th0 = math.asin(max(-1, min(1, yo / ry)))
            th = th0 + (math.pi / 2 * (1 if yo >= 0 else -1) - th0) * ((s - 0.5) / 0.5)
            x = cx - rx * math.cos(th) * 1.0 - 0
            x = cx - rx * math.cos(th) + (s - 0.5) * 2 * 200
            y = CY + ry * math.sin(th)
        _dot(draw, x, y, 5, _c(YELLOW, 230))
    _label(draw, (120, CY - 20), "solar wind", fonts, YELLOW, "mm")


def geodynamo(draw, p, t, fonts, color):
    _globe3d(draw, CX, CY, 200, t * 0.3, 0.45, color=BLUE)
    _solid(draw, CX, CY, 96, ORANGE, 220)
    for loop in range(5):
        for i in range(40):
            u = math.tau * i / 40 + t * 1.4 + loop
            r = 130 + 16 * math.sin(u * 2 + loop)
            x, y, z = r * math.cos(u) / 200 * 0.9, 0.35 * math.sin(loop + 1) * math.cos(u * 3), r * math.sin(u) / 200 * 0.9
            sx, sy, dz = _proj((x, y, z), CX, CY, 200, t * 0.3, 0.45)
            _dot(draw, sx, sy, 5 if dz > 0 else 3, _c(YELLOW, 240 if dz > 0 else 90))
    _label(draw, (CX, 930), "the geodynamo makes the field", fonts, WHITE, "mm")


def pole_flip(draw, p, t, fonts, color):
    s = min(1.0, max(0.0, (p - 0.35) / 0.4))
    s = s * s * (3 - 2 * s)
    rot = math.pi * s
    cy = CY + 10
    c, sn = math.cos(rot), math.sin(rot)

    def at(x, y):
        return CX + x * c - y * sn, cy + x * sn + y * c

    for sign, col in ((-1, RED), (1, BLUE)):
        pts = [at(-38, sign * 6), at(38, sign * 6), at(38, sign * 190), at(-38, sign * 190)]
        draw.polygon(pts, fill=_c(col, 215))
        draw.line(pts + [pts[0]], fill=_c(WHITE, 170), width=2)
    for L in (1.6, 2.2):
        for side in (-1, 1):
            pts = []
            for i in range(-70, 71):
                lat = math.radians(i * 1.2)
                rr = L * math.cos(lat) ** 2
                pts.append(at(side * 40 + side * 140 * (rr * math.cos(lat) - 1) * 0.9, 190 * math.sin(lat) * 1.0))
            draw.line(pts, fill=_c(CYAN, 140), width=2)
    nx, ny = at(0, -225)
    sx, sy = at(0, 225)
    _label(draw, (nx, ny), "N", fonts, WHITE, "mm")
    _label(draw, (sx, sy), "S", fonts, WHITE, "mm")


def ozone_shield(draw, p, t, fonts, color):
    cx, cy, R = CX, 960, 250
    _globe3d(draw, cx, cy, R, t * 0.15, 0.9, color=CYAN)
    for k, (rad, col, w) in enumerate(((1.16, (150, 90, 255), 8), (1.24, (150, 90, 255), 4))):
        draw.ellipse((cx - R * rad, cy - R * rad, cx + R * rad, cy + R * rad), outline=_c(col, 190 - 60 * k), width=w)
    shell = R * 1.16
    for k in range(9):
        x = 150 + k * 52
        top = 400
        dy = math.sqrt(max(0.0, shell ** 2 - (x - cx) ** 2))
        hit = cy - dy
        y = top + ((t * 170 + k * 70) % (hit - top + 120))
        draw.line((x, top, x, min(y, hit)), fill=_c(YELLOW, 220), width=4)
        if y > hit:
            draw.line((x, hit, x, min(y, hit + 60)), fill=_c(YELLOW, 40), width=3)
    _label(draw, (CX, 1065), "a sunscreen for the planet", fonts, WHITE, "mm")


def hurricane_spin(draw, p, t, fonts, color):
    cy = CY + 40
    tilt = 0.95
    draw.ellipse((CX - 300, cy - 110, CX + 300, cy + 110), fill=_c(WATER, 90))
    for layer in range(4):
        h = layer * 0.08
        for arm in range(4):
            pts = []
            for i in range(60):
                r = (0.12 + i * 0.016) * 280
                a = -t * 1.2 + arm * math.pi / 2 - i * 0.1
                x, y, z = r * math.cos(a), h * 130 + (i * 0.4), r * math.sin(a)
                pts.append((CX + x, cy - y * 0.0 - (h * 150) + z * math.sin(tilt) * 0.38))
            draw.line(pts, fill=_c(WHITE, 90 + layer * 35), width=7 - layer)
    _glow(draw, CX, cy - 60, 20, _c(CYAN, 110))
    _label(draw, (CX, cy - 60), "EYE", fonts, WHITE, "mm")
    _label(draw, (CX, 930), "south of it: clockwise · calm, clear eye", fonts, WHITE, "mm")


def flare_burst(draw, p, t, fonts, color):
    yaw = t * 0.3
    cx, cy, R = CX, CY + 60, 130
    _solid(draw, cx, cy, R, YELLOW)
    _globe3d(draw, cx, cy, R, yaw, 0.3, color=ORANGE)
    for k in range(3):
        base = yaw * 0.0 + k * 2.1 + 0.4
        pts = []
        for i in range(21):
            u = i / 20
            th = base + (u - 0.5) * 0.9
            h = 1.0 + 0.55 * math.sin(math.pi * u) * (1 + 0.4 * math.sin(t * 2 + k))
            sx, sy, dz = _proj((h * math.cos(th), 0.2 * math.sin(k + u * 3), h * math.sin(th)), cx, cy, R, yaw, 0.3)
            pts.append((sx, sy))
        draw.line(pts, fill=_c(RED, 230), width=6)
    if p > 0.5:
        e = (p - 0.5) * 2
        for k in range(36):
            a = k * 0.62
            rr = R * (1.1 + 1.5 * e * (0.6 + 0.4 * math.sin(k * 1.7)))
            _dot(draw, cx + rr * math.cos(a), cy - rr * math.sin(a) * 0.9, 4, _c(WHITE, int(230 * (1 - e * 0.5))))


def aurora_twin(draw, p, t, fonts, color):
    yaw = t * 0.35
    R = 125
    cy = CY + 10
    _globe3d(draw, CX, cy, R, yaw, 0.3)
    for sign, name in ((1, "N"), (-1, "S")):
        lat = math.radians(68)
        for layer in range(4):
            pts = []
            for i in range(73):
                u = math.tau * i / 72
                wave = 0.07 * math.sin(u * 5 + t * 2.2 + (0 if sign == 1 else 0.6))
                rr = 1.02 + layer * 0.05 + wave
                pts.append(_proj((rr * math.cos(lat) * math.cos(u), sign * rr * math.sin(lat), rr * math.cos(lat) * math.sin(u)), CX, cy, R, yaw, 0.3))
            for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:]):
                draw.line((x0, y0, x1, y1), fill=_c((90, 255, 150), (200 if z0 > 0 else 40) - layer * 30), width=3)
        _label(draw, (CX, cy - sign * (R + 70)), name, fonts, WHITE, "mm")


def heart_pump(draw, p, t, fonts, color):
    yaw = t * 0.7
    beat = 1.0 + 0.1 * max(0.0, math.sin(t * 6.0)) ** 2
    cx, cy, S = CX, CY + 20, 11.5
    pts2 = []
    for i in range(61):
        u = math.tau * i / 60
        x = 16 * math.sin(u) ** 3
        y = 13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)
        pts2.append((x / 17, y / 17))
    _glow(draw, cx, cy, 120, _c(RED, 60))
    for zi in range(-5, 6):
        z = zi / 5
        sc = math.sqrt(max(0.0, 1 - z * z)) * beat
        ring = [_proj((x * sc, y * sc, z * 0.55 * beat), cx, cy, S * 22, yaw, 0.15) for x, y in pts2]
        for (x0, y0, z0), (x1, y1, z1) in zip(ring, ring[1:]):
            near = (z0 + z1) / 2 > 0
            draw.line((x0, y0, x1, y1), fill=_c(RED, 235 if near else 70), width=3 if near else 1)
    for k in range(10):
        a = (t * 0.5 + k / 10) % 1.0
        ang = math.tau * a
        _dot(draw, cx + 235 * math.cos(ang), cy + 10 + 200 * math.sin(ang), 7, _c(ORANGE, 230))
    draw.ellipse((cx - 245, cy - 190, cx + 245, cy + 210), outline=_c(RED, 90), width=3)
    _label(draw, (CX, cy + 260), "valves keep blood flowing one way", fonts, WHITE, "mm")


MOTIFS_3D = {fn.__name__: fn for fn in (tidal_pull, tide_alignment, magnetosphere, geodynamo, pole_flip, ozone_shield,
                                          hurricane_spin, flare_burst, aurora_twin, heart_pump)}
