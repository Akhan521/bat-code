"""Analyze the Batman portrait to visualize figure vs background pixels.

Generates an HTML file showing the ASCII portrait with luminance data,
helping identify which areas are Batman's figure and which are noise.
"""
import sys
sys.path.insert(0, "libs/batman-cli")

from batman_code.widgets.portrait import generate_portrait, _luminance, _BG_COLOR
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path

WIDTH, HEIGHT = 160, 45  # representative terminal size

# Generate the portrait
portrait = generate_portrait(WIDTH, HEIGHT)

# Also get raw luminance map from the image for analysis
img = Image.open(Path(__file__).parent.parent / "libs/batman-cli/batman_code/assets/batman_portrait.jpg")
if img.mode != "RGB":
    img = img.convert("RGB")
img = ImageEnhance.Contrast(img).enhance(1.4)
img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
pixels = img.load()

html = ['<html><head><style>']
html.append('body { background: #0a0a0f; font-family: monospace; font-size: 11px; line-height: 1.1; }')
html.append('pre { margin: 20px; }')
html.append('.info { color: #f5c518; margin: 20px; font-size: 14px; }')
html.append('</style></head><body>')

# View 1: Full portrait with actual colors
html.append('<div class="info">VIEW 1: Full ASCII portrait (actual colors)</div>')
html.append('<pre>')
for r in range(HEIGHT):
    for c in range(WIDTH):
        ch, (pr, pg, pb) = portrait[r][c]
        if ch == ' ':
            html.append(' ')
        else:
            html.append(f'<span style="color:rgb({pr},{pg},{pb})">{ch}</span>')
    html.append('\n')
html.append('</pre>')

# View 2: Luminance heatmap — red = high lum (figure), blue = low lum (noise)
html.append('<div class="info">VIEW 2: Luminance heatmap (RED = bright/figure, BLUE = dark/noise, BLACK = below 0.05)</div>')
html.append('<pre>')
for r in range(HEIGHT):
    for c in range(WIDTH):
        pr, pg, pb = pixels[c, r][:3]
        lum = _luminance(pr, pg, pb)
        if lum < 0.05:
            html.append('<span style="color:#111">.</span>')
        elif lum < 0.10:
            html.append(f'<span style="color:rgb(0,0,{int(lum*2550)})">░</span>')
        elif lum < 0.20:
            html.append(f'<span style="color:rgb({int(lum*500)},0,{int(lum*1200)})">▒</span>')
        else:
            html.append(f'<span style="color:rgb({min(255,int(lum*400))},{int(lum*100)},{0})">█</span>')
    html.append('\n')
html.append('</pre>')

# View 3: Show what would be removed with threshold 0.08 in upper 45% outside center 30-70%
html.append('<div class="info">VIEW 3: Proposed removal — GREEN = kept, RED = would be removed (upper corners, lum&lt;0.10)</div>')
html.append('<pre>')
for r in range(HEIGHT):
    for c in range(WIDTH):
        ch, (pr, pg, pb) = portrait[r][c]
        lum = _luminance(pr, pg, pb)
        if ch == ' ':
            html.append(' ')
            continue
        # Check if pixel is in the "upper corner" zones
        in_upper = r < int(HEIGHT * 0.55)
        frac_c = c / WIDTH
        in_center = 0.25 < frac_c < 0.75
        would_remove = in_upper and not in_center and lum < 0.15
        if would_remove:
            html.append(f'<span style="color:#ff3333">{ch}</span>')
        else:
            html.append(f'<span style="color:#33ff33">{ch}</span>')
    html.append('\n')
html.append('</pre>')

# View 4: More aggressive — gradient threshold based on distance from center
html.append('<div class="info">VIEW 4: Gradient threshold — stronger cleanup far from center, none at center</div>')
html.append('<pre>')
cx, cy = WIDTH * 0.48, HEIGHT * 0.40  # approximate figure center (head area)
for r in range(HEIGHT):
    for c in range(WIDTH):
        ch, (pr, pg, pb) = portrait[r][c]
        lum = _luminance(pr, pg, pb)
        if ch == ' ':
            html.append(' ')
            continue
        # Distance from figure center (normalized 0-1)
        dx = (c - cx) / WIDTH
        dy = (r - cy) / HEIGHT
        dist = (dx*dx + dy*dy) ** 0.5
        # Threshold increases with distance: 0 at center, up to 0.15 at edges
        threshold = max(0, dist - 0.25) * 0.5
        would_remove = lum < threshold
        if would_remove:
            html.append(f'<span style="color:#ff3333">{ch}</span>')
        else:
            html.append(f'<span style="color:#33ff33">{ch}</span>')
    html.append('\n')
html.append('</pre>')

html.append('</body></html>')

out = Path(__file__).parent / "portrait_analysis.html"
out.write_text("".join(html), encoding="utf-8")
print(f"Wrote {out} — open in browser to analyze")
