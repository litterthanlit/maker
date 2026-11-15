"""Hypher's glyphs: machined letters, drawn in code.

Every letter is built from flat-sided polygons with rounded corners, after the
Hypher mark: sides are straight and curves happen only in corners. Each
function takes the weight parameters and returns (contours, ink, (lsb, rsb)).

How round the letters are is a style: a named set of numbers in STYLES. Each
style is a version of Hypher; set_style() picks one before drawing.
"""

import os

from core import geometry
from core.geometry import diag_hw, rotate180

XH, ASC, DSC = 560, 740, -185  # x-height; ascender and descender at 1.32 and 0.33 x-heights
CH = ASC

REGULAR_STEM = 92
SB = 96  # sidebearing beside a flat side; the lockup's loose tracking is built in

# Ink widths and sidebearings at Regular, per letter. Wordmark's are measured
# from the lockup's font (Michroma), with the lockup's +0.080em in the sides.
WM_WIDTHS = {
    "a": 635, "b": 685, "c": 670, "d": 685, "e": 657, "f": 451, "g": 671, "h": 654, "i": 93,
    "j": 251, "k": 622, "l": 93, "m": 1078, "n": 654, "o": 686, "p": 685, "q": 685, "r": 351,
    "s": 643, "t": 470, "u": 654, "v": 710, "w": 1021, "x": 698, "y": 707, "z": 591,
}
WM_SIDES = {
    "a": (103, 100), "b": (104, 87), "c": (87, 87), "d": (87, 104), "e": (87, 98), "f": (102, 40),
    "g": (89, 104), "h": (104, 101), "i": (102, 102), "j": (22, 133), "k": (105, 40), "l": (133, 133),
    "m": (104, 101), "n": (104, 101), "o": (87, 87), "p": (104, 87), "q": (87, 104), "r": (112, 97),
    "s": (107, 102), "t": (127, 114), "u": (100, 104), "v": (71, 71), "w": (74, 74), "x": (87, 87),
    "y": (62, 73), "z": (102, 102),
}
# The other versions are a little narrower and tighter; h y p e r n o keep the
# numbers they were first drawn with.
WIDTHS = {c: round(w * 0.92) for c, w in WM_WIDTHS.items()}
WIDTHS.update({"n": 600, "h": 600, "o": 640, "p": 640, "e": 640, "r": 360, "y": 620})
SIDES = {c: (l * 0.93, r * 0.93) for c, (l, r) in WM_SIDES.items()}
SIDES.update({"n": (SB, SB), "h": (SB, SB), "o": (SB * 0.92,) * 2, "p": (SB, SB * 0.92),
              "e": (SB * 0.92,) * 2, "r": (SB, SB * 0.55), "y": (SB * 0.5,) * 2})

# The versions, named after machining. Numbers:
#   radius  outer corner radius, in x-heights. The mark's own 0.043 reads as
#           pixel type at letter size; 0.26 drifts back to a squircle.
#   smooth  0 joins a corner to its sides as a circle; higher eases it in,
#           which reads rounder at the same radius. inner_smooth, if given,
#           sets it for counters alone.
#   inner   how far inside the outer corner a counter's corner sits, in stems:
#           smaller keeps more of the outer radius, so counters read rounder.
#   term    radius on cut ends (stem feet, terminals, the r's arm), in
#           x-heights. The mark rounds every corner, its flat ends included.
MILL = dict(radius=0.20, smooth=0.0, inner=0.75, term=0.0)
STYLES = {
    "Mill": MILL,  # 0.200: crisp, circular corners, sharp cuts
    "Fillet": {**MILL, "radius": 0.235},  # bigger corners
    "Polish": {**MILL, "smooth": 1.0},  # corners eased into the sides
    "Bore": {**MILL, "inner": 0.45},  # rounder counters
    "Deburr": {**MILL, "term": 0.025},  # softened cut ends
    "Finish": dict(radius=0.215, smooth=0.6, inner=0.55, term=0.02),  # a little of each: the default
    # The current wordmark's letters (Michroma), redrawn in this system. Widths,
    # sidebearings (with the lockup's +0.080em), stem tops and the e's bar and
    # terminal are measured from the lockup; the corners were fitted by
    # maximising overlap with its outlines: h 93%, r 93%, p 91%, e 85%, y 71%
    # (Michroma's y arms are not mirror images; these are).
    "Wordmark": dict(
        radius=0.23, smooth=2.2, inner_smooth=1.53, inner=0.55, term=0.0,
        stem_tops="square", e_bar=0.454, e_term=0.297, y_tail="hook", y_tail_end=0.19,
        widths=WM_WIDTHS,
        sides=WM_SIDES,
        kern=[("e", "r", -18)],  # e-r reads loose in the lockup: both letters open to the right
    ),
}
DEFAULT_STYLE = "Wordmark"



STYLE = {}


def set_style(name):
    s = {"stem_tops": "round", "e_bar": 0.44, "e_term": 0.27, "y_tail": "straight", "y_tail_end": 0.18, "y_bend": 1.0,
         "widths": {}, "sides": {}, "kern": []}
    s.update(STYLES[name])
    for key in ("radius", "smooth", "inner", "term"):  # HYPHER_RADIUS etc. try a mix without editing
        if f"HYPHER_{key.upper()}" in os.environ:
            s[key] = float(os.environ[f"HYPHER_{key.upper()}"])
    s.setdefault("inner_smooth", s["smooth"])
    STYLE.clear()
    STYLE.update(s, name=name)


class P:
    """Weight parameters, all derived from the stem and the style."""

    def __init__(self, wght, stem):
        self.wght = wght
        self.V = stem  # vertical stroke
        self.H = round(stem * 0.86)  # horizontal stroke: a little thinner, so it looks equal
        self.ro = STYLE["radius"] * XH  # outer corners
        self.ri = max(self.ro - STYLE["inner"] * stem, 0.3 * self.ro, 4)  # counters follow the outer corner
        self.rt = STYLE["term"] * XH  # cut ends
        self.grow = (stem - REGULAR_STEM) * 2.0  # letters widen as they gain weight, keeping counters open

    def w(self, letter):
        return STYLE["widths"].get(letter, WIDTHS[letter]) + self.grow

    def sides(self, letter):
        return STYLE["sides"].get(letter, SIDES[letter])


GLYPHS = {}


def glyph(name, char):
    def deco(fn):
        GLYPHS[name] = (char, fn)
        return fn
    return deco


def rounded(*corners):
    return geometry.rounded(*corners, smooth=STYLE["smooth"])


def box(x0, y0, x1, y1, bl, br, tr, tl):
    """A rectangle with its own radius at each corner, counter-clockwise."""
    return rounded((x0, y0, bl), (x1, y0, br), (x1, y1, tr), (x0, y1, tl))


def hole(x0, y0, x1, y1, r):
    """A counter: a rounded rectangle running clockwise."""
    return geometry.rounded((x0, y0, r), (x0, y1, r), (x1, y1, r), (x1, y0, r), smooth=STYLE["inner_smooth"])


def stem_top(p, x0, bottom):
    """With square stem tops (the wordmark's), a stem whose flat top sits at the x-height."""
    if STYLE["stem_tops"] != "square":
        return []
    return [box(x0, bottom, x0 + p.V, XH, p.rt, p.rt, 0, p.rt)]


def arch(p, x0, x1, top, bottom=0, left_bottom=None):
    """The n's arch: two stems joined by a flat top, open at the bottom.

    left_bottom ends the left leg higher, as a terminal (the a's hook)."""
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    lb = bottom if left_bottom is None else left_bottom
    return rounded(
        (x0, lb, rt), (x0 + V, lb, rt), (x0 + V, top - H, ri), (x1 - V, top - H, ri),
        (x1 - V, bottom, rt), (x1, bottom, rt), (x1, top, ro), (x0, top, ro),
    )


def rpoly(*corners):
    """rounded(), with the points put in counter-clockwise order first."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(corners, corners[1:] + corners[:1]))
    return rounded(*(corners if area > 0 else corners[::-1]))


def square(p, c):
    """A corner that is square on the wordmark (where its stems run straight into a bowl), round elsewhere."""
    return p.rt if STYLE["stem_tops"] == "square" else c


def dot(p, x0):
    """The i's and j's dot: a stem-wide square whose top sits on the ascender."""
    return box(x0, ASC - p.V, x0 + p.V, ASC, p.rt, p.rt, p.rt, p.rt)


def bowl(p, x0, x1, bottom=0, top=XH):
    return [box(x0, bottom, x1, top, p.ro, p.ro, p.ro, p.ro),
            hole(x0 + p.V, bottom + p.H, x1 - p.V, top - p.H, p.ri)]


@glyph("space", " ")
def g_space(p):
    return [], 0, (150, 150)


@glyph("n", "n")
def g_n(p):
    W = p.w("n")
    return stem_top(p, 0, 0) + [arch(p, 0, W, XH)], W, p.sides("n")


@glyph("h", "h")
def g_h(p):
    W = p.w("h")
    stem = box(0, 0, p.V, ASC, p.rt, p.rt, p.rt, p.rt)
    return [stem, arch(p, 0, W, XH)], W, p.sides("h")


@glyph("o", "o")
def g_o(p):
    W = p.w("o")
    return bowl(p, 0, W), W, p.sides("o")


@glyph("p", "p")
def g_p(p):
    W = p.w("p")
    tl = p.rt if STYLE["stem_tops"] == "square" else p.ro
    stem = box(0, DSC, p.V, XH, p.rt, p.rt, 0, tl)
    return [stem] + bowl(p, 0, W), W, p.sides("p")


@glyph("e", "e")
def g_e(p):
    """A bowl with a crossbar; the lower right opens above a flat terminal."""
    W = p.w("e")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    bar0 = XH * STYLE["e_bar"]  # bottom of the crossbar
    bar1 = bar0 + H
    term = XH * STYLE["e_term"]  # top of the lower terminal
    outer = rounded(
        (0, 0, ro), (W, 0, ro), (W, term, rt), (W - V, term, rt), (W - V, H, ri), (V, H, ri),
        (V, bar0, ri), (W, bar0, rt), (W, XH, ro), (0, XH, ro),
    )
    eye = hole(V, bar1, W - V, XH - H, ri)
    return [outer, eye], W, p.sides("e")


@glyph("r", "r")
def g_r(p):
    """A stem and a flat arm, cut square at the right."""
    W = p.w("r")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    c = rounded(
        (0, 0, rt), (V, 0, rt), (V, XH - H, ri), (W, XH - H, rt), (W, XH, ro), (0, XH, ro),
    )
    return stem_top(p, 0, 0) + [c], W, p.sides("r")


@glyph("y", "y")
def g_y(p):
    """A symmetric V meeting on the baseline; the right arm runs on into the descender."""
    W = p.w("y")
    V, r, rt = p.V, p.ri, p.rt
    cx = W / 2  # the arms' centre lines cross here, on the baseline
    hw = diag_hw(cx, XH, V)  # horizontal width of either arm
    slope = (cx - hw / 2) / XH  # x per unit of height, along a centre line
    xd = cx + slope * DSC  # right arm's centre at the descender
    if STYLE["y_tail"] == "hook":
        # The wordmark's tail: the arm bends into a flat foot running left.
        H, ro = p.H, p.ro

        def edge_x(y, off):  # the right arm's edge, offset from its centre line
            return cx + slope * y + off

        xt = STYLE["y_tail_end"] * W  # where the foot stops
        right = rounded(
            (xt, DSC, rt), (edge_x(DSC, hw / 2), DSC, ro * STYLE["y_bend"]), (W, XH, r), (W - hw, XH, rt),
            (edge_x(DSC + H, -hw / 2), DSC + H, p.ri * STYLE["y_bend"]), (xt, DSC + H, rt),
        )
    else:
        right = rounded(
            (xd - hw / 2, DSC, r), (xd + hw / 2, DSC, rt), (W, XH, r), (W - hw, XH, rt),
        )

    # The left arm mirrors the right and stops on the right arm's centre line,
    # so the join has no foot. Left centre: x = cx - slope*y; right: x = cx + slope*y.
    def meet(edge):
        y = edge / (2 * slope)
        return (cx + slope * y, y, 0)

    left = rounded((0, XH, r), meet(-hw / 2), meet(hw / 2), (hw, XH, rt))
    return [right, left], W, p.sides("y")



@glyph("a", "a")
def g_a(p):
    """A hook over a bowl: the hook's right leg is the stem; the bowl tucks under it."""
    W = p.w("a")
    top = XH * 0.58 + (p.H - 79) * 0.6  # top of the bowl, raised with weight so its counter stays open
    hook = arch(p, 0, W, XH, left_bottom=XH * 0.73)
    return [hook] + bowl(p, 0, W, top=top), W, p.sides("a")


@glyph("b", "b")
def g_b(p):
    W = p.w("b")
    stem = box(0, 0, p.V, ASC, square(p, p.ro), 0, p.rt, p.rt)
    return [stem] + bowl(p, 0, W), W, p.sides("b")


@glyph("c", "c")
def g_c(p):
    """A bowl opened on the right between two flat terminals."""
    W = p.w("c")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    t0, t1 = XH * 0.334, XH * 0.686
    c = rounded(
        (0, 0, ro), (W, 0, ro), (W, t0, rt), (W - V, t0, rt), (W - V, H, ri), (V, H, ri),
        (V, XH - H, ri), (W - V, XH - H, ri), (W - V, t1, rt), (W, t1, rt), (W, XH, ro), (0, XH, ro),
    )
    return [c], W, p.sides("c")


@glyph("d", "d")
def g_d(p):
    W = p.w("d")
    stem = box(W - p.V, 0, W, ASC, 0, square(p, p.ro), p.rt, p.rt)
    return [stem] + bowl(p, 0, W), W, p.sides("d")


@glyph("f", "f")
def g_f(p):
    """The r's arm raised above the ascender, with a crossbar at the x-height."""
    W = p.w("f")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    x0, top = W * 0.208, XH * 1.40
    c = rounded(
        (x0, 0, rt), (x0 + V, 0, rt), (x0 + V, top - H, ri), (W, top - H, rt), (W, top, rt), (x0, top, ro),
    )
    bar = box(0, XH - H, W, XH, rt, rt, rt, rt)
    return [c, bar], W, p.sides("f")


@glyph("g", "g")
def g_g(p):
    """A bowl with a stem that runs down into a tail ending in an upturned terminal."""
    W = p.w("g")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    deep, xt = -213, W * 0.037  # the g's tail goes below the other descenders
    tip = min(deep + H + XH * 0.12, -30)  # the terminal stands 0.12 x-heights above the tail, clear of the bowl
    tail = rounded(
        (xt, tip, rt), (xt, deep, ro), (W, deep, ro), (W, XH, square(p, ro)), (W - V, XH, rt),
        (W - V, deep + H, ri), (xt + V, deep + H, ri), (xt + V, tip, rt),
    )
    return [tail] + bowl(p, 0, W), W, p.sides("g")


@glyph("i", "i")
def g_i(p):
    stem = box(0, 0, p.V, XH, p.rt, p.rt, p.rt, p.rt)
    return [stem, dot(p, 0)], p.V, p.sides("i")


@glyph("j", "j")
def g_j(p):
    """A stem that hooks left below the baseline into a flat-cut tail."""
    W = p.w("j")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    c = rounded(
        (0, DSC + H, rt), (0, DSC, rt), (W, DSC, ro), (W, XH, rt), (W - V, XH, rt), (W - V, DSC + H, ri),
    )
    return [c, dot(p, W - V)], W, p.sides("j")


@glyph("k", "k")
def g_k(p):
    """A stem with an arm to the x-height and a leg to the baseline.

    The outer edges of arm and leg meet the stem at fixed heights, as in the
    wordmark's k; the crotch is wherever their inner edges cross. Arm and leg
    are one outline, so neither can poke past the other."""
    W = p.w("k")
    V, rt = p.V, p.rt
    t = V * 0.98  # diagonals look heavier than stems at the same thickness
    ya, yl = XH * 0.563, XH * 0.513  # where the arm's upper and the leg's lower edge leave the stem
    xt, xb = W * 0.748, W * 0.777  # the arm's top-left and the leg's bottom-left
    ha = diag_hw(xt - V, XH - ya, t)
    hl = diag_hw(xb - V, yl, t)

    def line(p0, p1):  # x = a + b*y through two points
        b = (p1[0] - p0[0]) / (p1[1] - p0[1])
        return (p0[0] - b * p0[1], b)

    def cross(l1, l2):
        y = (l2[0] - l1[0]) / (l1[1] - l2[1])
        return (l1[0] + l1[1] * y, y)

    arm_in = line((V + ha, ya), (xt + ha, XH))
    leg_in = line((V + hl, yl), (xb + hl, 0))
    crotch = cross(arm_in, leg_in)
    x0 = V - 2  # just inside the stem, so the outlines overlap
    diagonals = rounded(
        (x0, yl, 0), (xb, 0, rt), (xb + hl, 0, rt), crotch + (0,), (xt + ha, XH, rt), (xt, XH, rt), (x0, ya, 0),
    )
    stem = box(0, 0, V, ASC, rt, rt, rt, rt)
    return [stem, diagonals], W, p.sides("k")


@glyph("l", "l")
def g_l(p):
    return [box(0, 0, p.V, ASC, p.rt, p.rt, p.rt, p.rt)], p.V, p.sides("l")


@glyph("m", "m")
def g_m(p):
    """Two n arches sharing the middle stem, with equal counters."""
    W = p.w("m")
    W1 = (W + p.V) / 2
    return stem_top(p, 0, 0) + [arch(p, 0, W1, XH), arch(p, W1 - p.V, W, XH)], W, p.sides("m")


@glyph("q", "q")
def g_q(p):
    W = p.w("q")
    stem = box(W - p.V, DSC, W, XH, p.rt, p.rt, square(p, p.ro), 0)
    return [stem] + bowl(p, 0, W), W, p.sides("q")


@glyph("s", "s")
def g_s(p):
    """Two bowls sharing a middle bar, each opening onto a flat terminal."""
    W = p.w("s")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    m0 = XH * 0.523 - H / 2  # bottom of the middle bar
    m1 = m0 + H
    t0, t1 = XH * 0.29, XH * 0.72  # tops of the lower terminal, bottom of the upper
    c = rounded(
        (0, t0, rt), (0, 0, ro), (W, 0, ro), (W, m1, ro), (V, m1, ri), (V, XH - H, ri),
        (W - V, XH - H, ri), (W - V, t1, rt), (W, t1, rt), (W, XH, ro), (0, XH, ro), (0, m0, ro),
        (W - V, m0, ri), (W - V, H, ri), (V, H, ri), (V, t0, rt),
    )
    return [c], W, p.sides("s")


@glyph("t", "t")
def g_t(p):
    """A stem that turns right at the baseline into a short upturned foot, with a crossbar."""
    W = p.w("t")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    top, foot = XH * 1.273, XH * 0.436
    c = rounded(
        (0, top, rt), (0, 0, ro), (W, 0, ro), (W, foot, rt), (W - V, foot, rt), (W - V, H, ri),
        (V, H, ri), (V, top, rt),
    )
    bar = box(0, XH - H, W * 0.932, XH, rt, rt, rt, rt)
    return [c, bar], W, p.sides("t")


@glyph("u", "u")
def g_u(p):
    """The n turned upside down: its square stem foot lands on the right."""
    contours, W, _ = g_n(p)
    return rotate180(contours, W / 2, XH / 2), W, p.sides("u")


def v_shape(p, x0, W):
    """Two diagonals meeting on the baseline with a flat foot."""
    V, r, rt = p.V, p.ri, p.rt
    t = V * 0.98
    cx = x0 + W / 2
    hw = t
    for _ in range(4):  # the foot's width and the arms' slope depend on each other
        b = 0.85 * hw
        slope = (W / 2 - b / 2) / XH
        hw = diag_hw(W / 2 - b / 2, XH, t)
    y_in = XH - (W / 2 - hw) / slope  # where the inner edges meet
    return rpoly(
        (x0, XH, r), (cx - b / 2, 0, rt), (cx + b / 2, 0, rt), (x0 + W, XH, r), (x0 + W - hw, XH, rt),
        (cx, y_in, 0), (x0 + hw, XH, rt),
    ), hw


@glyph("v", "v")
def g_v(p):
    W = p.w("v")
    return [v_shape(p, 0, W)[0]], W, p.sides("v")


@glyph("w", "w")
def g_w(p):
    """Two v's whose middle arms coincide."""
    W = p.w("w")
    hw = p.V * 1.3
    for _ in range(4):
        Wv = (W + hw) / 2
        hw = v_shape(p, 0, Wv)[1]
    Wv = (W + hw) / 2
    return [v_shape(p, 0, Wv)[0], v_shape(p, W - Wv, Wv)[0]], W, p.sides("w")


@glyph("x", "x")
def g_x(p):
    W = p.w("x")
    rt = p.rt
    hw = diag_hw(W, XH, p.V * 0.98)
    down = rpoly((0, XH, rt), (hw, XH, rt), (W, 0, rt), (W - hw, 0, rt))
    up = rpoly((W - hw, XH, rt), (W, XH, rt), (hw, 0, rt), (0, 0, rt))
    return [down, up], W, p.sides("x")


@glyph("z", "z")
def g_z(p):
    W = p.w("z")
    H, rt = p.H, p.rt
    hw = diag_hw(W, XH - 2 * H, p.V * 0.98)
    top = box(0, XH - H, W, XH, rt, rt, rt, rt)
    bottom = box(0, 0, W, H, rt, rt, rt, rt)
    diagonal = rpoly((W - hw, XH - H, 0), (W, XH - H, 0), (hw, H, 0), (0, H, 0))
    return [top, bottom, diagonal], W, p.sides("z")

set_style(os.environ.get("HYPHER_STYLE", DEFAULT_STYLE))
