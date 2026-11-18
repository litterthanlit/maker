"""Score Hypher Extended's N I T R O U S against the reference wordmark, letter by letter.

    python3 families/hypher-extended/proof/fit.py              # overlap per letter
    python3 families/hypher-extended/proof/fit.py --png out.png # and an overlay: reference grey, ours red

Each letter is drawn at the reference's stem, rasterised at the reference's
scale, aligned on its ink box and compared by intersection over union.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent.parent / "src"))
sys.path.insert(0, str(HERE))

import glyphs as G  # noqa: E402
from core.geometry import _pt  # noqa: E402

REF = HERE / "proof" / "reference.png"
LETTERS = "NITROUS"
SS = 4  # supersampling


def reference():
    """The reference's letters as ink masks, and its scale in pixels per unit."""
    im = np.asarray(Image.open(REF).convert("L"), dtype=float)
    ink = np.clip((193 - im) / (193 - 150), 0, 1)  # background 193, ink 150
    cols = np.where((ink > 0.5).any(0))[0]
    spans, start = [], cols[0]
    for a, b in zip(cols, cols[1:]):
        if b != a + 1:
            spans.append((start, a))
            start = b
    spans.append((start, cols[-1]))
    rows = np.where((ink[:, spans[1][0]:spans[1][1] + 1] > 0.5).any(1))[0]  # the I: flat, no overshoot
    scale = (rows[-1] - rows[0] + 1) / G.CH
    return [ink[:, a:b + 1] for a, b in spans], scale


def raster(contours, scale):
    """Contours to an ink mask at scale, cropped to the ink, by summing each contour's winding."""
    polys = []
    for c in contours:
        pts, cur = [c[0]], c[0]
        for s in c[1:]:
            if s[0] == "l":
                pts.append(s[1])
            else:
                pts += [_pt((cur,) + s[1:], t / 12) for t in range(1, 13)]
            cur = s[-1]
        polys.append(pts)
    allp = [q for pl in polys for q in pl]
    x0, y0 = min(q[0] for q in allp), min(q[1] for q in allp)
    x1, y1 = max(q[0] for q in allp), max(q[1] for q in allp)
    k = scale * SS
    w, h = int((x1 - x0) * k) + 2, int((y1 - y0) * k) + 2
    acc = np.zeros((h, w), dtype=int)
    for pl in polys:
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pl, pl[1:] + pl[:1]))
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).polygon([((q[0] - x0) * k, (y1 - q[1]) * k) for q in pl], fill=1)
        acc += np.asarray(m, dtype=int) * (1 if area > 0 else -1)
    mask = Image.fromarray(((acc != 0) * 255).astype(np.uint8))
    return np.asarray(mask.resize((max(1, round(w / SS)), max(1, round(h / SS))), Image.BOX), dtype=float) / 255


def crop(m):
    ys, xs = np.where(m > 0.5)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def iou(a, b):
    h, w = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])
    pa, pb = np.zeros((h, w)), np.zeros((h, w))
    pa[:a.shape[0], :a.shape[1]] = a
    pb[:b.shape[0], :b.shape[1]] = b
    return np.minimum(pa, pb).sum() / np.maximum(pa, pb).sum(), pa, pb


def score():
    refs, scale = reference()
    p = G.P(600, G.REF_STEM)
    out = {}
    for ch, ref in zip(LETTERS, refs):
        ours = raster(G.GLYPHS[ch][1](p)[0], scale)
        out[ch] = iou(crop(ref), crop(ours))
    return out


if __name__ == "__main__":
    res = score()
    for ch, (v, _, _) in res.items():
        print(f"{ch} {v:.3f}")
    print(f"mean {np.mean([v for v, _, _ in res.values()]):.3f}")
    if "--png" in sys.argv:
        tiles = []
        for ch, (_, a, b) in res.items():
            rgb = np.full(a.shape + (3,), 255.0)
            rgb -= a[..., None] * np.array([110, 110, 110])  # the reference, grey
            rgb[..., 1:] -= b[..., None] * 120  # ours, red; where both, dark red
            tiles.append(np.pad(rgb, ((10, 10), (10, 10), (0, 0)), constant_values=255))
        h = max(t.shape[0] for t in tiles)
        row = np.concatenate([np.pad(t, ((0, h - t.shape[0]), (0, 0), (0, 0)), constant_values=255) for t in tiles], 1)
        img = Image.fromarray(np.clip(row, 0, 255).astype(np.uint8))
        img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(sys.argv[sys.argv.index("--png") + 1])
