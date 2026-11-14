"""Free, procedural sample-video renderer for QuantaTale.

Requires Pillow plus system executables ffmpeg, ffprobe and espeak-ng.
The renderer is deliberately separate from research assessment: the bundled
sample is a demonstration asset and is not cleared for public release.
"""
from __future__ import annotations

import json
import math
import random
import shutil
import subprocess
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WIDTH, HEIGHT, FPS = 720, 1280, 24
NAVY = (4, 10, 28)
CYAN = (73, 226, 255)
BLUE = (63, 142, 255)
VIOLET = (159, 104, 255)
WHITE = (232, 246, 255)
MUTED = (143, 174, 201)


def validate_sample_spec(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise ValueError("Sample specification must be a JSON object.")
    for field in ("title", "narration", "sources"):
        if field not in spec:
            raise ValueError(f"Sample specification is missing '{field}'.")
    if not isinstance(spec["title"], str) or not spec["title"].strip():
        raise ValueError("Sample title must be a non-empty string.")
    if not isinstance(spec["narration"], str) or len(spec["narration"].split()) < 12:
        raise ValueError("Sample narration must contain at least 12 words.")
    if not isinstance(spec["sources"], list) or not spec["sources"]:
        raise ValueError("At least one traceable source is required.")
    for source in spec["sources"]:
        if not isinstance(source, dict) or not str(source.get("url", "")).startswith("https://"):
            raise ValueError("Every source must include an HTTPS URL.")


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{millis:03}"


def _caption_segments(narration: str, duration: float) -> list[tuple[float, float, str]]:
    sentences = [part.strip() for part in narration.replace("—", ",").split(".") if part.strip()]
    if not sentences:
        sentences = [narration.strip()]
    weights = [max(1, len(sentence.split())) for sentence in sentences]
    total = sum(weights)
    cursor = 0.0
    segments = []
    for sentence, weight in zip(sentences, weights):
        start = cursor
        cursor += duration * weight / total
        segments.append((start, cursor, sentence.rstrip(" ,;:") + ( "." if not sentence.endswith((".", "?", "!")) else "")))
    if segments:
        segments[-1] = (segments[-1][0], duration, segments[-1][2])
    return segments


def _wrap_text(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_frame(spec: dict[str, Any], seconds: float, duration: float, caption: str, fonts: dict[str, Any], stars: list[tuple[int, int, int]]) -> Any:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image, "RGBA")

    # Subtle technical grid and fixed star field.
    for x in range(24, WIDTH, 48):
        draw.line((x, 0, x, HEIGHT), fill=(27, 68, 98, 35), width=1)
    for y in range(20, HEIGHT, 48):
        draw.line((0, y, WIDTH, y), fill=(27, 68, 98, 28), width=1)
    for x, y, radius in stars:
        pulse = 110 + int(90 * (0.5 + 0.5 * math.sin(seconds * 2 + x * 0.03)))
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(93, 204, 255, pulse))

    draw.text((48, 55), "QUANTATALE", font=fonts["small"], fill=CYAN)
    draw.text((48, 105), spec["title"].upper(), font=fonts["title"], fill=WHITE, stroke_width=1, stroke_fill=(25, 88, 120))
    draw.line((48, 177, WIDTH-48, 177), fill=(73, 226, 255, 130), width=2)

    phase = seconds / max(duration, 0.1)
    center_x, center_y = WIDTH // 2, 630
    pulse = 1.0 + 0.035 * math.sin(seconds * 2.2)

    # A luminous Sun and a white-light beam entering a stylized atmosphere.
    sun_x, sun_y = 125, 430
    sun_radius = int(48 * pulse)
    for grow, alpha in ((22, 18), (14, 30), (7, 55)):
        draw.ellipse((sun_x-sun_radius-grow, sun_y-sun_radius-grow,
                      sun_x+sun_radius+grow, sun_y+sun_radius+grow),
                     outline=(255, 207, 122, alpha), width=5)
    draw.ellipse((sun_x-sun_radius, sun_y-sun_radius,
                  sun_x+sun_radius, sun_y+sun_radius), fill=(255, 220, 153, 245))
    draw.text((62, 505), "SUNLIGHT", font=fonts["label"], fill=(255, 222, 165))

    # Atmosphere / Earth limb.
    earth_box = (center_x-270, 760, center_x+270, 1300)
    draw.ellipse(earth_box, fill=(5, 24, 55, 255), outline=(72, 204, 255, 230), width=5)
    draw.arc((center_x-292, 735, center_x+292, 1320), 190, 350, fill=(83, 210, 255, 190), width=12)
    draw.arc((center_x-310, 715, center_x+310, 1340), 190, 350, fill=(105, 113, 255, 80), width=4)

    # Incoming white beam, then a changing emphasis on blue scattered light.
    beam_end = (center_x-85, 770)
    draw.line((sun_x+36, sun_y+30, beam_end[0], beam_end[1]), fill=(255, 244, 207, 115), width=20)
    draw.line((sun_x+36, sun_y+30, beam_end[0], beam_end[1]), fill=(255, 255, 239, 235), width=3)

    # Molecules and scattering rays animate outward from the atmospheric shell.
    molecule_centers = [
        (300, 470), (410, 520), (525, 435), (245, 620), (455, 675),
        (565, 585), (330, 720), (515, 790), (185, 700),
    ]
    for index, (mx, my) in enumerate(molecule_centers):
        drift = math.sin(seconds * 1.3 + index) * 5
        x, y = int(mx + drift), my
        r = 7 if index % 2 else 9
        draw.ellipse((x-r-5, y-r-5, x+r+5, y+r+5), outline=(74, 218, 255, 70), width=2)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(110, 226, 255, 225))
        if phase > 0.18:
            length = 55 + int(22 * math.sin(seconds * 2 + index))
            dx = (-1 if index % 2 else 1) * length
            dy = -int(length * (0.55 + 0.25 * math.sin(index)))
            draw.line((x, y, x+dx, y+dy), fill=(65, 160, 255, 155), width=3)
            draw.ellipse((x+dx-4, y+dy-4, x+dx+4, y+dy+4), fill=(90, 180, 255, 220))

    # Blue wavelength motif and explanatory callout.
    wave_y = 300
    points = []
    for x in range(58, WIDTH-58, 4):
        y = wave_y + int(17 * math.sin((x-58) / 27 - seconds * 3.0))
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=(76, 174, 255, 205), width=4)
    draw.text((58, 342), "SHORTER BLUE WAVELENGTHS", font=fonts["label"], fill=(115, 190, 255))

    if phase < 0.32:
        headline, subline = "WHITE LIGHT ENTERS", "Sunlight contains many colours"
    elif phase < 0.72:
        headline, subline = "BLUE SCATTERS MORE", "Tiny air molecules redirect blue light"
    else:
        headline, subline = "THE SKY GLOWS BLUE", "Scattered light reaches us from every direction"
    box = (48, 835, WIDTH-48, 945)
    draw.rounded_rectangle(box, radius=20, fill=(5, 20, 43, 225), outline=(73, 226, 255, 170), width=2)
    draw.text((72, 855), headline, font=fonts["heading"], fill=CYAN)
    draw.text((72, 905), subline, font=fonts["small"], fill=WHITE)

    # Captions are burned into the picture and also exported as an SRT sidecar.
    caption_lines = _wrap_text(draw, caption, fonts["caption"], WIDTH-112)
    caption_lines = caption_lines[:2]
    cap_top = 1030
    cap_height = 44 * max(1, len(caption_lines)) + 40
    draw.rounded_rectangle((34, cap_top, WIDTH-34, cap_top+cap_height),
                           radius=16, fill=(1, 7, 19, 225), outline=(86, 190, 235, 120), width=2)
    for line_index, line in enumerate(caption_lines):
        bbox = draw.textbbox((0, 0), line, font=fonts["caption"])
        text_width = bbox[2] - bbox[0]
        draw.text(((WIDTH-text_width)//2, cap_top+18+line_index*44), line,
                  font=fonts["caption"], fill=WHITE)

    draw.text((48, 1215), "KNOW MORE. SEE DIFFERENTLY.", font=fonts["tiny"], fill=MUTED)
    draw.text((WIDTH-235, 1215), "RESEARCH DEMO", font=fonts["tiny"], fill=VIOLET)
    return image


def render_sample_video(spec_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    """Render a narrated 9:16 MP4 sample and quality-check the encoded file."""
    from PIL import ImageFont

    spec_path = Path(spec_path)
    output_dir = Path(output_dir)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    validate_sample_spec(spec)
    output_dir.mkdir(parents=True, exist_ok=True)

    for executable in ("ffmpeg", "ffprobe", "espeak-ng"):
        if shutil.which(executable) is None:
            raise RuntimeError(f"Required free system tool '{executable}' was not found.")

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not Path(font_path).is_file() or not Path(bold_path).is_file():
        raise RuntimeError("DejaVu fonts are required; install fonts-dejavu-core.")

    fonts = {
        "title": ImageFont.truetype(bold_path, 37),
        "heading": ImageFont.truetype(bold_path, 30),
        "caption": ImageFont.truetype(bold_path, 27),
        "label": ImageFont.truetype(bold_path, 19),
        "small": ImageFont.truetype(font_path, 20),
        "tiny": ImageFont.truetype(font_path, 14),
    }

    audio_path = output_dir / "narration.wav"
    video_path = output_dir / "quantatale-sample-vertical.mp4"
    thumbnail_path = output_dir / "thumbnail.png"
    srt_path = output_dir / "captions.srt"
    metadata_path = output_dir / "sample-metadata.json"

    subprocess.run(
        ["espeak-ng", "-v", "en-us", "-s", "148", "-w", str(audio_path), spec["narration"]],
        check=True, capture_output=True, text=True,
    )
    with wave.open(str(audio_path), "rb") as audio:
        duration = audio.getnframes() / float(audio.getframerate())
    if not 8 <= duration <= 90:
        raise RuntimeError(f"Sample narration duration {duration:.1f}s is outside the safe 8-90s range.")

    segments = _caption_segments(spec["narration"], duration)
    with srt_path.open("w", encoding="utf-8") as handle:
        for index, (start, end, text) in enumerate(segments, 1):
            handle.write(f"{index}\n{_timestamp(start)} --> {_timestamp(end)}\n{text}\n\n")

    rng = random.Random(20261114)
    stars = [(rng.randrange(20, WIDTH-20), rng.randrange(190, HEIGHT-80), rng.choice((1, 1, 2))) for _ in range(95)]
    frame_count = math.ceil(duration * FPS)
    ffmpeg_command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s:v", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
        "-i", str(audio_path), "-map", "0:v:0", "-map", "1:a:0",
        "-frames:v", str(frame_count), "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", str(video_path),
    ]
    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert process.stdin is not None
        for frame_index in range(frame_count):
            seconds = frame_index / FPS
            caption = next((text for start, end, text in segments if start <= seconds < end), segments[-1][2])
            frame = _draw_frame(spec, seconds, duration, caption, fonts, stars)
            if frame_index == min(frame_count - 1, FPS):
                frame.save(thumbnail_path, format="PNG", optimize=True)
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
    except Exception:
        process.kill()
        process.wait()
        raise
    if return_code != 0:
        raise RuntimeError(f"FFmpeg video encoding failed: {stderr[-3000:]}")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,width,height:format=duration",
         "-of", "json", str(video_path)],
        check=True, capture_output=True, text=True,
    )
    probe_data = json.loads(probe.stdout)
    streams = probe_data.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), None)
    encoded_duration = float(probe_data.get("format", {}).get("duration", 0))
    if not video_stream or not audio_stream:
        raise RuntimeError("Quality check failed: encoded MP4 must contain both video and audio.")
    if (video_stream.get("width"), video_stream.get("height")) != (WIDTH, HEIGHT):
        raise RuntimeError("Quality check failed: video dimensions do not match the 9:16 preset.")
    if not 8 <= encoded_duration <= 90 or not video_path.stat().st_size:
        raise RuntimeError("Quality check failed: encoded video duration or file size is invalid.")

    metadata = {
        "schema_version": 1,
        "project": "QuantaTale",
        "title": spec["title"],
        "format": "vertical_9_16",
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
        "duration_seconds": round(encoded_duration, 3),
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name"),
        "narration_engine": "eSpeak NG",
        "animation": "procedural Python/Pillow graphics",
        "render_engine": "FFmpeg",
        "sources": spec["sources"],
        "publication_status": "sample_not_approved_for_publication",
        "editorial_review_required": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": [video_path.name, audio_path.name, srt_path.name, thumbnail_path.name],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "video": str(video_path),
        "thumbnail": str(thumbnail_path),
        "captions": str(srt_path),
        "metadata": str(metadata_path),
        "duration_seconds": round(encoded_duration, 3),
        "size_bytes": video_path.stat().st_size,
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
    }
