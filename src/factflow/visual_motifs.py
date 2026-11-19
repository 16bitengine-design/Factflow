"""Reusable procedural science animations ("motifs") for authored topics.

Each motif draws one concept so that what appears on screen matches what the
narration says (for example water vapour rising, or red light fading with depth).
A scene selects a motif by name in its ``motif`` field. Unknown or missing names
fall back to the generic holographic core. Motifs draw into the centre area of
the frame (about y 380-940) and are driven only by scene progress ``p`` (0-1)
and elapsed seconds ``t``, so renders are reproducible.
"""
from __future__ import annotations

import math
from typing import Any, Callable

CX, CY = 360, 660
WHITE = (232, 246, 255, 235)
CYAN = (73, 226, 255, 230)
BLUE = (65, 155, 255, 230)
WATER = (40, 120, 215, 150)
ORANGE = (255, 160, 60, 230)
YELLOW = (255, 225, 90, 230)
RED = (255, 85, 85, 230)
GREEN = (90, 220, 130, 230)
GREY = (150, 175, 200, 200)


def _c(color: tuple, alpha: int) -> tuple:
    return (*color[:3], alpha)


def _label(draw: Any, xy: tuple[int, int], text: str, fonts: dict[str, Any], color: tuple = WHITE, anchor: str = "la") -> None:
    draw.text(xy, text, font=fonts["label"], fill=color, anchor=anchor, stroke_width=1, stroke_fill=(3, 20, 42, 210))


def _dot(draw: Any, x: float, y: float, r: float, color: tuple) -> None:
    draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def _glow(draw: Any, x: float, y: float, r: float, color: tuple) -> None:
    for extra, alpha in ((r * 1.9, 28), (r * 1.4, 55), (r * 1.1, 95)):
        draw.ellipse((x - extra, y - extra, x + extra, y + extra), fill=_c(color, alpha))
    _dot(draw, x, y, r, color)


def _arrow(draw: Any, x0: float, y0: float, x1: float, y1: float, color: tuple, width: int = 4) -> None:
    draw.line((x0, y0, x1, y1), fill=color, width=width)
    angle = math.atan2(y1 - y0, x1 - x0)
    for side in (-0.5, 0.5):
        draw.line((x1, y1, x1 - 16 * math.cos(angle + side), y1 - 16 * math.sin(angle + side)), fill=color, width=width)


def _gauge(draw: Any, x: int, y0: int, y1: int, level: float, color: tuple) -> None:
    draw.rounded_rectangle((x - 14, y0, x + 14, y1), radius=14, outline=GREY, width=3)
    top = y1 - (y1 - y0 - 8) * max(0.02, min(1.0, level))
    draw.rounded_rectangle((x - 9, top, x + 9, y1 - 5), radius=9, fill=color)


def _sun(draw: Any, x: int, y: int, r: int = 46) -> None:
    _glow(draw, x, y, r, YELLOW)


def _star_field_waves(draw: Any, y: int, amp: float, t: float, color: tuple, x0: int = 90, x1: int = 630) -> None:
    pts = [(x, y + amp * math.sin(x * 0.045 + t * 3)) for x in range(x0, x1, 12)]
    draw.line(pts, fill=color, width=3)


# --------------------------------------------------------------- clouds

def evaporation(draw, p, t, fonts, color):
    _sun(draw, 580, 430)
    draw.rectangle((90, 800, 630, 930), fill=WATER)
    _star_field_waves(draw, 800, 6, t, _c(CYAN, 200), 90, 630)
    for i in range(26):
        phase = (t * 0.35 + i * 0.137) % 1.0
        x = 120 + (i * 53) % 480 + 14 * math.sin(phase * 9 + i)
        y = 790 - phase * 360
        _dot(draw, x, y, 5 + 3 * phase, _c(WHITE, int(200 * (1 - phase * 0.6))))
    _label(draw, (CX, 880), "WATER", fonts, WHITE, "mm")
    _label(draw, (CX, 440), "INVISIBLE WATER VAPOUR RISES", fonts, CYAN, "mm")


def rising_cooling(draw, p, t, fonts, color):
    y = 880 - 400 * p
    r = 34 + 56 * p
    _glow(draw, 300, y, r, _c(BLUE, 200))
    _arrow(draw, 300, 900, 300, 470, _c(WHITE, 160), 3)
    _gauge(draw, 560, 420, 920, 1.0 - 0.85 * p, _c(ORANGE if p < 0.5 else CYAN, 230))
    _label(draw, (560, 395), f"{int(25 - 40 * p)}°C", fonts, WHITE, "mm")
    _label(draw, (300, 935), "AIR RISES, EXPANDS, COOLS", fonts, CYAN, "mm")


def condensation(draw, p, t, fonts, color):
    nuclei = [(250, 640), (360, 700), (470, 630), (310, 780), (430, 790)]
    for i, (x, y) in enumerate(nuclei):
        _dot(draw, x, y, 7, GREY)
        for k in range(9):
            a = k * 0.7 + i
            start = (x + 190 * math.cos(a), y + 190 * math.sin(a))
            pos = (start[0] + (x - start[0]) * min(1, p * 1.3), start[1] + (y - start[1]) * min(1, p * 1.3))
            _dot(draw, pos[0], pos[1], 4, _c(WHITE, 190))
        radius = 14 + 46 * p
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=_c(CYAN, int(60 + 150 * p)), width=3,
                     fill=_c(WHITE, int(20 + 70 * p)))
    _label(draw, (CX, 480), "VAPOUR GATHERS ON TINY PARTICLES", fonts, CYAN, "mm")
    _label(draw, (CX, 900), "dust · sea salt · smoke", fonts, GREY, "mm")


# --------------------------------------------------------------- Moon

def moon_phases(draw, p, t, fonts, color):
    _sun(draw, 110, CY, 40)
    for k in range(5):
        draw.line((170, CY - 80 + k * 40, 600, CY - 80 + k * 40), fill=_c(YELLOW, 60), width=2)
    _glow(draw, CX, CY, 46, _c(BLUE, 220))
    angle = math.pi * 2 * p
    mx, my = CX + 200 * math.cos(angle + math.pi), CY + 200 * 0.45 * math.sin(angle + math.pi)
    _dot(draw, mx, my, 34, GREY)
    draw.pieslice((mx - 34, my - 34, mx + 34, my + 34), 90, 270, fill=WHITE)
    _label(draw, (CX, 850), "THE SUN ALWAYS LIGHTS HALF THE MOON", fonts, CYAN, "mm")
    _label(draw, (CX, 890), "we see a changing part of that half", fonts, WHITE, "mm")


def eclipse_shadow(draw, p, t, fonts, color):
    _sun(draw, 110, CY, 40)
    _glow(draw, 340, CY, 52, _c(BLUE, 220))
    draw.polygon([(340, CY - 52), (620, CY - 26), (620, CY + 26), (340, CY + 52)], fill=(5, 10, 25, 150))
    mx = 640 - 230 * p
    _dot(draw, mx, CY, 30, GREY if p < 0.5 else (120, 50, 40, 230))
    _label(draw, (CX, 850), "ONLY IN A LUNAR ECLIPSE", fonts, CYAN, "mm")
    _label(draw, (CX, 890), "does Earth's shadow fall on the Moon", fonts, WHITE, "mm")


# --------------------------------------------------------------- ocean

def light_absorption(draw, p, t, fonts, color):
    draw.rectangle((220, 460, 500, 930), fill=_c(WATER, 120))
    colours = [(RED, 560), (ORANGE, 640), (YELLOW, 720), (GREEN, 790), (BLUE, 910)]
    for i, (col, depth) in enumerate(colours):
        x = 255 + i * 52
        reach = min(depth - 460, (depth - 460) * min(1.0, p * 1.6)) + 40
        draw.line((x, 400, x, 460 + reach), fill=col, width=9)
    _label(draw, (CX, 380), "WHITE LIGHT ENTERS WATER", fonts, WHITE, "mm")
    _label(draw, (150, 560), "red fades", fonts, RED, "mm")
    _label(draw, (CX, 950), "blue travels deepest", fonts, BLUE, "mm")


def scattering_compare(draw, p, t, fonts, color):
    draw.line((CX, 400, CX, 930), fill=_c(GREY, 120), width=2)
    _label(draw, (210, 420), "SKY: SCATTERING", fonts, CYAN, "mm")
    _label(draw, (510, 420), "SEA: ABSORPTION", fonts, CYAN, "mm")
    for i in range(14):
        a = (t * 0.6 + i * 0.5) % 6.28
        _dot(draw, 210 + 110 * math.cos(a + i), 640 + 90 * math.sin(a * 1.3 + i), 6, _c(BLUE, 200))
    draw.line((90, 520, 210, 640), fill=WHITE, width=5)
    draw.rectangle((410, 560, 620, 920), fill=_c(WATER, 120))
    draw.line((470, 480, 470, 560 + 260 * p), fill=RED, width=6)
    draw.line((560, 480, 560, 920), fill=BLUE, width=6)
    _label(draw, (CX, 960), "two different effects", fonts, WHITE, "mm")


def sediment_colors(draw, p, t, fonts, color):
    tints = [(40, 120, 215), (40, 170, 160), (80, 170, 80), (150, 120, 70)]
    pos = p * (len(tints) - 1)
    i = min(len(tints) - 2, int(pos))
    f = pos - i
    tint = tuple(int(tints[i][k] * (1 - f) + tints[i + 1][k] * f) for k in range(3))
    draw.rounded_rectangle((220, 500, 500, 900), radius=24, fill=(*tint, 170), outline=_c(CYAN, 180), width=3)
    for n in range(30):
        phase = (t * 0.2 + n * 0.07) % 1.0
        _dot(draw, 240 + (n * 37) % 240, 520 + phase * 360, 3 + n % 3, _c(WHITE, 160))
    _label(draw, (CX, 450), "SEDIMENT · ALGAE · DISSOLVED MATERIAL", fonts, CYAN, "mm")
    _label(draw, (CX, 940), "the colour shifts", fonts, WHITE, "mm")


# --------------------------------------------------------------- lightning

def _bolt(draw, x0, y0, y1, seed, color, width):
    pts = [(x0, y0)]
    y = y0
    k = 0
    while y < y1:
        y += 46
        k += 1
        pts.append((x0 + 46 * math.sin(seed + k * 1.9) + 18 * math.sin(k * 5.1), y))
    draw.line(pts, fill=color, width=width)
    return pts


def lightning_bolt(draw, p, t, fonts, color):
    draw.ellipse((150, 330, 570, 470), fill=_c(GREY, 120))
    flash = 0.5 + 0.5 * math.sin(t * 14)
    _bolt(draw, 360, 440, 900, 1.3, _c(WHITE, int(150 + 100 * flash)), 7)
    _bolt(draw, 360, 440, 900, 1.3, _c(CYAN, 90), 16)
    _label(draw, (CX, 950), "A LIGHTNING CHANNEL", fonts, CYAN, "mm")


def heat_halo(draw, p, t, fonts, color):
    pts = _bolt(draw, 360, 420, 900, 1.3, _c(WHITE, 240), 6)
    for r, a in ((190, 35), (140, 60), (95, 95)):
        draw.ellipse((360 - r, 660 - r * 1.4, 360 + r, 660 + r * 1.4), fill=_c(ORANGE, int(a * (0.6 + 0.4 * p))))
    _gauge(draw, 600, 420, 900, p, _c(RED, 230))
    _label(draw, (600, 395), f"{int(54000 * p):,}°F", fonts, WHITE, "mm")
    _label(draw, (CX, 950), "the AIR around the channel", fonts, ORANGE, "mm")


def pressure_wave(draw, p, t, fonts, color):
    _glow(draw, CX, 560, 20, _c(WHITE, 240))
    for k in range(4):
        r = ((p * 1.4 + k * 0.22) % 1.0) * 260
        draw.ellipse((CX - r, 560 - r, CX + r, 560 + r), outline=_c(CYAN, int(220 * (1 - r / 260))), width=4)
    pts = [(x, 850 + (60 * math.sin((x - 90) * 0.09 - t * 6) * min(1.0, p * 2)) * math.exp(-(x - 90) / 420)) for x in range(90, 630, 6)]
    draw.line(pts, fill=ORANGE, width=3)
    _label(draw, (CX, 930), "THE AIR EXPANDS · WE HEAR THUNDER", fonts, WHITE, "mm")


# --------------------------------------------------------------- stars

def star_beam(draw, p, t, fonts, color):
    _glow(draw, CX, 420, 18, _c(YELLOW, 240))
    draw.line((CX, 440, CX, 760), fill=_c(YELLOW, 150), width=5)
    draw.ellipse((120, 800, 600, 1150), outline=_c(BLUE, 200), width=4)
    _label(draw, (CX, 380), "A DISTANT STAR", fonts, CYAN, "mm")
    _label(draw, (CX, 780), "steady light", fonts, WHITE, "mm")


def star_twinkle(draw, p, t, fonts, color):
    _glow(draw, CX, 420, 18, _c(YELLOW, 240))
    for k, y in enumerate((560, 640, 720)):
        _star_field_waves(draw, y, 9, t + k, _c(CYAN, 140))
    x = CX
    pts = [(x, 440)]
    for y in (560, 640, 720, 820):
        x = CX + 24 * math.sin(t * 7 + y * 0.05)
        pts.append((x, y))
    draw.line(pts, fill=_c(YELLOW, 190), width=4)
    _glow(draw, x, 840 + 6 * math.sin(t * 11), 10 + 3 * math.sin(t * 13), _c(WHITE, 240))
    _label(draw, (CX, 930), "MOVING AIR BENDS THE LIGHT", fonts, CYAN, "mm")


def twinkle_compare(draw, p, t, fonts, color):
    draw.line((CX, 400, CX, 930), fill=_c(GREY, 120), width=2)
    _label(draw, (210, 420), "FROM THE GROUND", fonts, CYAN, "mm")
    _label(draw, (510, 420), "FROM SPACE", fonts, CYAN, "mm")
    _glow(draw, 210 + 10 * math.sin(t * 9), 700 + 8 * math.cos(t * 11), 12 + 4 * math.sin(t * 13), _c(WHITE, 240))
    _glow(draw, 510, 700, 12, _c(WHITE, 240))
    _label(draw, (210, 880), "twinkles", fonts, YELLOW, "mm")
    _label(draw, (510, 880), "steady", fonts, GREEN, "mm")


# --------------------------------------------------------------- Earth

def plates_globe(draw, p, t, fonts, color):
    draw.ellipse((130, 430, 590, 890), fill=_c(BLUE, 70), outline=_c(CYAN, 200), width=3)
    shades = [GREEN, ORANGE, YELLOW, RED, CYAN, WHITE]
    for k in range(6):
        a0 = k * 60 + t * 6
        draw.pieslice((140, 440, 580, 880), a0, a0 + 56, fill=_c(shades[k], 85), outline=_c(WHITE, 200), width=2)
    _label(draw, (CX, 950), "EARTH'S SHELL IS BROKEN INTO PLATES", fonts, CYAN, "mm")


def plates_boundary(draw, p, t, fonts, color):
    shift = 40 * p
    draw.rectangle((90, 620, 340 + shift, 780), fill=_c(ORANGE, 150), outline=WHITE, width=2)
    draw.rectangle((380 - shift, 620, 630, 780), fill=_c(GREEN, 150), outline=WHITE, width=2)
    _arrow(draw, 150, 700, 150 + 70, 700, WHITE)
    _arrow(draw, 570, 700, 570 - 70, 700, WHITE)
    draw.line((120, 860, 600, 860), fill=GREY, width=3)
    for i in range(13):
        draw.line((120 + i * 40, 850, 120 + i * 40, 870), fill=GREY, width=2)
    _label(draw, (CX, 900), "a few centimetres per year", fonts, WHITE, "mm")
    _label(draw, (CX, 470), "SLOW AS A GROWING FINGERNAIL", fonts, CYAN, "mm")


def plates_timelapse(draw, p, t, fonts, color):
    gap = 120 * (1 - p)
    draw.polygon([(90, 800), (90, 700), (320 - gap, 700), (320 - gap, 800)], fill=_c(ORANGE, 150))
    draw.polygon([(630, 800), (630, 700), (400 + gap, 700), (400 + gap, 800)], fill=_c(GREEN, 150))
    peak = 220 * p
    draw.polygon([(250, 700), (360, 700 - peak), (470, 700)], fill=_c(WHITE, int(60 + 140 * p)))
    _label(draw, (CX, 880), f"{int(p * 50)} MILLION YEARS", fonts, YELLOW, "mm")
    _label(draw, (CX, 470), "COLLISION BUILDS MOUNTAINS", fonts, CYAN, "mm")


def globe_bulge(draw, p, t, fonts, color):
    squash = 1.0 - 0.18 * min(1.0, p * 1.5)
    rx, ry = 230, 230 * squash
    draw.ellipse((CX - rx, CY - ry, CX + rx, CY + ry), fill=_c(BLUE, 90), outline=_c(CYAN, 220), width=4)
    for k in range(-2, 3):
        draw.arc((CX - rx, CY - ry * abs(math.cos(t * 0.7 + k * 0.6)), CX + rx, CY + ry * abs(math.cos(t * 0.7 + k * 0.6))), 0, 360, fill=_c(WHITE, 90), width=2)
    draw.line((CX - rx - 20, CY, CX + rx + 20, CY), fill=_c(YELLOW, 170), width=2)
    _label(draw, (CX, 900), "ROTATION MAKES THE EQUATOR BULGE", fonts, CYAN, "mm")


def gravity_surface(draw, p, t, fonts, color):
    pts = []
    for k in range(120):
        a = k / 120 * math.tau
        r = 220 + 14 * math.sin(a * 5 + t) + 9 * math.sin(a * 9 - t * 1.4)
        pts.append((CX + r * math.cos(a), CY + r * 0.92 * math.sin(a)))
    draw.polygon(pts, fill=_c(BLUE, 60), outline=_c(CYAN, 230))
    _label(draw, (CX, 900), "MOUNTAINS · TRENCHES · GRAVITY", fonts, CYAN, "mm")
    _label(draw, (CX, 935), "the real shape is irregular", fonts, WHITE, "mm")


# --------------------------------------------------------------- leaves

def leaf_pigments(draw, p, t, fonts, color):
    draw.ellipse((150, 480, 570, 880), fill=_c(GREEN, int(190 - 120 * p)), outline=_c(WHITE, 200), width=3)
    draw.line((150, 680, 570, 680), fill=_c(WHITE, 140), width=3)
    for k, (col, name) in enumerate(((GREEN, "green"), (YELLOW, "yellow"), (ORANGE, "orange"), (RED, "red"))):
        level = (1 - p) if k == 0 else (0.35 + 0.65 * p if k < 3 else p * 0.8)
        draw.rectangle((110 + k * 130, 960 - 70 * level, 190 + k * 130, 960), fill=col)
        _label(draw, (150 + k * 130, 985), name, fonts, WHITE, "mm")
    _label(draw, (CX, 440), "HIDDEN PIGMENTS BEHIND THE GREEN", fonts, CYAN, "mm")


def daylight_fade(draw, p, t, fonts, color):
    _sun(draw, 360, 560 + 100 * p, int(52 - 14 * p))
    draw.arc((120, 420, 600, 900), 200, 340, fill=_c(YELLOW, 150), width=3)
    draw.rectangle((140, 900, 580, 940), outline=GREY, width=3)
    draw.rectangle((144, 904, 144 + 432 * (1 - p), 936), fill=_c(GREEN, 220))
    _label(draw, (CX, 880), "SHORTER DAYS · LESS CHLOROPHYLL", fonts, CYAN, "mm")


# --------------------------------------------------------------- Mercury

def _orbit(draw, angle, planet_color):
    _sun(draw, CX, CY, 36)
    draw.ellipse((CX - 210, CY - 210, CX + 210, CY + 210), outline=_c(GREY, 110), width=2)
    _glow(draw, CX + 210 * math.cos(angle), CY + 210 * math.sin(angle), 15, planet_color)


def orbit_year(draw, p, t, fonts, color):
    _orbit(draw, p * math.tau - math.pi / 2, _c(ORANGE, 240))
    _label(draw, (CX, 440), f"DAY {int(88 * p)} OF 88", fonts, YELLOW, "mm")
    _label(draw, (CX, 940), "one Mercury year", fonts, WHITE, "mm")


def orbit_rotation(draw, p, t, fonts, color):
    _orbit(draw, p * 2 * math.tau - math.pi / 2, _c(ORANGE, 240))
    days = 176 * p
    _label(draw, (CX, 420), f"DAY {int(days)} · SPINS {days / 59:.1f} · ORBITS {days / 88:.1f}", fonts, CYAN, "mm")
    _label(draw, (CX, 455), "ONE SUNRISE-TO-SUNRISE = 176 DAYS", fonts, YELLOW, "mm")
    _label(draw, (CX, 940), "one solar day ≈ two Mercury years", fonts, WHITE, "mm")


# --------------------------------------------------------------- geyser

def geyser_eruption(draw, p, t, fonts, color):
    draw.polygon([(230, 900), (490, 900), (420, 830), (300, 830)], fill=_c(GREY, 150))
    height = 400 * math.sin(min(1.0, p * 1.2) * math.pi) ** 0.7
    for k in range(70):
        a = (k * 0.137 + t * 1.3) % 1.0
        reach = 0.45 + 0.55 * ((k * 37) % 10) / 10
        x = CX + (k % 9 - 4) * (5 + 16 * a)
        y = 830 - height * a * reach
        _dot(draw, x, y, 5 + 4 * (1 - a), _c(WHITE, int(230 * (1 - a * 0.55))))
    _label(draw, (CX, 430), f"NEXT ERUPTION IN ABOUT {60 + int(50 * p)} MIN", fonts, YELLOW, "mm")
    _label(draw, (CX, 950), "predictable, but not a clock", fonts, WHITE, "mm")


def interval_timeline(draw, p, t, fonts, color):
    draw.line((110, 700, 610, 700), fill=_c(GREY, 200), width=4)
    for i, (x, h, name) in enumerate(((140, 60, "short"), (330, 60, "long"), (560, 60, "next"))):
        _glow(draw, x, 700, 12, _c(CYAN, 230))
    _arrow(draw, 150, 640, 130 + 190 * min(1, p * 2), 640, YELLOW)
    _arrow(draw, 340, 640, 340 + 210 * max(0.0, min(1, p * 2 - 0.6)), 640, ORANGE)
    _label(draw, (235, 600), "shorter wait", fonts, YELLOW, "mm")
    _label(draw, (445, 600), "longer wait", fonts, ORANGE, "mm")
    _label(draw, (CX, 470), "THE LAST ERUPTION HELPS PREDICT THE NEXT", fonts, CYAN, "mm")


def geyser_cutaway(draw, p, t, fonts, color):
    draw.rectangle((190, 450, 530, 920), fill=_c(GREY, 60), outline=_c(WHITE, 160), width=2)
    draw.polygon([(340, 470), (380, 470), (390, 700), (430, 760), (430, 880), (290, 880), (290, 760), (330, 700)], fill=_c(WATER, 170))
    for k in range(14):
        a = (t * 0.5 + k * 0.17) % 1.0
        _dot(draw, 330 + (k % 5) * 18, 870 - a * 380 * (0.4 + 0.6 * p), 5, _c(WHITE, 190))
    draw.ellipse((300, 850, 420, 905), fill=_c(RED, int(80 + 120 * p)))
    _label(draw, (CX, 420), "HEATED WATER AND STEAM UNDERGROUND", fonts, CYAN, "mm")


def tidal_pull(draw, p, t, fonts, color):
    r = 70
    draw.ellipse((CX - r - 38, CY - r, CX + r + 38, CY + r), fill=_c(WATER, 120))  # ocean bulged toward and away from the Moon
    _glow(draw, CX, CY, r - 14, _c(GREEN, 170))
    angle = math.pi * 2 * p * 0.5
    mx, my = CX + 250 * math.cos(angle), CY + 250 * 0.35 * math.sin(angle) - 40
    _dot(draw, mx, my, 28, GREY)
    _arrow(draw, CX + 80 * math.cos(angle), CY + 80 * 0.35 * math.sin(angle), mx - 40 * math.cos(angle), my + 10, YELLOW)
    _sun(draw, 80, 450, 34)
    _label(draw, (CX, 850), "THE MOON'S AND SUN'S PULL", fonts, CYAN, "mm")
    _label(draw, (CX, 890), "raises the ocean on Earth", fonts, WHITE, "mm")


def tide_alignment(draw, p, t, fonts, color):
    _sun(draw, 90, CY, 40)
    _glow(draw, CX, CY, 46, _c(BLUE, 220))
    k = 0.4 + 0.6 * min(1.0, p * 1.6)
    draw.ellipse((CX - 60 - 40 * k, CY - 60, CX + 60 + 40 * k, CY + 60), fill=_c(WATER, 120))
    _dot(draw, 600, CY - 100 * (1 - min(1.0, p * 1.6)), 26, GREY)
    draw.line((120, CY, 580, CY), fill=_c(WHITE, 60), width=2)
    _label(draw, (CX, 850), "FULL OR NEW MOON: SPRING TIDES", fonts, CYAN, "mm")
    _label(draw, (CX, 890), "Sun, Moon and Earth in a line", fonts, WHITE, "mm")


def tide_gauge(draw, p, t, fonts, color):
    days = 2 * p
    level = 0.5 + 0.5 * math.sin(2 * math.pi * 2 * days)  # about two high tides per day
    draw.line((140, 780, 600, 780), fill=GREY, width=3)
    pts = [(140 + 460 * (i / 80), 600 - 90 * math.sin(2 * math.pi * 2 * (2 * i / 80))) for i in range(81)]
    draw.line(pts, fill=_c(CYAN, 120), width=3)
    x = 140 + 460 * (days / 2)
    y = 600 - 90 * math.sin(2 * math.pi * 2 * days)
    _glow(draw, x, y, 12, YELLOW)
    _gauge(draw, 90, 480, 720, level, BLUE)
    _label(draw, (CX + 20, 830), f"HIGH TIDES SO FAR: {int(2 * days * 1.0 + 0.25)}", fonts, YELLOW, "mm")
    _label(draw, (CX + 20, 870), "tidal range = high minus low", fonts, WHITE, "mm")


def seafloor_quake(draw, p, t, fonts, color):
    draw.rectangle((100, 820, 620, 940), fill=(90, 70, 55, 230))
    shift = 14 * math.sin(t * 40) * max(0.0, 1 - p) if p < 0.5 else 0
    draw.polygon([(100, 820), (360 + shift, 820), (360 + shift, 940), (100, 940)], fill=(120, 95, 70, 235))
    draw.rectangle((100, 600, 620, 820), fill=_c(WATER, 110))
    for k in range(4):
        rr = 30 + 90 * ((p * 2 + k * 0.25) % 1.0)
        draw.arc((360 - rr, 820 - rr, 360 + rr, 820 + rr), 200, 340, fill=_c(YELLOW, int(220 * (1 - rr / 120))), width=4)
    lift = 34 * min(1.0, p * 2)
    draw.arc((160, 590 - lift, 560, 630 + lift), 190, 350, fill=WHITE, width=5)
    _label(draw, (CX, 430), "UNDERSEA EARTHQUAKE OR ERUPTION", fonts, CYAN, "mm")
    _label(draw, (CX, 470), "sets off a giant wave", fonts, WHITE, "mm")


def tsunami_deep(draw, p, t, fonts, color):
    draw.rectangle((80, 700, 640, 900), fill=_c(WATER, 90))
    pts = [(80 + 560 * i / 120, 700 - 18 * math.sin((i / 120) * 2 * math.pi * 1.4 - p * 16)) for i in range(121)]
    draw.line(pts, fill=WHITE, width=5)
    _glow(draw, 80 + 560 * ((p * 3) % 1.0), 640, 12, YELLOW)
    _label(draw, (CX, 470), "OUT AT SEA: LOW, FAST WAVES", fonts, YELLOW, "mm")
    _label(draw, (CX, 510), "they do not grow dramatically in height", fonts, WHITE, "mm")


def tsunami_shore(draw, p, t, fonts, color):
    draw.polygon([(80, 900), (640, 700 - 0), (640, 900)], fill=(120, 95, 70, 235))
    draw.polygon([(80, 760), (640, 700), (640, 900), (80, 900)], fill=_c(WATER, 70))
    x = 120 + 420 * p
    height = 18 + 90 * p
    width = 140 - 70 * p
    pts = [(x - width + 2 * width * i / 40, (760 - 60 * (x - 80) / 560) - height * math.exp(-(((i - 20) / 9) ** 2))) for i in range(41)]
    draw.line(pts, fill=WHITE, width=5)
    _label(draw, (CX, 470), "NEAR SHORE: A VERY FAST TIDE", fonts, CYAN, "mm")
    _label(draw, (CX, 510), "reaching farther inland than usual", fonts, WHITE, "mm")


def salt_sources(draw, p, t, fonts, color):
    draw.polygon([(60, 760), (60, 560), (260, 640), (330, 760)], fill=(110, 95, 75, 235))  # land
    draw.rectangle((60, 760, 660, 920), fill=_c(WATER, 120))
    for k in range(6):
        y = 470 + ((t * 120 + k * 45) % 150)
        draw.line((110 + k * 26, y, 104 + k * 26, y + 16), fill=_c(CYAN, 200), width=3)  # rain on the rocks
    draw.line((250, 640, 330, 760), fill=_c(BLUE, 220), width=5)  # river to the sea
    for k in range(4):
        draw.line((470 + k * 40, 920, 470 + k * 40, 870 - 20 * math.sin(t * 3 + k)), fill=_c(ORANGE, 200), width=5)  # seafloor vents
    for k in range(int(70 * p)):
        _dot(draw, 340 + (k * 53) % 300, 780 + (k * 37) % 120, 4, _c(WHITE, 220))
    _label(draw, (CX, 420), "SALT ARRIVES FROM TWO SOURCES", fonts, CYAN, "mm")
    _label(draw, (180, 520), "rocks + rivers", fonts, WHITE, "mm")
    _label(draw, (545, 840), "seafloor vents", fonts, ORANGE, "mm")


def salt_share(draw, p, t, fonts, color):
    draw.rectangle((80, 560, 640, 640), outline=GREY, width=3)
    width = 560 * 0.035 * min(1.0, p * 1.5)
    draw.rectangle((80, 560, 80 + max(4, width), 640), fill=WHITE)
    _label(draw, (CX, 520), "ABOUT 3.5% OF SEAWATER'S WEIGHT IS SALT", fonts, CYAN, "mm")
    draw.rectangle((80, 740, 640, 800), outline=GREY, width=3)
    draw.rectangle((80, 740, 80 + 560 * 0.85 * min(1.0, p * 1.5), 800), fill=_c(YELLOW, 200))
    _label(draw, (CX, 700), "SODIUM + CHLORIDE: ABOUT 85% OF DISSOLVED IONS", fonts, YELLOW, "mm")


def dense_float(draw, p, t, fonts, color):
    draw.rectangle((60, 700, 660, 940), fill=_c(WATER, 140))
    bob = 6 * math.sin(t * 2)
    draw.rounded_rectangle((250, 665 + bob, 470, 705 + bob), radius=18, fill=_c(ORANGE, 230))
    _dot(draw, 480, 668 + bob, 22, _c(ORANGE, 230))
    for k in range(40):
        _dot(draw, 80 + (k * 71) % 560, 720 + (k * 43) % 200, 3, _c(WHITE, 150))
    _label(draw, (CX, 520), "THE EXTREMELY SALTY DEAD SEA", fonts, CYAN, "mm")
    _label(draw, (CX, 560), "dense water holds you up like a mattress", fonts, WHITE, "mm")


def enso_winds(draw, p, t, fonts, color):
    draw.rectangle((60, 700, 660, 880), fill=_c(WATER, 110))
    shift = max(0.0, min(1.0, (p - 0.45) * 2.2))
    bx = 190 + 340 * shift
    for extra, alpha in ((120, 60), (85, 110), (55, 170)):
        draw.ellipse((bx - extra, 760 - extra * 0.5, bx + extra, 760 + extra * 0.5), fill=_c(ORANGE, alpha))
    strength = 1 - shift
    for k in range(4):
        x = 150 + k * 130
        if shift < 0.5:
            _arrow(draw, x + 90, 620, x, 620, _c(WHITE, 230), 3 + int(2 * strength))
        else:
            _arrow(draw, x, 620, x + 40, 620, _c(WHITE, 110), 2)
    _label(draw, (110, 930), "INDONESIA", fonts, WHITE, "mm")
    _label(draw, (610, 930), "S. AMERICA", fonts, WHITE, "mm")
    _label(draw, (CX, 470), "NORMAL: WINDS PUSH WARM WATER WEST" if shift < 0.5 else "EL NIÑO: WINDS WEAKEN", fonts, CYAN, "mm")
    if shift >= 0.5:
        _label(draw, (CX, 510), "warm water piles up near South America", fonts, WHITE, "mm")


def jet_stream_shift(draw, p, t, fonts, color):
    y0 = 560 + 150 * min(1.0, p * 1.4)
    pts = [(60 + 600 * i / 80, y0 + 28 * math.sin(i / 7 + t * 2)) for i in range(81)]
    draw.line(pts, fill=_c(CYAN, 230), width=6)
    draw.ellipse((330, 820, 650, 900), fill=_c(ORANGE, 150))
    for k in range(5):
        _dot(draw, 440 + k * 38, 780 - 8 * (k % 2), 26, _c(GREY, 210))
    for k in range(6):
        y = 790 + ((t * 110 + k * 40) % 90)
        draw.line((430 + k * 36, y, 426 + k * 36, y + 14), fill=_c(BLUE, 210), width=3)
    _label(draw, (CX, 450), "WARMER WATER: JET STREAM SHIFTS SOUTH", fonts, CYAN, "mm")
    _label(draw, (CX, 490), "much more rain in some places, drought in others", fonts, WHITE, "mm")


def upwelling(draw, p, t, fonts, color):
    draw.rectangle((100, 560, 620, 920), fill=_c(WATER, 110))
    strength = 1 - min(1.0, p * 1.3)
    for k in range(5):
        x = 170 + k * 95
        rise = 200 * strength
        if rise > 6:
            _arrow(draw, x, 900, x, 900 - rise, _c(CYAN, int(60 + 170 * strength)), 4)
    for k in range(int(12 * strength)):
        _dot(draw, 130 + (k * 83) % 460, 640 + (k * 47) % 180, 4, _c(GREEN, 220))
    _label(draw, (CX, 500), "COLD, NUTRIENT-RICH WATER RISES", fonts, CYAN, "mm")
    _label(draw, (CX, 960), "in El Niño, upwelling weakens or stops", fonts, WHITE, "mm")


def hurricane_engine(draw, p, t, fonts, color):
    draw.rectangle((60, 800, 660, 940), fill=_c(WATER, 140))
    for k in range(10):
        a = (t * 0.5 + k / 10) % 1.0
        x = 150 + 420 * ((k * 0.37) % 1.0)
        y = 800 - 240 * a
        _arrow(draw, x, y + 40, x, y, _c(RED, 210), 3)
    for k in range(int(6 * p) + 1):
        _dot(draw, 200 + k * 60, 575 - 12 * (k % 2), 40, _c(WHITE, 190))
    _label(draw, (CX, 430), "WARM, MOIST AIR IS THE FUEL", fonts, CYAN, "mm")
    _label(draw, (CX, 470), "rising air cools and forms clouds", fonts, WHITE, "mm")


def hurricane_spin(draw, p, t, fonts, color):
    for arm in range(4):
        pts = []
        for i in range(60):
            r = 30 + i * 4.2
            a = -t * 1.2 + arm * math.pi / 2 - i * 0.09
            pts.append((CX + r * math.cos(a), CY + r * 0.9 * math.sin(a)))
        draw.line(pts, fill=_c(WHITE, 200), width=9)
    _glow(draw, CX, CY, 24, _c(CYAN, 120))
    _label(draw, (CX, CY), "EYE", fonts, WHITE, "mm")
    _label(draw, (CX, 450), "NORTH OF THE EQUATOR: COUNTERCLOCKWISE", fonts, CYAN, "mm")
    _label(draw, (CX, 930), "south of it: clockwise · calm, clear eye", fonts, WHITE, "mm")


def hurricane_landfall(draw, p, t, fonts, color):
    draw.rectangle((60, 760, 380, 920), fill=_c(WATER, 140))
    draw.rectangle((380, 760, 660, 920), fill=(110, 95, 75, 235))
    x = 150 + 400 * p
    size = 120 if x < 380 else max(30, 120 - (x - 380) * 0.6)
    alpha = 220 if x < 380 else int(max(60, 220 - (x - 380) * 0.8))
    for arm in range(3):
        pts = [(x + (size * i / 40) * math.cos(-t * 1.5 + arm * 2.1 - i * 0.18), 640 + (size * i / 40) * 0.8 * math.sin(-t * 1.5 + arm * 2.1 - i * 0.18)) for i in range(40)]
        draw.line(pts, fill=_c(WHITE, alpha), width=7)
    _gauge(draw, 90, 450, 700, 0.9 if x < 380 else max(0.1, 0.9 - (x - 380) / 300), RED)
    _label(draw, (CX + 30, 450), "74 MPH WINDS = HURRICANE", fonts, CYAN, "mm")
    _label(draw, (CX + 30, 500), "over land it loses its ocean fuel", fonts, WHITE, "mm")


def sleep_vitals(draw, p, t, fonts, color):
    for row, (name, col, base) in enumerate((("HEART RATE", RED, 560), ("BLOOD PRESSURE", ORANGE, 760))):
        pts = [(100 + 520 * i / 60, base - 60 + 50 * min(1.0, i / 60 * 1.4) + 8 * math.sin(i / 3 + t * 3 + row)) for i in range(int(61 * min(1.0, p * 1.3 + 0.05)))]
        if len(pts) > 1:
            draw.line(pts, fill=_c(col, 230), width=5)
        _label(draw, (110, base - 90), name, fonts, col, "la")
    _label(draw, (CX, 450), "IN NON-REM SLEEP BOTH FALL", fonts, CYAN, "mm")


def sleep_memory(draw, p, t, fonts, color):
    nodes = [(CX + 190 * math.cos(k * 0.9), CY + 150 * math.sin(k * 1.3)) for k in range(12)]
    lit = int(12 * min(1.0, p * 1.3))
    for i in range(lit):
        for j in range(i):
            if (i + j) % 3 == 0:
                draw.line((*nodes[i], *nodes[j]), fill=_c(CYAN, 110), width=2)
    for i, (x, y) in enumerate(nodes):
        _glow(draw, x, y, 10, YELLOW if i < lit else _c(GREY, 120))
    _label(draw, (CX, 450), "SLEEP HELPS FORM LONG-TERM MEMORIES", fonts, CYAN, "mm")
    _label(draw, (CX, 930), "and supports learning", fonts, WHITE, "mm")


def sleep_ages(draw, p, t, fonts, color):
    draw.line((100, 820, 620, 820), fill=GREY, width=3)
    for k in range(7):
        h = 260 - 22 * k
        draw.rectangle((130 + k * 70, 820 - h, 170 + k * 70, 820), fill=_c(BLUE, 120))
    i = min(6, int(p * 7))
    h = 260 - 22 * i
    draw.rectangle((130 + i * 70, 820 - h, 170 + i * 70, 820), fill=_c(YELLOW, 230))
    _label(draw, (CX, 860), "AGE  →", fonts, WHITE, "mm")
    _label(draw, (CX, 450), "THE HOURS YOU NEED CHANGE AS YOU AGE", fonts, CYAN, "mm")


MOTIFS: dict[str, Callable[..., None]] = {
    name: fn for name, fn in {
        "evaporation": evaporation, "rising_cooling": rising_cooling, "condensation": condensation,
        "moon_phases": moon_phases, "eclipse_shadow": eclipse_shadow,
        "light_absorption": light_absorption, "scattering_compare": scattering_compare, "sediment_colors": sediment_colors,
        "lightning_bolt": lightning_bolt, "heat_halo": heat_halo, "pressure_wave": pressure_wave,
        "star_beam": star_beam, "star_twinkle": star_twinkle, "twinkle_compare": twinkle_compare,
        "plates_globe": plates_globe, "plates_boundary": plates_boundary, "plates_timelapse": plates_timelapse,
        "globe_bulge": globe_bulge, "gravity_surface": gravity_surface,
        "leaf_pigments": leaf_pigments, "daylight_fade": daylight_fade,
        "orbit_year": orbit_year, "orbit_rotation": orbit_rotation,
        "tidal_pull": tidal_pull, "tide_alignment": tide_alignment, "tide_gauge": tide_gauge,
        "seafloor_quake": seafloor_quake, "tsunami_deep": tsunami_deep, "tsunami_shore": tsunami_shore,
        
        "salt_sources": salt_sources, "salt_share": salt_share, "dense_float": dense_float, "enso_winds": enso_winds, "jet_stream_shift": jet_stream_shift, "upwelling": upwelling, "hurricane_engine": hurricane_engine, "hurricane_spin": hurricane_spin, "hurricane_landfall": hurricane_landfall, "sleep_vitals": sleep_vitals, "sleep_memory": sleep_memory, "sleep_ages": sleep_ages,
        "geyser_eruption": geyser_eruption, "interval_timeline": interval_timeline, "geyser_cutaway": geyser_cutaway,
    }.items()
}


def draw_motif(name: str | None, draw: Any, progress: float, seconds: float, fonts: dict[str, Any], color: tuple = CYAN) -> bool:
    """Draw a named motif; return False when the name is unknown (caller falls back)."""
    fn = MOTIFS.get(str(name or ""))
    if fn is None:
        return False
    fn(draw, max(0.0, min(1.0, progress)), seconds, fonts, color)
    return True
