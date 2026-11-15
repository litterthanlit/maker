"""Hypher's glyphs: machined letters, drawn in code.

Every letter is built from flat-sided polygons with rounded corners, after the
Hypher mark: sides are straight and curves happen only in corners. Each
function takes the weight parameters and returns (contours, ink, (lsb, rsb)).

How round the letters are is a style: a named set of numbers in STYLES. Each
style is a version of Hypher; set_style() picks one before drawing.
"""

import os

from core import geometry
from core.geometry import diag_hw

XH, ASC, DSC = 560, 740, -185  # x-height; ascender and descender at 1.32 and 0.33 x-heights
CH = ASC

REGULAR_STEM = 92
SB = 96  # sidebearing beside a flat side; the lockup's loose tracking is built in

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
        widths={"h": 654, "n": 654, "o": 686, "p": 685, "e": 657, "r": 351, "y": 707},
        sides={"h": (104, 101), "n": (104, 101), "o": (87, 87), "p": (104, 87), "e": (87, 98),
               "r": (112, 97), "y": (62, 73)},
        kern=[("e", "r", -18)],  # e-r reads loose in the lockup: both letters open to the right
    ),
}
DEFAULT_STYLE = "Finish"

# Ink widths and sidebearings at Regular, per letter.
WIDTHS = {"n": 600, "h": 600, "o": 640, "p": 640, "e": 640, "r": 360, "y": 620}
SIDES = {"n": (SB, SB), "h": (SB, SB), "o": (SB * 0.92,) * 2, "p": (SB, SB * 0.92),
         "e": (SB * 0.92,) * 2, "r": (SB, SB * 0.55), "y": (SB * 0.5,) * 2}

STYLE = {}


def set_style(name):
    s = {"stem_tops": "round", "e_bar": 0.44, "e_term": 0.27, "y_tail": "straight", "y_tail_end": 0.18, "y_bend": 1.0,
         "widths": {}, "sides": {}, "kern": []}
    s.update(STYLES[name])
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


def arch(p, x0, x1, top, bottom=0):
    """The n's arch: two stems joined by a flat top, open at the bottom."""
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    return rounded(
        (x0, bottom, rt), (x0 + V, bottom, rt), (x0 + V, top - H, ri), (x1 - V, top - H, ri),
        (x1 - V, bottom, rt), (x1, bottom, rt), (x1, top, ro), (x0, top, ro),
    )


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


set_style(os.environ.get("HYPHER_STYLE", DEFAULT_STYLE))
