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


def rounded(*corners, smooth=0.0):
    """A polygon whose corners are rounded: rounded((x, y, r), (x, y, r), ...).

    Points run counter-clockwise for an outline, clockwise for a counter.
    Each corner with r > 0 becomes a circular arc tangent to both edges; r = 0
    stays sharp. A corner's kind (sharp or round) must not change between
    masters, so give a round corner a small radius rather than 0.

    smooth (0 to 1) starts each curve further back along the sides, with
    longer handles, so the curve eases out of the straight edge instead of
    joining it as a circle does: a softer corner at the same radius.
    """
    n = len(corners)
    pts = [(c[0], c[1]) for c in corners]
    pieces = []
    for i, (x, y, r) in enumerate(corners):
        a, b = pts[i - 1], pts[(i + 1) % n]
        if r <= 0:
            pieces.append(None)
            continue
        ua = _unit((a[0] - x, a[1] - y))
        ub = _unit((b[0] - x, b[1] - y))
        theta = math.acos(max(-1.0, min(1.0, ua[0] * ub[0] + ua[1] * ub[1])))  # interior angle
        t = r / math.tan(theta / 2) * (1 + 0.6 * smooth)
        t = min(t, 0.5 * math.dist(a, (x, y)), 0.5 * math.dist(b, (x, y)))
        r = t * math.tan(theta / 2) / (1 + 0.6 * smooth)
        h = 4 / 3 * math.tan((math.pi - theta) / 4) * r * (1 + 0.6 * smooth) * (1 + 0.22 * smooth)
        t1 = (x + ua[0] * t, y + ua[1] * t)
        t2 = (x + ub[0] * t, y + ub[1] * t)
        c1 = (t1[0] - ua[0] * h, t1[1] - ua[1] * h)
        c2 = (t2[0] - ub[0] * h, t2[1] - ub[1] * h)
        pieces.append((t1, c1, c2, t2))
    last = pieces[-1]
    out = [last[3] if last else pts[-1]]
    for i, pc in enumerate(pieces):
        if pc is None:
            out.append(("l", pts[i]))
        else:
            out.append(("l", pc[0]))
            out.append(("c", pc[1], pc[2], pc[3]))
    if out[-1][0] == "l" and out[-1][1] == out[0]:
        out.pop()
    return out


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


# --- pen strokes ---------------------------------------------------------------
# Letters that are one movement of the pen (S, 2, 3, 5, 6, 9, &, braces, ~) are
# drawn as a skeleton of cubics expanded by an elliptical pen: the stroke is V
# thick where it travels vertically and H where it travels horizontally, and
# varies smoothly between. Each skeleton cubic yields exactly one cubic per
# side, so every weight has the same point structure.

def seg(p0, h0, p1, h1):
    """A skeleton cubic from p0 to p1: h0 is the handle leaving p0, h1 the
    handle arriving at p1 (so the second control point is p1 - h1)."""
    return (p0, (p0[0] + h0[0], p0[1] + h0[1]), (p1[0] - h1[0], p1[1] - h1[1]), p1)


def _d(c, t):
    mt = 1 - t
    return tuple(3 * mt * mt * (c[1][j] - c[0][j]) + 6 * mt * t * (c[2][j] - c[1][j]) + 3 * t * t * (c[3][j] - c[2][j])
                 for j in (0, 1))


def _unit(v):
    l = math.hypot(*v)
    return (v[0] / l, v[1] / l)


def _tangent_at(c, t):
    d = _d(c, t)
    if math.hypot(*d) < 1e-9:  # a handle sits on its point: look a little inward
        d = _d(c, min(max(t, 0.02), 0.98))
    return _unit(d)


def _fit(samples, ts, t0, t1):
    """Least-squares cubic through samples with fixed ends and end directions."""
    s0, s1 = samples[0], samples[-1]
    m = [[0.0, 0.0], [0.0, 0.0]]
    r = [0.0, 0.0]
    for s, t in zip(samples, ts):
        mt = 1 - t
        b0, b1, b2, b3 = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
        base = [(b0 + b1) * s0[j] + (b2 + b3) * s1[j] for j in (0, 1)]
        res = [s[j] - base[j] for j in (0, 1)]
        u = [b1 * t0[j] for j in (0, 1)]
        v = [-b2 * t1[j] for j in (0, 1)]
        m[0][0] += u[0] * u[0] + u[1] * u[1]
        m[0][1] += u[0] * v[0] + u[1] * v[1]
        m[1][1] += v[0] * v[0] + v[1] * v[1]
        r[0] += u[0] * res[0] + u[1] * res[1]
        r[1] += v[0] * res[0] + v[1] * res[1]
    m[1][0] = m[0][1]
    det = m[0][0] * m[1][1] - m[0][1] * m[1][0]
    chord = math.hypot(s1[0] - s0[0], s1[1] - s0[1])
    if abs(det) < 1e-9:
        a = b = chord / 3
    else:
        a = (r[0] * m[1][1] - r[1] * m[0][1]) / det
        b = (m[0][0] * r[1] - m[1][0] * r[0]) / det
    floor = chord * 0.05
    a, b = max(a, floor), max(b, floor)
    return [s0, (s0[0] + a * t0[0], s0[1] + a * t0[1]), (s1[0] - b * t1[0], s1[1] - b * t1[1]), s1]


def _cut(curve, end, outward, cut):
    """Bring one end of a fitted side curve onto a cut line ("line", point,
    direction). A side that falls short is extended along its tangent; a side
    that overshoots is trimmed where the curve itself crosses the line."""
    if cut[0] == "p":
        return curve
    _, P, u = cut
    cross = lambda a, b: a[0] * b[1] - a[1] * b[0]
    i, j = (0, 1) if end == 0 else (3, 2)
    E = curve[i]
    den = cross(outward, u)
    if abs(den) < 1e-9:
        return curve
    s = cross((P[0] - E[0], P[1] - E[1]), u) / den
    if s >= 0:
        dx, dy = outward[0] * s, outward[1] * s
        curve = list(curve)
        curve[i] = (E[0] + dx, E[1] + dy)
        curve[j] = (curve[j][0] + dx, curve[j][1] + dy)
        return curve
    c = tuple(tuple(q) for q in curve)
    f = lambda t: cross((_pt(c, t)[0] - P[0], _pt(c, t)[1] - P[1]), u)
    a, b = (1.0, 0.0) if end == 1 else (0.0, 1.0)
    fa = f(a)
    for _ in range(50):
        m = (a + b) / 2
        if (f(m) > 0) == (fa > 0):
            a, fa = m, f(m)
        else:
            b = m
    t = (a + b) / 2
    return list(splitCubicAtT(*c, t)[0] if end == 1 else splitCubicAtT(*c, t)[1])


def pen(skeleton, V, H, cap0=("p",), cap1=("p",), n=16):
    """Expand a skeleton (a list of joined cubics) into one closed contour.

    Ends are cut square to the stroke ("p",), level ("h", y) or upright ("v", x).
    """
    left, right = [], []
    for c in skeleton:
        ts = [k / n for k in range(n + 1)]
        ls, rs = [], []
        for t in ts:
            p = _pt(c, t)
            tx, ty = _tangent_at(c, t)
            # full stem weight once the stroke climbs past ~30 deg; thin only
            # where it runs close to level, as type designers weight spines
            s = min(1.0, abs(ty) / 0.5)
            s = s * s * (3 - 2 * s)
            half = 0.5 * (H + (V - H) * s)
            nx, ny = -ty * half, tx * half
            ls.append((p[0] + nx, p[1] + ny))
            rs.append((p[0] - nx, p[1] - ny))
        ta, tb = _tangent_at(c, 0.0), _tangent_at(c, 1.0)
        left.append(_fit(ls, ts, ta, tb))
        right.append(_fit(rs, ts, ta, tb))
    t_start = _tangent_at(skeleton[0], 0.0)
    t_end = _tangent_at(skeleton[-1], 1.0)

    def line(cap, pt, tang):
        """Turn a cap into a cut line through the skeleton's end.
        ("h", y) / ("v", x): level / upright through that coordinate.
        ("H", tilt) / ("V", tilt): level / upright through the end, turned
        `tilt` of the way toward square to the stroke (0 = exactly level)."""
        kind = cap[0]
        if kind == "p":
            return cap
        if kind == "h":
            return ("line", (pt[0], cap[1]), (1.0, 0.0))
        if kind == "v":
            return ("line", (cap[1], pt[1]), (0.0, 1.0))
        tilt = cap[1] if len(cap) > 1 else 0.0
        base = 0.0 if kind == "H" else math.pi / 2
        square = math.atan2(tang[1], tang[0]) + math.pi / 2
        diff = math.atan2(math.sin(square - base), math.cos(square - base))
        if abs(diff) > math.pi / 2:  # a line has no direction: take the nearer turn
            diff -= math.copysign(math.pi, diff)
        ang = base + diff * tilt
        return ("line", pt, (math.cos(ang), math.sin(ang)))

    def trim_only(cap, a, b, outward):
        """Move a terminal's cut back to the side that ends first, so the other
        side is trimmed along its own curve and neither is extended (a straight
        extension reads as a spur)."""
        if cap[0] != "line":
            return cap
        _, P, u = cap
        proj = lambda q: (q[0] - P[0]) * outward[0] + (q[1] - P[1]) * outward[1]
        # where along the stroke each side meets the line
        cross = lambda p, q: p[0] * q[1] - p[1] * q[0]
        den = cross(outward, u)
        if abs(den) < 1e-9:
            return cap
        s_a = cross((P[0] - a[0], P[1] - a[1]), u) / den
        s_b = cross((P[0] - b[0], P[1] - b[1]), u) / den
        shift = min(0.0, -max(s_a, s_b))  # pull the line back until neither side must grow
        return ("line", (P[0] + outward[0] * shift, P[1] + outward[1] * shift), u)

    back = (-t_start[0], -t_start[1])
    terminal0, terminal1 = cap0[0] in ("H", "V"), cap1[0] in ("H", "V")
    cap0 = line(cap0, skeleton[0][0], t_start)
    cap1 = line(cap1, skeleton[-1][3], t_end)
    if terminal0 and cap0[0] == "line" and abs(cap0[2][1]) < 0.9:  # level-ish terminal cuts only
        cap0 = trim_only(cap0, left[0][0], right[0][0], back)
    if terminal1 and cap1[0] == "line" and abs(cap1[2][1]) < 0.9:
        cap1 = trim_only(cap1, left[-1][3], right[-1][3], t_end)
    left[0] = _cut(left[0], 0, back, cap0)
    right[0] = _cut(right[0], 0, back, cap0)
    left[-1] = _cut(left[-1], 1, t_end, cap1)
    right[-1] = _cut(right[-1], 1, t_end, cap1)
    con = [tuple(left[0][0])]
    for c in left:
        con.append(("c", tuple(c[1]), tuple(c[2]), tuple(c[3])))
    con.append(("l", tuple(right[-1][3])))
    for c in reversed(right):
        con.append(("c", tuple(c[2]), tuple(c[1]), tuple(c[0])))
    # travelling along the left side and back along the right runs clockwise
    return reverse(con)
