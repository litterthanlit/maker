"""Hypher's glyphs: Michroma's outlines (OFL), weighted by offsetting every edge.

Regular is Michroma unchanged, so the word set in Hypher Regular is the brand
lockup. Other weights move each edge of the outline outward (bolder) or
inward (lighter) by the same distance, the way FreeType emboldens a glyph,
then remap heights so the baseline, x-height and ascender stay where they
were. Points are moved, never added, so every weight has the same points in
the same order and the masters interpolate.
"""

import math
import os
from functools import lru_cache

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from core.geometry import reverse, translate

BASE = os.path.join(os.path.dirname(__file__), "data", "base", "Michroma-Regular.ttf")
UPM = 2048
XH, CH, ASC, DSC = 1152, 1536, 1536, -384

# The lockup sets Michroma 0.080em looser than its own spacing, the same
# between every pair. Half goes on each side of every glyph.
TRACK = round(0.080 * UPM)

REGULAR_STEM = 192  # Michroma's n stem
CONTRAST = 0.75  # horizontals gain or lose this fraction of what verticals do

LOWER = "abcdefghijklmnopqrstuvwxyz"
CHARS = LOWER + " .-"


class P:
    """Weight parameters: dx is how far each vertical edge moves, dy each horizontal one."""

    def __init__(self, wght, stem):
        self.wght = wght
        self.dx = (stem - REGULAR_STEM) / 2
        self.dy = self.dx * CONTRAST


@lru_cache(maxsize=None)
def _font():
    return TTFont(BASE)


def _cubic_contours(name):
    """Michroma's glyph as cubic contours in maker's convention (outer counter-clockwise)."""
    f = _font()
    gs = f.getGlyphSet()
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)
    contours, cur, start, last = [], None, None, None
    for op, args in rec.value:
        if op == "moveTo":
            cur, start, last = [args[0]], args[0], args[0]
        elif op == "lineTo":
            if math.dist(args[0], last) < 2:
                continue  # Michroma's m has a 1-unit step that offsets into a hook
            cur.append(("l", args[0]))
            last = args[0]
        elif op == "qCurveTo":
            offs = list(args[:-1])
            end = args[-1] if args[-1] is not None else start
            for i, q in enumerate(offs):
                nxt = end if i == len(offs) - 1 else ((q[0] + offs[i + 1][0]) / 2, (q[1] + offs[i + 1][1]) / 2)
                c1 = (last[0] + 2 / 3 * (q[0] - last[0]), last[1] + 2 / 3 * (q[1] - last[1]))
                c2 = (nxt[0] + 2 / 3 * (q[0] - nxt[0]), nxt[1] + 2 / 3 * (q[1] - nxt[1]))
                cur.append(("c", c1, c2, nxt))
                last = nxt
        elif op in ("closePath", "endPath"):
            if cur[-1][-1] == cur[0] and cur[-1][0] == "l":
                cur.pop()  # the closing line back to the start is implicit
            contours.append(reverse(cur))  # TrueType runs outer contours clockwise
            cur = None
    return contours


def _points(contour):
    pts = [contour[0]]
    for seg in contour[1:]:
        pts += list(seg[1:])
    return pts


def _on_curve(contour):
    flags = [True]
    for seg in contour[1:]:
        flags += [False] * (len(seg) - 2) + [True]
    return flags


def _rebuild(contour, pts):
    it = iter(pts)
    out = [next(it)]
    for seg in contour[1:]:
        out.append((seg[0],) + tuple(next(it) for _ in seg[1:]))
    return out


def _signed_area(pts):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2


def _offset(contour, dx, dy):
    """Move every edge of a contour outward by dx horizontally and dy vertically.

    Each point, on-curve or control, moves along the bisector of its two
    neighbouring edges, by the distance that shifts both edges by one unit;
    the result is then scaled to (dx, dy). Counters run the other way, so
    they shrink as the outer contour grows.
    """
    pts = _points(contour)
    on = _on_curve(contour)
    n = len(pts)

    def neighbour(i, step):
        j = (i + step) % n
        while math.dist(pts[j], pts[i]) < 1e-6 and j != i:
            j = (j + step) % n
        return j

    out = []
    for i, p in enumerate(pts):
        ia, ib = neighbour(i, -1), neighbour(i, 1)
        a, b = pts[ia], pts[ib]
        line1, line2 = on[i] and on[ia], on[i] and on[ib]  # a straight edge joins two on-curve points
        e1 = ((p[0] - a[0]), (p[1] - a[1]))
        e2 = ((b[0] - p[0]), (b[1] - p[1]))
        l1, l2 = math.hypot(*e1), math.hypot(*e2)
        n1 = (e1[1] / l1, -e1[0] / l1)  # right of travel: outward on a counter-clockwise contour
        n2 = (e2[1] / l2, -e2[0] / l2)
        d = 1 + n1[0] * n2[0] + n1[1] * n2[1]
        if d < 0.5 and line1 != line2:
            # A hairpin where a curve doubles back into a straight edge (the
            # a's bowl into its stem): the bisector would throw the point far
            # off and fold the curve into a hook. Slide it with the line.
            sx, sy = n1 if line1 else n2
        else:
            # Straight corners, however sharp (the k's arms), take the miter.
            d = max(d, 0.2)
            sx, sy = (n1[0] + n2[0]) / d, (n1[1] + n2[1]) / d
        mx, my = sx * dx, sy * dy
        if d < 0.5 and line1 and line2:
            # ...but never past another corner: the k's crotch points sit 58
            # units apart on the stem and would cross when it gets lighter.
            # Shorten only the slide along the edge that points at the crowding
            # corner, so the point stays on that edge's offset line.
            q = min((q for k, q in enumerate(pts) if on[k] and k != i), key=lambda q: math.dist(p, q))
            room = 0.45 * math.dist(p, q)
            v = (q[0] - p[0], q[1] - p[1])
            e, l = max(((e1, l1), (e2, l2)), key=lambda el: abs(el[0][0] * v[0] + el[0][1] * v[1]) / el[1])
            t = (e[0] / l, e[1] / l)
            along = mx * t[0] + my * t[1]
            if abs(along) > room:
                cut = along - math.copysign(room, along)
                mx, my = mx - cut * t[0], my - cut * t[1]
        out.append((p[0] + mx, p[1] + my))
    # A short straight edge between two sharp corners (the k's stem between
    # its arms) can flip when both ends move toward each other; the true
    # offset has no edge there, so collapse it to its midpoint.
    for i in range(n):
        j = (i + 1) % n
        if on[i] and on[j]:
            e0 = (pts[j][0] - pts[i][0], pts[j][1] - pts[i][1])
            e1 = (out[j][0] - out[i][0], out[j][1] - out[i][1])
            if e0[0] * e1[0] + e0[1] * e1[1] < 0:
                mid = ((out[i][0] + out[j][0]) / 2, (out[i][1] + out[j][1]) / 2)
                out[i] = out[j] = mid
    return _rebuild(contour, out)


def _remap_y(y, dy, top):
    """Pull the grown outline back so baseline and `top` (and everything above it) don't move."""
    if y <= -dy:
        return y + dy
    if y >= top + dy:
        return y - dy
    return (y + dy) * top / (top + 2 * dy)


def _weighted(contours, p, top):
    if p.dx == 0 and p.dy == 0:
        return contours
    out = []
    for c in contours:
        c = _offset(c, p.dx, p.dy)
        pts = [(x, _remap_y(y, p.dy, top)) for x, y in _points(c)]
        out.append(_rebuild(c, pts))
    return out


def _bounds_x(contours):
    xs = [x for c in contours for x, _ in _points(c)]
    return min(xs), max(xs)


def michroma(char):
    f = _font()
    name = f.getBestCmap()[ord(char)]
    contours = _cubic_contours(name)
    adv = f["hmtx"][name][0]
    pen = BoundsPen(f.getGlyphSet())
    f.getGlyphSet()[name].draw(pen)
    top = XH if char in LOWER else CH

    def draw(p):
        if not contours:  # space
            return [], 0, (adv / 2 + TRACK / 2 + p.dx, adv / 2 + TRACK / 2 + p.dx)
        x0, x1 = pen.bounds[0], pen.bounds[2]
        c = _weighted(contours, p, top)
        nx0, nx1 = _bounds_x(c)
        lsb, rsb = x0 + TRACK / 2, adv - x1 + TRACK / 2
        return translate(c, -nx0), nx1 - nx0, (lsb, rsb)

    return name, draw


GLYPHS = {}
for _ch in CHARS:
    _name, _fn = michroma(_ch)
    GLYPHS[_name] = (_ch, _fn)
