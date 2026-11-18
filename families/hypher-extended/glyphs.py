"""Hypher Extended's glyphs: wide, caps-only letters, drawn in code.

The letters follow a reference wordmark (proof/reference.png). Stems, bars
and cut ends are square; only the corners of bowls are round, with tight
counters. Diagonals run between the stems' inner edges, a stem thick measured
upright. Each function takes the weight parameters and returns
(contours, ink, (lsb, rsb)). Lowercase keys type the capitals.
"""

from core import geometry
from core.geometry import diag_hw, mirror_x, rotate180

CH = 700  # cap height; the figures stand at it too
OV = round(CH * 0.017)  # round letters overshoot the baseline and cap height, as the reference's do

REF_STEM = 165  # the reference wordmark's stem at this cap height; widths below are measured at it

# Ink widths at REF_STEM. N T R O U S are measured from the reference; the rest are drawn to sit with them.
WIDTHS = {
    "A": 1250, "B": 1210, "C": 1225, "D": 1244, "E": 1080, "F": 1060, "G": 1244, "H": 1250, "J": 1100,
    "K": 1230, "L": 1060, "M": 1480, "N": 1290, "O": 1244, "P": 1210, "Q": 1244, "R": 1264, "S": 1238,
    "T": 1225, "U": 1251, "V": 1330, "W": 1900, "X": 1300, "Y": 1300, "Z": 1220,
    "zero": 1060, "one": 560, "two": 1040, "three": 1040, "four": 1080, "five": 1040, "six": 1050,
    "seven": 980, "eight": 1060, "nine": 1050,
    "question": 900, "hyphen": 520, "endash": 700, "emdash": 1100, "parenleft": 360, "parenright": 360,
    "bracketleft": 340, "bracketright": 340, "slash": 640, "plus": 640, "equal": 640, "underscore": 900,
    "ampersand": 1250, "percent": 1250,
}
SB = 78  # beside a flat side: the reference sets letters a stem apart
SIDES = {
    "A": (SB, SB), "B": (SB, 70), "C": (70, 60), "D": (SB, 70), "E": (SB, 60), "F": (SB, 50), "G": (70, SB),
    "H": (SB, SB), "I": (SB, SB), "J": (50, SB), "K": (SB, 30), "L": (SB, 40), "M": (SB, SB), "N": (SB, SB),
    "O": (70, 70), "P": (SB, 60), "Q": (70, 50), "R": (SB, SB), "S": (66, 66), "T": (50, 50), "U": (SB, SB),
    "V": (30, 30), "W": (30, 30), "X": (30, 30), "Y": (30, 30), "Z": (60, 60),
    "zero": (70, 70), "one": (60, SB), "two": (66, 66), "three": (60, 70), "four": (66, SB), "five": (66, 66),
    "six": (70, 66), "seven": (60, SB), "eight": (70, 70), "nine": (66, 70),
    "period": (SB, SB), "comma": (SB, SB), "colon": (SB, SB), "semicolon": (SB, SB), "exclam": (SB, SB),
    "question": (60, SB), "hyphen": (60, 60), "endash": (60, 60), "emdash": (40, 40),
    "quotesingle": (SB, SB), "quotedbl": (SB, SB), "quoteleft": (SB, SB), "quoteright": (SB, SB),
    "quotedblleft": (SB, SB), "quotedblright": (SB, SB), "parenleft": (SB, 50), "parenright": (50, SB),
    "bracketleft": (SB, 50), "bracketright": (50, SB), "slash": (30, 30), "plus": (70, 70), "equal": (70, 70),
    "underscore": (20, 20), "ampersand": (66, 50), "percent": (60, 60),
}

# Corners, fitted to the reference by overlap (proof/fit.py), as fractions of the cap height.
RADIUS = 0.17  # outer corners of bowls
INNER = 0.70  # a counter's corner sits this many stems inside the outer one...
INNER_MIN = 0.02  # ...but never squarer than this
SMOOTH = 0.35  # eases each corner into its sides; 0 joins them as a circle


class P:
    """Weight parameters, all derived from the stem."""

    def __init__(self, wght, stem):
        self.wght = wght
        self.V = stem  # vertical stroke
        self.H = round(stem * 0.93)  # horizontal stroke, as measured in the reference
        self.ro = RADIUS * CH
        self.ri = max(self.ro - INNER * stem, INNER_MIN * CH)
        self.grow = (stem - REF_STEM) * 1.0  # lighter weights narrow a little, keeping their counters

    def w(self, name):
        return WIDTHS[name] + self.grow

    def sides(self, name):
        return SIDES[name]


GLYPHS = {}


def glyph(name, chars):
    def deco(fn):
        GLYPHS[name] = (chars, fn)
        return fn
    return deco


def rounded(*corners):
    return geometry.rounded(*corners, smooth=SMOOTH)


def rpoly(*corners):
    """rounded(), with the points put in counter-clockwise order first."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(corners, corners[1:] + corners[:1]))
    return rounded(*(corners if area > 0 else corners[::-1]))


def box(x0, y0, x1, y1, bl=0, br=0, tr=0, tl=0):
    """A rectangle with its own radius at each corner; square unless given."""
    return rounded((x0, y0, bl), (x1, y0, br), (x1, y1, tr), (x0, y1, tl))


def hole(x0, y0, x1, y1, r):
    """A counter: a rounded rectangle running clockwise."""
    return rounded((x0, y0, r), (x0, y1, r), (x1, y1, r), (x1, y0, r))


def stem(p, x0, y0=0, y1=CH):
    return box(x0, y0, x0 + p.V, y1)


def bar(p, x0, x1, y0):
    return box(x0, y0, x1, y0 + p.H)


def ring(p, x0, y0, x1, y1, ro=None, ri=None):
    ro = p.ro if ro is None else ro
    ri = p.ri if ri is None else ri
    return [box(x0, y0, x1, y1, ro, ro, ro, ro), hole(x0 + p.V, y0 + p.H, x1 - p.V, y1 - p.H, ri)]


def between(p, x0, y0, x1, y1, t=None):
    """A diagonal whose ends are vertical cuts: from x0 at height y0 to x1 at height y1, t thick measured upright.

    This is the N's diagonal: it runs between two stems' inner edges, its ends
    lying along them, so the joins stay sharp."""
    t = p.V * 1.02 if t is None else t
    return rpoly((x0, y0, 0), (x0, y0 - t, 0), (x1, y1 - t, 0), (x1, y1, 0))


def slant(p, xb, yb, xt, yt, t=None):
    """A diagonal cut level at both ends: its left edge from (xb, yb) to (xt, yt), t thick across the stroke."""
    t = p.V * 0.86 if t is None else t
    hw = diag_hw(xt - xb, yt - yb, t)
    return rpoly((xb, yb, 0), (xb + hw, yb, 0), (xt + hw, yt, 0), (xt, yt, 0)), hw


def vee(p, x0, W, top=CH, bottom=0, foot=None):
    """A V standing on a flat foot, its tops cut level."""
    t = p.V * 0.86
    hw = geometry.solve_hw(t, top - bottom, lambda h: W / 2 - (foot if foot is not None else h * 0.6) / 2)
    f = foot if foot is not None else hw * 0.6
    run = W / 2 - f / 2
    yi = top - (top - bottom) * (W / 2 - hw) / run  # where the inner edges meet
    return rpoly((x0, top, 0), (x0 + hw, top, 0), (x0 + W / 2, yi, 0), (x0 + W - hw, top, 0), (x0 + W, top, 0),
                 (x0 + W / 2 + f / 2, bottom, 0), (x0 + W / 2 - f / 2, bottom, 0)), hw


@glyph("space", " ")
def g_space(p):
    return [], 0, (190, 190)


# --- Capitals -------------------------------------------------------------

@glyph("A", "Aa")
def g_A(p):
    """The U turned over, with a bar just under the middle."""
    W = p.w("A")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    y0 = CH * 0.43 - H / 2
    arch = rounded((0, 0, 0), (V, 0, 0), (V, CH - H, ri), (W - V, CH - H, ri), (W - V, 0, 0), (W, 0, 0),
                   (W, CH + OV, ro), (0, CH + OV, ro))
    return [arch, bar(p, V / 2, W - V / 2, y0)], W, p.sides("A")


def bowl_right(p, x0, x1, y0, y1):
    """A bowl square on the left, where it meets a stem: B, D, P, R."""
    return [box(x0, y0, x1, y1, 0, p.ro, p.ro, 0), hole(x0 + p.V, y0 + p.H, x1 - p.V, y1 - p.H, p.ri)]


@glyph("B", "Bb")
def g_B(p):
    W = p.w("B")
    m0 = CH * 0.51 - p.H / 2
    return bowl_right(p, 0, W, 0, m0 + p.H) + bowl_right(p, 0, W * 0.96, m0, CH), W, p.sides("B")


@glyph("C", "Cc")
def g_C(p):
    """The O, open on the right: its bars end square at full width, as the S's top does."""
    W = p.w("C")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    c = rounded((0, -OV, ro), (W, -OV, 0), (W, H, 0), (V, H, ri), (V, CH - H, ri), (W, CH - H, 0), (W, CH + OV, 0),
                (0, CH + OV, ro))
    return [c], W, p.sides("C")


@glyph("D", "Dd")
def g_D(p):
    W = p.w("D")
    return bowl_right(p, 0, W, 0, CH), W, p.sides("D")


@glyph("E", "Ee")
def g_E(p):
    W = p.w("E")
    return [stem(p, 0), bar(p, 0, W, CH - p.H), bar(p, 0, W * 0.92, CH * 0.5 - p.H / 2), bar(p, 0, W, 0)], W, p.sides("E")


@glyph("F", "Ff")
def g_F(p):
    W = p.w("F")
    return [stem(p, 0), bar(p, 0, W, CH - p.H), bar(p, 0, W * 0.92, CH * 0.5 - p.H / 2)], W, p.sides("F")


@glyph("G", "Gg")
def g_G(p):
    """The C, whose right side climbs to a bar reaching back into the counter."""
    W = p.w("G")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    gt, xb = CH * 0.52, W * 0.55
    c = rounded(
        (0, -OV, ro), (W, -OV, ro), (W, gt, 0), (xb, gt, 0), (xb, gt - H, 0), (W - V, gt - H, 0), (W - V, H, ri),
        (V, H, ri), (V, CH - H, ri), (W, CH - H, 0), (W, CH + OV, 0), (0, CH + OV, ro),
    )
    return [c], W, p.sides("G")


@glyph("H", "Hh")
def g_H(p):
    W = p.w("H")
    return [stem(p, 0), stem(p, W - p.V), bar(p, 0, W, CH * 0.5 - p.H / 2)], W, p.sides("H")


@glyph("I", "Ii")
def g_I(p):
    return [stem(p, 0)], p.V, p.sides("I")


@glyph("J", "Jj")
def g_J(p):
    """A stem that rounds into the baseline and turns up in a short square terminal."""
    W = p.w("J")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    jt = CH * 0.32
    c = rounded((0, jt, 0), (0, -OV, ro), (W, -OV, ro), (W, CH, 0), (W - V, CH, 0), (W - V, H, ri), (V, H, ri), (V, jt, 0))
    return [c], W, p.sides("J")


@glyph("K", "Kk")
def g_K(p):
    """An arm and a leg leaving the stem together at mid-height, cut like the N's diagonal."""
    W = p.w("K")
    V = p.V
    t = V * 1.02
    c = CH / 2
    run = W - V
    aw = run * t / (CH - c + t / 2)  # the arm's cut at the cap height, so both its edges stay parallel
    arm = rpoly((V - 1, c - t / 2, 0), (W, CH, 0), (W - aw, CH, 0), (V - 1, c + t / 2, 0))
    leg = rpoly((V - 1, c + t / 2, 0), (W, 0, 0), (W - aw, 0, 0), (V - 1, c - t / 2, 0))
    return [stem(p, 0), arm, leg], W, p.sides("K")


@glyph("L", "Ll")
def g_L(p):
    W = p.w("L")
    return [stem(p, 0), bar(p, 0, W, 0)], W, p.sides("L")


@glyph("M", "Mm")
def g_M(p):
    """Two stems, and two of the N's diagonals meeting on the baseline between them."""
    W = p.w("M")
    V = p.V
    t = V * 1.02
    left = rpoly((V - 1, CH, 0), (V - 1, CH - t, 0), (W / 2, 0, 0), (W / 2, t, 0))
    return [stem(p, 0), stem(p, W - V), left] + mirror_x([left], W), W, p.sides("M")


@glyph("N", "Nn")
def g_N(p):
    W = p.w("N")
    V = p.V
    return [stem(p, 0), stem(p, W - V), between(p, V - 1, CH, W - V + 1, p.V * 1.02)], W, p.sides("N")


@glyph("O", "Oo")
def g_O(p):
    W = p.w("O")
    return ring(p, 0, -OV, W, CH + OV), W, p.sides("O")


@glyph("P", "Pp")
def g_P(p):
    W = p.w("P")
    return [stem(p, 0)] + bowl_right(p, 0, W, CH * 0.278, CH), W, p.sides("P")


@glyph("Q", "Qq")
def g_Q(p):
    """The O, with a short level tail leaving its lower right."""
    W = p.w("Q")
    V, H = p.V, p.H
    tail = box(W * 0.62, -OV, W + V * 0.55, H - OV)
    return ring(p, 0, -OV, W, CH + OV) + [tail], W, p.sides("Q")


R_FILLET = 1.0  # the leg's fillet into the bowl, in stems
R_LEG_TOP = 0.5  # how far the leg's top reaches into the bowl's lower bar, in bars
R_LEG_CORNER = 1.0  # the leg's outer top corner, in outer radii; the notch on the right is where it meets the bowl's


@glyph("R", "Rr")
def g_R(p):
    """The P, with a leg dropping straight from the bowl's right side, filleted into its underside."""
    W = p.w("R")
    V, H = p.V, p.H
    pb = CH * 0.278  # the bowl's bottom
    f = V * R_FILLET
    top = pb + H * R_LEG_TOP
    leg = rounded((W - V, 0, 0), (W, 0, 0), (W, top, p.ro * R_LEG_CORNER), (W - V - 2 * f, top, 0),
                  (W - V - 2 * f, pb, 0), (W - V, pb, f))
    return [stem(p, 0)] + bowl_right(p, 0, W, pb, CH) + [leg], W, p.sides("R")


@glyph("S", "Ss")
def g_S(p):
    """Two offset C's: the top bar ends square at the right, the bottom bar square at the left."""
    W = p.w("S")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    m0 = CH * 0.51 - H / 2
    m1 = m0 + H
    c = rounded(
        (0, -OV, 0), (W, -OV, ro), (W, m1, ro), (V, m1, ri), (V, CH - H, ri), (W, CH - H, 0), (W, CH + OV, 0),
        (0, CH + OV, ro), (0, m0, ro), (W - V, m0, ri), (W - V, H, ri), (0, H, 0),
    )
    return [c], W, p.sides("S")


@glyph("T", "Tt")
def g_T(p):
    W = p.w("T")
    return [bar(p, 0, W, CH - p.H), stem(p, W / 2 - p.V / 2)], W, p.sides("T")


@glyph("U", "Uu")
def g_U(p):
    W = p.w("U")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    c = rounded((0, CH, 0), (0, -OV, ro), (W, -OV, ro), (W, CH, 0), (W - V, CH, 0), (W - V, H, ri), (V, H, ri), (V, CH, 0))
    return [c], W, p.sides("U")


@glyph("V", "Vv")
def g_V(p):
    W = p.w("V")
    return [vee(p, 0, W)[0]], W, p.sides("V")


@glyph("W", "Ww")
def g_W(p):
    """Two V's sharing the middle stroke."""
    W = p.w("W")
    hw = p.V
    for _ in range(4):
        Wv = (W + hw) / 2
        hw = vee(p, 0, Wv)[1]
    Wv = (W + hw) / 2
    return [vee(p, 0, Wv)[0], vee(p, W - Wv, Wv)[0]], W, p.sides("W")


@glyph("X", "Xx")
def g_X(p):
    W = p.w("X")
    t = p.V * 0.86
    hw = diag_hw(W, CH, t)
    return [rpoly((0, CH, 0), (hw, CH, 0), (W, 0, 0), (W - hw, 0, 0)),
            rpoly((W - hw, CH, 0), (W, CH, 0), (hw, 0, 0), (0, 0, 0))], W, p.sides("X")


@glyph("Y", "Yy")
def g_Y(p):
    """A V whose foot is a stem wide, standing on a stem."""
    W = p.w("Y")
    yj = CH * 0.42
    return [vee(p, 0, W, bottom=yj, foot=p.V)[0], stem(p, W / 2 - p.V / 2, 0, yj + 1)], W, p.sides("Y")


@glyph("Z", "Zz")
def g_Z(p):
    """Two bars and the N's diagonal turned, running between them."""
    W = p.w("Z")
    H = p.H
    t = p.V * 1.02
    hw = W * t / (CH - 2 * H + t)  # horizontal cut that keeps the stroke t thick upright
    diagonal = rpoly((W - hw, CH - H + 1, 0), (W, CH - H + 1, 0), (hw, H - 1, 0), (0, H - 1, 0))
    return [bar(p, 0, W, CH - H), bar(p, 0, W, 0), diagonal], W, p.sides("Z")


# --- Figures --------------------------------------------------------------
# Lining, at cap height, built from the same parts as the capitals.

@glyph("zero", "0")
def g_zero(p):
    W = p.w("zero")
    return ring(p, 0, -OV, W, CH + OV), W, p.sides("zero")


@glyph("one", "1")
def g_one(p):
    """A stem with a square flag to its left."""
    W = p.w("one")
    xs = W - p.V
    return [stem(p, xs), box(0, CH - p.H, xs + 1, CH)], W, p.sides("one")


@glyph("two", "2")
def g_two(p):
    """The S turned: square where the bars end, round where they turn."""
    W = p.w("two")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    m0 = CH * 0.51 - H / 2
    m1 = m0 + H
    c = rounded(
        (0, 0, 0), (W, 0, 0), (W, H, 0), (V, H, ri), (V, m0, ri), (W, m0, ro), (W, CH + OV, ro), (0, CH + OV, 0),
        (0, CH - H, 0), (W - V, CH - H, ri), (W - V, m1, ri), (0, m1, ro),
    )
    return [c], W, p.sides("two")


@glyph("three", "3")
def g_three(p):
    """Three bars on a right side; the middle one stops short."""
    W = p.w("three")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    m0 = CH * 0.51 - H / 2
    m1 = m0 + H
    xm = W * 0.28
    c = rounded(
        (0, -OV, 0), (W, -OV, ro), (W, CH + OV, ro), (0, CH + OV, 0), (0, CH - H, 0), (W - V, CH - H, ri),
        (W - V, m1, 0), (xm, m1, 0), (xm, m0, 0), (W - V, m0, 0), (W - V, H, ri), (0, H, 0),
    )
    return [c], W, p.sides("three")


@glyph("four", "4")
def g_four(p):
    """A rounded L hung from the cap height, crossed by a full-height stem."""
    W = p.w("four")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    cb = CH * 0.30
    xs = W * 0.70
    l = rounded((0, CH, 0), (0, cb, ro), (W, cb, 0), (W, cb + H, 0), (V, cb + H, ri), (V, CH, 0))
    return [l, stem(p, xs)], W, p.sides("four")


@glyph("five", "5")
def g_five(p):
    """The S, its top left square where the bar meets the side."""
    W = p.w("five")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    m0 = CH * 0.53 - H / 2
    m1 = m0 + H
    c = rounded(
        (0, -OV, 0), (W, -OV, ro), (W, m1, ro), (V, m1, 0), (V, CH - H, 0), (W, CH - H, 0), (W, CH, 0),
        (0, CH, 0), (0, m0, 0), (W - V, m0, ri), (W - V, H, ri), (0, H, 0),
    )
    return [c], W, p.sides("five")


def six(p, W):
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    m1 = CH * 0.53 + H / 2
    outer = rounded((0, -OV, ro), (W, -OV, ro), (W, m1, ro), (V, m1, ri), (V, CH - H, ri), (W, CH - H, 0),
                    (W, CH + OV, 0), (0, CH + OV, ro))
    return [outer, hole(V, H, W - V, m1 - H, ri)]


@glyph("six", "6")
def g_six(p):
    W = p.w("six")
    return six(p, W), W, p.sides("six")


@glyph("seven", "7")
def g_seven(p):
    W = p.w("seven")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    c = rounded((W - V, 0, 0), (W, 0, 0), (W, CH + OV, ro), (0, CH + OV, 0), (0, CH - H, 0), (W - V, CH - H, ri))
    return [c], W, p.sides("seven")


@glyph("eight", "8")
def g_eight(p):
    W = p.w("eight")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    m0 = CH * 0.51 - H / 2
    return [box(0, -OV, W, CH + OV, ro, ro, ro, ro), hole(V, H, W - V, m0, ri), hole(V, m0 + H, W - V, CH - H, ri)], W, p.sides("eight")


@glyph("nine", "9")
def g_nine(p):
    W = p.w("nine")
    return rotate180(six(p, W), W / 2, CH / 2), W, p.sides("nine")


# --- Punctuation and symbols ----------------------------------------------

def square(p, x0, y0):
    return box(x0, y0, x0 + p.V, y0 + p.V)


def comma_at(p, x0, top):
    """A square whose right side drops into a short tail, leaning nowhere: the reference has no slant."""
    V = p.V
    return rpoly((x0, top - V, 0), (x0 + V, top - V * 1.9, 0), (x0 + V, top, 0), (x0, top, 0))


@glyph("period", ".")
def g_period(p):
    return [square(p, 0, 0)], p.V, p.sides("period")


@glyph("comma", ",")
def g_comma(p):
    return [comma_at(p, 0, p.V)], p.V, p.sides("comma")


@glyph("colon", ":")
def g_colon(p):
    return [square(p, 0, 0), square(p, 0, CH * 0.62 - p.V)], p.V, p.sides("colon")


@glyph("semicolon", ";")
def g_semicolon(p):
    return [comma_at(p, 0, p.V), square(p, 0, CH * 0.62 - p.V)], p.V, p.sides("semicolon")


@glyph("exclam", "!")
def g_exclam(p):
    V = p.V
    return [box(0, V * 1.6, V, CH), square(p, 0, 0)], V, p.sides("exclam")


@glyph("question", "?")
def g_question(p):
    """The seven's corner, with a stem dropping from the middle to a full stop."""
    W = p.w("question")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    m0 = CH * 0.46 - H / 2
    xs = W * 0.42
    c = rounded(
        (xs, V * 1.6, 0), (xs + V, V * 1.6, 0), (xs + V, m0 + 1, 0), (W - V, m0 + 1, 0), (W - V, m0, 0), (W, m0, ro),
        (W, CH + OV, ro), (0, CH + OV, 0), (0, CH - H, 0), (W - V, CH - H, ri), (W - V, m0 + H, ri), (xs, m0 + H, 0),
    )
    return [c, square(p, xs, 0)], W, p.sides("question")


def dash(p, name, y=None):
    W = p.w(name)
    y = CH * 0.47 - p.H / 2 if y is None else y
    return [bar(p, 0, W, y)], W, p.sides(name)


@glyph("hyphen", "-")
def g_hyphen(p):
    return dash(p, "hyphen")


@glyph("endash", "–")
def g_endash(p):
    return dash(p, "endash")


@glyph("emdash", "—")
def g_emdash(p):
    return dash(p, "emdash")


@glyph("underscore", "_")
def g_underscore(p):
    return dash(p, "underscore", y=-p.H * 1.6)


@glyph("quotesingle", "'")
def g_quotesingle(p):
    return [box(0, CH - p.V * 1.9, p.V, CH)], p.V, p.sides("quotesingle")


@glyph("quotedbl", '"')
def g_quotedbl(p):
    V = p.V
    return [box(0, CH - V * 1.9, V, CH), box(V * 1.7, CH - V * 1.9, V * 2.7, CH)], V * 2.7, p.sides("quotedbl")


def quote(p, n, turned):
    """n commas hung at the cap height; turned ones (opening quotes) point up."""
    V = p.V
    marks = [comma_at(p, i * V * 1.7, CH) for i in range(n)]
    W = V * (1 + 1.7 * (n - 1))
    if turned:
        marks = rotate180(marks, W / 2, CH - V * 0.95)
    return marks, W


@glyph("quoteright", "’")
def g_quoteright(p):
    c, W = quote(p, 1, False)
    return c, W, p.sides("quoteright")


@glyph("quoteleft", "‘")
def g_quoteleft(p):
    c, W = quote(p, 1, True)
    return c, W, p.sides("quoteleft")


@glyph("quotedblright", "”")
def g_quotedblright(p):
    c, W = quote(p, 2, False)
    return c, W, p.sides("quotedblright")


@glyph("quotedblleft", "“")
def g_quotedblleft(p):
    c, W = quote(p, 2, True)
    return c, W, p.sides("quotedblleft")


def bracket(p, W, r):
    """An open box, its corners r round: square brackets have none, parentheses the bowls'."""
    V, H = p.V, p.H
    top, bot = CH + H * 0.9, -H * 0.9
    ri = max(r - p.V * INNER, INNER_MIN * CH) if r else 0
    return rpoly((0, bot, r), (W, bot, 0), (W, bot + H, 0), (V, bot + H, ri), (V, top - H, ri), (W, top - H, 0),
                 (W, top, 0), (0, top, r))


@glyph("parenleft", "(")
def g_parenleft(p):
    W = p.w("parenleft")
    return [bracket(p, W, p.ro)], W, p.sides("parenleft")


@glyph("parenright", ")")
def g_parenright(p):
    W = p.w("parenright")
    return mirror_x([bracket(p, W, p.ro)], W), W, p.sides("parenright")


@glyph("bracketleft", "[")
def g_bracketleft(p):
    W = p.w("bracketleft")
    return [bracket(p, W, 0)], W, p.sides("bracketleft")


@glyph("bracketright", "]")
def g_bracketright(p):
    W = p.w("bracketright")
    return mirror_x([bracket(p, W, 0)], W), W, p.sides("bracketright")


@glyph("slash", "/")
def g_slash(p):
    W = p.w("slash")
    c, hw = slant(p, 0, -p.H * 0.9, W - diag_hw(W, CH, p.V * 0.86), CH + p.H * 0.9)
    return [c], W, p.sides("slash")


@glyph("plus", "+")
def g_plus(p):
    W = p.w("plus")
    cy = CH * 0.47
    return [bar(p, 0, W, cy - p.H / 2), box(W / 2 - p.V / 2, cy - W / 2, W / 2 + p.V / 2, cy + W / 2)], W, p.sides("plus")


@glyph("equal", "=")
def g_equal(p):
    W = p.w("equal")
    cy, gap = CH * 0.47, p.H * 0.9
    return [bar(p, 0, W, cy + gap / 2), bar(p, 0, W, cy - gap / 2 - p.H)], W, p.sides("equal")


@glyph("ampersand", "&")
def g_ampersand(p):
    """The eight, its right side cut away above a bar that runs out past it."""
    W = p.w("ampersand")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    Wb = W * 0.84  # the body; the bar runs on to W
    m0 = CH * 0.51 - H / 2
    xt = Wb * 0.86  # the upper bowl's right side
    body = rounded(
        (0, -OV, ro), (Wb, -OV, ro), (Wb, m0, 0), (W, m0, 0), (W, m0 + H, 0), (Wb - V, m0 + H, 0), (Wb - V, H, ri),
        (V, H, ri), (V, m0, ri), (Wb * 0.55, m0, 0), (Wb * 0.55, m0 + H, 0), (V * 0.6 + V, m0 + H, ri),
        (V * 0.6 + V, CH - H, ri), (xt - V, CH - H, ri), (xt - V, m0 + H, 0), (xt, m0 + H, 0), (xt, CH + OV, ro),
        (V * 0.6, CH + OV, ro), (V * 0.6, m0 + H, ro), (0, m0 + H, ro),
    )
    return [body], W, p.sides("ampersand")


@glyph("percent", "%")
def g_percent(p):
    """Two small rings either side of the slash."""
    W = p.w("percent")
    V, H = p.V, p.H
    rw, rh = W * 0.32, CH * 0.44
    r = min(p.ro, rh / 2.5)
    c, hw = slant(p, W * 0.22, 0, W * 0.78 - diag_hw(W * 0.56, CH, V * 0.86), CH)
    return ring(p, 0, CH - rh, rw, CH, r, max(r - V * INNER, 6)) + ring(p, W - rw, 0, W, rh, r, max(r - V * INNER, 6)) + [c], W, p.sides("percent")
