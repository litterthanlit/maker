"""Finds shape faults that a reader sees and the outline check does not.

    HYPHER_STYLE=Wordmark python3 families/hypher-display/proof/check_shapes.py

Every glyph is drawn at each master and its parts merged into the one outline
a reader sees. Three faults are looked for in it:

- ledge: a short straight step with a corner at each end, where one part
  sticks out past another (the Z's diagonal past its bar, the 7's bar past its
  diagonal).
- cusp: two curves meeting at an angle, where overlapping parts each round a
  corner the other one fills (the w's notch between its two v's).
- heavy: ink much thicker than a stem, away from where diagonals meet (a
  counter rounder than its outside, or two counters back to back across a thin
  bar, as the 8 and e were at Light).

Some cusps are drawn on purpose (the 3's and 8's waists, the &'s joins) and
some heavy spots belong to every typeface (where diagonals cross or meet);
those are listed in ALLOW. Exits 1 if anything else is found.
"""

import math
import sys
from pathlib import Path

import numpy as np
import pathops
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent.parent / "src"))
sys.path.insert(0, str(HERE.parent))

import build  # noqa: E402
import glyphs as G  # noqa: E402

MIN_STEP = 5  # font units: a step this small does not show
LEDGE = 0.35  # a straight step shorter than this many bars, cornered at both ends
TURN = 25  # degrees: a turn sharper than this is a corner, not a curve running on
HEAVY = 1.5  # ink thicker than this many stems: a filleted joint like the e's reaches 1.33; the blobby 8 and e of 0.500 reached 1.53 to 1.67
SCALE = 0.5  # raster pixels per font unit for the heavy check

WAISTS = {"three", "eight", "ampersand", "B", "R", "P", "ae", "oe", "OE", "germandbls", "uni1E9E", "eth", "ordfeminine"}  # bowls or parts that meet in a cusp on purpose
SHOULDERS = set("nmhrpbdquga") | {"dcroat", "thorn", "hbar", "eng", "uni01E5"}  # with the wordmark's shoulder notch ("notch" in STYLES), their steps and dips are drawn on purpose
ALLOW = {"numbersign": {"ledge"}, "tbar": {"ledge"}}  # the # at Bold: the stems' short sides between close bars are slots, not steps
SOLID = {"bullet", "paragraph"}  # filled on purpose
CROSSINGS = {"uni01E5", "uni01E4", "tbar", "Tbar", "uni0292", "uni01B7", "dollar", "cent", "yen", "sterling", "Euro", "dcroat", "hbar", "Hbar", "Eth", "Dcroat", "Lslash", "lslash", "section"}  # a bar through a stem is heavy where they cross, in any typeface
DIAGONALS = SOLID | CROSSINGS | set("AKMNVWXYZkvwxyz") | {"multiply", "AE", "less", "greater", "guillemotleft", "guillemotright", "guilsinglleft", "guilsinglright", "ampersand", "percent", "four", "seven", "asterisk", "numbersign", "Q", "y"}


def merged(contours):
    path = pathops.Path()
    pen = path.getPen()
    for c in contours:
        pen.moveTo(c[0])
        for s in c[1:]:
            pen.lineTo(s[1]) if s[0] == "l" else pen.curveTo(*s[1:])
        pen.closePath()
    path.simplify(fix_winding=True)
    return path


def segments(path):
    """Per contour: [(kind, points from start to end)]."""
    out = []
    for contour in path.contours:
        segs, cur = [], None
        for verb, pts in contour.segments:
            if verb == "moveTo":
                cur = pts[0]
            elif verb == "lineTo":
                segs.append(("line", [cur, pts[0]]))
                cur = pts[0]
            elif verb == "curveTo":
                segs.append(("curve", [cur, *pts]))
                cur = pts[-1]
            elif verb == "qCurveTo":
                segs.append(("curve", [cur, *pts]))
                cur = pts[-1]
            elif verb == "closePath" and segs and cur != segs[0][1][0]:
                segs.append(("line", [cur, segs[0][1][0]]))
        out.append([s for s in segs if math.dist(s[1][0], s[1][-1]) > 1e-6 or s[0] == "curve"])
    return out


def direction(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def tangent_out(seg):
    pts = seg[1]
    for q in pts[1:]:
        if math.dist(q, pts[0]) > 1e-6:
            return direction(pts[0], q)
    return 0.0


def tangent_in(seg):
    pts = seg[1]
    for q in reversed(pts[:-1]):
        if math.dist(q, pts[-1]) > 1e-6:
            return direction(q, pts[-1])
    return 0.0


def turn(a, b):
    d = abs(b - a) % (2 * math.pi)
    return math.degrees(min(d, 2 * math.pi - d))


def outline_faults(path, H):
    faults = []
    contours = segments(path)
    areas = [sum(s[1][0][0] * s[1][-1][1] - s[1][-1][0] * s[1][0][1] for s in segs) for segs in contours]
    outer = max(areas, key=abs) if areas else 0
    for segs, area in zip(contours, areas):
        n = len(segs)
        if n < 3 or area * outer <= 0:  # a counter: its small inner corners are not what a reader sees as a fault
            continue
        turns = [turn(tangent_in(segs[i - 1]), tangent_out(segs[i])) for i in range(n)]  # turn at the start of seg i
        for i, (kind, pts) in enumerate(segs):
            a, b = turns[i], turns[(i + 1) % n]
            length = math.dist(pts[0], pts[-1])
            if kind == "line" and MIN_STEP < length < LEDGE * H and a > TURN and b > TURN:
                faults.append(("ledge", pts[0], round(length)))
            if kind == "curve" and segs[i - 1][0] == "curve" and a > TURN:
                faults.append(("cusp", pts[0], round(a)))
    return faults


def raster(path, scale):
    """The merged outline as a boolean array (even-odd), with its origin: (array, x0, y1, pad)."""
    x0, y0, x1, y1 = path.bounds
    pad = 2
    size = (int((x1 - x0) * scale) + 2 * pad, int((y1 - y0) * scale) + 2 * pad)
    ink = np.zeros(size[::-1], bool)
    for contour in path.contours:
        pts = []
        for verb, ps in contour.segments:
            if verb == "moveTo":
                pts = [ps[0]]
            elif verb == "lineTo":
                pts.append(ps[0])
            elif verb == "curveTo":
                a, b, c, d = pts[-1], *ps
                for k in range(1, 13):
                    t, mt = k / 12, 1 - k / 12
                    pts.append(tuple(mt ** 3 * a[j] + 3 * mt * mt * t * b[j] + 3 * mt * t * t * c[j] + t ** 3 * d[j] for j in (0, 1)))
            elif verb == "qCurveTo":
                pts.extend(ps)
        if len(pts) > 2:
            layer = Image.new("1", size, 0)
            ImageDraw.Draw(layer).polygon([((x - x0) * scale + pad, (y1 - y) * scale + pad) for x, y in pts], fill=1)
            ink ^= np.array(layer)
    return ink, x0, y1, pad


def erode(ink, k):
    """Square erosion by k pixels each way, separably."""
    if k < 1:
        return ink
    padded = np.pad(ink, k, constant_values=False)
    rows = sliding_window_view(padded, 2 * k + 1, axis=1).all(axis=-1)
    return sliding_window_view(rows, 2 * k + 1, axis=0).all(axis=-1)


def heavy_spot(path, V):
    """Where ink is thicker than HEAVY stems, if anywhere: (x, y) in font units."""
    if not path.bounds:
        return None
    ink, x0, y1, pad = raster(path, SCALE)
    left = erode(ink, int(HEAVY * V / 2 * SCALE))  # ink this far from every edge is too thick
    ys, xs = np.nonzero(left)
    if not len(xs):
        return None
    return round((xs.mean() - pad) / SCALE + x0), round(y1 - (ys.mean() - pad) / SCALE)


def check(style):
    G.set_style(style)
    found = []
    for wght, stem in build.MASTERS.items():
        p = G.P(wght, stem)
        for name, (_, fn) in G.GLYPHS.items():
            base = G.BASE.get(name, name)
            contours = fn(p)[0]
            if not contours:
                continue
            path = merged(contours)
            for kind, at, size in outline_faults(path, p.H):
                if kind == "cusp" and base in WAISTS or kind in ALLOW.get(base, ()):
                    continue
                if G.STYLE.get("notch") and base in SHOULDERS and kind in ("ledge", "cusp"):
                    continue
                found.append((name, wght, kind, at, size))
            if base not in DIAGONALS:
                spot = heavy_spot(path, p.V)
                if spot:
                    found.append((name, wght, "heavy", spot, ""))
    return found


if __name__ == "__main__":
    style = G.STYLE["name"]
    faults = check(style)
    for name, wght, kind, (x, y), size in faults:
        print(f"{style} {wght} {name:10} {kind:5} at ({x:.0f}, {y:.0f}) {size}")
    print(f"{len(faults)} shape faults in {len(G.GLYPHS)} glyphs x {len(build.MASTERS)} masters")
    sys.exit(1 if faults else 0)
