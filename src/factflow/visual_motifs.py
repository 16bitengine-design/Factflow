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
