"""Print a compact luminance map to understand figure vs background."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent / "libs/batman-cli"))

from batman_code.widgets.portrait import generate_portrait, _luminance

W, H = 80, 25  # small for readability
portrait = generate_portrait(W, H)

print("=== Luminance map (0-9 scale, '.' = below 0.05) ===")
print(f"Size: {W}x{H}")
print()
for r in range(H):
    line = []
    for c in range(W):
        ch, (pr, pg, pb) = portrait[r][c]
        lum = _luminance(pr, pg, pb)
        if lum < 0.05:
            line.append('.')
        else:
            line.append(str(min(9, int(lum * 10))))
    print(f"r{r:02d} {''.join(line)}")

print()
print("=== Row averages (helps find where the figure is vertically) ===")
for r in range(H):
    lums = [_luminance(*portrait[r][c][1]) for c in range(W)]
    avg = sum(lums) / len(lums)
    bar = '#' * int(avg * 200)
    print(f"r{r:02d} avg={avg:.3f} {bar}")

print()
print("=== Column averages (helps find where the figure is horizontally) ===")
for c in range(0, W, 4):
    lums = [_luminance(*portrait[r][c][1]) for r in range(H)]
    avg = sum(lums) / len(lums)
    bar = '#' * int(avg * 200)
    print(f"c{c:02d} avg={avg:.3f} {bar}")
