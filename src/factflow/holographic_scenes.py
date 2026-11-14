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
        # White sunlight enters a holographic prism and separates into seven colours.
        _label(draw, (92, 365), "WHITE SUNLIGHT", fonts["label"], WHITE)
        sx, sy = 125, 540
        for r, a in ((48, 25), (37, 55), (25, 120)):
            draw.ellipse((sx-r, sy-r, sx+r, sy+r),
                         outline=(255, 242, 190, a), width=4)
        draw.ellipse((sx-17, sy-17, sx+17, sy+17), fill=(255, 250, 220, 245))
        beam_x = int(220 + progress * 65)
        draw.line((145, sy, beam_x, sy), fill=(255, 255, 238, 220), width=7)
        # Wireframe prism.
        p1, p2, p3 = (beam_x, 450), (beam_x+115, sy), (beam_x, 630)
        draw.line((p1, p2, p3, p1), fill=CYAN, width=4, joint="curve")
        draw.line((beam_x, sy, beam_x+115, sy), fill=(160, 245, 255, 150), width=2)
        labels = ["RED", "ORANGE", "YELLOW", "GREEN", "BLUE", "INDIGO", "VIOLET"]
        for i, color in enumerate(SPECTRUM):
            y = 390 + i*48
            end_x = int(570 + 12*math.sin(seconds*2+i))
            draw.line((beam_x+115, sy, end_x, y), fill=(*color[:3], 65), width=13)
            draw.line((beam_x+115, sy, end_x, y), fill=color, width=4)
            draw.ellipse((end_x-5, y-5, end_x+5, y+5), fill=color)
            _label(draw, (end_x-5, y+10), labels[i], fonts["tiny"], color)
        _label(draw, (235, 710), "VISIBLE LIGHT SPECTRUM", fonts["heading"])
        _label(draw, (210, 758), "WHITE LIGHT = MANY WAVELENGTHS", fonts["small"], WHITE)
        return "ONE BEAM. MANY COLOURS.", "Sunlight contains the full visible spectrum"

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
