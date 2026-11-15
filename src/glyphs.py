"""Glyph drawings for the family.

Design brief: the spirit of mid-century Swiss grotesques. Tall x-height,
horizontal terminals, tight apertures, squarish rounds, low contrast. Its own
details: straight-legged R, spurless G, tailless a and t, straight-tailed y,
flat-topped t, square dots.

Units: 1000 per em. Every glyph function takes the weight parameters `p` and
returns (contours, ink_width, (left_sidebearing, right_sidebearing)). Contours
are drawn with the leftmost ink at x = 0; the builder adds the sidebearings.
"""

import math
from dataclasses import dataclass

from geometry import (
    Ellipse, band, bounds, diag, stroke, diag_hw, flip_y, mirror_x, poly, rect, ring,
    rotate, rotate180, solve_hw, transform, translate,
)

XH, CH, ASC, DSC = 540, 720, 760, -212
O = 12  # overshoot of round shapes
LCW = 1.05  # lowercase width factor: wider letters read better at UI sizes
K = 0.60  # superellipse squareness, outer
KI = 0.62  # inner counters, slightly squarer


@dataclass
class P:
    wght: float
    V: float  # lowercase vertical stem

    def __post_init__(self):
        t = (self.wght - 300) / 400
        V = self.V
        self.t = t
        self.dV = V - 84  # offset from the Regular stem
        self.H = V * (0.90 - 0.10 * t)  # horizontal strokes
        self.VC = V * 1.07  # cap stems
        self.HC = self.H * 1.05
        self.VR = V * 1.06  # sides of round letters
        self.HR = self.H * 0.97  # tops and bottoms of round letters
        self.D = V * 0.98  # diagonals
        self.SB = 70 + self.dV * 0.18  # lowercase straight sidebearing
        self.SBR = self.SB * 0.64  # round sidebearing
        self.SBC = self.SB * 1.12  # caps
        self.SBCR = self.SBC * 0.6
        self.SBD = 14 + self.dV * 0.05  # diagonals

    def c(self, base, shrink=0.75):
        """A counter width that tightens as weight grows."""
        return base - self.dV * shrink


GLYPHS = {}


def glyph(name, uni):
    def deco(fn):
        GLYPHS[name] = (uni, fn)
        return fn
    return deco


# --- shared constructions -------------------------------------------------

def arch(xl, xr, v_right, top, cy, h, V, join=0.42):
    """n-shoulder: an arch from a left stem (starting at xl, width V) to a right
    stem whose outer edge is xr. The left end of the arch hides inside the left
    stem so it springs from the stem with a notch, as in classic grotesques."""
    outer = Ellipse(xl + join * V, 2 * cy - top, xr, top, K)
    inner = Ellipse(xl + (join + 0.5) * V, 2 * cy - (top - h), xr - v_right, top - h, KI)
    return band(outer, inner, (0, 0.0), (1, 1.0))


def bowl(xl, xr, bottom, top, v_side, h, V, k=K, ki=KI, join=0.5):
    """A round bowl attached to a stem on its left (stem starts at xl)."""
    outer = Ellipse(xl + join * V, bottom, xr, top, k)
    inner = Ellipse(xl + (join + 0.42) * V, bottom + h, xr - v_side, top - h, ki)
    return ring(outer, inner)


def c_shape(w, bottom, top, v, h, t_top=0.42, t_bot=0.42, k=K, ki=KI, wi=None):
    """Open round with horizontally cut terminals on the right."""
    outer = Ellipse(0, bottom, w, top, k)
    inner = Ellipse(v, bottom + h, w - v if wi is None else wi, top - h, ki)
    yt = outer.cy + t_top * outer.ry
    yb = outer.cy - t_bot * outer.ry
    return band(outer, inner, outer.at_y(0, yt), outer.at_y(3, yb),
                inner.at_y(0, yt), inner.at_y(3, yb)), outer, inner


def s_shape(w, bottom, top, v, h, spine, t_top=0.50, t_bot=0.50, k=0.62, top_w=0.94):
    """S: two stacked open bowls whose inner strokes meet in a shared spine."""
    mid = (bottom + top) / 2 + (top - bottom) * 0.01
    inset = w * (1 - top_w) / 2
    up_o = Ellipse(inset, mid - spine / 2, w - inset, top, k)
    up_i = Ellipse(inset + v, mid + spine / 2, w - inset - v * 0.96, top - h, k + 0.02)
    lo_o = Ellipse(0, bottom, w, mid + spine / 2, k)
    lo_i = Ellipse(v * 0.96, bottom + h, w - v, mid - spine / 2, k + 0.02)
    yt = up_o.cy + t_top * up_o.ry
    yb = lo_o.cy - t_bot * lo_o.ry
    # each bowl runs a little past the centre so the spine reads as one diagonal
    upper = band(up_o, up_i, up_o.at_y(0, yt), (3, 0.08), up_i.at_y(0, yt), (3, 0.08))
    lower = band(lo_o, lo_i, lo_o.at_y(2, yb), (5, 0.08), lo_i.at_y(2, yb), (5, 0.08))
    return [upper, lower]


def hook_down(x_stem, V, h, bottom, rx, ry, term=0.35):
    """A descending stem's hook curving left (j). The hook ends in a vertical cut
    `term` of the way from the counter's left edge to its centre. Returns the
    contour and the height where the stem should start."""
    outer = Ellipse(x_stem + V - 2 * rx, bottom, x_stem + V, bottom + 2 * ry, K)
    inner = Ellipse(outer.l + V, bottom + h, x_stem, outer.t - h, KI)
    term_x = inner.l + term * inner.rx
    return band(outer, inner, outer.at_x(2, term_x), (3, 1.0),
                inner.at_x(2, term_x), (3, 1.0)), outer.cy


# --- lowercase ------------------------------------------------------------

def n_parts(p, cn, stem_top=XH):
    V = p.V
    w = cn + 2 * V
    cy = XH * 0.58
    return [
        rect(0, 0, V, stem_top),
        rect(w - V, 0, w, cy),
        arch(0, w, V, XH + O, cy, p.H, V),
    ], w


@glyph("n", "n")
def g_n(p):
    c, w = n_parts(p, p.c(270 * LCW, 1.2))
    return c, w, (p.SB, p.SB * 0.96)


@glyph("h", "h")
def g_h(p):
    c, w = n_parts(p, p.c(270 * LCW, 1.2), ASC)
    return c, w, (p.SB, p.SB * 0.96)


@glyph("m", "m")
def g_m(p):
    V, cm = p.V, p.c(232 * LCW, 1.22)
    w = 2 * cm + 3 * V
    cy = XH * 0.58
    x2 = V + cm
    c = [
        rect(0, 0, V, XH),
        rect(x2, 0, x2 + V, cy),
        rect(w - V, 0, w, cy),
        arch(0, x2 + V, V, XH + O, cy, p.H, V),
        arch(x2, w, V, XH + O, cy, p.H, V),
    ]
    return c, w, (p.SB, p.SB * 0.96)


@glyph("u", "u")
def g_u(p):
    c, w = n_parts(p, p.c(270 * LCW, 1.2))
    return rotate180(c, w / 2, XH / 2), w, (p.SB * 0.96, p.SB)


@glyph("r", "r")
def g_r(p):
    V = p.V
    cn = p.c(270 * LCW, 1.2)
    wn = cn + 2 * V
    cy = XH * 0.58
    outer = Ellipse(0.42 * V, 2 * cy - (XH + O), wn, XH + O, K)
    inner = Ellipse(0.92 * V, 2 * cy - (XH + O - p.H), wn - V, XH + O - p.H, KI)
    cut = V + cn * 0.58 + p.dV * 0.15
    arm = band(outer, inner, outer.at_x(0, cut), (1, 1.0), inner.at_x(0, cut), (1, 1.0))
    return [rect(0, 0, V, XH), arm], cut, (p.SB, p.SBD + 6)


@glyph("l", "l")
def g_l(p):
    """A stem with a short tail at the foot, so l is never mistaken for I, 1 or |."""
    V = p.V
    rx = 92 + V * 0.5
    ry = 92 + V * 0.4
    o = Ellipse(0, -O, 2 * rx, -O + 2 * ry, 0.6)
    i = Ellipse(V, -O + p.H * 0.95, 2 * rx - V, -O + 2 * ry - p.H * 0.95, 0.62)
    w = rx + V * 0.6 + 30
    tail = band(o, i, (2, 0.0), o.at_x(3, w), (2, 0.0), i.at_x(3, w))
    return [rect(0, o.cy, V, ASC), tail], w, (p.SB, p.SBD + 10)


def dot(x, w, top):
    s = w * 1.0
    return rect(x, top - s, x + w, top)


@glyph("i", "i")
def g_i(p):
    V = p.V
    gap = 70 + p.dV * 0.35
    d = V * 1.04 + 6
    return [rect(0, 0, V, XH), rect(0, XH + gap, V, XH + gap + d)], V, (p.SB, p.SB)


@glyph("j", "j")
def g_j(p):
    V = p.V
    rx, ry = 120 + V * 0.6, 120 + V * 0.4
    x_stem = 2 * rx - V - 30
    hook, cy = hook_down(x_stem, V, p.H, DSC - O * 0.5, rx, ry)
    gap = 70 + p.dV * 0.35
    d = V * 1.04 + 6
    c = [hook, rect(x_stem, cy, x_stem + V, XH), rect(x_stem, XH + gap, x_stem + V, XH + gap + d)]
    x0 = bounds(c)[0]
    return translate(c, -x0), x_stem + V - x0, (-44 + p.dV * 0.1, p.SB)


@glyph("o", "o")
def g_o(p):
    w = p.c(296 * LCW, 1.17) + 2 * p.VR
    outer = Ellipse(0, -O, w, XH + O, K)
    inner = Ellipse(p.VR, -O + p.HR, w - p.VR, XH + O - p.HR, KI)
    return ring(outer, inner), w, (p.SBR, p.SBR)


@glyph("c", "c")
def g_c(p):
    # terminals at about 66% and 34% of the x-height: closer to Archivo's (63/37)
    # so the c sits with the s, a touch more open for 13px
    w = p.c(289 * LCW, 1.17) + 2 * p.VR
    con, _, _ = c_shape(w, -O, XH + O, p.VR, p.HR, 0.30, 0.30)
    return [con], w, (p.SBR, p.SBR * 0.7)


@glyph("e", "e")
def g_e(p):
    w = p.c(290 * LCW, 1.17) + 2 * p.VR
    outer = Ellipse(0, -O, w, XH + O, K)
    inner = Ellipse(p.VR, -O + p.HR, w - p.VR, XH + O - p.HR, KI)
    bar_b = XH * 0.46
    bar_t = bar_b + p.H
    yb = outer.cy - 0.55 * outer.ry
    body = band(outer, inner, outer.at_y(3, bar_b), outer.at_y(7, yb),
                inner.at_y(3, bar_b), inner.at_y(7, yb))
    xr = min(outer.x_at(bar_b), outer.x_at(bar_t))
    bar = rect(p.VR * 0.5, bar_b, xr, bar_t)
    return [body, bar], w, (p.SBR, p.SBR * 0.85)


@glyph("a", "a")
def g_a(p):
    V, H = p.V, p.H
    w = p.c(283 * LCW, 1.22) + V + p.VR  # 8% wider, nearer Archivo's proportion
    cyh = XH * 0.60
    # top hook, from the stem over the top to a horizontal cut at the left
    ho = Ellipse(V * 0.35, 2 * cyh - (XH + O), w, XH + O, K)
    hi = Ellipse(V * 0.35 + p.VR * 0.98, 2 * cyh - (XH + O - p.HR), w - V, XH + O - p.HR, KI)
    yt = XH * 0.72 - p.dV * 0.12  # the hook closes a little, as the s does
    hook = band(ho, hi, (0, 0.0), ho.at_y(1, yt), (0, 0.0), hi.at_y(1, yt))
    # bowl
    top = XH * 0.52 + H * 0.5  # a lower bowl gives the hook room; the a no longer sits heavy
    bo = Ellipse(0, -O, w - V * 0.4, top, (0.62, 0.66, 0.62, 0.60))
    bi = Ellipse(p.VR, -O + p.HR, w - V * 0.9, top - H, (0.64, 0.68, 0.64, 0.62))
    return [rect(w - V, 0, w, cyh), hook] + ring(bo, bi), w, (p.SBR * 1.1, p.SB * 0.96)


def b_parts(p, stem_bottom, stem_top):
    V = p.V
    w = p.c(296 * LCW, 1.17) + V + p.VR
    return [rect(0, stem_bottom, V, stem_top)] + bowl(0, w, -O, XH + O, p.VR, p.HR, V), w


@glyph("b", "b")
def g_b(p):
    c, w = b_parts(p, 0, ASC)
    return c, w, (p.SB, p.SBR)


@glyph("d", "d")
def g_d(p):
    c, w = b_parts(p, 0, ASC)
    return mirror_x(c, w), w, (p.SBR, p.SB)


@glyph("p", "p")
def g_p(p):
    c, w = b_parts(p, DSC, XH)
    return c, w, (p.SB, p.SBR)


@glyph("q", "q")
def g_q(p):
    c, w = b_parts(p, DSC, XH)
    return mirror_x(c, w), w, (p.SBR, p.SB)


@glyph("g", "g")
def g_g(p):
    V = p.V
    w = p.c(296 * LCW, 1.17) + V + p.VR
    bw = bowl(0, w, -O + 20, XH + O, p.VR, p.HR, V)
    bw = mirror_x(bw, w)
    # descending hook
    ry = 150 + p.dV * 0.2
    cy = DSC - O + ry
    ho = Ellipse(p.VR * 0.1, DSC - O, w, DSC - O + 2 * ry, K)
    hi = Ellipse(p.VR * 0.1 + p.VR, DSC - O + p.HR, w - V, DSC - O + 2 * ry - p.HR, KI)
    yt = cy - 0.30 * ry
    hook = band(ho, hi, ho.at_y(2, yt), (3, 1.0), hi.at_y(2, yt), (3, 1.0))
    return bw + [hook, rect(w - V, cy, w, XH)], w, (p.SBR, p.SB)


@glyph("t", "t")
def g_t(p):
    V, H = p.V, p.H
    L = 72 + p.dV * 0.2
    R = 114 + p.dV * 0.2
    w = L + V + R
    rx = 118 + V * 0.45
    ry = 100 + V * 0.4
    outer = Ellipse(L, -O, L + 2 * rx, -O + 2 * ry, K)
    inner = Ellipse(L + V, -O + H * 0.95, L + 2 * rx - V, -O + 2 * ry - H * 0.95, KI)
    hook = band(outer, inner, (2, 0.0), outer.at_x(3, w), (2, 0.0), inner.at_x(3, w))
    top = XH + 150
    return [hook, rect(L, outer.cy, L + V, top), rect(0, XH - H, w, XH)], w, (p.SBD + 8, p.SBD + 4)


@glyph("f", "f")
def g_f(p):
    V, H = p.V, p.H
    L = 66 + p.dV * 0.2
    R = 138 + p.dV * 0.25
    w = L + V + R
    rx = 128 + V * 0.45
    ry = 110 + V * 0.4
    top = ASC + O
    outer = Ellipse(L, top - 2 * ry, L + 2 * rx, top, K)
    inner = Ellipse(L + V, top - 2 * ry + H, L + 2 * rx - V, top - H * 0.95, KI)
    hook = band(outer, inner, outer.at_x(0, w), (1, 1.0), inner.at_x(0, w), (1, 1.0))
    return [hook, rect(L, 0, L + V, outer.cy), rect(0, XH - H, L + V + R * 0.82, XH)], w, (p.SBD + 8, p.SBD)


@glyph("k", "k")
def g_k(p):
    V, D = p.V, p.D
    w = p.c(268 * LCW, 0.55) + V
    hw = diag_hw(w - V, XH * 0.7, D)
    arm = stroke((V * 0.5, XH * 0.30), (w - hw / 2, XH), D, ("v", V * 0.5), ("h", XH))
    t = 0.42  # where the leg leaves the arm, along the arm
    j = (V * 0.5 + (w - hw / 2 - V * 0.5) * t, XH * 0.30 + XH * 0.70 * t)
    leg = stroke(j, (w + 6 - hw / 2, 0), D * 1.02, ("p",), ("h", 0))
    return [rect(0, 0, V, ASC), arm, leg], w + 6, (p.SB, p.SBD)


def _reorder(c):
    """Points of a polygon contour as a list."""
    return [c[0]] + [s[-1] for s in c[1:]]


def v_shape(p, w, top, D, apex=None):
    apex = (D * 0.9) if apex is None else apex
    dy = top
    hw = solve_hw(D, dy, lambda hw: w / 2 + apex / 2 - hw)
    left = diag(w / 2 - apex / 2, 0, 0, top, D, "left")
    left = poly((w / 2 + apex / 2 - hw, 0), (w / 2 + apex / 2, 0), (hw, top), (0, top))
    right = poly((w / 2 - apex / 2, 0), (w / 2 - apex / 2 + hw, 0), (w, top), (w - hw, top))
    return [left, right], hw


@glyph("v", "v")
def g_v(p):
    w = p.c(420 * LCW, 0.0) + p.dV * 0.75
    c, _ = v_shape(p, w, XH, p.D)
    return c, w, (p.SBD, p.SBD)


@glyph("y", "y")
def g_y(p):
    w = p.c(430 * LCW, 0.0) + p.dV * 0.75
    D = p.D
    apex = D * 0.9
    hw = solve_hw(D, XH, lambda hw: w / 2 + apex / 2 - hw)
    # right stroke runs from the descender straight up to the x-height
    top_r = (w - hw / 2, XH)
    x_base = w / 2 - apex / 2 + hw / 2  # its centre at the baseline
    slope = (top_r[0] - x_base) / XH
    bot_r = (x_base + slope * DSC, DSC)
    right = stroke(bot_r, top_r, D, ("h", DSC), ("h", XH))
    # left stroke ends inside the right one, so the join stays clean
    yj = D * 0.35
    join = (x_base + slope * yj, yj)
    left = stroke(join, (hw / 2, XH), D, ("p",), ("h", XH))
    c = [left, right]
    x0 = bounds(c)[0]
    return translate(c, -x0), w - x0, (p.SBD, p.SBD)


@glyph("w", "w")
def g_w(p):
    D = p.D * 0.94
    w1 = p.c(330 * LCW, 0.0) + p.dV * 0.8
    a, hw = v_shape(p, w1, XH, D, apex=D * 0.8)
    b = translate(v_shape(p, w1, XH, D, apex=D * 0.8)[0], w1 - hw * 1.05)
    w = 2 * w1 - hw * 1.05
    # middle peak lowered slightly, then trimmed by keeping strokes at full height
    return a + b, w, (p.SBD, p.SBD)


@glyph("x", "x")
def g_x(p):
    D = p.D
    w = p.c(400 * LCW, 0.0) + p.dV * 0.75
    hw = diag_hw(w, XH, D) * 0.98
    s1 = poly((0, 0), (hw, 0), (w, XH), (w - hw, XH))
    s2 = poly((w - hw, 0), (w, 0), (hw, XH), (0, XH))
    return [s1, s2], w, (p.SBD + 4, p.SBD + 4)


@glyph("z", "z")
def g_z(p):
    H, D = p.H, p.D
    w = p.c(360 * LCW, 0.99) + p.dV * 0.5
    hw = diag_hw(w, XH - 2 * H, D * 1.05)
    diag_c = poly((0, H), (hw, H), (w, XH - H), (w - hw, XH - H))
    return [rect(0, 0, w, H), rect(6, XH - H, w, XH), diag_c], w, (p.SBD + 18, p.SBD + 18)


@glyph("s", "s")
def g_s(p):
    w = p.c(330 * LCW, 1.12) + 2 * p.VR * 0.92
    c = s_shape(w, -O, XH + O, p.VR * 0.94, p.HR, p.HR * 1.06)
    return c, w, (p.SBR * 1.1, p.SBR * 1.1)


# --- uppercase ------------------------------------------------------------

def cap_stems(p, w, top=CH):
    return [rect(0, 0, p.VC, top), rect(w - p.VC, 0, w, top)]


@glyph("H", "H")
def g_H(p):
    w = p.c(420, 1.17) + 2 * p.VC
    yb = CH * 0.47
    return cap_stems(p, w) + [rect(p.VC / 2, yb, w - p.VC / 2, yb + p.HC)], w, (p.SBC, p.SBC)


@glyph("I", "I")
def g_I(p):
    return [rect(0, 0, p.VC, CH)], p.VC, (p.SBC, p.SBC)


@glyph("L", "L")
def g_L(p):
    w = p.c(340, 1.08) + p.VC
    return [rect(0, 0, p.VC, CH), rect(p.VC / 2, 0, w, p.HC)], w, (p.SBC, p.SBD + 14)


@glyph("E", "E")
def g_E(p):
    w = p.c(360, 1.08) + p.VC
    hc = p.HC
    yb = CH * 0.47
    return [rect(0, 0, p.VC, CH), rect(p.VC / 2, 0, w, hc), rect(p.VC / 2, yb, w - 18, yb + hc),
            rect(p.VC / 2, CH - hc, w - 6, CH)], w, (p.SBC, p.SBD + 22)


@glyph("F", "F")
def g_F(p):
    w = p.c(340, 1.08) + p.VC
    hc = p.HC
    yb = CH * 0.45
    return [rect(0, 0, p.VC, CH), rect(p.VC / 2, yb, w - 22, yb + hc),
            rect(p.VC / 2, CH - hc, w, CH)], w, (p.SBC, p.SBD + 16)


@glyph("T", "T")
def g_T(p):
    w = p.c(520, 0.0) + p.dV * 0.54
    return [rect(w / 2 - p.VC / 2, 0, w / 2 + p.VC / 2, CH), rect(0, CH - p.HC, w, CH)], w, (p.SBD + 10, p.SBD + 10)


@glyph("O", "O")
def g_O(p):
    v, h = p.VC * 1.05, p.HC * 0.97
    w = p.c(500, 1.17) + 2 * v
    outer = Ellipse(0, -O, w, CH + O, K)
    inner = Ellipse(v, -O + h, w - v, CH + O - h, KI)
    return ring(outer, inner), w, (p.SBCR, p.SBCR)


@glyph("Q", "Q")
def g_Q(p):
    c, w, sb = g_O(p)
    D = p.D * 1.08
    tail = stroke((w * 0.62, CH * 0.20), (w + 10, -O - 34), D, ("p",), ("h", -O - 34))
    return c + [tail], w, (p.SBCR, p.SBCR)


@glyph("C", "C")
def g_C(p):
    v, h = p.VC * 1.05, p.HC * 0.97
    w = p.c(470, 1.17) + 2 * v
    con, _, _ = c_shape(w, -O, CH + O, v, h, 0.50, 0.48)
    return [con], w, (p.SBCR, p.SBCR * 0.9)


@glyph("G", "G")
def g_G(p):
    v, h = p.VC * 1.05, p.HC * 0.97
    w = p.c(490, 1.17) + 2 * v
    outer = Ellipse(0, -O, w, CH + O, K)
    inner = Ellipse(v, -O + h, w - v, CH + O - h, KI)
    yt = outer.cy + 0.50 * outer.ry
    bar_t = CH * 0.46
    body = band(outer, inner, outer.at_y(0, yt), outer.at_y(3, bar_t),
                inner.at_y(0, yt), inner.at_y(3, bar_t))
    xr = outer.x_at(bar_t)
    bar = rect(w * 0.52, bar_t - p.HC, xr, bar_t)
    stem = rect(xr - p.VC, outer.cy - outer.ry * 0.6, xr, bar_t)
    return [body, bar, stem], w, (p.SBCR, p.SBC * 0.9)


@glyph("D", "D")
def g_D(p):
    V, v, h = p.VC, p.VC * 1.05, p.HC
    w = p.c(450, 1.17) + V + v
    rx = min(w * 0.5, CH * 0.5)
    outer = Ellipse(w - 2 * rx, 0, w, CH, K + 0.04)
    inner = Ellipse(w - 2 * rx + v, h, w - v, CH - h, KI + 0.04)
    curve = band(outer, inner, (3, 0.0), (4, 1.0))
    return [rect(0, 0, V, CH), rect(V / 2, 0, outer.cx + 1, h), rect(V / 2, CH - h, outer.cx + 1, CH), curve], w, (p.SBC, p.SBCR)


def cap_bowl(x0, x1, y0, y1, V, v, h):
    """Closed D-shaped bowl on a stem (P, B, R)."""
    ry = (y1 - y0) / 2
    rx = min(ry * 1.05, (x1 - x0) * 0.6)
    outer = Ellipse(x1 - 2 * rx, y0, x1, y1, K + 0.04)
    inner = Ellipse(x1 - 2 * rx + v, y0 + h, x1 - v, y1 - h, KI + 0.04)
    curve = band(outer, inner, (3, 0.0), (4, 1.0))
    return [rect(V / 2, y0, outer.cx + 1, y0 + h), rect(V / 2, y1 - h, outer.cx + 1, y1), curve]


@glyph("P", "P")
def g_P(p):
    V, v, h = p.VC, p.VC * 1.02, p.HC
    w = p.c(400, 1.17) + V + v
    return [rect(0, 0, V, CH)] + cap_bowl(0, w, CH * 0.40 - h * 0.5, CH, V, v, h), w, (p.SBC, p.SBCR)


@glyph("R", "R")
def g_R(p):
    V, v, h, D = p.VC, p.VC * 1.02, p.HC, p.D * 1.04
    w = p.c(410, 1.17) + V + v
    yb = CH * 0.42 - h * 0.5
    parts = cap_bowl(0, w * 0.97, yb, CH, V, v, h)
    xl = w * 0.97 - (CH - yb) * 0.5 - v * 0.2
    leg = diag(w + 6, 0, xl, yb + h * 0.7, D, "right")
    return [rect(0, 0, V, CH)] + parts + [leg], w + 6, (p.SBC, p.SBD + 4)


@glyph("B", "B")
def g_B(p):
    V, v, h = p.VC, p.VC * 1.0, p.HC
    w = p.c(420, 1.17) + V + v
    ym = CH * 0.54
    top = cap_bowl(0, w * 0.94, ym - h, CH, V, v * 0.96, h)
    bot = cap_bowl(0, w, 0, ym, V, v, h)
    return [rect(0, 0, V, CH)] + top + bot, w, (p.SBC, p.SBCR)


@glyph("U", "U")
def g_U(p):
    V, v, h = p.VC, p.VC * 1.04, p.HC * 0.97
    w = p.c(440, 1.17) + 2 * v
    ry = w * 0.46
    outer = Ellipse(0, -O, w, -O + 2 * ry, K)
    inner = Ellipse(v, -O + h, w - v, -O + 2 * ry - h, KI)
    curve = band(outer, inner, (2, 0.0), (3, 1.0))
    return [rect(0, outer.cy, v, CH), rect(w - v, outer.cy, w, CH), curve], w, (p.SBC, p.SBC)


@glyph("J", "J")
def g_J(p):
    V, v, h = p.VC, p.VC * 1.04, p.HC * 0.97
    w = p.c(330, 1.12) + 2 * v
    ry = w * 0.5
    outer = Ellipse(0, -O, w, -O + 2 * ry, K)
    inner = Ellipse(v, -O + h, w - v, -O + 2 * ry - h, KI)
    yt = outer.cy - 0.05 * ry
    curve = band(outer, inner, outer.at_y(2, yt), (3, 1.0), inner.at_y(2, yt), (3, 1.0))
    return [rect(w - v, outer.cy, w, CH), curve], w, (p.SBD + 22, p.SBC)


@glyph("S", "S")
def g_S(p):
    v = p.VC * 1.0
    w = p.c(430, 1.17) + 2 * v
    c = s_shape(w, -O, CH + O, v, p.HC * 0.97, p.HC * 1.04, 0.50, 0.48, 0.62)
    return c, w, (p.SBCR * 1.15, p.SBCR * 1.15)


@glyph("A", "A")
def g_A(p):
    D = p.D * 1.06
    w = p.c(560, 0.0) + p.dV * 0.59
    apex = D * 0.8
    hw = solve_hw(D, CH, lambda hw: w / 2 + apex / 2 - hw)
    left = poly((0, 0), (hw, 0), (w / 2 + apex / 2 - hw * 0.0, CH), (w / 2 - apex / 2, CH))
    left = poly((0, 0), (hw, 0), (w / 2 + apex / 2, CH), (w / 2 + apex / 2 - hw, CH))
    right = poly((w - hw, 0), (w, 0), (w / 2 - apex / 2 + hw, CH), (w / 2 - apex / 2, CH))
    yb = CH * 0.24
    bar = rect(w * 0.2, yb, w * 0.8, yb + p.HC)
    return [left, right, bar], w, (p.SBD, p.SBD)


@glyph("V", "V")
def g_V(p):
    w = p.c(560, 0.0) + p.dV * 0.59
    c, _ = v_shape(p, w, CH, p.D * 1.06, apex=p.D * 0.85)
    return c, w, (p.SBD, p.SBD)


@glyph("W", "W")
def g_W(p):
    D = p.D * 1.0
    w1 = p.c(460, 0.0) + p.dV * 0.45
    a, hw = v_shape(p, w1, CH, D, apex=D * 0.8)
    off = w1 - hw * 1.05
    b = translate(v_shape(p, w1, CH, D, apex=D * 0.8)[0], off)
    return a + b, w1 + off, (p.SBD, p.SBD)


@glyph("X", "X")
def g_X(p):
    D = p.D * 1.05
    w = p.c(520, 0.0) + p.dV * 0.54
    hw = diag_hw(w, CH, D) * 0.98
    s1 = poly((0, 0), (hw, 0), (w, CH), (w - hw, CH))
    s2 = poly((w - hw, 0), (w, 0), (hw, CH), (0, CH))
    return [s1, s2], w, (p.SBD + 4, p.SBD + 4)


@glyph("Y", "Y")
def g_Y(p):
    D = p.D * 1.05
    w = p.c(560, 0.0) + p.dV * 0.54
    yj = CH * 0.42
    V = p.VC
    x0 = w / 2 - V / 2
    hw = diag_hw(w / 2, CH - yj, D)
    left = poly((x0, yj - 2), (x0 + V, yj - 2), (hw, CH), (0, CH))
    right = poly((x0, yj - 2), (x0 + V, yj - 2), (w, CH), (w - hw, CH))
    return [rect(x0, 0, x0 + V, yj), left, right], w, (p.SBD, p.SBD)


@glyph("K", "K")
def g_K(p):
    V, D = p.VC, p.D * 1.06
    w = p.c(462, 0.7) + V
    hw = diag_hw(w - V, CH * 0.7, D)
    y0 = CH * 0.26
    arm = stroke((V * 0.5, y0), (w - hw / 2, CH), D, ("v", V * 0.5), ("h", CH))
    t = 0.40
    j = (V * 0.5 + (w - hw / 2 - V * 0.5) * t, y0 + (CH - y0) * t)
    leg = stroke(j, (w + 8 - hw / 2, 0), D * 1.03, ("p",), ("h", 0))
    return [rect(0, 0, V, CH), arm, leg], w + 8, (p.SBC, p.SBD)


@glyph("M", "M")
def g_M(p):
    V, D = p.VC, p.D * 1.02
    w = p.c(560, 1.08) + 2 * V + p.dV * 0.4
    vee = diag_hw(w / 2 - V, CH, D)
    apex = D * 0.8
    left = poly((w / 2 - apex / 2, 0), (w / 2 + apex / 2, 0), (vee, CH), (0, CH))
    left = poly((w / 2 - apex / 2 + 0, 0), (w / 2 + apex / 2, 0), (V + 2, CH), (V + 2 - vee, CH))
    right = poly((w / 2 - apex / 2, 0), (w / 2 + apex / 2, 0), (w - V - 2 + vee, CH), (w - V - 2, CH))
    return [rect(0, 0, V, CH), rect(w - V, 0, w, CH), left, right], w, (p.SBC, p.SBC)


@glyph("N", "N")
def g_N(p):
    V, D = p.VC, p.D * 1.06
    w = p.c(430, 1.17) + 2 * V
    hw = diag_hw(w - 2 * V, CH, D)
    d = poly((w - V - hw + V, 0), (w, 0), (V + hw - V, CH), (0, CH))
    d = poly((w - hw, 0), (w, 0), (hw, CH), (0, CH))
    return [rect(0, 0, V, CH), rect(w - V, 0, w, CH), d], w, (p.SBC, p.SBC)


@glyph("Z", "Z")
def g_Z(p):
    h, D = p.HC, p.D * 1.08
    w = p.c(500, 0.99) + p.dV * 0.6
    hw = diag_hw(w, CH - 2 * h, D)
    d = poly((0, h), (hw, h), (w, CH - h), (w - hw, CH - h))
    return [rect(0, 0, w, h), rect(10, CH - h, w, CH), d], w, (p.SBD + 18, p.SBD + 18)


# --- figures ----------------------------------------------------------------
# Lining figures at cap height on one shared width, so the tabular forms (`tnum`)
# centre cleanly; extended.py makes the default figures proportional. Round
# figures take the round letters' strokes, so numbers sit in text at its weight.

def fig_width(p):
    return 524 + p.dV * 0.9


def fig_sb(p, ink):
    return ((fig_width(p) + 2 * p.SBR) - ink) / 2


def fig_strokes(p):
    return p.VR * 1.02, p.HR


def _tangent(e, pos, eps=1e-3):
    i, t = pos
    a = e.point((i, max(0.0, t - eps)))
    b = e.point((i, min(1.0, t + eps)))
    return math.atan2(b[1] - a[1], b[0] - a[0])


@glyph("zero", "0")
def g_0(p):
    v, h = fig_strokes(p)
    w = fig_width(p) - 8
    outer = Ellipse(0, -O, w, CH + O, 0.64)
    inner = Ellipse(v, -O + h, w - v, CH + O - h, 0.66)
    return ring(outer, inner), w, (fig_sb(p, w),) * 2


@glyph("one", "1")
def g_1(p):
    V = p.VC
    W = fig_width(p)
    xs = W * 0.58 - V / 2  # stem's left edge
    t = p.H * 1.08  # flag thickness, square to the stroke
    reach, drop = 176 + p.dV * 0.55, 128
    tv = t * math.hypot(reach, drop) / reach  # its vertical thickness
    xe = xs - reach
    # an even stroke leaving the stem's top-left corner, its end cut vertically
    flag = poly((xs + V * 0.5, CH), (xs, CH), (xe, CH - drop), (xe, CH - drop - tv),
                (xs, CH - tv), (xs + V * 0.5, CH - tv))
    c = [rect(xs, 0, xs + V, CH), flag]
    x0 = bounds(c)[0]
    ink = xs + V - x0
    return translate(c, -x0), ink, ((W + 2 * p.SBR - ink) / 2,) * 2


@glyph("two", "2")
def g_2(p):
    v, h = fig_strokes(p)
    W = fig_width(p)
    hb = p.HC
    D = p.D * 1.08
    ry = CH * 0.30
    o = Ellipse(0, CH + O - 2 * ry, W, CH + O, 0.62)
    i = Ellipse(v, CH + O - 2 * ry + h, W - v, CH + O - h, 0.64)
    # the diagonal leaves the bowl where the bowl is already heading its way,
    # so the outer edge runs on without a kink
    best = None
    for k in range(4, 60):
        t0 = k / 80
        po = o.point((3, t0))
        hw = D
        for _ in range(4):
            hw = diag_hw(po[0] - hw, po[1] - hb, D)
        ang = math.atan2(po[1] - hb, po[0] - hw)
        err = abs(_tangent(o, (3, t0)) - ang)
        if best is None or err < best[0]:
            best = (err, t0, hw)
    _, t0, hw = best
    po, pi = o.point((3, t0)), i.point((3, t0))
    yt = o.cy + 0.10 * ry
    so, si = o.at_y(1, yt), i.at_y(1, yt)
    arc = band(o, i, (3, t0), (so[0] + 4, so[1]), (3, t0), (si[0] + 4, si[1]))
    diag_c = poly(po, pi, (0, hb - 1), (hw, hb - 1))
    return [arc, diag_c, rect(0, 0, W, hb)], W, (fig_sb(p, W),) * 2


@glyph("three", "3")
def g_3(p):
    v, h = fig_strokes(p)
    W = fig_width(p)
    ym = CH * 0.56
    lo_o = Ellipse(0, -O, W, ym + h * 0.5, 0.62)
    lo_i = Ellipse(v, -O + h, W - v, ym - h * 0.5, 0.64)
    up_o = Ellipse(W * 0.07, ym - h * 0.5, W * 0.95, CH + O, 0.62)
    up_i = Ellipse(W * 0.07 + v * 0.96, ym + h * 0.5, W * 0.95 - v * 0.96, CH + O - h, 0.64)
    yl = lo_o.cy - 0.46 * lo_o.ry
    yu = up_o.cy + 0.46 * up_o.ry
    lower = band(lo_o, lo_i, lo_o.at_y(2, yl), (4, 1.0), lo_i.at_y(2, yl), (4, 1.0))
    upper = band(up_o, up_i, (3, 0.0), up_o.at_y(1, yu), (3, 0.0), up_i.at_y(1, yu))
    bar = rect(W * 0.40, ym - h * 0.5, up_o.cx + 2, ym + h * 0.5)
    return [lower, upper, bar], W, (fig_sb(p, W),) * 2


@glyph("four", "4")
def g_4(p):
    V, h = p.VC, p.HC
    D = p.D * 1.10
    W = fig_width(p) + 16
    xs = W * 0.64
    yb = CH * 0.25
    hw = diag_hw(xs + V, CH - yb, D)
    for _ in range(3):
        hw = diag_hw(xs + V - hw, CH - yb, D)
    diag_c = poly((0, yb), (hw, yb), (xs + V, CH), (xs + V - hw, CH))
    return [rect(xs, 0, xs + V, CH), rect(0, yb, W, yb + h), diag_c], W, (fig_sb(p, W),) * 2


@glyph("five", "5")
def g_5(p):
    v, h = fig_strokes(p)
    V = p.VC
    W = fig_width(p)
    top = CH * 0.62
    bo = Ellipse(0, -O, W, top + O, 0.62)
    bi = Ellipse(v, -O + h, W - v, top + O - h, 0.64)
    yl = bo.cy - 0.48 * bo.ry
    x0 = W * 0.06  # the stem's left edge
    xc = x0 + V  # the bowl springs from the stem's right edge
    a, ai = bo.at_x(1, xc), bi.at_x(1, xc)
    arc = band(bo, bi, bo.at_y(2, yl), (a[0] + 4, a[1]), bi.at_y(2, yl), (ai[0] + 4, ai[1]))
    foot = bi.point(ai)[1]
    return [arc, rect(x0, foot, xc, CH), rect(x0, CH - p.HC, W * 0.92, CH)], W, (fig_sb(p, W),) * 2


@glyph("six", "6")
def g_6(p):
    v, h = fig_strokes(p)
    W = fig_width(p)
    top = CH * 0.62
    bo = Ellipse(0, -O, W, top + O, 0.62)
    bi = Ellipse(v, -O + h, W - v, top + O - h, 0.64)
    # The top arc is the upper quadrant of an ellipse centred on the bowl's
    # middle, so it reaches its widest at the bowl's widest: both run straight
    # up at the join and the left side reads as one curve.
    tw = W * 0.96
    ao = Ellipse(0, 2 * bo.cy - (CH + O), tw, CH + O, 0.58)
    ai = Ellipse(v, 2 * bi.cy - (CH + O - h), tw - v, CH + O - h, 0.60)
    yt = CH * 0.80
    arc = band(ao, ai, ao.at_y(0, yt), (1, 1.0), ai.at_y(0, yt), (1, 1.0))
    return ring(bo, bi) + [arc], W, (fig_sb(p, W),) * 2


@glyph("seven", "7")
def g_7(p):
    h = p.HC
    D = p.D * 1.12
    W = fig_width(p)
    xb = W * 0.20
    hw = D
    for _ in range(4):
        hw = diag_hw(W - hw - xb, CH - h, D)
    d = poly((xb, 0), (xb + hw, 0), (W, CH - h), (W - hw, CH - h))
    return [rect(0, CH - h, W, CH), d], W, (fig_sb(p, W),) * 2


@glyph("eight", "8")
def g_8(p):
    v, h = fig_strokes(p)
    W = fig_width(p)
    ym = CH * 0.545
    lo_o = Ellipse(0, -O, W, ym + h * 0.5, 0.62)
    lo_i = Ellipse(v, -O + h, W - v, ym - h * 0.5, 0.64)
    up_o = Ellipse(W * 0.07, ym - h * 0.5, W * 0.93, CH + O, 0.62)
    up_i = Ellipse(W * 0.07 + v * 0.95, ym + h * 0.5, W * 0.93 - v * 0.95, CH + O - h, 0.64)
    return ring(lo_o, lo_i) + ring(up_o, up_i), W, (fig_sb(p, W),) * 2


@glyph("nine", "9")
def g_9(p):
    c, w, sb = g_6(p)
    return rotate180(c, w / 2, CH / 2), w, sb


# --- punctuation & symbols ------------------------------------------------

def dot_size(p):
    return p.V * 1.08 + 10


@glyph("space", " ")
def g_space(p):
    return [], 0, (136 + p.dV * 0.3, 136 + p.dV * 0.3)


@glyph("period", ".")
def g_period(p):
    d = dot_size(p)
    return [rect(0, 0, d, d)], d, (p.SB, p.SB)


@glyph("comma", ",")
def g_comma(p):
    d = dot_size(p)
    tail = poly((d * 0.25, -d * 1.1), (d * 0.62, -d * 1.1), (d, 0), (d * 0.0, 0))
    tail = poly((d * 0.08, -d * 1.05), (d * 0.48, -d * 1.05), (d, d * 0.3), (0, d * 0.3))
    return [rect(0, 0, d, d), tail], d, (p.SB, p.SB)


@glyph("colon", ":")
def g_colon(p):
    d = dot_size(p)
    return [rect(0, 0, d, d), rect(0, XH - d, d, XH)], d, (p.SB, p.SB)


@glyph("semicolon", ";")
def g_semicolon(p):
    c, d, sb = g_comma(p)
    return c + [rect(0, XH - d, d, XH)], d, sb


@glyph("exclam", "!")
def g_exclam(p):
    d = dot_size(p)
    V = p.VC
    x = (d - V) / 2
    stem = poly((x + V * 0.12, d + 80 + p.dV * 0.3), (x + V * 0.88, d + 80 + p.dV * 0.3), (x + V, CH), (x, CH))
    return [rect(0, 0, d, d), stem], d, (p.SB * 1.1, p.SB * 1.1)


@glyph("question", "?")
def g_question(p):
    v, h, V = p.VR, p.HR, p.V
    W = 390 + p.dV * 0.8
    ry = CH * 0.27
    outer = Ellipse(0, CH + O - 2 * ry, W, CH + O, 0.62)
    inner = Ellipse(v, CH + O - 2 * ry + h, W - v, CH + O - h, 0.64)
    yt = outer.cy - 0.05 * ry
    arc = band(outer, inner, (3, 0.0), outer.at_y(5, yt), (3, 0.0), inner.at_y(5, yt))
    d = dot_size(p)
    xs = W / 2 - V / 2 + 6
    stem = rect(xs, d + 80 + p.dV * 0.3, xs + V, outer.b + h * 0.5)
    neck = poly((xs, outer.b + h * 0.2), (xs + V, outer.b + h * 0.2), (outer.cx + 4, outer.b + h), (outer.cx - V + 4, outer.b + 2))
    neck = rect(xs, outer.b - 1, outer.cx + 6, outer.b + h)
    return [arc, stem, neck, rect(W / 2 - d / 2 + 6, 0, W / 2 + d / 2 + 6, d)], W, (p.SBR, p.SBR)


@glyph("quotesingle", "'")
def g_quotesingle(p):
    V = p.V
    return [poly((V * 0.15, CH - 240), (V * 0.85, CH - 240), (V, CH), (0, CH))], V, (p.SB, p.SB)


@glyph("quotedbl", '"')
def g_quotedbl(p):
    V = p.V
    gap = 80 + p.dV * 0.2
    one = poly((V * 0.15, CH - 240), (V * 0.85, CH - 240), (V, CH), (0, CH))
    return [one, translate([one], V + gap)[0]], 2 * V + gap, (p.SB, p.SB)


@glyph("grave", "`")
def g_grave(p):
    D = p.D * 0.9
    c = [stroke((0, XH + 230), (140, XH + 130), D)]
    x0, _, x1, _ = bounds(c)
    return translate(c, -x0), x1 - x0, (p.SB, p.SB)


@glyph("hyphen", "-")
def g_hyphen(p):
    w = 220 + p.dV * 0.4
    y = XH * 0.42
    return [rect(0, y, w, y + p.H * 1.05)], w, (p.SBR + 10, p.SBR + 10)


@glyph("underscore", "_")
def g_underscore(p):
    w = 500
    return [rect(0, -140, w, -140 + p.H)], w, (0, 0)


def bracket_paren(p, mirror=False):
    V = p.V * 1.0
    w = 190 + p.dV * 0.6
    outer = Ellipse(0, DSC + 10, w * 2.4, ASC + 40, 0.56)
    inner = Ellipse(V * 1.0, DSC + 10 + 26, w * 2.4 - V, ASC + 14, 0.56)
    yt = outer.cy + 0.84 * outer.ry
    yb = outer.cy - 0.84 * outer.ry
    c = [band(outer, inner, outer.at_y(1, yt), outer.at_y(2, yb), inner.at_y(1, yt), inner.at_y(2, yb))]
    x0, _, x1, _ = bounds(c)
    c = translate(c, -x0)
    ink = outer.x_at(yt, "left") - x0
    ink = max(s[-1][0] for s in c[0][1:] if True)
    if mirror:
        c = mirror_x(c, ink)
    return c, ink


@glyph("parenleft", "(")
def g_parenleft(p):
    c, w = bracket_paren(p)
    return c, w, (p.SBR + 20, p.SBR)


@glyph("parenright", ")")
def g_parenright(p):
    c, w = bracket_paren(p, True)
    return c, w, (p.SBR, p.SBR + 20)


@glyph("bracketleft", "[")
def g_bracketleft(p):
    V, h = p.V, p.H
    w = 180 + p.dV * 0.4
    return [rect(0, DSC + 30, V, ASC + 20), rect(V / 2, DSC + 30, w, DSC + 30 + h),
            rect(V / 2, ASC + 20 - h, w, ASC + 20)], w, (p.SB, p.SBD + 10)


@glyph("bracketright", "]")
def g_bracketright(p):
    c, w, sb = g_bracketleft(p)
    return mirror_x(c, w), w, sb[::-1]


@glyph("braceleft", "{")
def g_braceleft(p):
    """Each half is an arm curving into the stem and the stem curving into a
    flat middle point; the lower half mirrors the upper."""
    V, h = p.V * 0.9, p.H * 0.92
    top, bot = ASC + 20, DSC + 30
    mid = (top + bot) / 2
    R = 92 + p.dV * 0.35  # corner radius, across
    Rv = R * 1.15  # and down
    nub = 80 + p.dV * 0.2  # how far the middle point reaches past the curve
    xs = nub + R - V  # the stem's left edge
    # top arm into the stem
    ao = Ellipse(xs, top - 2 * Rv, xs + 2 * R, top, 0.6)
    ai = Ellipse(xs + V, top - 2 * Rv + h, xs + 2 * R, top - h, 0.62)
    arm_end = ao.cx + R * 0.55
    arm = band(ao, ai, (1, 0.0), (1, 1.0))
    # the stem into the middle point
    no = Ellipse(xs + V - 2 * R, mid - h / 2, xs + V, mid - h / 2 + 2 * Rv, 0.6)
    ni = Ellipse(no.l + V, mid + h / 2, xs, no.t - h, 0.62)
    turn = band(no, ni, (3, 0.0), (3, 1.0))
    upper = [rect(ao.cx - 1, top - h, arm_end, top), arm, rect(xs, no.cy, xs + V, ao.cy), turn]
    c = upper + flip_y(upper, mid) + [rect(0, mid - h / 2, no.cx + 1, mid + h / 2)]
    return c, arm_end, (p.SB * 0.7, p.SBD + 18)


@glyph("braceright", "}")
def g_braceright(p):
    c, w, sb = g_braceleft(p)
    return mirror_x(c, w), w, sb[::-1]


@glyph("slash", "/")
def g_slash(p):
    w = 300 + p.dV * 0.4
    D = p.D * 0.92
    hw = diag_hw(w, ASC - DSC + 40, D)
    return [poly((0, DSC + 30), (hw, DSC + 30), (w, ASC + 20), (w - hw, ASC + 20))], w, (p.SBD, p.SBD)


@glyph("backslash", "\\")
def g_backslash(p):
    c, w, sb = g_slash(p)
    return mirror_x(c, w), w, sb


@glyph("bar", "|")
def g_bar(p):
    return [rect(0, DSC + 30, p.V * 0.9, ASC + 20)], p.V * 0.9, (p.SB * 1.3, p.SB * 1.3)


def math_width(p):
    return 470 + p.dV * 0.6


def math_sb(p, ink):
    return ((math_width(p) + 2 * p.SBR) - ink) / 2


@glyph("plus", "+")
def g_plus(p):
    w = math_width(p) - 50
    h = p.H
    cy = 300
    return [rect(0, cy - h / 2, w, cy + h / 2), rect(w / 2 - h / 2, cy - w / 2, w / 2 + h / 2, cy + w / 2)], w, (math_sb(p, w),) * 2


@glyph("equal", "=")
def g_equal(p):
    w = math_width(p) - 50
    h = p.H
    cy = 300
    g = 70 + p.dV * 0.3
    return [rect(0, cy - g / 2 - h, w, cy - g / 2), rect(0, cy + g / 2, w, cy + g / 2 + h)], w, (math_sb(p, w),) * 2


@glyph("less", "<")
def g_less(p):
    w = math_width(p) - 80
    D = p.D * 0.95
    cy, hh = 300, 210
    hw = diag_hw(w, hh, D)
    up = poly((0, cy - D * 0.6), (hw, cy - D * 0.6), (w, cy + hh - D * 0.7), (w, cy + hh), )
    up = poly((0, cy), (w, cy + hh - hw * hh / w), (w, cy + hh), (0, cy + hw * hh / w * 0.0))
    t = D * math.hypot(w, hh) / w  # vertical thickness of the stroke
    up = poly((0, cy - t / 2), (w, cy + hh - t), (w, cy + hh), (0, cy + t / 2))
    dn = poly((0, cy - t / 2), (w, cy - hh), (w, cy - hh + t), (0, cy + t / 2))
    return [up, dn], w, (math_sb(p, w),) * 2


@glyph("greater", ">")
def g_greater(p):
    c, w, sb = g_less(p)
    return mirror_x(c, w), w, sb


@glyph("asciicircum", "^")
def g_asciicircum(p):
    w = math_width(p) - 60
    D = p.D * 0.95
    y0, y1 = 360, CH
    c, _ = v_shape(p, w, y1 - y0, D, apex=D * 0.8)
    c = flip_y(c, (y1 - y0) / 2)
    c = translate(c, 0, y0)
    return c, w, (math_sb(p, w),) * 2


@glyph("asciitilde", "~")
def g_asciitilde(p):
    w = math_width(p) - 40
    t = p.H * 1.05
    cy, a = 300, 46 + p.dV * 0.1
    pts_top = [(0, cy - a * 0.3 + t / 2), (w * 0.3, cy + a + t / 2), (w * 0.7, cy - a + t / 2), (w, cy + a * 0.3 + t / 2)]
    c = [
        (0, cy - a * 0.3 - t / 2),
        ("c", (w * 0.3, cy + a - t / 2 - 30), (w * 0.62, cy - a - t / 2 - 10), (w, cy + a * 0.3 - t / 2)),
        ("l", (w, cy + a * 0.3 + t / 2)),
        ("c", (w * 0.7, cy - a + t / 2 + 30), (w * 0.38, cy + a + t / 2 + 10), (0, cy - a * 0.3 + t / 2)),
    ]
    del pts_top
    return [c], w, (math_sb(p, w),) * 2


@glyph("asterisk", "*")
def g_asterisk(p):
    t = p.H * 0.95
    L = 130 + p.dV * 0.2
    cx, cy = L, CH - L * 1.0
    spoke = rect(cx - t / 2, cy, cx + t / 2, cy + L)
    c = [rotate([spoke], a, cx, cy)[0] for a in (0, 72, 144, 216, 288)]
    x0, y0, x1, y1 = bounds(c)
    c = translate(c, -x0, CH - y1)
    return c, x1 - x0, (p.SBR, p.SBR)


@glyph("numbersign", "#")
def g_numbersign(p):
    w = 480 + p.dV * 0.5
    t = p.H * 0.98
    V = p.V * 0.92
    y0, y1 = 0, CH - 40
    sl = 40
    s1 = diag(w * 0.30 - sl, y0, w * 0.30 + sl, y1, V, "center")
    s2 = diag(w * 0.66 - sl, y0, w * 0.66 + sl, y1, V, "center")
    h1 = rect(0, 220, w, 220 + t)
    h2 = rect(0, 450, w, 450 + t)
    return [s1, s2, h1, h2], w, (p.SBD + 10, p.SBD + 10)


@glyph("percent", "%")
def g_percent(p):
    v, h = p.V * 0.9, p.H * 0.88
    rw = 210 + p.dV * 0.4
    rh = 300
    gap = 140 + p.dV * 0.3
    w = 2 * rw + gap
    r1 = ring(Ellipse(0, CH - rh, rw, CH, 0.6), Ellipse(v, CH - rh + h, rw - v, CH - h, 0.62))
    r2 = ring(Ellipse(w - rw, 0, w, rh, 0.6), Ellipse(w - rw + v, h, w - v, rh - h, 0.62))
    sl = diag(rw * 0.6, 0, w - rw * 0.6, CH, p.D * 0.92, "center")
    return r1 + r2 + [sl], w, (p.SBR, p.SBR)


@glyph("dollar", "$")
def g_dollar(p):
    c, w, sb = GLYPHS["S"][1](p)
    V = p.V * 0.82
    return c + [rect(w / 2 - V / 2, -90, w / 2 + V / 2, CH + 90)], w, sb


def _mid(e1, e2, pos):
    a, b = e1.point(pos), e2.point(pos)
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def _leave(e_o, e_i, seg, target, flip=False):
    """Where a straight stroke heading for `target` should leave a curved
    stroke: the point on quadrant `seg` whose direction best matches it."""
    best = None
    for k in range(2, 99):
        t = k / 100
        a, b = e_o.point((seg, t - 0.01)), e_o.point((seg, t + 0.01))
        tang = math.atan2(b[1] - a[1], b[0] - a[0])
        if flip:
            tang += math.pi
        m = _mid(e_o, e_i, (seg, t))
        aim = math.atan2(target[1] - m[1], target[0] - m[0])
        err = abs(math.atan2(math.sin(tang - aim), math.cos(tang - aim)))
        if best is None or err < best[0]:
            best = (err, t, m)
    return best[1], best[2]


@glyph("ampersand", "&")
def g_ampersand(p):
    """A small loop on top, two strokes crossing under it (one down into the
    bowl, one out to the foot), and an open bowl ending in a level arm. Both
    strokes leave the loop along its own curve, so the joins are clean."""
    v, h = p.VR * 0.96, p.HR
    D = p.D * 0.98
    W = 610 + p.dV * 0.9
    lx, lw = W * 0.15, 236 + p.dV * 1.3
    lo = Ellipse(lx, CH * 0.58, lx + lw, CH + O, 0.6)
    li = Ellipse(lx + v, CH * 0.58 + h, lx + lw - v, CH + O - h, 0.62)
    bo = Ellipse(0, -O, W * 0.80, CH * 0.60, 0.6)
    bi = Ellipse(v, -O + h, W * 0.80 - v, CH * 0.60 - h, 0.62)
    # The cross-stroke runs from the loop's right side down into the bowl's
    # upper left. Pick the bowl's start so the bowl is already heading the
    # stroke's way there, as the loop is at the other end: no corners.
    best = None
    for k in range(20, 95):
        tb = k / 100
        pb = _mid(bo, bi, (1, tb))
        _, pl = _leave(lo, li, 3, pb, flip=True)
        a, b = bo.point((1, tb - 0.01)), bo.point((1, tb + 0.01))
        tang = math.atan2(b[1] - a[1], b[0] - a[0])
        aim = math.atan2(pb[1] - pl[1], pb[0] - pl[0])
        err = abs(math.atan2(math.sin(tang - aim), math.cos(tang - aim)))
        if best is None or err < best[0]:
            best = (err, tb, pb, pl)
    _, tb, pb, pl = best
    start = (1, tb)
    y_arm = CH * 0.40
    bowl = band(bo, bi, start, bo.at_y(4, y_arm), start, bi.at_y(4, y_arm))
    link = stroke(pl, pb, D)
    # from the loop's left side out to the foot (quadrant 2 runs down-right)
    hw = diag_hw(W * 0.5, CH * 0.6, D)
    foot = (W - hw / 2, 0)
    _, pf = _leave(lo, li, 2, foot)
    leg = stroke(pf, foot, D * 1.02, ("p",), ("h", 0))
    return ring(lo, li) + [bowl, link, leg], W, (p.SBR, p.SBD)


@glyph("at", "@")
def g_at(p):
    v, h = p.V * 0.80, p.H * 0.80
    w = 830 + p.dV * 0.8
    outer = Ellipse(0, -150, w, CH + 10, 0.6)
    inner = Ellipse(v, -150 + h, w - v, CH + 10 - h, 0.62)
    big = band(outer, inner, (0, 0.0), (3, 0.45))
    # a single-storey a in the middle: a bowl and a stem flush with its top
    yb, yt = 96, 492
    bw = 236 + p.dV * 0.9
    bx = w / 2 - bw / 2 - 34
    bo = Ellipse(bx, yb, bx + bw, yt, 0.62)
    bi = Ellipse(bx + v, yb + h, bx + bw - v, yt - h, 0.64)
    xs = bx + bw - v * 0.35  # the stem's right edge
    stem = rect(xs - v, yb + h * 0.5, xs, yt)
    # the stem's foot curves out and up into the ring's right side
    fo = Ellipse(xs - v - (w - xs + v), yb, w, 2 * outer.cy - yb, 0.6)
    fi = Ellipse(fo.l + v, yb + h, w - v, fo.t - h, 0.62)
    foot = band(fo, fi, (3, 0.0), (3, 1.0))
    return [big, stem, foot] + ring(bo, bi), w, (p.SBR, p.SBR)


# Shapes drawn as pen strokes replace the constructions above.
import penglyphs  # noqa: E402,F401
