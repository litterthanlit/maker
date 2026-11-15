"""Outline primitives.

A contour is a list: [start_point, seg, seg, ...] and is implicitly closed.
Each seg is ("l", p) or ("c", c1, c2, p). Outer contours run counter-clockwise
(PostScript convention), counters run clockwise. The build step reverses
everything for TrueType.

Every primitive emits the same number and kind of points for any parameter
values. That keeps masters of different weights compatible for interpolation.
"""

import math

from fontTools.misc.bezierTools import splitCubicAtT


def rect(x0, y0, x1, y1):
    return [(x0, y0), ("l", (x1, y0)), ("l", (x1, y1)), ("l", (x0, y1))]


def poly(*pts):
    """Polygon from points, normalised to counter-clockwise."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts = pts[::-1]
    return [pts[0]] + [("l", p) for p in pts[1:]]


def diag(x_bot, y_bot, x_top, y_top, w, anchor="left"):
    """A straight stroke with horizontal cuts at y_bot and y_top.

    x_bot / x_top locate the stroke's `anchor` edge ("left", "right" or
    "center") at each end; w is the stroke thickness measured perpendicular
    to the stroke.
    """
    dx, dy = x_top - x_bot, y_top - y_bot
    hw = w * math.hypot(dx, dy) / abs(dy)
    off = {"left": 0.0, "center": -hw / 2, "right": -hw}[anchor]
    a, b = x_bot + off, x_top + off
    return poly((a, y_bot), (a + hw, y_bot), (b + hw, y_top), (b, y_top))


def diag_hw(dx, dy, w):
    """Horizontal width of a stroke of thickness w with the given slope."""
    return w * math.hypot(dx, dy) / abs(dy)


def solve_hw(w, dy, span_fn, iters=6):
    """Horizontal width of a diagonal whose horizontal run depends on that width."""
    hw = w
    for _ in range(iters):
        hw = diag_hw(span_fn(hw), dy, w)
    return hw


class Ellipse:
    """Superellipse made of four cubic quadrants, counter-clockwise from the right.

    seg 0: right -> top, 1: top -> left, 2: left -> bottom, 3: bottom -> right.
    k is the handle ratio (0.552 = circle, larger = squarer). It may be a single
    value or one per quadrant.
    """

    def __init__(self, left, bottom, right, top, k=0.6):
        self.l, self.b, self.r, self.t = left, bottom, right, top
        self.cx, self.cy = (left + right) / 2, (bottom + top) / 2
        self.rx, self.ry = (right - left) / 2, (top - bottom) / 2
        self.k = k if isinstance(k, (list, tuple)) else (k, k, k, k)

    def seg(self, i):
        i %= 4
        cx, cy, rx, ry, k = self.cx, self.cy, self.rx, self.ry, self.k[i]
        if i == 0:
            return ((cx + rx, cy), (cx + rx, cy + k * ry), (cx + k * rx, cy + ry), (cx, cy + ry))
        if i == 1:
            return ((cx, cy + ry), (cx - k * rx, cy + ry), (cx - rx, cy + k * ry), (cx - rx, cy))
        if i == 2:
            return ((cx - rx, cy), (cx - rx, cy - k * ry), (cx - k * rx, cy - ry), (cx, cy - ry))
        return ((cx, cy - ry), (cx + k * rx, cy - ry), (cx + rx, cy - k * ry), (cx + rx, cy))

    def _solve(self, i, axis, value):
        c = self.seg(i)
        f = lambda t: _pt(c, t)[axis]
        lo, hi = 0.0, 1.0
        flo = f(lo)
        for _ in range(60):
            mid = (lo + hi) / 2
            if (f(mid) - value) * (flo - value) > 0:
                lo, flo = mid, f(mid)
            else:
                hi = mid
        return (lo + hi) / 2

    def at_y(self, i, y):
        """Position on quadrant i where the outline crosses height y."""
        return (i, self._solve(i, 1, y))

    def at_x(self, i, x):
        return (i, self._solve(i, 0, x))

    def point(self, pos):
        i, t = pos
        return _pt(self.seg(i), t)

    def x_at(self, y, side="right"):
        cy = self.cy
        if side == "right":
            i = 0 if y >= cy else 3
        else:
            i = 1 if y >= cy else 2
        return self.point(self.at_y(i, y))[0]

    def path(self, a, b):
        """Cubic pieces from position a to b, counter-clockwise.

        Positions are (quadrant, t). b's quadrant may exceed 3 to wrap around.
        """
        (ia, ta), (ib, tb) = a, b
        while ib < ia or (ib == ia and tb < ta):
            ib += 4
        out = []
        for i in range(ia, ib + 1):
            t0 = ta if i == ia else 0.0
            t1 = tb if i == ib else 1.0
            out.append(_sub(self.seg(i), t0, t1))
        return out

    def contour(self):
        return [self.seg(0)[0]] + [("c",) + self.seg(i)[1:] for i in range(4)]


def _pt(c, t):
    mt = 1 - t
    return tuple(
        mt**3 * c[0][j] + 3 * mt * mt * t * c[1][j] + 3 * mt * t * t * c[2][j] + t**3 * c[3][j]
        for j in (0, 1)
    )


def _sub(c, t0, t1):
    if t0 == 0.0 and t1 == 1.0:
        return c
    if t0 == 0.0:
        return splitCubicAtT(*c, t1)[0]
    if t1 == 1.0:
        return splitCubicAtT(*c, t0)[1]
    return splitCubicAtT(*c, t0, t1)[1]


def _rev(c):
    return (c[3], c[2], c[1], c[0])


def band(outer, inner, a, b, ai=None, bi=None):
    """An open stroke between two ellipses, running counter-clockwise from a to b.

    a/b are positions on the outer ellipse, ai/bi on the inner one (they default
    to the same quadrant/t). The ends are straight lines joining outer to inner.
    """
    ai = ai or a
    bi = bi or b
    o = outer.path(a, b)
    n = [_rev(c) for c in reversed(inner.path(ai, bi))]
    contour = [o[0][0]]
    contour += [("c",) + c[1:] for c in o]
    contour.append(("l", n[0][0]))
    contour += [("c",) + c[1:] for c in n]
    return contour


def ring(outer, inner):
    return [outer.contour(), reverse(inner.contour())]


def reverse(contour):
    """Reverse a contour's direction, keeping its segment types."""
    pts = [contour[0]] + [s[-1] for s in contour[1:]]
    segs = contour[1:]
    out = [pts[0]]
    if pts[-1] != pts[0]:
        out.append(("l", pts[-1]))  # the implicit closing line, reversed
    for i in range(len(segs) - 1, -1, -1):
        s, dest = segs[i], pts[i]
        out.append(("l", dest) if s[0] == "l" else ("c", s[2], s[1], dest))
    if out[-1][0] == "l":
        out.pop()  # lands on the start point; closure is implicit
    return out


def transform(contours, a=1, b=0, c=0, d=1, e=0, f=0):
    """Affine transform x' = a*x + c*y + e, y' = b*x + d*y + f."""

    def tp(p):
        return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)

    out = []
    for con in contours:
        new = [tp(con[0])] + [(s[0],) + tuple(tp(p) for p in s[1:]) for s in con[1:]]
        if a * d - b * c < 0:
            new = reverse(new)
        out.append(new)
    return out


def mirror_x(contours, width):
    return transform(contours, a=-1, e=width)


def flip_y(contours, axis_y):
    return transform(contours, d=-1, f=2 * axis_y)


def rotate180(contours, cx, cy):
    return transform(contours, a=-1, d=-1, e=2 * cx, f=2 * cy)


def rotate(contours, angle_deg, cx, cy):
    r = math.radians(angle_deg)
    co, si = math.cos(r), math.sin(r)
    return transform(contours, a=co, b=si, c=-si, d=co,
                     e=cx - co * cx + si * cy, f=cy - si * cx - co * cy)


def translate(contours, dx, dy=0):
    return transform(contours, e=dx, f=dy)


def bounds(contours):
    xs = [p[0] for con in contours for p in [con[0]] + [s[-1] for s in con[1:]]]
    ys = [p[1] for con in contours for p in [con[0]] + [s[-1] for s in con[1:]]]
    return min(xs), min(ys), max(xs), max(ys)


def stroke(p0, p1, w, cut0=("p",), cut1=("p",)):
    """A straight stroke of thickness w along the centreline p0 -> p1.

    Each end is cut by: ("h", y) a horizontal line, ("v", x) a vertical line,
    or ("p",) square to the stroke at the endpoint.
    """
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy * w / 2, ux * w / 2

    def end(p, cut):
        a = (p[0] + nx, p[1] + ny)
        b = (p[0] - nx, p[1] - ny)
        if cut[0] == "p":
            return a, b
        axis = 1 if cut[0] == "h" else 0
        val = cut[1]
        out = []
        for q in (a, b):
            d = (ux, uy)[axis]
            s = (val - q[axis]) / d
            out.append((q[0] + ux * s, q[1] + uy * s))
        return tuple(out)

    a0, b0 = end(p0, cut0)
    a1, b1 = end(p1, cut1)
    return poly(a0, b0, b1, a1)
