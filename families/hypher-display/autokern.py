"""Kerning measured from Hypher Display's own outlines.

For a pair, take each row the two glyphs share and measure the empty space
between the left glyph's right edge and the right glyph's left edge, beyond
their sidebearings: the recess. Counters deeper than DEPTH are not space a
reader sees between letters, so each side's recess is clipped there. A pair
is scored by 0.6 of its mean recess plus 0.4 of its narrowest, and kerned by
the difference from a reference pair whose sides have the same shape (the
spacing already allows for those): T before o is compared with v before o, so
T tucks over the o, while v before v, already spaced for its slant, is left
alone. Kerning only closes space, never opens it.
"""

import pathops

STEP = 8  # row height, in font units
MIN_KERN = 10  # smaller kerns are noise
MAX_KERN = 0.22  # of the em


def profile(contours, lo, hi):
    """{row y: (leftmost x, rightmost x)} for the ink of a glyph drawn at x = 0."""
    p = pathops.Path()
    pen = p.getPen()
    for c in contours:
        pen.moveTo(c[0])
        for s in c[1:]:
            pen.lineTo(s[1]) if s[0] == "l" else pen.curveTo(*s[1:])
        pen.closePath()
    p.simplify(fix_winding=True)
    segs = []
    for contour in p.contours:
        pts = []
        for verb, points in contour.segments:
            if verb in ("moveTo", "lineTo"):
                pts.append(points[0])
            elif verb == "curveTo":  # flatten
                a = pts[-1]
                b, c, d = points
                for i in range(1, 9):
                    t = i / 8
                    mt = 1 - t
                    pts.append(tuple(mt ** 3 * a[j] + 3 * mt * mt * t * b[j] + 3 * mt * t * t * c[j] + t ** 3 * d[j] for j in (0, 1)))
            elif verb == "qCurveTo":
                pts.extend(points)
        segs += list(zip(pts, pts[1:] + pts[:1]))
    out = {}
    y = lo
    while y <= hi:
        xs = [a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) for a, b in segs if (a[1] - y) * (b[1] - y) < 0]
        if xs:
            out[y] = (min(xs), max(xs))
        y += STEP
    return out


def pairs(glyphs, params, _unused, depth, refs, types, candidates):
    """Kerning for candidates (left, right) as {pair: value}.

    glyphs: name -> fn(params); refs: {"left": type -> glyph whose left side is that type,
    "right": type -> glyph whose right side is that type}; types: name -> side types (left, right).
    """
    shapes = {}

    def shape(name):
        if name not in shapes:
            contours, ink, _ = glyphs[name](params)
            shapes[name] = (profile(contours, -260, 1000), ink)
        return shapes[name]

    def score(l, r):
        (pl, wl), (pr, _) = shape(l), shape(r)
        rows = [y for y in pl if y in pr]
        if not rows:
            return None
        recess = [min(wl - pl[y][1], depth) + min(pr[y][0], depth) for y in rows]
        return 0.6 * sum(recess) / len(recess) + 0.4 * min(recess)

    out = {}
    for l, r in candidates:
        if l not in types or r not in types:
            continue
        s = score(l, r)
        ref = score(refs["right"][types[l][1]], refs["left"][types[r][0]])
        if s is None or ref is None:
            continue
        k = round(max(-(s - ref), -MAX_KERN * 1000))
        if k <= -MIN_KERN:
            out[(l, r)] = k
    return out
