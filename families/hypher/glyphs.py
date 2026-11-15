"""Hypher's glyphs: machined letters, drawn in code.

Every letter is built from flat-sided polygons with rounded corners, after the
Hypher mark: sides are straight and curves happen only in corners. The outer
corner radius is RADIUS x-heights; counters follow it, one stroke inside. Each
function takes the weight parameters and returns (contours, ink, (lsb, rsb)).
"""

import os

from core import geometry
from core.geometry import diag_hw

XH, ASC, DSC = 560, 740, -185  # x-height; ascender and descender at 1.32 and 0.33 x-heights
CH = ASC

# Outer corner radius as a share of the x-height. The mark's own 0.043 reads as
# pixel type at letter size and 0.26 drifts back to a squircle; 0.20 reads as
# machined, and 0.215 with the softening below reads a little rounder (0.210).
# The HYPHER_* variables override each number to compare versions in a proof.
RADIUS = float(os.environ.get("HYPHER_RADIUS", "0.215"))

# How softly corners ease into the sides: 0 is a circular arc, 1 a long,
# eased curve that reads rounder at the same radius.
SMOOTH = float(os.environ.get("HYPHER_SMOOTH", "0.6"))

# How far inside the outer corner a counter's corner sits, in stems: smaller
# keeps more of the outer radius, so counters read rounder.
INNER = float(os.environ.get("HYPHER_INNER", "0.55"))

# Radius on cut ends (stem feet, terminals, the r's arm), in x-heights. The
# mark rounds every corner, its flat ends included.
TERM = float(os.environ.get("HYPHER_TERM", "0.02"))

REGULAR_STEM = 92
SB = 96  # sidebearing beside a flat side; the lockup's loose tracking is built in


class P:
    """Weight parameters, all derived from the stem."""

    def __init__(self, wght, stem):
        self.wght = wght
        self.V = stem  # vertical stroke
        self.H = round(stem * 0.86)  # horizontal stroke: a little thinner, so it looks equal
        self.ro = RADIUS * XH  # outer corners
        self.ri = max(self.ro - INNER * stem, 0.3 * self.ro, 4)  # counters follow the outer corner
        self.rt = TERM * XH  # cut ends
        self.grow = (stem - REGULAR_STEM) * 2.0  # letters widen as they gain weight, keeping counters open

    def w(self, base):
        return base + self.grow


GLYPHS = {}


def rounded(*corners):
    return geometry.rounded(*corners, smooth=SMOOTH)


def glyph(name, char):
    def deco(fn):
        GLYPHS[name] = (char, fn)
        return fn
    return deco


def box(x0, y0, x1, y1, bl, br, tr, tl):
    """A rectangle with its own radius at each corner, counter-clockwise."""
    return rounded((x0, y0, bl), (x1, y0, br), (x1, y1, tr), (x0, y1, tl))


def hole(x0, y0, x1, y1, r):
    """A counter: a rounded rectangle running clockwise."""
    return rounded((x0, y0, r), (x0, y1, r), (x1, y1, r), (x1, y0, r))


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
    W = p.w(600)
    return [arch(p, 0, W, XH)], W, (SB, SB)


@glyph("h", "h")
def g_h(p):
    W = p.w(600)
    stem = box(0, 0, p.V, ASC, p.rt, p.rt, p.rt, p.rt)
    return [stem, arch(p, 0, W, XH)], W, (SB, SB)


@glyph("o", "o")
def g_o(p):
    W = p.w(640)
    return bowl(p, 0, W), W, (SB * 0.92, SB * 0.92)


@glyph("p", "p")
def g_p(p):
    W = p.w(640)
    stem = box(0, DSC, p.V, XH, p.rt, p.rt, 0, p.ro)
    return [stem] + bowl(p, 0, W), W, (SB, SB * 0.92)


@glyph("e", "e")
def g_e(p):
    """A bowl with a crossbar; the lower right opens above a flat terminal."""
    W = p.w(640)
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    bar0 = XH * 0.44  # bottom of the crossbar
    bar1 = bar0 + H
    term = XH * 0.27  # top of the lower terminal
    outer = rounded(
        (0, 0, ro), (W, 0, ro), (W, term, rt), (W - V, term, rt), (W - V, H, ri), (V, H, ri),
        (V, bar0, ri), (W, bar0, rt), (W, XH, ro), (0, XH, ro),
    )
    eye = hole(V, bar1, W - V, XH - H, ri)
    return [outer, eye], W, (SB * 0.92, SB * 0.92)


@glyph("r", "r")
def g_r(p):
    """A stem and a flat arm, cut square at the right."""
    W = p.w(360)
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    c = rounded(
        (0, 0, rt), (V, 0, rt), (V, XH - H, ri), (W, XH - H, rt), (W, XH, ro), (0, XH, ro),
    )
    return [c], W, (SB, SB * 0.55)


@glyph("y", "y")
def g_y(p):
    """A symmetric V meeting on the baseline; the right arm runs on into the descender."""
    W = p.w(620)
    V, r, rt = p.V, p.ri, p.rt
    cx = W / 2  # the arms' centre lines cross here, on the baseline
    dx = cx - 0  # each arm travels half the width over the x-height
    hw = diag_hw(dx, XH, V)  # horizontal width of either arm
    slope = (cx - hw / 2) / XH  # x per unit of height, along a centre line

    def on_right(y, off):  # x on the right arm, offset from its centre line
        return cx + slope * y + off

    xd = on_right(DSC, 0)  # right arm's centre at the descender
    right = rounded(
        (xd - hw / 2, DSC, r), (xd + hw / 2, DSC, rt), (W, XH, r), (W - hw, XH, rt),
    )
    # The left arm mirrors the right and stops on the right arm's centre line,
    # so the join has no foot.
    def meet(edge):  # where a left-arm edge (offset from its centre) crosses the right centre line
        # left centre: x = cx - slope * y; edge: x = cx - slope * y + edge; right centre: x = cx + slope * y
        y = edge / (2 * slope)
        return (cx + slope * y, y)
    left = rounded(
        (0, XH, r), meet(-hw / 2) + (0,), meet(hw / 2) + (0,), (hw, XH, rt),
    )
    return [right, left], W, (SB * 0.5, SB * 0.5)
