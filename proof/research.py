"""Measure the centre line of a glyph across reference grotesques.

    python3 proof/research.py <out_dir> [glyphs...]   (default: six nine s S)

For each reference font the glyph is rasterised, thinned to its one-pixel
skeleton (scikit-image), and ordered into a path from its terminal. Paths are
normalised to the glyph's ink box, resampled by arc length and averaged. The
average is the genre's shared shape; no single font's outline is used.

Writes <out_dir>/research.json (mean paths, per-font metrics) and
<out_dir>/<glyph>.svg (every font's centre line in grey, the mean in black).
"""

import json
import math
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw
from skimage.morphology import skeletonize
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

R = "/tmp/claude-0/-home-user-maker/e61551db-f8ed-5e98-b397-f01c02bf5363/scratchpad/ref/"
REFS = {
    "Heros (Helvetica)": "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheros-regular.otf",
    "Inter": R + "fontsource-variable-inter-5.3.0/package/files/inter-latin-wght-normal.woff2",
    "Geist": R + "geist-1.9.2/package/dist/fonts/geist-sans/Geist-Variable.ttf",
    "IBM Plex Sans": R + "ibm-plex-sans.woff2",
    "Roboto": R + "roboto.woff2",
    "Public Sans": R + "public-sans.woff2",
    "Hanken Grotesk": R + "hanken-grotesk.woff2",
    "Schibsted Grotesk": R + "schibsted-grotesk.woff2",
    "Instrument Sans": R + "instrument-sans.woff2",
    "Work Sans": R + "work-sans.woff2",
    "Archivo": R + "archivo.woff2",
}
CHARS = {"six": "6", "nine": "9", "s": "s", "S": "S"}
SIZE = 900  # raster height of the ink box


class Poly(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.contours, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, a, b, c):
        p0 = self.cur[-1]
        for i in range(1, 25):
            t = i / 24
            mt = 1 - t
            self.cur.append(tuple(mt ** 3 * p0[j] + 3 * mt * mt * t * a[j] + 3 * mt * t * t * b[j] + t ** 3 * c[j] for j in (0, 1)))

    def _qCurveToOne(self, a, b):
        p0 = self.cur[-1]
        for i in range(1, 17):
            t = i / 16
            mt = 1 - t
            self.cur.append(tuple(mt * mt * p0[j] + 2 * mt * t * a[j] + t * t * b[j] for j in (0, 1)))

    def _closePath(self):
        self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def area(c):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(c, c[1:] + c[:1])) / 2


def raster(path, ch, wght=400):
    f = TTFont(path)
    if "fvar" in f:
        f = instantiateVariableFont(f, {"wght": wght})
    gs = f.getGlyphSet()
    pen = Poly(gs)
    gs[f.getBestCmap()[ord(ch)]].draw(pen)
    pts = [p for c in pen.contours for p in c]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    s = SIZE / (y1 - y0)
    W, H = int((x1 - x0) * s) + 20, SIZE + 20
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    cons = sorted(pen.contours, key=lambda c: -abs(area(c)))
    sign = math.copysign(1, area(cons[0]))
    for c in cons:  # outers fill, counters (opposite winding) clear
        d.polygon([((p[0] - x0) * s + 10, (y1 - p[1]) * s + 10) for p in c], fill=255 if math.copysign(1, area(c)) == sign else 0)
    return np.array(img) > 127, (x1 - x0) / (y1 - y0)


N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def graph(sk):
    pts = set(zip(*np.nonzero(sk)))
    nb = {p: [(p[0] + a, p[1] + b) for a, b in N8 if (p[0] + a, p[1] + b) in pts] for p in pts}
    return nb


def prune(nb, length=40):
    """Remove short spurs the thinning leaves at corners."""
    changed = True
    while changed:
        changed = False
        ends = [p for p, n in nb.items() if len(n) == 1]
        for e in ends:
            path, cur, prev = [e], e, None
            while True:
                nxt = [q for q in nb[cur] if q != prev]
                if len(nxt) != 1 or len(path) > length:
                    break
                prev, cur = cur, nxt[0]
                path.append(cur)
            if len(path) <= length and len(nb.get(cur, [])) >= 3:
                for q in path[:-1]:
                    for r in nb.pop(q, []):
                        if r in nb:
                            nb[r] = [x for x in nb[r] if x != q]
                changed = True
    return nb


def bfs(nb, a, b, banned=()):
    prev = {a: None}
    q = deque([a])
    while q:
        u = q.popleft()
        if u == b:
            break
        for v in nb[u]:
            if v not in prev and v not in banned:
                prev[v] = u
                q.append(v)
    path, u = [], b
    while u is not None:
        path.append(u)
        u = prev[u]
    return path[::-1]


def resample(path, n):
    p = np.array(path, float)
    d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
    t = np.linspace(0, d[-1], n)
    return np.stack([np.interp(t, d, p[:, 0]), np.interp(t, d, p[:, 1])], 1)


def centre_lines(mask, kind, kind_dir=0):
    """Ordered centre line(s) in ink-box units: x right 0..w/h, y up 0..1."""
    sk = skeletonize(mask)
    nb = prune(graph(sk))
    H = mask.shape[0] - 20

    def norm(path):
        return [((c - 10) / H, 1 - (r - 10) / H) for r, c in path]

    ends = [p for p, n in nb.items() if len(n) == 1]
    if kind == "s":
        a, b = sorted(ends, key=lambda p: p[0])[:1][0], sorted(ends, key=lambda p: -p[0])[0]  # top end, bottom end
        return {"path": norm(bfs(nb, a, b))}
    # 6 / 9: walk from the terminal as a pen would: at the junction carry
    # straight on (down into the bowl), round the bowl, and stop on meeting
    # stroke already drawn
    term = ends[0]
    path, seen = [term], {term}
    while True:
        cur = path[-1]
        nxt = [v for v in nb[cur] if v not in seen]
        if not nxt:
            break
        if len(nxt) > 1:
            back = path[max(0, len(path) - 12)]
            d0 = (cur[0] - back[0], cur[1] - back[1])

            def turn(v):
                d1 = (v[0] - cur[0], v[1] - cur[1])
                return -(d0[0] * d1[0] + d0[1] * d1[1]) / (math.hypot(*d0) * math.hypot(*d1) + 1e-9)
            # at the junction the pen keeps going the way the glyph is built:
            # a 6 continues down its left side, a 9 up its right side
            if len(nxt) > 1 and len(path) > 30 and kind_dir:
                nxt.sort(key=lambda v: kind_dir * v[0])
            else:
                nxt.sort(key=turn)
        path.append(nxt[0])
        seen.add(nxt[0])
        # mark the junction's sibling pixels seen once passed, so the walk can't double back
        for v in nb[cur]:
            if v != nxt[0] and len(path) > 30 and v in nb and len(nb[v]) >= 3:
                seen.add(v)
    return {"path": norm(path)}


def main():
    out = sys.argv[1]
    names = sys.argv[2:] or ["six", "nine", "s", "S"]
    os.makedirs(out, exist_ok=True)
    result = {}
    for name in names:
        ch = CHARS[name]
        kind = "s" if name in ("s", "S") else "6"
        per = {}
        for font, path in REFS.items():
            mask, ratio = raster(path, ch)
            lines = centre_lines(mask, kind, {"six": -1, "nine": 1}.get(name, 0))
            per[font] = {"ratio": ratio, "path": resample(np.array(lines["path"]), 200).tolist()}
        keys = [k for k in per[next(iter(per))] if k != "ratio"]
        mean = {k: np.mean([v[k] for v in per.values()], axis=0).tolist() for k in keys}
        mean["ratio"] = float(np.mean([v["ratio"] for v in per.values()]))
        result[name] = {"mean": mean, "fonts": per}
        # overlay
        W = 1.0
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-0.1 -1.1 {W + 0.2} 1.2" width="420" height="504">',
               '<rect x="-0.1" y="-1.1" width="2" height="2" fill="#fff"/>']
        for font, v in per.items():
            for k in keys:
                pts = " ".join(f"{x:.4f},{-y:.4f}" for x, y in v[k])
                col = "#e0731f" if "Helvetica" in font else "#bbb"
                svg.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="0.006"/>')
        for k in keys:
            pts = " ".join(f"{x:.4f},{-y:.4f}" for x, y in mean[k])
            svg.append(f'<polyline points="{pts}" fill="none" stroke="#000" stroke-width="0.012"/>')
        svg.append("</svg>")
        open(os.path.join(out, f"{name}.svg"), "w").write("".join(svg))
        print(f"{name}: {len(per)} fonts, mean width/height {mean['ratio']:.3f}")
    json.dump(result, open(os.path.join(out, "research.json"), "w"))


if __name__ == "__main__":
    main()


# --- landmark-aligned average and skeleton fit ---------------------------------
# Curved-arc (Swiss) 6 and 9 only: IBM Plex, Roboto and Hanken use a straight
# diagonal, a different tradition, and would blur the average.
COHORT = {
    "six": ["Heros (Helvetica)", "Inter", "Geist", "Public Sans", "Archivo"],
    "nine": ["Heros (Helvetica)", "Inter", "Geist", "Public Sans", "Schibsted Grotesk", "Instrument Sans", "Work Sans", "Archivo"],
    "s": list(REFS), "S": list(REFS),
}


def landmarks(p, name):
    """Indices of structural points along a centre line that starts at the terminal."""
    x, y = p[:, 0], p[:, 1]
    n = len(p)
    if name == "six":
        top = int(np.argmax(y[: n // 2]))
        bot = int(np.argmin(y))
        left = top + int(np.argmin(x[top:bot]))
        right = bot + int(np.argmax(x[bot:]))
        btop = right + int(np.argmax(y[right:]))
        return [0, top, left, bot, right, btop, n - 1]
    if name == "nine":
        bot = int(np.argmin(y[: n // 2]))
        top = int(np.argmax(y))
        right = bot + int(np.argmax(x[bot:top]))
        left = top + int(np.argmin(x[top:]))
        bbot = left + int(np.argmin(y[left:]))
        return [0, bot, right, top, left, bbot, n - 1]
    top = int(np.argmax(y))
    bot = int(np.argmin(y))
    left = top + int(np.argmin(x[top: (top + bot) // 2 + 1]))
    right = (top + bot) // 2 + int(np.argmax(x[(top + bot) // 2: bot]))
    mid = left + int(np.argmin(np.abs(y[left:right] - (y[left] + y[right]) / 2)))
    return [0, top, left, mid, right, bot, n - 1]


def aligned(path, name, per_seg=40, trim=0.06):
    p = np.array(path)
    # a terminal's skeleton forks into the cut's corners: drop it. A 6 or 9 has
    # one terminal (where the path starts); its other end joins the side.
    k = max(1, int(len(p) * trim))
    p = p[k: len(p) - k] if name in ("s", "S") else p[k:]
    lm = landmarks(p, name)
    out = [resample(p[a: b + 1], per_seg) for a, b in zip(lm, lm[1:])]
    return out


def fit_segment(pts, t0=None, t1=None):
    pts = np.array(pts)
    d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    ts = d / d[-1]
    s0, s1 = pts[0], pts[-1]
    # an open end (a terminal) takes its direction from a longer stretch of
    # stroke, so the fork the thinning leaves in a cut corner can't bend it
    w = max(3, len(pts) // 5)
    t0 = np.array(t0) if t0 is not None else (pts[w] - pts[0]) / np.linalg.norm(pts[w] - pts[0])
    t1 = np.array(t1) if t1 is not None else (pts[-1] - pts[-1 - w]) / np.linalg.norm(pts[-1] - pts[-1 - w])
    A, rhs = [], []
    for s, t in zip(pts, ts):
        mt = 1 - t
        b0, b1, b2, b3 = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
        base = (b0 + b1) * s0 + (b2 + b3) * s1
        for j in (0, 1):
            A.append([b1 * t0[j], -b2 * t1[j]])
            rhs.append(s[j] - base[j])
    (a, b), *_ = np.linalg.lstsq(np.array(A), np.array(rhs), rcond=None)
    chord = np.linalg.norm(s1 - s0)
    a, b = max(a, chord * 0.05), max(b, chord * 0.05)
    return [s0.tolist(), (s0 + a * t0).tolist(), (s1 - b * t1).tolist(), s1.tolist()]


# the tangent at each landmark, by its role: extremes are level or upright
ROLE = {
    "six": [None, (-1, 0), (0, -1), (1, 0), (0, 1), (-1, 0), None],
    "nine": [None, (1, 0), (0, 1), (-1, 0), (0, -1), (1, 0), None],
    "s": [None, (-1, 0), (0, -1), None, (0, -1), (-1, 0), None],
}
ROLE["S"] = ROLE["s"]


def consensus(result):
    """Average each glyph across its cohort and fit one cubic per landmark span,
    in centre-line box units (the box the skeleton itself spans, 0..1 high)."""
    out = {}
    for name, data in result.items():
        def complete(f):  # a trace that stopped early (a spur at a terminal) can't be aligned
            p = np.array(data["fonts"][f]["path"])
            span = p[:, 1].max() - p[:, 1].min()
            length = np.sum(np.hypot(*np.diff(p, axis=0).T))
            return span > 0.85 and length > 2.5
        used = [f for f in COHORT[name] if f in data["fonts"] and complete(f)]
        segs = [aligned(data["fonts"][f]["path"], name) for f in used]
        mean = [np.mean([s[i] for s in segs], axis=0) for i in range(len(segs[0]))]
        allp = np.concatenate(mean)
        x0, y0 = allp.min(0)
        x1, y1 = allp.max(0)
        h = y1 - y0
        mean = [(m - [x0, y0]) / h for m in mean]
        roles = ROLE[name]
        cubics = []
        for i, m in enumerate(mean):
            cubics.append(fit_segment(m, roles[i], roles[i + 1]))
        out[name] = {"aspect": float((x1 - x0) / h), "cubics": cubics, "fonts": used,
                     "mean": [m.tolist() for m in mean]}
    return out


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--consensus":
    pass
