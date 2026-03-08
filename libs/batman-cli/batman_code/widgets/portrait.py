"""Runtime ASCII portrait converter — sizes to actual terminal dimensions.

Converts the bundled Batman portrait image into colored ASCII art at
whatever resolution the terminal provides. Uses the "gotham" charset
(visible characters only, no block elements) with per-character truecolor.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
from rich.text import Text

# Gotham night background
_BG_COLOR = (10, 10, 15)  # #0a0a0f
_BG_HEX = "#0a0a0f"

# Gotham charset: visible chars only, ordered dark→bright by visual density
_GOTHAM_RAMP = " .·':;~-=+?!*/|\\)(1{}[]<>tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

_ASSET_PATH = Path(__file__).parent.parent / "assets" / "batman_portrait.jpg"


def _luminance(r: int, g: int, b: int) -> float:
    """Perceptual luminance (0.0 = black, 1.0 = white)."""
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def _load_image(width: int, height: int, contrast: float, sharpen_percent: int) -> Image.Image:
    """Load, enhance, and resize the portrait image."""
    img = Image.open(_ASSET_PATH)

    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, _BG_COLOR)
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if sharpen_percent > 0:
        img = img.filter(
            ImageFilter.UnsharpMask(radius=2, percent=sharpen_percent, threshold=3)
        )

    return img.resize((width, height), Image.LANCZOS)


def generate_portrait(
    width: int,
    height: int,
    contrast: float = 1.4,
    sharpen_percent: int = 150,
) -> list[list[tuple[str, tuple[int, int, int]]]]:
    """Convert the bundled Batman portrait to fit the given terminal size.

    Returns:
        2D list of (character, (r, g, b)) tuples sized to width x height.
    """
    img = _load_image(width, height, contrast, sharpen_percent)
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


def generate_portrait_frames(
    width: int,
    height: int,
    num_steps: int = 8,
    contrast: float = 1.4,
    sharpen_percent: int = 150,
) -> list[Text]:
    """Pre-render the portrait at multiple brightness levels as Rich Text.

    Returns a list of `num_steps` Rich Text objects, from fully dark (step 0)
    to full brightness (step num_steps-1). Each is a complete frame ready
    to display — no per-frame computation needed during animation.
    """
    img = _load_image(width, height, contrast, sharpen_percent)
    ramp = _GOTHAM_RAMP
    ramp_len = len(ramp)
    pixels = img.load()

    # Build the full-brightness grid once
    grid: list[list[tuple[str, int, int, int]]] = []
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = pixels[x, y][:3]
            lum = _luminance(r, g, b)
            idx = min(int(lum * (ramp_len - 1)), ramp_len - 1)
            row.append((ramp[idx], r, g, b))
        grid.append(row)

    # Generate frames at each brightness level
    frames: list[Text] = []
    for step in range(num_steps):
        brightness = step / (num_steps - 1)  # 0.0 → 1.0
        text = Text(overflow="fold", no_wrap=True)

        for row in grid:
            col = 0
            w = len(row)
            while col < w:
                ch, r, g, b = row[col]
                # Scale RGB by brightness
                br = int(r * brightness)
                bg = int(g * brightness)
                bb = int(b * brightness)
                color = f"#{br:02x}{bg:02x}{bb:02x}"

                # Find run of same color (after brightness scaling)
                start = col
                while col < w:
                    ch2, r2, g2, b2 = row[col]
                    c2 = f"#{int(r2*brightness):02x}{int(g2*brightness):02x}{int(b2*brightness):02x}"
                    if c2 != color:
                        break
                    col += 1

                # At very low brightness, dim chars become spaces
                if brightness < 0.15:
                    run_text = " " * (col - start)
                else:
                    run_text = "".join(row[i][0] for i in range(start, col))
                text.append(run_text, style=color)
            text.append("\n")

        frames.append(text)

    return frames
