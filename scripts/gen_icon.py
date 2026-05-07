"""Generate voice_dictate/resources/icon.ico using Pillow."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZES = [16, 24, 32, 48, 64, 128, 256]
OUT = Path(__file__).parent.parent / "voice_dictate" / "resources" / "icon.ico"


def make_frame(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = max(1, size // 10)
    # Dark circle background
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(42, 42, 48, 230),
        outline=(180, 180, 190, 200),
        width=max(1, size // 32),
    )

    # Mic emoji text
    emoji = "🎤"
    font_size = int(size * 0.52)
    font = None
    for font_path in [
        "C:/Windows/Fonts/seguiemj.ttf",   # Segoe UI Emoji
        "C:/Windows/Fonts/seguisym.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except Exception:
            pass
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), emoji, font=font, embedded_color=True)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1]
    draw.text((x, y), emoji, font=font, embedded_color=True)
    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [make_frame(s) for s in SIZES]
    frames[0].save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    print(f"Icon saved: {OUT}")


if __name__ == "__main__":
    main()
