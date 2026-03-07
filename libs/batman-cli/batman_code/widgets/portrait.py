"""Runtime ASCII portrait converter — sizes to actual terminal dimensions.

Converts the bundled Batman portrait image into colored ASCII art at
whatever resolution the terminal provides. Uses the "gotham" charset
(visible characters only, no block elements) with per-character truecolor.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

# Gotham night background
_BG_COLOR = (10, 10, 15)  # #0a0a0f

# Gotham charset: visible chars only, ordered dark→bright by visual density
_GOTHAM_RAMP = " .·':;~-=+?!*/|\\)(1{}[]<>tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

_ASSET_PATH = Path(__file__).parent.parent / "assets" / "batman_portrait.jpg"


def _luminance(r: int, g: int, b: int) -> float:
    """Perceptual luminance (0.0 = black, 1.0 = white)."""
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def generate_portrait(
    width: int,
    height: int,
    contrast: float = 1.4,
    sharpen_percent: int = 150,
) -> list[list[tuple[str, tuple[int, int, int]]]]:
    """Convert the bundled Batman portrait to fit the given terminal size.

    Args:
        width: Terminal width in columns.
        height: Terminal height in rows.
        contrast: Contrast boost (1.0 = none, 1.4 = recommended).
        sharpen_percent: Unsharp mask strength (0 = off).

    Returns:
        2D list of (character, (r, g, b)) tuples sized to width x height.
    """
    img = Image.open(_ASSET_PATH)

    # Flatten alpha
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, _BG_COLOR)
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Pre-process at full resolution
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if sharpen_percent > 0:
        img = img.filter(
            ImageFilter.UnsharpMask(radius=2, percent=sharpen_percent, threshold=3)
        )

    # Resize to terminal dimensions
    img = img.resize((width, height), Image.LANCZOS)

    # Convert to ASCII with per-character truecolor
    ramp = _GOTHAM_RAMP
    ramp_len = len(ramp)
    pixels = img.load()
    rows = []

    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = pixels[x, y][:3]
            lum = _luminance(r, g, b)
            idx = min(int(lum * (ramp_len - 1)), ramp_len - 1)
            row.append((ramp[idx], (r, g, b)))
        rows.append(row)

    return rows
