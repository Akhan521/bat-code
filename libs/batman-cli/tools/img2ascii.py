#!/usr/bin/env python3
"""Convert an image to colored ASCII art using density-mapped characters.

Each pixel block maps to an ASCII character based on brightness, with
per-character truecolor for maximum fidelity. Characters like @#%*+:-.
visibly form the image — it looks like text art, not colored blocks.

Usage:
    python tools/img2ascii.py <image_path> [--width W] [--height H]
        [--contrast C] [--sharpen S] [--charset CHARSET]
        [--preview] [--output FILE] [--html FILE]

Examples:
    # Preview at 100 columns:
    python tools/img2ascii.py batman.png --width 100 --preview

    # Generate Python module with portrait data:
    python tools/img2ascii.py batman.png --width 120 --output portrait_data.py

    # HTML preview for browser:
    python tools/img2ascii.py batman.png --width 120 --html portrait.html
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# Gotham night background
BG_COLOR = (10, 10, 15)  # #0a0a0f

# Character ramps ordered from darkest (least dense) to brightest (most dense).
# Each ramp maps luminance 0.0-1.0 to a character.
CHARSETS = {
    # Standard: 10 levels, good balance
    "standard": " .:-=+*#%@",
    # Extended: 70 levels, maximum tonal range
    "extended": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    # Blocks: uses Unicode block elements for denser fills
    "blocks": " .░▒▓█",
    # Minimal: fewer levels, bolder look
    "minimal": " .:+*#@",
    # Gotham: pure visible characters — no block elements (░▒▓█▄▀).
    # Uses line-drawing, symbols, and alphanumerics for a true ASCII art look.
    # Ordered dark→bright by visual density.
    "gotham": " .·':;~-=+?!*/|\\)(1{}[]<>tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
}


def load_and_preprocess(
    image_path: str,
    target_width: int,
    target_height: int | None = None,
    contrast: float = 1.3,
    sharpen_percent: int = 150,
) -> Image.Image:
    """Load an image and preprocess for maximum ASCII art fidelity.

    Args:
        image_path: Path to source image.
        target_width: Target width in terminal columns (1 char = 1 pixel).
        target_height: Target height in terminal rows. If None, auto from aspect.
        contrast: Contrast multiplier (1.0 = unchanged, 1.3 = recommended).
        sharpen_percent: Unsharp mask strength (0 = off, 150 = recommended).

    Returns:
        Preprocessed PIL Image at target dimensions.
    """
    img = Image.open(image_path)

    # Flatten alpha onto Gotham-black background
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, BG_COLOR)
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Contrast enhancement at full resolution
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)

    # Unsharp mask — sharpens edges so they survive downscaling
    if sharpen_percent > 0:
        img = img.filter(
            ImageFilter.UnsharpMask(radius=2, percent=sharpen_percent, threshold=3)
        )

    # Calculate target dimensions
    # Terminal chars are ~2:1 (height:width), so we halve the vertical samples
    # to correct aspect ratio
    orig_w, orig_h = img.size
    aspect = orig_h / orig_w
    if target_height is not None:
        pixel_height = target_height
    else:
        # Halve height to correct for tall terminal characters
        pixel_height = int(target_width * aspect * 0.5)

    # LANCZOS downscale
    img = img.resize((target_width, pixel_height), Image.LANCZOS)

    return img


def pixel_luminance(r: int, g: int, b: int) -> float:
    """Perceptual luminance (0.0 = black, 1.0 = white)."""
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def image_to_ascii(
    img: Image.Image,
    charset: str = "standard",
) -> list[list[tuple[str, tuple[int, int, int]]]]:
    """Convert image to ASCII art with per-character color.

    Args:
        img: Preprocessed RGB PIL Image.
        charset: Name of character ramp from CHARSETS.

    Returns:
        2D list of (character, (r, g, b)) tuples.
    """
    ramp = CHARSETS.get(charset, CHARSETS["standard"])
    ramp_len = len(ramp)
    width, height = img.size
    pixels = img.load()
    rows = []

    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = pixels[x, y][:3]
            lum = pixel_luminance(r, g, b)
            # Map luminance to character index
            idx = int(lum * (ramp_len - 1))
            idx = min(idx, ramp_len - 1)
            ch = ramp[idx]
            row.append((ch, (r, g, b)))
        rows.append(row)

    return rows


def render_ansi(rows: list[list[tuple[str, tuple[int, int, int]]]]) -> str:
    """Render ASCII art with ANSI truecolor escape sequences."""
    lines = []
    for row in rows:
        parts = []
        for ch, (r, g, b) in row:
            if ch == " ":
                parts.append(" ")
            else:
                parts.append(f"\033[38;2;{r};{g};{b}m{ch}")
        lines.append("".join(parts) + "\033[0m")
    return "\n".join(lines)


def render_html(
    rows: list[list[tuple[str, tuple[int, int, int]]]],
) -> str:
    """Render ASCII art as an HTML page for browser preview."""
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html><head><style>")
    parts.append("body { background: #0a0a0f; margin: 20px; }")
    parts.append("pre { font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace; ")
    parts.append("  font-size: 12px; line-height: 1.15; letter-spacing: 0.05em; color: #333; }")
    parts.append("</style></head><body><pre>")

    for row in rows:
        for ch, (r, g, b) in row:
            if ch == " ":
                parts.append(" ")
            else:
                # HTML-escape special chars
                display = ch.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                parts.append(f'<span style="color:rgb({r},{g},{b})">{display}</span>')
        parts.append("\n")

    parts.append("</pre></body></html>")
    return "".join(parts)


def render_rich_module(rows: list[list[tuple[str, tuple[int, int, int]]]]) -> str:
    """Generate Python module with ASCII portrait data and Rich Text builder."""
    lines = []
    lines.append('"""Auto-generated colored ASCII portrait data."""')
    lines.append("")
    lines.append("from rich.text import Text")
    lines.append("from rich.style import Style")
    lines.append("")
    lines.append(f"PORTRAIT_WIDTH = {len(rows[0]) if rows else 0}")
    lines.append(f"PORTRAIT_HEIGHT = {len(rows)}  # terminal rows")
    lines.append("")
    lines.append("# Each entry: (character, (r, g, b))")
    lines.append("PORTRAIT_DATA = [")

    for row in rows:
        row_data = ", ".join(
            f'({repr(ch)},({r},{g},{b}))'
            for ch, (r, g, b) in row
        )
        lines.append(f"    [{row_data}],")

    lines.append("]")
    lines.append("")
    lines.append("")
    lines.append("def build_portrait(brightness: float = 1.0) -> Text:")
    lines.append('    """Build a Rich Text renderable of the ASCII portrait.')
    lines.append("")
    lines.append("    Args:")
    lines.append("        brightness: Multiplier for fade-in (0.0 = black, 1.0 = full).")
    lines.append("")
    lines.append("    Returns:")
    lines.append("        Rich Text object ready for rendering.")
    lines.append('    """')
    lines.append("    text = Text()")
    lines.append("    bg = Style(bgcolor='rgb(10,10,15)')")
    lines.append("    for i, row in enumerate(PORTRAIT_DATA):")
    lines.append("        for ch, (r, g, b) in row:")
    lines.append("            if brightness < 1.0:")
    lines.append("                r = int(r * brightness)")
    lines.append("                g = int(g * brightness)")
    lines.append("                b = int(b * brightness)")
    lines.append("            if ch == ' ':")
    lines.append("                text.append(' ', style=bg)")
    lines.append("            else:")
    lines.append("                style = Style(")
    lines.append('                    color=f"rgb({r},{g},{b})",')
    lines.append("                    bgcolor='rgb(10,10,15)',")
    lines.append("                )")
    lines.append("                text.append(ch, style=style)")
    lines.append("        if i < len(PORTRAIT_DATA) - 1:")
    lines.append("            text.append('\\n')")
    lines.append("    return text")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert an image to colored ASCII art.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("image", help="Path to source image")
    parser.add_argument(
        "--width", "-w", type=int, default=100,
        help="Target width in terminal columns (default: 100)",
    )
    parser.add_argument(
        "--height", type=int, default=None,
        help="Target height in terminal rows (default: auto from aspect ratio)",
    )
    parser.add_argument(
        "--contrast", "-c", type=float, default=1.3,
        help="Contrast multiplier (default: 1.3)",
    )
    parser.add_argument(
        "--sharpen", "-s", type=int, default=150,
        help="Unsharp mask percent (default: 150, 0 = off)",
    )
    parser.add_argument(
        "--charset", type=str, default="standard",
        choices=list(CHARSETS.keys()),
        help="Character ramp (default: standard)",
    )
    parser.add_argument(
        "--preview", "-p", action="store_true",
        help="Print to terminal with ANSI truecolor",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output Python module with Rich Text portrait data",
    )
    parser.add_argument(
        "--html", type=str, default=None,
        help="Output HTML file for browser preview",
    )

    args = parser.parse_args()

    if not Path(args.image).exists():
        print(f"Error: Image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {args.image}", file=sys.stderr)
    img = load_and_preprocess(
        args.image,
        target_width=args.width,
        target_height=args.height,
        contrast=args.contrast,
        sharpen_percent=args.sharpen,
    )
    w, h = img.size
    print(f"Target: {w}x{h} characters (charset: {args.charset})", file=sys.stderr)

    rows = image_to_ascii(img, charset=args.charset)

    if args.preview:
        print(render_ansi(rows))

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(render_rich_module(rows), encoding="utf-8")
        print(f"Written: {output_path}", file=sys.stderr)

    if args.html:
        html_path = Path(args.html)
        html_path.write_text(render_html(rows), encoding="utf-8")
        print(f"HTML preview: {html_path}", file=sys.stderr)

    if not args.preview and not args.output and not args.html:
        print("No action. Use --preview, --output, or --html.", file=sys.stderr)


if __name__ == "__main__":
    main()
