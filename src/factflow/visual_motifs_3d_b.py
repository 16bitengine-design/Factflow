"""3D column and gauge motifs (batch A): shares, comparisons and level gauges drawn as holographic solids."""

from __future__ import annotations

import math

from .holo3d import box, columns, floor_grid, pt, view
from .visual_motifs import BLUE, CYAN, GREEN, GREY, ORANGE, RED, WATER, WHITE, YELLOW, _c, _label

water_share_bars = columns([
    ("ADULT BODY", 60, BLUE, "60%"), ("BONES", 31, BLUE, "31%"), ("BRAIN + HEART", 73, CYAN, "73%"),
    ("LUNGS", 83, CYAN, "83%"), ("BABY AT BIRTH", 78, WATER, "78%")])

glacier_share = columns([
    ("OF THE WORLD'S LAND", 10, CYAN, "ABOUT 10%"), ("OF FRESH WATER", 69, WHITE, "ABOUT 69%")], rise=1.3)

salt_share = columns([
    ("OF SEAWATER'S WEIGHT IS SALT", 3.5, WHITE, "ABOUT 3.5%"), ("OF DISSOLVED IONS ARE SODIUM + CHLORIDE", 85, YELLOW, "ABOUT 85%")], rise=1.3)

_sleep_columns = columns([(f"", 100 - 12 * k, BLUE, "") for k in range(7)], height=300, rise=1.4,
                         highlight=lambda p: min(6, int(p * 7)))


def sleep_ages(draw, p, t, fonts, color):
    _sleep_columns(draw, p, t, fonts, color)
    sx, sy = pt(0, -8, 0, view(t))
    _label(draw, (sx, sy + 40), "AGE  →", fonts, WHITE, "mm")

clock_drift = columns([
    ("QUARTZ WRISTWATCH: ABOUT 15 SECONDS A MONTH", 100, ORANGE, "~15 s / month"),
    ("BEST CESIUM CLOCK: ABOUT 1/300,000,000 SECOND A YEAR", 1, GREEN, "")], rise=1.3)


def heart_risks(draw, p, t, fonts, color):
    ang = view(t)
    floor_grid(draw, ang)
    names = ("HIGH BLOOD PRESSURE", "HIGH BLOOD CHOLESTEROL", "SMOKING")
    for i, name in enumerate(names):
        x = -200 + i * 200
        on = p * 3 > i
        box(draw, x, 0, 70, 70, 210 if on else 60, ang, RED if on else GREY, 235 if on else 150)
        sx, sy = pt(x, -10, 55, ang)
        for k, line in enumerate(name.split(" ", 1) if len(name) > 12 else [name]):
            _label(draw, (sx, sy + 22 + k * 22), line, fonts, WHITE, "mm")
    sx, sy = pt(0, 300, 0, ang)
    _label(draw, (sx, sy), "47% OF PEOPLE IN THE US HAVE AT LEAST ONE", fonts, YELLOW, "mm")


def noise_gauge(draw, p, t, fonts, color):
    ang = view(t)
    floor_grid(draw, ang, half=220)
    level = 0.25 + 0.65 * min(1.0, p * 1.4)
    box(draw, 0, 0, 120, 120, 330, ang, BLUE, 70, wire=True)
    box(draw, 0, 0, 100, 100, 330 * level, ang, ORANGE if level > 0.7 else GREEN, 235, wire=False)
    y85 = 330 * 0.7
    a, b = pt(-170, y85, -120, ang), pt(170, y85, 120, ang)
    draw.line((*a, *b), fill=_c(RED, 240), width=4)
    sx, sy = pt(-175, y85 + 30, -120, ang)
    _label(draw, (sx, sy), "85 dBA: HAZARDOUS", fonts, RED, "mm")


def heat_stroke_gauge(draw, p, t, fonts, color):
    ang = view(t)
    floor_grid(draw, ang, half=220)
    level = 0.35 + 0.6 * min(1.0, p * 1.3)
    box(draw, 0, 0, 120, 120, 330, ang, BLUE, 70)
    box(draw, 0, 0, 100, 100, 330 * level, ang, RED, 235, wire=False)
    ok = level < 0.8
    sx, sy = pt(0, 360, 0, ang)
    _label(draw, (sx, sy), "SWEATING WORKS" if ok else "SWEATING FAILS", fonts, GREEN if ok else RED, "mm")
    sx, sy = pt(0, -10, 90, ang)
    _label(draw, (sx, sy + 24), "body temperature rises rapidly", fonts, WHITE, "mm")


MOTIFS_3D_B = {fn_name: fn for fn_name, fn in (
    ("water_share_bars", water_share_bars), ("glacier_share", glacier_share), ("salt_share", salt_share),
    ("sleep_ages", sleep_ages), ("clock_drift", clock_drift), ("heart_risks", heart_risks),
    ("noise_gauge", noise_gauge), ("heat_stroke_gauge", heat_stroke_gauge))}
