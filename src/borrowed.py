"""Glyphs taken from an open-licence (OFL) base font, fitted to Litt's numbers.

Following the make-font skill (design.how): outlines come from an open font;
only numbers are matched. For each Litt master the base's weight axis is solved
so its stem matches Litt's stem after scaling, the glyph is scaled to Litt's
x-height (or cap height), and its sidebearings scale with it. A variable base
gives every weight the same points in the same order, so Litt's masters stay
compatible.

The base's licence travels with the font: see LICENSES/ and FONTLOG.md.
"""

import os
from functools import lru_cache

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from geometry import reverse, translate

HERE = os.path.dirname(__file__)
BASE = os.path.join(HERE, "data", "base")


@lru_cache(maxsize=None)
def _instance(path, wght):
    return instantiateVariableFont(TTFont(path), {"wght": wght}, inplace=False)


def _stem(font, glyph="n"):
    """Thickness of the left stem of n at mid x-height, by scanning the outline."""
    gs = font.getGlyphSet()
    rec = RecordingPen()
    gs[glyph].draw(rec)
    pen = BoundsPen(gs)
    gs[glyph].draw(pen)
    x0, y0, x1, y1 = pen.bounds
    y = (y0 + y1) * 0.35
    xs = []
    pts = []
    for op, args in rec.value:
        if op == "moveTo":
            pts = [args[0]]
        elif op in ("lineTo", "qCurveTo", "curveTo"):
            pts += list(args)
        elif op == "closePath" and pts:
            ring = pts + pts[:1]
            for a, b in zip(ring, ring[1:]):
                if (a[1] - y) * (b[1] - y) < 0:
                    xs.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
    xs.sort()
    return xs[1] - xs[0] if len(xs) >= 2 else 0


def _xheight(font):
    return font["OS/2"].sxHeight or 500


def _cap(font):
    return font["OS/2"].sCapHeight or 700


def solve_weight(path, target_stem, scale_of, lo=None, hi=None):
    """Base weight whose n stem, after Litt's scaling, equals target_stem."""
    f = TTFont(path)
    ax = next(a for a in f["fvar"].axes if a.axisTag == "wght")
    lo, hi = lo or ax.minValue, hi or ax.maxValue
    for _ in range(30):
        mid = (lo + hi) / 2
        inst = _instance(path, round(mid, 2))
        s = _stem(inst) * scale_of(inst)
        if s < target_stem:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 2)


def take(path, glyph, target_stem, target_height, use="x"):
    """Litt-ready contours for `glyph` from the base at path: (contours, ink, (lsb, rsb))."""
    scale_of = (lambda f: target_height / _xheight(f)) if use == "x" else (lambda f: target_height / _cap(f))
    w = solve_weight(path, target_stem, scale_of)
    f = _instance(path, w)
    k = scale_of(f)
    gs = f.getGlyphSet()
    rec = RecordingPen()
    gs[glyph].draw(rec)
    adv = f["hmtx"][glyph][0]
    contours, cur, start = [], None, None

    def sc(p):
        return (p[0] * k, p[1] * k)

    for op, args in rec.value:
        if op == "moveTo":
            cur = [sc(args[0])]
            start = sc(args[0])
            last = start
        elif op == "lineTo":
            cur.append(("l", sc(args[0])))
            last = sc(args[0])
        elif op == "qCurveTo":
            # a TrueType quadratic spline: implied on-curve points between off-curves
            offs = [sc(a) for a in args[:-1]]
            end = sc(args[-1]) if args[-1] is not None else start
            for i, q in enumerate(offs):
                nxt = end if i == len(offs) - 1 else ((q[0] + offs[i + 1][0]) / 2, (q[1] + offs[i + 1][1]) / 2)
                c1 = (last[0] + 2 / 3 * (q[0] - last[0]), last[1] + 2 / 3 * (q[1] - last[1]))
                c2 = (nxt[0] + 2 / 3 * (q[0] - nxt[0]), nxt[1] + 2 / 3 * (q[1] - nxt[1]))
                cur.append(("c", c1, c2, nxt))
                last = nxt
        elif op == "curveTo":
            a, b, c = (sc(x) for x in args)
            cur.append(("c", a, b, c))
            last = c
        elif op in ("closePath", "endPath"):
            if cur and cur[-1][-1] == cur[0] and cur[-1][0] == "l":
                cur.pop()  # closing line onto the start is implicit
            contours.append(reverse(cur))  # TrueType runs outer contours clockwise; Litt draws them counter-clockwise
            cur = None
    pen = BoundsPen(gs)
    gs[glyph].draw(pen)
    x0, _, x1, _ = pen.bounds
    lsb, rsb = x0 * k, (adv - x1) * k
    return translate(contours, -x0 * k), (x1 - x0) * k, (lsb, rsb), w


@lru_cache(maxsize=None)
def glyph_for(path, char):
    """The base font's glyph name for a character, by its cmap."""
    return TTFont(path).getBestCmap()[ord(char)]
