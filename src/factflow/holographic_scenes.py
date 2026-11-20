"""Procedural holographic science storyboard scenes for the QuantaTale sample."""
from __future__ import annotations

import math
from typing import Any

W, H = 720, 1280
CYAN = (73, 226, 255, 230)
BLUE = (65, 155, 255, 230)
VIOLET = (165, 105, 255, 230)
WHITE = (230, 247, 255, 235)
SPECTRUM = [
    (255, 76, 83, 230), (255, 151, 67, 230), (255, 221, 86, 230),
    (100, 238, 151, 230), (75, 180, 255, 230), (89, 112, 255, 230),
    (177, 105, 255, 230),
]


def _glow_circle(draw: Any, x: int, y: int, r: int, color: tuple, width: int = 3) -> None:
    for extra, alpha in ((12, 30), (7, 55), (3, 95)):
        draw.ellipse((x-r-extra, y-r-extra, x+r+extra, y+r+extra),
                     outline=(*color[:3], alpha), width=max(1, width))
    draw.ellipse((x-r, y-r, x+r, y+r), outline=color, width=width)


def _label(draw: Any, xy: tuple[int, int], text: str, font: Any,
           color: tuple = CYAN) -> None:
    draw.text(xy, text, font=font, fill=color, stroke_width=1,
              stroke_fill=(3, 20, 42, 210))


def draw_holographic_scene(draw: Any, scene: int, progress: float,
                           seconds: float, fonts: dict[str, Any]) -> tuple[str, str]:
    """Draw one distinct, animated holographic scene; return its title and caption."""
    cx, cy = 360, 590
    scan = int((seconds * 110) % 500)
    draw.line((90, 300 + scan, 630, 300 + scan),
              fill=(75, 226, 255, 35), width=2)

    if scene == 0:
        # A white solar beam crosses space and enters Earth's curved atmosphere.
        # Sunlight is white because it contains a range of visible wavelengths.
        # Their different scattering is shown in scene 1; the atmosphere is not
        # depicted as a prism splitting the beam into a rainbow.
        _label(draw, (82, 315), "SUNLIGHT APPROACHING EARTH", fonts["label"], WHITE)

        # Holographic Earth limb and two transparent atmospheric shells.
        earth_cx, earth_cy = 405, 1015
        earth_r = 405
        for radius, alpha, width in ((earth_r + 55, 35, 3), (earth_r + 34, 75, 4),
                                     (earth_r + 15, 125, 5)):
            draw.arc((earth_cx-radius, earth_cy-radius,
                      earth_cx+radius, earth_cy+radius),
                     205, 335, fill=(75, 205, 255, alpha), width=width)
        draw.ellipse((earth_cx-earth_r, earth_cy-earth_r,
                      earth_cx+earth_r, earth_cy+earth_r),
                     outline=(73, 226, 255, 175), width=3)
        # A dark, translucent planetary surface gives the atmospheric edge depth.
        draw.pieslice((earth_cx-earth_r, earth_cy-earth_r,
                       earth_cx+earth_r, earth_cy+earth_r),
                      205, 335, fill=(5, 30, 66, 115),
                      outline=(73, 226, 255, 150), width=3)

        # Sun source with layered holographic corona.
        sx, sy = 112, 430
        for radius, alpha in ((55, 28), (43, 55), (31, 100)):
            draw.ellipse((sx-radius, sy-radius, sx+radius, sy+radius),
                         outline=(255, 225, 155, alpha), width=4)
        draw.ellipse((sx-20, sy-20, sx+20, sy+20),
                     fill=(255, 250, 220, 250))
        _label(draw, (77, 505), "SUN", fonts["tiny"], (255, 225, 155, 230))

        # Entry point on the atmospheric limb; pulse and animate the incoming
        # white beam so the viewer can follow the light into the atmosphere.
        entry = (345, 575)
        draw.ellipse((entry[0]-42, entry[1]-42, entry[0]+42, entry[1]+42),
                     outline=(73, 226, 255, 70), width=3)
        draw.ellipse((entry[0]-25, entry[1]-25, entry[0]+25, entry[1]+25),
                     outline=(73, 226, 255, 145), width=3)
        draw.line((sx+24, sy+18, entry[0], entry[1]),
                  fill=(255, 255, 238, 65), width=24)
        draw.line((sx+24, sy+18, entry[0], entry[1]),
                  fill=(255, 255, 238, 245), width=6)
        for i in range(6):
            travel = (progress * 1.35 + i / 6) % 1.0
            px = int(sx+24 + (entry[0]-(sx+24))*travel)
            py = int(sy+18 + (entry[1]-(sy+18))*travel)
            rr = 5 + int(2 * math.sin(seconds*8+i))
            draw.ellipse((px-rr*2, py-rr*2, px+rr*2, py+rr*2),
                         fill=(255, 244, 190, 65))
            draw.ellipse((px-rr, py-rr, px+rr, py+rr),
                         fill=(255, 255, 245, 250))

        _label(draw, (375, 535), "ATMOSPHERE", fonts["tiny"])
        # White sunlight already contains a range of visible wavelengths.
        # Show their colours as a compact legend, not as rays splitting at the
        # atmospheric boundary. Scene 1 then visualizes wavelength-dependent
        # scattering by air molecules.
        _label(draw, (155, 755), "COLOURS WITHIN WHITE SUNLIGHT", fonts["small"], WHITE)
        swatch_x, swatch_y = 155, 790
        swatch_width, swatch_gap = 54, 7
        for index, color in enumerate(SPECTRUM):
            left = swatch_x + index * (swatch_width + swatch_gap)
            draw.rounded_rectangle(
                (left, swatch_y, left + swatch_width, swatch_y + 12),
                radius=5, fill=color,
            )
        _label(draw, (155, 835), "ONE WHITE BEAM", fonts["heading"], WHITE)
        _label(draw, (155, 885), "MANY VISIBLE WAVELENGTHS", fonts["small"])
        _label(draw, (155, 930), "ENTERING THE ATMOSPHERE", fonts["small"], WHITE)
        return "SUNLIGHT ENTERS THE ATMOSPHERE", "White sunlight contains many visible wavelengths"

    if scene == 1:
        # Molecule field and blue/red scattering comparison.
        _label(draw, (155, 365), "EARTH'S ATMOSPHERE", fonts["label"])
        centers = [(235,455),(360,420),(490,470),(275,590),(430,620),(535,555),(185,690),(365,760)]
        for i,(mx,my) in enumerate(centers):
            x = int(mx + math.sin(seconds*1.2+i)*12)
            y = int(my + math.cos(seconds*1.1+i)*10)
            _glow_circle(draw,x,y,15,CYAN,3)
            for k in range(3):
                a = seconds*1.5+i+k*2.1
                ex,ey=int(x+math.cos(a)*90),int(y+math.sin(a)*90)
                col = BLUE if k < 2 else (255,100,110,190)
                draw.line((x,y,ex,ey),fill=(*col[:3],100),width=7)
                draw.line((x,y,ex,ey),fill=col,width=3)
                rr=int(5+2*math.sin(seconds*5+i+k))
                draw.ellipse((ex-rr,ey-rr,ex+rr,ey+rr),fill=col)
            ring=int((seconds*35+i*23)%75)
            draw.ellipse((x-ring,y-ring,x+ring,y+ring),outline=(75,180,255,max(25,130-ring)),width=2)
        _label(draw,(105,850),"BLUE: SCATTERED MORE",fonts["heading"],BLUE)
        _label(draw,(105,900),"RED: SCATTERED LESS",fonts["heading"],(255,125,135,230))
        return "MOLECULES REDIRECT THE LIGHT", "Shorter blue wavelengths scatter more strongly"

    if scene == 2:
        # Recognizable side-profile holographic eye with iris, pupil and retina.
        _label(draw, (230, 365), "HUMAN EYE — HOLOGRAM", fonts["label"])
        # Eyeball silhouette / sclera.
        draw.ellipse((125,430,595,760),outline=(73,226,255,110),width=3)
        # Upper and lower eyelid contours.
        draw.arc((105,410,615,780),185,355,fill=CYAN,width=5)
        draw.arc((105,410,615,780),5,175,fill=CYAN,width=5)
        # Iris and pupil.
        ix,iy=365,595
        for radius in (112,100,86,70):
            _glow_circle(draw,ix,iy,radius,(73,190,255,190),2)
        draw.ellipse((ix-43,iy-43,ix+43,iy+43),fill=(2,24,55,255),outline=CYAN,width=4)
        # Iris radial fibres.
        for i in range(32):
            a=i*math.tau/32+seconds*.12
            draw.line((int(ix+48*math.cos(a)),int(iy+48*math.sin(a)),
                       int(ix+91*math.cos(a)),int(iy+91*math.sin(a))),
                      fill=(85,205,255,130),width=2)
        # Lens and retina highlight.
        draw.arc((245,485,325,705),270,90,fill=VIOLET,width=5)
        draw.arc((475,455,575,735),260,100,fill=(175,120,255,210),width=6)
        # Incoming blue rays visibly enter pupil and continue to retina.
        for offset in (-24,0,24):
            y=int(iy+offset+math.sin(seconds*3+offset)*5)
            draw.line((70,y-40,ix-44,iy+offset//2),fill=(70,170,255,85),width=11)
            draw.line((70,y-40,ix-44,iy+offset//2),fill=BLUE,width=3)
            draw.line((ix+44,iy+offset//2,520,y+offset),fill=(145,115,255,170),width=2)
        _label(draw,(78,790),"INCOMING BLUE LIGHT",fonts["small"],BLUE)
        _label(draw,(480,790),"RETINA",fonts["label"],VIOLET)
        draw.line((530,775,530,710),fill=VIOLET,width=2)
        _label(draw,(286,845),"PUPIL",fonts["label"])
        draw.line((330,825,350,650),fill=CYAN,width=2)
        return "LIGHT ENTERS YOUR EYE", "Scattered blue light reaches the eye"

    # Scene 3: holographic Earth and atmospheric shell.
    _label(draw,(225,365),"EARTH'S BLUE SKY",fonts["label"])
    ex,ey,er=360,610,205
    for radius,alpha in ((er+42,35),(er+27,65),(er+12,110)):
        draw.ellipse((ex-radius,ey-radius,ex+radius,ey+radius),
                     outline=(65,185,255,alpha),width=5)
    draw.ellipse((ex-er,ey-er,ex+er,ey+er),fill=(3,27,66,255),outline=CYAN,width=4)
    # Holographic continent-like paths.
    for points in [
        [(250,500),(280,465),(320,480),(335,530),(300,565),(270,550)],
        [(390,480),(440,470),(485,520),(460,565),(420,550),(400,520)],
        [(300,640),(340,665),(355,720),(325,755),(290,700)],
        [(420,635),(465,650),(475,700),(440,730),(410,685)],
    ]:
        draw.line(points,fill=(80,220,190,190),width=5,joint="curve")
    # Atmosphere rays scatter outward in animated directions.
    for i in range(24):
        a=i*math.tau/24+seconds*.08
        x1,y1=int(ex+(er+5)*math.cos(a)),int(ey+(er+5)*math.sin(a))
        x2,y2=int(ex+(er+85+20*math.sin(seconds*2+i))*math.cos(a)),int(ey+(er+85)*math.sin(a))
        draw.line((x1,y1,x2,y2),fill=(70,175,255,110),width=3)
        draw.ellipse((x2-4,y2-4,x2+4,y2+4),fill=BLUE)
    _label(draw,(195,870),"RAYLEIGH SCATTERING",fonts["heading"])
    _label(draw,(165,920),"BLUE LIGHT ARRIVES FROM ALL DIRECTIONS",fonts["small"],WHITE)
    return "WHY THE SKY LOOKS BLUE", "Scattered blue light fills the daytime sky"


def draw_sunset_scene(draw: Any, scene: int, progress: float,
                      seconds: float, fonts: dict[str, Any]) -> tuple[str, str]:
    """Draw topic-specific holographic scenes explaining red sunsets."""
    warm = (255, 139, 83, 230)
    red = (255, 91, 105, 230)
    orange = (255, 177, 83, 230)
    pale = (255, 235, 190, 235)
    scan = int((seconds * 95) % 430)
    draw.line((70, 280 + scan, 650, 280 + scan), fill=(255, 142, 96, 38), width=2)

    if scene == 0:
        _label(draw, (115, 340), "THE SUN SINKS TOWARD THE HORIZON", fonts["label"], pale)
        # Layered Earth limb and transparent atmosphere.
        earth = (360, 910, 700)
        for radius, alpha, width in ((310, 28, 3), (285, 65, 4), (260, 115, 5)):
            draw.arc((earth[0]-radius, earth[1]-radius, earth[0]+radius, earth[1]+radius),
                     195, 345, fill=(255, 139, 83, alpha), width=width)
        draw.ellipse((earth[0]-earth[2]//2, earth[1]-earth[2]//2,
                      earth[0]+earth[2]//2, earth[1]+earth[2]//2),
                     outline=(73, 190, 255, 120), width=3)
        sx, sy = 360, 635
        for radius, alpha in ((70, 28), (54, 55), (38, 105)):
            draw.ellipse((sx-radius, sy-radius, sx+radius, sy+radius),
                         outline=(255, 171, 95, alpha), width=4)
        draw.ellipse((sx-25, sy-25, sx+25, sy+25), fill=pale)
        _label(draw, (300, 730), "LOW SUN", fonts["tiny"], orange)
        # The long slanted sunlight path is the key causal visual.
        for offset in (-15, 0, 15):
            draw.line((70, 410+offset, 330, 630+offset), fill=(255, 210, 150, 55), width=15)
            draw.line((70, 410+offset, 330, 630+offset), fill=pale, width=3)
        for i in range(8):
            t = (progress * 1.4 + i/8) % 1
            x, y = int(70+260*t), int(410+220*t)
            draw.ellipse((x-5, y-5, x+5, y+5), fill=pale)
        _label(draw, (125, 825), "A LONGER ATMOSPHERIC PATH", fonts["small"], warm)
        return "SUNLIGHT TRAVELS FARTHER", "Low-angle sunlight crosses more atmosphere"

    if scene == 1:
        _label(draw, (150, 350), "AIR MOLECULES SCATTER SHORT WAVES", fonts["label"], pale)
        centers = [(190,470),(330,430),(480,480),(255,610),(420,650),(545,575),(180,755),(365,790)]
        for i, (mx, my) in enumerate(centers):
            x = int(mx + math.sin(seconds*1.25+i)*10)
            y = int(my + math.cos(seconds*1.1+i)*9)
            _glow_circle(draw, x, y, 14, CYAN, 3)
            for k in range(3):
                angle = seconds*1.4 + i + k*2.1
                ex, ey = int(x+math.cos(angle)*75), int(y+math.sin(angle)*75)
                color = BLUE if k < 2 else (255, 120, 120, 185)
                draw.line((x,y,ex,ey), fill=(*color[:3],95), width=7)
                draw.line((x,y,ex,ey), fill=color, width=3)
        _label(draw, (105, 875), "BLUE AND VIOLET: REDIRECTED", fonts["heading"], BLUE)
        _label(draw, (105, 925), "LONGER RED WAVELENGTHS CONTINUE", fonts["small"], warm)
        return "BLUE LIGHT SCATTERS AWAY", "Shorter wavelengths leave the direct sunlight path"

    if scene == 2:
        _label(draw, (175, 350), "WHAT REACHES THE OBSERVER?", fonts["label"], pale)
        # A beam with blue side-scattering and a warm direct beam.
        for i in range(7):
            y = 470 + i*48
            draw.line((90, y, 590, y+int(25*math.sin(seconds*1.2+i))), fill=(255, 170, 95, 55), width=12)
            draw.line((90, y, 590, y+int(25*math.sin(seconds*1.2+i))), fill=orange, width=3)
        for i in range(10):
            x = 170 + i*42
            y = 615 + int(18*math.sin(seconds*2+i))
            draw.line((x,y,x-55,y-95), fill=(70,160,255,165), width=3)
            draw.ellipse((x-5,y-5,x+5,y+5), fill=BLUE)
        _glow_circle(draw, 575, 760, 62, warm, 4)
        draw.ellipse((545,730,605,790), fill=orange)
        _label(draw, (150, 865), "RED • ORANGE • PINK", fonts["heading"], warm)
        _label(draw, (160, 915), "LONGER WAVES REACH YOUR EYES", fonts["small"], pale)
        return "WARM COLOURS REACH YOUR EYES", "Less blue remains in the direct beam"

    # A final holographic horizon with layered sunset bands and drifting particles.
    _label(draw, (180, 350), "THE SCIENCE OF A RED SUNSET", fonts["label"], pale)
    bands = [
        (420, 500, (90, 65, 145, 90)), (500, 590, (155, 75, 125, 115)),
        (590, 680, (220, 92, 92, 145)), (680, 770, (255, 135, 78, 165)),
        (770, 870, (255, 185, 100, 180)),
    ]
    for top, bottom, color in bands:
        draw.rectangle((65, top, 655, bottom), fill=color)
        draw.line((65, top, 655, top), fill=(255, 205, 145, 90), width=2)
    sun_x = 360
    sun_y = int(825 + 10*math.sin(seconds*0.7))
    for radius, alpha in ((95, 28), (76, 55), (58, 105)):
        draw.ellipse((sun_x-radius, sun_y-radius, sun_x+radius, sun_y+radius),
                     outline=(255, 170, 92, alpha), width=4)
    draw.ellipse((sun_x-48, sun_y-48, sun_x+48, sun_y+48), fill=(255, 183, 100, 235))
    draw.line((65, 875, 655, 875), fill=(73, 226, 255, 175), width=3)
    for i in range(24):
        x = int(80 + (i*71 + seconds*18) % 560)
        y = int(465 + (i*37) % 340)
        draw.ellipse((x-2,y-2,x+2,y+2), fill=(255, 218, 165, 150))
    _label(draw, (150, 930), "ONE SCATTERING PROCESS", fonts["heading"], pale)
    return "WHY SUNSETS TURN RED", "The atmosphere filters sunlight before it reaches us"


def _wrap(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


_STOP = {"the", "and", "that", "this", "with", "from", "into", "than", "then", "when", "while", "your", "their", "there",
         "they", "them", "what", "which", "will", "have", "been", "were", "also", "each", "over", "more", "most", "some"}


def _tokens(text: str) -> set[str]:
    words = {w.strip(".,;:!?\"'()").lower() for w in text.split()}
    return {w for w in words if len(w) > 3 and w not in _STOP}


def sentence_scene_map(narration: str, scenes: list[dict[str, Any]]) -> tuple[list[float], list[int]]:
    """Which scene each narrated sentence belongs to, and each sentence's share of the video.

    Scenes keep their order and each is used at least once; a sentence goes with the
    scene whose ``narration_segment`` shares the most words with it.
    """
    sentences = [x.strip() for x in narration.replace("\u2014", ",").split(".") if x.strip()]
    if not sentences or not scenes:
        return [1.0], [0]
    weights = [max(1, len(x.split())) for x in sentences]
    total = float(sum(weights))
    shares = [w / total for w in weights]
    n, m = len(sentences), len(scenes)
    if n < m:  # fewer sentences than scenes: spread scenes evenly over time instead
        return [1.0 / m] * m, list(range(m))
    seg_tokens = [_tokens(str(sc.get("narration_segment", "")) + " " + str(sc.get("visual_description", ""))) for sc in scenes]
    score = [[len(_tokens(sent) & seg_tokens[j]) / (1.0 + 0.5 * len(seg_tokens[j])) for j in range(m)] for sent in sentences]
    neg = float("-inf")
    best = [[neg] * m for _ in range(n)]
    back = [[0] * m for _ in range(n)]
    best[0][0] = score[0][0]
    for i in range(1, n):
        for j in range(m):
            for prev in (j, j - 1):
                if prev >= 0 and best[i - 1][prev] > neg and best[i - 1][prev] + score[i][j] > best[i][j]:
                    best[i][j] = best[i - 1][prev] + score[i][j]
                    back[i][j] = prev
    j = m - 1
    assignment = [0] * n
    for i in range(n - 1, -1, -1):
        assignment[i] = j
        j = back[i][j]
    return shares, assignment


def scene_position(narration: str, scenes: list[dict[str, Any]], seconds: float, duration: float) -> tuple[int, float]:
    """Scene index and 0-1 progress inside it for this moment of the narration."""
    shares, assignment = sentence_scene_map(narration, scenes)
    fraction = min(0.9999, max(0.0, seconds / duration if duration else 0.0))
    spans: dict[int, list[float]] = {}
    cursor = 0.0
    for share, scene in zip(shares, assignment):
        lo, hi = spans.setdefault(scene, [cursor, cursor])
        spans[scene] = [lo, cursor + share]
        cursor += share
    for scene, (lo, hi) in spans.items():
        if lo <= fraction < hi or (scene == max(spans) and fraction >= lo):
            return scene, (fraction - lo) / max(1e-6, hi - lo)
    return 0, 0.0


def _hologram_stage(draw: Any, seconds: float, color: Any) -> None:
    """Projector platform under the animation: rotating rings and a faint light cone."""
    cx, cy = 360, 1010
    for i in range(14):  # light cone fading upward
        y = cy - i * 38
        half = 250 - i * 6
        draw.line((cx - half, y, cx + half, y), fill=(*color[:3], max(6, 34 - i * 2)), width=3)
    for k, (rx, ry) in enumerate(((290, 52), (225, 40), (160, 28))):
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=(*color[:3], 190 - k * 40), width=3 - (k == 2))
        for t in range(24):
            ang = seconds * (0.6 + 0.25 * k) * (-1 if k % 2 else 1) + t * math.tau / 24
            x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
            draw.line((x, y, x, y - 9), fill=(*color[:3], 170), width=2)
    draw.ellipse((cx - 14, cy - 5, cx + 14, cy + 5), fill=(*color[:3], 220))


def _draw_motif_raised(draw: Any, motif: str, progress: float, seconds: float, fonts: dict[str, Any], color: Any) -> None:
    """Draw the motif on its own layer and lift it into the free space under the title."""
    from PIL import Image, ImageDraw
    from .visual_motifs import draw_motif

    base = getattr(draw, "_image", None) or getattr(draw, "im", None)
    if not isinstance(base, Image.Image):
        draw_motif(motif, draw, progress, seconds, fonts, color)
        return
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw_motif(motif, ImageDraw.Draw(layer, "RGBA"), progress, seconds, fonts, color)
    region = layer.crop((0, 300, base.width, 1100))
    base.paste(region.convert("RGB") if base.mode == "RGB" else region, (0, 255), region)


def draw_generic_science_scene(draw: Any, scene: int, progress: float, seconds: float,
                               fonts: dict[str, Any], scenes: list[dict[str, Any]],
                               narration: str = "", duration: float = 0.0) -> tuple[str, str]:
    """Generic holographic scene for authored topics.

    Each scene shows its own animated motif, switched in step with the narrated sentences.
    Nothing from the scene notes is printed on screen: the picture must explain the narration.
    """
    from .visual_motifs import MOTIFS, draw_motif

    count = max(1, len(scenes))
    if narration and duration and scenes:
        position, local_progress = scene_position(narration, scenes, seconds, duration)
    else:
        overall = min(0.9999, (scene + min(1.0, max(0.0, progress))) / 4)
        position = min(count - 1, int(overall * count))
        local_progress = overall * count - position
    palette = [CYAN, VIOLET, BLUE, CYAN]
    color = palette[position % 4]
    cx, cy = 360, 690
    scan = int((seconds * 110) % 560)
    draw.line((90, 250 + scan, 630, 250 + scan), fill=(75, 226, 255, 35), width=2)

    motif = str(scenes[position].get("motif", "")) if scenes else ""
    if motif in MOTIFS:
        _hologram_stage(draw, seconds, color)
        _draw_motif_raised(draw, motif, local_progress, seconds, fonts, color)
        if position == 0:
            headline = "THE QUESTION"
        elif position == count - 1:
            headline = "THE TAKEAWAY"
        else:
            headline = "HOW IT WORKS"
        return headline, ""

    # Pulsing holographic core with orbiting nodes; node count grows with the scene.
    for k in range(4):
        radius = 70 + k * 52 + int(10 * math.sin(seconds * 2.2 + k + position))
        _glow_circle(draw, cx, cy, radius, color, width=2 + (k == 0))
    nodes = 3 + position * 2
    points = []
    for n in range(nodes):
        angle = seconds * (0.7 + 0.15 * (n % 3)) + n * 2 * math.pi / nodes
        orbit = 120 + 52 * (n % 3)
        x, y = int(cx + orbit * math.cos(angle)), int(cy + orbit * 0.62 * math.sin(angle))
        points.append((x, y))
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(*color[:3], 220))
    for a, b in zip(points, points[1:] + points[:1]):
        draw.line((*a, *b), fill=(*color[:3], 70), width=2)
    draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(*color[:3], 235))
    end = 360 * min(1.0, max(0.0, progress))
    draw.arc((cx - 250, cy - 250, cx + 250, cy + 250), -90, -90 + end, fill=(*WHITE[:3], 200), width=4)

    if position == 0:
        headline = "THE QUESTION"
    elif position == count - 1:
        headline = "THE TAKEAWAY"
    else:
        headline = "HOW IT WORKS"
    return headline, ""
