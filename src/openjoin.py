"""The open join: Archivo's 4 as a recurring detail in Litt's own letters.

Measured from Archivo's 4 (weight 400): the diagonal reaches full height and
ends in a level cut; the upright stops short at about 87% of the cap height,
its tip bevelled toward the diagonal down to about half the stroke; the two
never meet, leaving a gap of about 1.1 stroke widths.

By default N and k carry it: tested at 14px they read at once. Z and A read as
broken at UI sizes, so they are kept only as options. LITT_OPEN_JOIN overrides
the set (any of N k Z A; "" for none).
"""

import os

import glyphs as G
from glyphs import ASC, CH, XH, glyph
from geometry import diag_hw, poly, rect, stroke

SHORT = 0.87  # the upright stops at this share of the full height
BEVEL = 0.20  # the bevel runs this share of the height down the inner side
TIP = 0.5  # the bevelled tip keeps this share of the stroke
GAP = 1.1  # gap between the strokes, in stroke widths


def short_stem(x0, x1, top, inner="left"):
    """An upright that stops short, its tip bevelled on the side facing the other stroke."""
    V = x1 - x0
    h = top * SHORT
    b = top * BEVEL
    if inner == "left":
        return poly((x0, 0), (x1, 0), (x1, h), (x1 - V * TIP, h), (x0, h - b))
    return poly((x0, 0), (x1, 0), (x1, h - b), (x0 + V * TIP, h), (x0, h))


def g_N(p):
    V, D = p.VC, p.D * 1.06
    w = p.c(430, 0.3) + 2 * V
    hw = diag_hw(w - 2 * V, CH, D)
    d = poly((w - hw, 0), (w, 0), (hw, CH), (0, CH))
    # the right stem stops short of the top, bevelled toward the diagonal, as the 4's stem does
    return [rect(0, 0, V, CH), short_stem(w - V, w, CH, "left"), d], w, (p.SBC, p.SBC)


def g_k(p):
    V, D = p.V, p.D
    w = p.c(268, 0.55) + V
    hw = diag_hw(w - V, XH * 0.7, D)
    y0 = XH * 0.30
    top = (w - hw / 2, XH)
    # the leg leaves the stem; the arm rests on the leg and stops short of the stem
    leg = stroke((V * 0.5, XH * 0.46), (w + 6 - hw / 2, 0), D * 1.02, ("v", V * 0.5), ("h", 0))
    arm = stroke((V * 0.5, y0), top, D, ("v", V + GAP * V * 0.75), ("h", XH))
    return [rect(0, 0, V, ASC), leg, arm], w + 6, (p.SB, p.SBD)


def g_Z(p):
    h, D = p.HC, p.D * 1.08
    w = p.c(500, 0.1) + p.dV * 0.6
    hw = diag_hw(w, CH - 2 * h, D)
    gap = GAP * p.VC
    # the diagonal stops short of the top bar, its end cut level
    top = CH - h - gap
    run = (top - h) / (CH - 2 * h)
    d = poly((0, h), (hw, h), (hw + (w - hw) * run, top), ((w - hw) * run, top))
    return [rect(0, 0, w, h), rect(10, CH - h, w, CH), d], w, (p.SBD + 18, p.SBD + 18)


def g_A(p):
    D = p.D * 1.06
    w = p.c(560, 0.0) + p.dV * 1.3
    apex = D * 0.8
    hw = diag_hw(w / 2, CH, D)
    left = poly((0, 0), (hw, 0), (w / 2 + apex / 2, CH), (w / 2 + apex / 2 - hw, CH))
    # the right stroke stops short of the apex, cut level, leaving the top open
    top = CH * SHORT
    run = top / CH
    xr0, xr1 = w - hw, w
    xt1 = w + (w / 2 - apex / 2 + hw - w) * run
    right = poly((xr0, 0), (xr1, 0), (xt1, top), (xt1 - hw, top))
    yb = CH * 0.24
    bar = rect(w * 0.2, yb, w * 0.8, yb + p.HC)
    return [left, right, bar], w, (p.SBD, p.SBD)


FORMS = {"N": g_N, "k": g_k, "Z": g_Z, "A": g_A}


DEFAULT = "Nk"


def register():
    for ch in os.environ.get("LITT_OPEN_JOIN", DEFAULT):
        if ch in FORMS:
            glyph(ch, ch)(FORMS[ch])
