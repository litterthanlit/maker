"""Glyphs drawn as pen strokes: one movement each, expanded by an elliptical pen.

These replace the ellipse-segment constructions in glyphs.py for the shapes
that read as a single gesture. Imported at the end of glyphs.py, so each
registration overrides the earlier one under the same name.

Skeleton coordinates run along the middle of the stroke. With the pen V wide
on uprights and H on horizontals, a skeleton box inset by V/2 at the sides
and H/2 at top and bottom puts the ink exactly on the glyph's edges.
"""

import json
import math
import os

import glyphs as G
from glyphs import ASC, CH, DSC, O, XH, dot_size, fig_sb, fig_strokes, fig_width, glyph, math_sb, math_width
from fontTools.misc.bezierTools import splitCubicAtT

from geometry import _d, _pt, flip_y, mirror_x, pen, rect, rotate180, seg, translate


def _u(dx, dy):
    l = math.hypot(dx, dy)
    return dx / l, dy / l


def _box(w, bottom, top, V, H):
    """Skeleton box for ink spanning 0..w and bottom..top."""
    xl, xr = V / 2, w - V / 2
    yb, yt = bottom + H / 2, top - H / 2
    return xl, xr, yb, yt, xr - xl, yt - yb, (xl + xr) / 2


# --- shapes from research ------------------------------------------------------
# data/consensus.json holds the centre lines of 6, 9, s and S averaged across
# curved-Swiss grotesques (Helvetica via TeX Gyre Heros, Inter, Public Sans,
# Archivo and others), aligned at their structural landmarks and fitted with
# one cubic per span: see proof/research.py. Being an average of several, it
# is the genre's shared shape rather than any one font's drawing. Litt maps
# it into its own widths and strokes.

with open(os.path.join(os.path.dirname(__file__), "data", "consensus.json")) as _f:
    CONSENSUS = json.load(_f)


# fraction of the first / last span removed at a terminal
SHORTEN = {"six": (0.18, 0), "nine": (0.18, 0), "s": (0.18, 0.18), "S": (0.18, 0.18)}


def consensus_skeleton(name, w, bottom, top, V, H):
    data = CONSENSUS[name]
    xl, xr, yb, yt, sw, sh, xm = _box(w, bottom, top, V, H)
    aspect = data["aspect"]

    def m(p):
        return (xl + p[0] / aspect * sw, yb + p[1] * sh)

    sk = [tuple(m(p) for p in c) for c in data["cubics"]]
    # Stop the terminals a little early, nearer Helvetica's stopping point: the
    # averaged arcs curl further round, which closes the aperture. The ends are
    # then cut square to the stroke, which stays blunt and crisp at UI sizes.
    short = SHORTEN.get(name, (0, 0))
    if short[0]:
        sk[0] = tuple(splitCubicAtT(*sk[0], short[0])[1])
    if short[1]:
        sk[-1] = tuple(splitCubicAtT(*sk[-1], 1 - short[1])[0])
    if name in ("six", "nine"):
        # the bowl closes on the side it leaves from: end on that side's centre line
        side = xl if name == "six" else xr
        p0, c1, c2, p3 = sk[-1]
        dx = side - p3[0]
        sk[-1] = (p0, c1, (c2[0] + dx, c2[1]), (side, p3[1]))
    return sk


def from_consensus(name, w, bottom, top, V, H, cap0, cap1):
    """Caps ("p",) cut the terminals level, tilting toward square as
    the weight grows; ("V",) closes a bowl upright on its side."""
    sk = consensus_skeleton(name, w, bottom, top, V, H)
    c0, c1 = cap0, cap1
    return pen(sk, V, H, c0, c1)


# --- S and s -------------------------------------------------------------------

def s_form(w, bottom, top, V, H, top_term=0.77, bot_term=0.22, spine=24, upper=0.93):
    """An S: top-right terminal, over the top, down the left, a diagonal spine,
    round the bottom right, to the bottom-left terminal. Both terminals level."""
    xl, xr, yb, yt, sw, sh, xm = _box(w, bottom, top, V, H)
    inset = sw * (1 - upper) / 2  # the upper bowl is a little narrower
    a = math.radians(spine)
    d = (math.cos(a), -math.sin(a))
    k = 0.30 * sw
    P0 = (xr - inset - 0.03 * sw, yb + top_term * sh)
    T = (xm + 0.01 * sw, yt)
    # measured from Helvetica-class and UI grotesques: the shoulders sit at
    # 73% and 27% of the height, and the spine crosses the centre at about 24 deg
    L = (xl + inset, yb + 0.73 * sh)
    M = (xm, yb + 0.50 * sh)
    R = (xr, yb + 0.27 * sh)
    B = (xm - 0.01 * sw, yb)
    P5 = (xl + 0.03 * sw, yb + bot_term * sh)
    sk = [
        seg(P0, (-0.02 * sw, 0.13 * sh), T, (-k, 0)),
        seg(T, (-k, 0), L, (0, -0.12 * sh)),
        seg(L, (0, -0.11 * sh), M, (d[0] * 0.31 * sw, d[1] * 0.31 * sw)),
        seg(M, (d[0] * 0.31 * sw, d[1] * 0.31 * sw), R, (0, -0.11 * sh)),
        seg(R, (0, -0.12 * sh), B, (-k, 0)),
        seg(B, (-k, 0), P5, (0.02 * sw, 0.13 * sh)),
    ]
    return pen(sk, V, H, ("h", P0[1]), ("h", P5[1]))


@glyph("s", "s")
def g_s(p):
    w = p.c(272 * G.LCW, 0.35) + 2 * p.VR * 0.92
    return [from_consensus("s", w, -O, XH + O, p.VR * 0.96, p.HR * 1.02, ("p",), ("p",))], w, (p.SBR * 1.1, p.SBR * 1.1)


@glyph("S", "S")
def g_S(p):
    v = p.VC * 1.02
    w = p.c(392, 0.45) + 2 * v
    return [from_consensus("S", w, -O, CH + O, v, p.HC * 1.0, ("p",), ("p",))], w, (p.SBCR * 1.15, p.SBCR * 1.15)


# --- l ---------------------------------------------------------------------------

@glyph("l", "l")
def g_l(p):
    return [rect(0, 0, p.V, ASC)], p.V, (p.SB, p.SB)


# --- figures ---------------------------------------------------------------------

def _fig(p):
    v, h = fig_strokes(p)
    W = fig_width(p)
    return v, h, W


@glyph("two", "2")
def g_2(p):
    v, h, W = _fig(p)
    hb = p.HC
    xl, xr, yb, yt, sw, sh, xm = _box(W, -O, CH + O, v, h)
    P0 = (xl + 0.01 * sw, yb + 0.70 * sh)
    T = (xm + 0.02 * sw, yt)
    R = (xr, yb + 0.685 * sh)
    Dn = (v * 0.80, hb * 0.6)  # where the diagonal meets the base
    dd = _u(R[0] - 0.10 * sw - Dn[0], R[1] - 0.30 * sh - Dn[1])
    L = math.hypot(R[0] - Dn[0], R[1] - Dn[1])
    sk = [
        seg(P0, (0, 0.13 * sh), T, (0.31 * sw, 0)),
        seg(T, (0.31 * sw, 0), R, (0, -0.14 * sh)),
        seg(R, (0, -0.20 * sh), Dn, (-dd[0] * 0.42 * L, -dd[1] * 0.42 * L)),
    ]
    return [pen(sk, v, h, ("p",), ("h", hb * 0.9)), rect(0, 0, W, hb)], W, (fig_sb(p, W),) * 2


@glyph("three", "3")
def g_3(p):
    v, h, W = _fig(p)
    xl, xr, yb, yt, sw, sh, xm = _box(W, -O, CH + O, v, h)
    ym = yb + 0.555 * sh
    J = (xm - 0.12 * sw, ym)
    P0 = (xl + 0.03 * sw, yb + 0.77 * sh)
    T = (xm, yt)
    R1 = (xr - 0.05 * sw, yb + 0.775 * sh)
    R2 = (xr, yb + 0.28 * sh)
    B = (xm, yb)
    P5 = (xl + 0.02 * sw, yb + 0.22 * sh)
    upper = [
        seg(P0, (0, 0.12 * sh), T, (0.31 * sw, 0)),
        seg(T, (0.30 * sw, 0), R1, (0, -0.11 * sh)),
        seg(R1, (0, -0.11 * sh), J, (-0.30 * sw, 0)),
    ]
    lower = [
        seg(J, (0.32 * sw, 0), R2, (0, -0.15 * sh)),
        seg(R2, (0, -0.15 * sh), B, (-0.32 * sw, 0)),
        seg(B, (-0.32 * sw, 0), P5, (0, 0.14 * sh)),
    ]
    return [pen(upper, v, h, ("p",)), pen(lower, v, h, ("p",), ("p",))], W, (fig_sb(p, W),) * 2


@glyph("five", "5")
def g_5(p):
    v, h, W = _fig(p)
    V = p.VC
    xl, xr, yb, yt, sw, sh, xm = _box(W, -O, CH + O, v, h)
    x0 = W * 0.05  # stem's left edge
    P0 = (x0 + V * 0.5, yb + 0.50 * sh)
    Tb = (xm + 0.03 * sw, yb + 0.585 * sh)
    R = (xr, yb + 0.29 * sh)
    B = (xm, yb)
    P5 = (xl + 0.02 * sw, yb + 0.20 * sh)
    sk = [
        seg(P0, (0.09 * sw, 0.06 * sh), Tb, (0.28 * sw, 0)),
        seg(Tb, (0.29 * sw, 0), R, (0, -0.15 * sh)),
        seg(R, (0, -0.15 * sh), B, (-0.32 * sw, 0)),
        seg(B, (-0.32 * sw, 0), P5, (0, 0.14 * sh)),
    ]
    bowl = pen(sk, v, h, ("p",), ("p",))
    return [bowl, rect(x0, P0[1] - 0.04 * sh, x0 + V, CH), rect(x0, CH - p.HC, W * 0.93, CH)], W, (fig_sb(p, W),) * 2


@glyph("six", "6")
def g_6(p):
    v, h, W = _fig(p)
    return [from_consensus("six", W, -O, CH + O, v, h, ("p",), ("V",))], W, (fig_sb(p, W),) * 2


@glyph("nine", "9")
def g_9(p):
    v, h, W = _fig(p)
    return [from_consensus("nine", W, -O, CH + O, v, h, ("p",), ("V",))], W, (fig_sb(p, W),) * 2


# --- punctuation and symbols -------------------------------------------------------

def paren(p):
    V, H = p.V * 0.92, p.H * 0.9
    top, bot = ASC + 30, DSC + 10
    w = 200 + p.dV * 0.7
    xl, xr = V / 2, w - V * 0.35
    ym = (top + bot) / 2
    up, dn = top - ym, ym - bot
    sk = [
        seg((xr, top), (-(xr - xl) * 0.62, -up * 0.22), (xl, ym), (0, -up * 0.50)),
        seg((xl, ym), (0, -dn * 0.50), (xr, bot), ((xr - xl) * 0.62, -dn * 0.22)),
    ]
    c = [pen(sk, V, H, ("h", top), ("h", bot))]
    return c, w


@glyph("parenleft", "(")
def g_parenleft(p):
    c, w = paren(p)
    return c, w, (p.SBR + 22, p.SBR + 4)


@glyph("parenright", ")")
def g_parenright(p):
    c, w = paren(p)
    return mirror_x(c, w), w, (p.SBR + 4, p.SBR + 22)


@glyph("braceleft", "{")
def g_braceleft(p):
    """Arm, corner, upright, corner into a point; the lower half mirrors it."""
    V, H = p.V * 0.86, p.H * 0.86
    top, bot = ASC + 30, DSC + 10
    ym = (top + bot) / 2
    r = 72 + p.dV * 0.3  # corner radius
    tip = V * 0.5  # point's centre line starts here
    xs = tip + 92 + p.dV * 0.4  # upright's centre line
    xr = xs + r + 54 + p.dV * 0.2  # arm's end
    yt = top - H / 2
    sk = [
        seg((xr, yt), (-(xr - xs) * 0.55, 0), (xs, yt - r), (0, -r * 0.55)),
        seg((xs, yt - r), (0, -(yt - r - (ym + r)) / 3), (xs, ym + r), (0, -(yt - r - (ym + r)) / 3)),
        seg((xs, ym + r), (0, -r * 0.55), (tip, ym), (-(xs - tip) * 0.55, 0)),
    ]
    upper = pen(sk, V, H, ("v", xr), ("v", 0))
    return [upper, flip_y([upper], ym)[0]], xr, (p.SB * 0.7, p.SBD + 14)


@glyph("braceright", "}")
def g_braceright(p):
    c, w, sb = g_braceleft(p)
    return mirror_x(c, w), w, sb[::-1]


@glyph("asciitilde", "~")
def g_asciitilde(p):
    w = math_width(p) - 40
    a = 58 + p.dV * 0.1
    cy = 300
    V, H = p.H * 1.15, p.H * 1.0
    sk = [seg((V * 0.3, cy - a * 0.35), (w * 0.30, a * 2.1), (w - V * 0.3, cy + a * 0.35), (w * 0.30, a * 2.1))]
    return [pen(sk, V, H)], w, (math_sb(p, w),) * 2


@glyph("question", "?")
def g_question(p):
    v, h = p.VR * 0.98, p.HR
    W = 430 + p.dV * 0.8
    top = CH + O
    xl, xr = v / 2, W - v / 2
    yt = top - h / 2
    xm = (xl + xr) / 2
    sw = xr - xl
    d = dot_size(p)
    y_stem = d + 86 + p.dV * 0.3
    P0 = (xl, CH * 0.70)
    T = (xm, yt)
    R = (xr, CH * 0.73)
    S = (xm - 0.04 * sw, CH * 0.36)
    sk = [
        seg(P0, (0, 0.10 * CH), T, (0.30 * sw, 0)),
        seg(T, (0.30 * sw, 0), R, (0, -0.10 * CH)),
        seg(R, (0, -0.12 * CH), S, (0, -0.09 * CH)),
    ]
    V = p.VC
    stem = rect(S[0] - V / 2, y_stem, S[0] + V / 2, S[1] + 2)
    c = [pen(sk, v, h, ("p",), ("h", S[1])), stem, rect(S[0] - d / 2, 0, S[0] + d / 2, d)]
    return c, W, (p.SBR, p.SBR)


def _mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


@glyph("ampersand", "&")
def g_ampersand(p):
    """Two strokes. One rises from the foot, round the loop's left side, to the
    top. The other leaves the top, comes down the loop's right side, swings
    across into the bowl, round the bottom and up to a level arm."""
    v, h = p.VR * 0.98, p.HR
    W = 640 + p.dV * 0.9
    top = CH + O
    yt = top - h / 2
    yb = -O + h / 2
    lx0, lx1 = W * 0.12 + v / 2, W * 0.62 - v / 2  # loop's sides, on the centre line
    ltop = (_mid((lx0, 0), (lx1, 0))[0], yt)
    ly = CH * 0.74
    xl = v / 2
    foot = (W - (v * 0.75), 0)
    leg_dir = _u(foot[0] - lx0, foot[1] - (ly - 0.10 * CH))
    a = [
        seg(ltop, (-(lx1 - lx0) * 0.32, 0), (lx0, ly), (0, -0.10 * CH)),
        seg((lx0, ly), (0, -0.16 * CH), foot, (leg_dir[0] * 0.30 * W, leg_dir[1] * 0.30 * W)),
    ]
    Lb = (xl, CH * 0.24)
    Bb = (W * 0.40, yb)
    arm_y = CH * 0.44
    Ar = (W * 0.79, arm_y)
    b = [
        seg(ltop, ((lx1 - lx0) * 0.32, 0), (lx1, ly), (0, -0.10 * CH)),
        seg((lx1, ly), (0, -0.16 * CH), Lb, (0, -0.18 * CH)),
        seg(Lb, (0, -0.13 * CH), Bb, (0.22 * W, 0)),
        seg(Bb, (0.24 * W, 0), Ar, (0.02 * W, 0.15 * CH)),
    ]
    return [pen(a, v, h, ("p",), ("h", 0)), pen(b, v, h, ("p",), ("h", arm_y))], W, (p.SBR, p.SBD)


@glyph("at", "@")
def g_at(p):
    """A single-storey a whose stem runs on, round and up, into an open ring."""
    v, h = p.V * 0.80, p.H * 0.80
    W = 840 + p.dV * 0.8
    bot, top = -150, CH + 10
    xl, xr = v / 2, W - v / 2
    yb, yt = bot + h / 2, top - h / 2
    cx, cy = W / 2, (bot + top) / 2
    rx, ry = (xr - xl) / 2, (yt - yb) / 2
    k = 0.56
    # the inner a: a bowl, and a stem on its right
    bw = 250 + p.dV * 0.9
    bx0 = cx - bw / 2 - 24
    by0, by1 = 80, 500
    xs = bx0 + bw - v / 2  # stem's centre line
    bowl = G.ring(G.Ellipse(bx0, by0, bx0 + bw, by1, 0.60),
                  G.Ellipse(bx0 + v, by0 + h, bx0 + bw - v, by1 - h, 0.62))
    foot_y = by0 + h / 2
    rr = 0.07 * W  # radius of the turn at the stem's foot
    run = by1 - (foot_y + rr)
    sk = [
        seg((xs, by1), (0, -run / 3), (xs, foot_y + rr), (0, -run / 3)),  # the stem, straight down
        seg((xs, foot_y + rr), (0, -0.55 * rr), (xs + rr, foot_y), (0.55 * rr, 0)),
        seg((xs + rr, foot_y), (0.10 * W, 0), (xr, cy), (0, 0.20 * (cy - foot_y) + 30)),
        seg((xr, cy), (0, k * ry), (cx, yt), (-k * rx, 0)),
        seg((cx, yt), (-k * rx, 0), (xl, cy), (0, -k * ry)),
        seg((xl, cy), (0, -k * ry), (cx, yb), (k * rx, 0)),
        seg((cx, yb), (k * rx * 0.8, 0), (W * 0.80, yb + 0.06 * (yt - yb)), (0.10 * W, 0.04 * (yt - yb))),
    ]
    return bowl + [pen(sk, v, h, ("h", by1))], W, (p.SBR, p.SBR)


@glyph("percent", "%")
def g_percent(p):
    v, h = p.V * 0.86, p.H * 0.84
    rw = 262 + p.dV * 0.5
    rh = 318
    gap = 84 + p.dV * 0.2
    W = 2 * rw + gap
    r1 = G.ring(G.Ellipse(0, CH - rh, rw, CH, 0.6), G.Ellipse(v, CH - rh + h, rw - v, CH - h, 0.62))
    r2 = G.ring(G.Ellipse(W - rw, 0, W, rh, 0.6), G.Ellipse(W - rw + v, h, W - v, rh - h, 0.62))
    from geometry import stroke
    sl = stroke((rw * 0.55, -6), (W - rw * 0.55, CH + 6), p.D * 0.95, ("h", 0), ("h", CH))
    return r1 + r2 + [sl], W, (p.SBR, p.SBR)


# --- s and S from an open-licence base (make-font skill) -----------------------
# The s, S, 6 and 9 are Archivo's (OFL), fitted to Litt's stem, x-height and cap
# height by src/borrowed.py: Archivo's weight axis is solved per master so its
# stem matches Litt's, and the outline is scaled, never traced or redrawn.
# data/base holds a subset with only s, S, 6, 9 and n (n is measured for the stem),
# with its licence. LITT_BORROW_S can point at another variable OFL font to try it.
_BORROW = os.environ.get("LITT_BORROW_S") or os.path.join(
    os.path.dirname(__file__), "data", "base", "Archivo-base[wdth,wght].ttf")
if _BORROW:
    import borrowed

    @glyph("s", "s")
    def g_s_borrowed(p):
        c, ink, sb, _ = borrowed.take(_BORROW, "s", p.V, XH + 0, "x")
        return c, ink, sb

    @glyph("S", "S")
    def g_S_borrowed(p):
        c, ink, sb, _ = borrowed.take(_BORROW, "S", p.V * 1.04, CH, "cap")
        return c, ink, sb

    @glyph("six", "6")
    def g_6_borrowed(p):
        c, ink, _, _ = borrowed.take(_BORROW, "six", p.VR * 1.02, CH, "cap")
        return c, ink, (fig_sb(p, ink),) * 2  # centred in the shared figure width

    @glyph("nine", "9")
    def g_9_borrowed(p):
        c, ink, _, _ = borrowed.take(_BORROW, "nine", p.VR * 1.02, CH, "cap")
        return c, ink, (fig_sb(p, ink),) * 2
