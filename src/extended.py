"""Coverage beyond Basic Latin, for UI use.

- Accent marks, drawn once, then every precomposed letter in Latin-1 and
  Latin Extended-A built from Unicode's own decompositions (é = e + acute).
- Letters that can't be composed (ß Æ Ø Ł Ð Þ ı ...).
- UI punctuation and symbols: typographic quotes and dashes, currency,
  arrows, math, ©®™, superscripts and fractions.
- Alternates for OpenType features: case-sensitive forms (`case`),
  disambiguation (`ss01`), slashed zero (`zero`), proportional one (`pnum`).

Importing this module registers everything into glyphs.GLYPHS.
"""

import math
import unicodedata

from fontTools.agl import UV2AGL

import glyphs as G
from glyphs import ASC, CH, DSC, O, XH, P, dot_size, fig_width, math_width, math_sb
from geometry import (
    Ellipse, band, bounds, diag_hw, flip_y, mirror_x, poly, rect, ring, rotate,
    rotate180, stroke, transform, translate,
)

GLYPHS = G.GLYPHS
BASE = {}  # composite glyph -> base glyph, used to extend kerning classes
ALT = {}  # feature tag -> [(glyph, alternate)]


def name_for(cp):
    return UV2AGL.get(cp, f"uni{cp:04X}")


def add(name, char, fn):
    GLYPHS[name] = (char, fn)


def fn_of(name):
    return GLYPHS[name][1]


def scale(contours, sx, sy=None, ox=0, oy=0):
    sy = sx if sy is None else sy
    return transform(contours, a=sx, d=sy, e=ox, f=oy)


def centered(contours):
    x0, _, x1, _ = bounds(contours)
    return translate(contours, -(x0 + x1) / 2), x1 - x0


# --- accent marks -----------------------------------------------------------
# Each returns contours centred on x = 0 with their bottom at y = 0, and a width.

def acc_acute(p, h):
    t = p.D * 0.80
    return centered([stroke((-50, 0), (60, h), t, ("h", 0), ("h", h))])


def acc_grave(p, h):
    c, w = acc_acute(p, h)
    return mirror_x(c, 0), w


def acc_circumflex(p, h):
    w = 250 + p.dV * 0.8
    t = p.D * 0.78
    hw = diag_hw(w / 2, h, t)
    left = poly((-w / 2, 0), (-w / 2 + hw, 0), (hw * 0.5, h), (-hw * 0.5, h))
    right = poly((w / 2 - hw, 0), (w / 2, 0), (hw * 0.5, h), (-hw * 0.5, h))
    return [left, right], w


def acc_caron(p, h):
    c, w = acc_circumflex(p, h)
    return flip_y(c, h / 2), w


def acc_dieresis(p, h):
    d = dot_size(p) * 0.94
    gap = 72 + p.dV * 0.25
    w = 2 * d + gap
    return [rect(-w / 2, 0, -w / 2 + d, d), rect(w / 2 - d, 0, w / 2, d)], w


def acc_dotaccent(p, h):
    d = dot_size(p) * 0.94
    return [rect(-d / 2, 0, d / 2, d)], d


def acc_ring(p, h):
    s = 150 + p.dV * 0.5
    v, t = p.V * 0.82, p.H * 0.82
    return ring(Ellipse(-s / 2, 0, s / 2, s, 0.6), Ellipse(-s / 2 + v, t, s / 2 - v, s - t, 0.62)), s


def tilde_shape(w, amp, t, y0):
    """A wave: centreline from low-left to high-right through an S-curve,
    thickened vertically by t. Its bottom sits near y0."""
    cy = y0 + amp + t / 2
    k = 0.38 * w
    lo, hi = cy - amp, cy + amp
    return [
        (-w / 2, lo - t / 2),
        ("c", (-w / 2 + k, lo + 2.3 * amp - t / 2), (w / 2 - k, hi - 2.3 * amp - t / 2), (w / 2, hi - t / 2)),
        ("l", (w / 2, hi + t / 2)),
        ("c", (w / 2 - k, hi - 2.3 * amp + t / 2), (-w / 2 + k, lo + 2.3 * amp + t / 2), (-w / 2, lo + t / 2)),
    ]


def acc_tilde(p, h):
    w = 270 + p.dV * 0.7
    return [tilde_shape(w, h * 0.30, p.H * 0.92, 0)], w


def acc_macron(p, h):
    w = 250 + p.dV * 0.6
    return [rect(-w / 2, h * 0.3, w / 2, h * 0.3 + p.H)], w


def acc_breve(p, h):
    w = 250 + p.dV * 0.7
    hh = h * 0.95
    o = Ellipse(-w / 2, -hh, w / 2, hh, 0.6)
    i = Ellipse(-w / 2 + p.V * 0.8, -hh + p.H * 0.9, w / 2 - p.V * 0.8, hh - p.H * 0.9, 0.62)
    return [band(o, i, (2, 0.0), (3, 1.0))], w


def acc_hungarumlaut(p, h):
    a, w = acc_acute(p, h)
    off = 64 + p.dV * 0.4
    return translate(a, -off) + translate(a, off), w + 2 * off


def comma_shape(p, s=1.0):
    """The comma's tail-and-dot, top at y = 0, centred on x = 0."""
    c, d, _ = fn_of("comma")(p)
    c = translate(c, 0, -d)
    c = scale(c, s)
    return centered(c)


def acc_commaaccent(p, h):  # below the baseline
    c, w = comma_shape(p, 0.82)
    return translate(c, 0, -46), w


def acc_commaturned(p, h):  # above, for ģ
    c, w = comma_shape(p, 0.82)
    c = rotate180(c, 0, 0)
    return translate(c, 0, h * 0.0), w


def acc_caron_vertical(p, h):  # the apostrophe-like caron on ď ľ ť Ľ
    c, w = comma_shape(p, 0.82)
    return c, w


def acc_cedilla(p, h):
    V, H = p.V * 0.78, p.H * 0.82
    rx, ry = 80 + V * 0.55, 62 + H * 0.4
    cx, cy = 26, -ry - 70
    o = Ellipse(cx - rx, cy - ry, cx + rx, cy + ry, 0.6)
    i = Ellipse(cx - rx + V, cy - ry + H, cx + rx - V, cy + ry - H, 0.62)
    hook = band(o, i, (2, 0.45), (5, 0.45))
    top = o.point((1, 0.45))
    stem = rect(top[0] - V * 0.15, top[1] - H, top[0] + V * 0.85, 10)
    return centered([hook, stem])


def acc_ogonek(p, h):
    V, H = p.V * 0.82, p.H * 0.85
    rx, ry = 60 + V * 0.6, 78 + H * 0.3
    o = Ellipse(-rx, -2 * ry, rx, 0, 0.6)
    i = Ellipse(-rx + V, -2 * ry + H, rx - V, -H, 0.62)
    c = [band(o, i, (1, 0.0), (3, 0.55))]
    return translate(c, rx * 0.25, 40), 2 * rx


ACCENTS = {
    0x0300: acc_grave, 0x0301: acc_acute, 0x0302: acc_circumflex, 0x0303: acc_tilde,
    0x0304: acc_macron, 0x0306: acc_breve, 0x0307: acc_dotaccent, 0x0308: acc_dieresis,
    0x030A: acc_ring, 0x030B: acc_hungarumlaut, 0x030C: acc_caron, 0x0326: acc_commaaccent,
    0x0327: acc_cedilla, 0x0328: acc_ogonek,
}
BELOW = {0x0326, 0x0327, 0x0328}

# Lowercase accents sit this far above the x-height; capital ones are flatter
# and closer, so accented caps don't crash into the line above.
LC_GAP, LC_H = 96, 150
UC_GAP, UC_H = 56, 116


# --- accent glyphs themselves (spacing versions) -------------------------------

def spacing_accent(fn, below=False):
    def g(p):
        c, w = fn(p, LC_H)
        y = 0 if below else XH + LC_GAP
        c = translate(c, w / 2, y)
        return c, w, (40, 40)
    return g


for cp, nm, fn, below in [
    (0x00B4, "acute", acc_acute, False), (0x02C6, "circumflex", acc_circumflex, False),
    (0x02DC, "tilde", acc_tilde, False), (0x00AF, "macron", acc_macron, False),
    (0x02D8, "breve", acc_breve, False), (0x02D9, "dotaccent", acc_dotaccent, False),
    (0x00A8, "dieresis", acc_dieresis, False), (0x02DA, "ring", acc_ring, False),
    (0x02DD, "hungarumlaut", acc_hungarumlaut, False), (0x02C7, "caron", acc_caron, False),
    (0x00B8, "cedilla", acc_cedilla, True), (0x02DB, "ogonek", acc_ogonek, True),
]:
    add(nm, chr(cp), spacing_accent(fn, below))


def combining(fn, below=False):
    """Zero-width combining mark, positioned over an average lowercase letter.
    `ccmp` replaces base + mark pairs with precomposed glyphs where they exist."""
    def g(p):
        c, w = fn(p, LC_H)
        y = 0 if below else XH + LC_GAP
        return translate(c, -270, y), 0, (0, 0)
    return g


for cp, fn in ACCENTS.items():
    add(name_for(cp), chr(cp), combining(fn, cp in BELOW))


# --- letters that composites build on ------------------------------------------

def g_dotlessi(p):
    c, w, sb = fn_of("i")(p)
    return c[:1], w, sb


def g_dotlessj(p):
    c, w, sb = fn_of("j")(p)
    return c[:2], w, sb


add("dotlessi", "ı", g_dotlessi)
add("uni0237", "ȷ", g_dotlessj)


# --- precomposed letters ---------------------------------------------------------

ACC_X = {  # optical horizontal position of top accents, as a fraction of ink width
    "a": 0.46, "b": 0.6, "d": 0.4, "g": 0.48, "h": 0.6, "k": 0.4, "l": 0.5, "r": 0.4,
    "t": 0.45, "y": 0.55, "j": 0.75, "uni0237": 0.75, "G": 0.52, "J": 0.6, "L": 0.3,
}
STEM_X = {"t": None}


def compose(base, marks, uc):
    def g(p):
        c, ink, (lsb, rsb) = fn_of(base)(p)
        out = list(c)
        stacked_top = None
        for cp in marks:
            fn = ACCENTS[cp]
            h = UC_H if uc else LC_H
            if base in ("d", "l", "t", "L") and cp == 0x030C:
                # vertical caron: an apostrophe beside the ascender
                a, aw = acc_caron_vertical(p, h)
                top = CH if base == "L" else ASC
                if base == "t":
                    top = XH + 150
                xs = {"d": ink + 50, "l": ink + 50, "t": ink * 0.78, "L": p.VC + 70}[base]
                a = translate(a, xs + aw / 2, top)
                out += a
                rsb = rsb + (aw + 40 if base in ("d", "l") else (0 if base == "t" else -40))
                continue
            if base == "g" and cp == 0x0327:
                a, aw = acc_commaturned(p, h)
                out += translate(a, ink * 0.48, XH + 72 + aw * 0.0)
                continue
            if cp == 0x0327 and base in "KkLlNnRrGg":
                fn = acc_commaaccent
            a, aw = fn(p, h)
            if cp in BELOW:
                if cp == 0x0328:
                    x = {"a": ink - p.V * 0.5, "e": ink * 0.66, "i": ink / 2, "u": ink - p.V * 0.5,
                         "A": ink - 60, "E": ink - 70, "I": ink / 2, "U": ink * 0.62, "o": ink * 0.6}.get(base, ink * 0.6)
                    out += translate(a, x - aw * 0.15, 0)
                else:
                    x = {"t": (68 + p.dV * 0.2) + p.V / 2, "T": ink / 2}.get(base, ink / 2)
                    out += translate(a, x, 0)
                continue
            x = ink * ACC_X.get(base, 0.5)
            if base in "ij" or base in ("dotlessi", "uni0237"):
                x = ink - p.V / 2
            if uc:
                y = CH + UC_GAP
            elif base in "bdhklt" or base in "fbdhkl":
                y = ASC + 60  # accents over ascenders (ĥ ħ) sit higher
            else:
                y = XH + LC_GAP
            if stacked_top is not None:
                y = stacked_top + 30
            out += translate(a, x, y)
            # keep wide accents (î ï) from colliding with neighbours
            half = aw / 2
            if base in "ij" or base in ("dotlessi", "uni0237", "I"):
                extra = max(0.0, half - (x if base != "I" else ink / 2) - lsb * 0.5)
                lsb_shift = extra
                out = translate(out, lsb_shift)
                ink += lsb_shift
                rsb = max(rsb, rsb + max(0.0, x + half - ink - rsb * 0.5))
        return out, ink, (lsb, rsb)
    return g


def precomposed():
    """Every precomposed Latin letter in U+00C0..U+017F we can build."""
    have = {chr(ord(c)) for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"}
    for cp in list(range(0x00C0, 0x0100)) + list(range(0x0100, 0x0180)):
        d = unicodedata.decomposition(chr(cp))
        if not d or d.startswith("<"):
            continue
        parts = [int(x, 16) for x in d.split()]
        base_cp, marks = parts[0], parts[1:]
        # recursive decompositions don't occur in this range; skip anything odd
        if chr(base_cp) not in have or any(m not in ACCENTS for m in marks):
            continue
        base = chr(base_cp)
        uc = base.isupper()
        if base == "i" and all(m not in BELOW for m in marks):
            base = "dotlessi"
        if base == "j":
            base = "uni0237"
        nm = name_for(cp)
        add(nm, chr(cp), compose(base, marks, uc))
        BASE[nm] = {"dotlessi": "i", "uni0237": "j"}.get(base, base)


precomposed()


# --- letters drawn specially ---------------------------------------------------------

def bar_through(p, x0, x1, y, uc=False):
    t = (p.HC if uc else p.H) * 0.95
    return rect(x0, y - t / 2, x1, y + t / 2)


def g_lslash(p):
    c, ink, (lsb, rsb) = fn_of("l")(p)
    w = 240 + p.dV * 0.5
    s = stroke((ink / 2 - w / 2, XH * 0.42), (ink / 2 + w / 2, XH * 0.42 + w * 0.55), p.H * 0.95)
    c = c + [s]
    x0, _, x1, _ = bounds(c)
    return translate(c, -x0), x1 - x0, (p.SBD + 18, p.SBD + 18)


def g_Lslash(p):
    c, ink, sb = fn_of("L")(p)
    w = 250 + p.dV * 0.5
    xc = p.VC / 2
    s = stroke((xc - w * 0.42, CH * 0.36), (xc + w * 0.58, CH * 0.36 + w * 0.55), p.HC * 0.95)
    c = c + [s]
    x0 = bounds(c)[0]
    return translate(c, -x0), ink - x0, (p.SBD + 12, sb[1])


def g_Eth(p):  # Ð and Đ
    c, ink, sb = fn_of("D")(p)
    pad = 70 + p.dV * 0.3
    c = translate(c, pad) + [bar_through(p, 0, pad + p.VC + 120, CH * 0.48, True)]
    return c, ink + pad, (p.SBD + 10, sb[1])


def g_dcroat(p):
    c, ink, sb = fn_of("d")(p)
    x1 = ink + 60 + p.dV * 0.2
    c = c + [bar_through(p, ink - p.V - 110, x1, ASC - 110)]
    return c, x1, (sb[0], p.SBD + 10)


def g_hbar(p):
    c, ink, sb = fn_of("h")(p)
    pad = 60 + p.dV * 0.2
    c = translate(c, pad) + [bar_through(p, 0, pad + p.V + 120, ASC - 110)]
    return c, ink + pad, (p.SBD + 10, sb[1])


def g_Hbar(p):
    c, ink, sb = fn_of("H")(p)
    pad = 50 + p.dV * 0.2
    c = translate(c, pad) + [bar_through(p, 0, ink + 2 * pad, CH * 0.76, True)]
    return c, ink + 2 * pad, (p.SBD + 8, p.SBD + 8)


def g_tbar(p):
    c, ink, sb = fn_of("t")(p)
    L = 68 + p.dV * 0.2
    return c + [bar_through(p, L - 50, L + p.V + 60, XH * 0.52)], ink, sb


def g_Tbar(p):
    c, ink, sb = fn_of("T")(p)
    return c + [bar_through(p, ink / 2 - 150 - p.dV * 0.3, ink / 2 + 150 + p.dV * 0.3, CH * 0.46, True)], ink, sb


def g_oslash(p, base="o", top=XH):
    c, ink, sb = fn_of(base)(p)
    ext = 40
    s = stroke((-ext + 20, -O - ext + 6), (ink + ext - 20, top + O + ext - 6), p.D * (0.9 if base == "o" else 0.95),
               ("h", -O - ext + 6), ("h", top + O + ext - 6))
    c = c + [s]
    x0, _, x1, _ = bounds(c)
    return translate(c, -x0), x1 - x0, (sb[0] - (0 - x0) * 0.6, sb[1] - (x1 - ink) * 0.6)


def g_Oslash(p):
    return g_oslash(p, "O", CH)


def g_AE(p):
    D, V, hc = p.D * 1.06, p.VC, p.HC
    xs = 330 + p.dV * 0.8  # where the E stem starts
    w = xs + V + p.c(300, 0.5)
    hw = diag_hw(xs, CH, D)
    leg = poly((0, 0), (hw, 0), (xs + V, CH), (xs + V - hw, CH))
    yb = CH * 0.24
    c = [leg, rect(xs, 0, xs + V, CH), rect(xs + V / 2, 0, w, hc),
         rect(xs + V / 2, CH * 0.47, w - 18, CH * 0.47 + hc), rect(xs, CH - hc, w - 6, CH),
         rect(hw * 0.6, yb, xs + 2, yb + hc)]
    return c, w, (p.SBD, p.SBD + 22)


def merged(p, left, right, overlap, keep_left=None):
    """Join two glyphs (æ, œ): `right` overlaps `left` by `overlap` units."""
    cl, il, sbl = fn_of(left)(p)
    cr, ir, sbr = fn_of(right)(p)
    if keep_left is not None:
        cl = [cl[i] for i in keep_left]
    return cl + translate(cr, il - overlap), il + ir - overlap, (sbl[0], sbr[1])


def g_ae(p):
    return merged(p, "a", "e", p.V * 0.95 + 4, keep_left=[1, 2, 3])


def g_oe(p):
    return merged(p, "o", "e", p.VR * 1.0)


def g_OE(p):
    v, h = p.VC * 1.05, p.HC
    w = p.c(500, 0.9) + 2 * v
    o = Ellipse(0, 0, w, CH, G.K)
    i = Ellipse(v, h, w - v, CH - h, G.KI)
    left = band(o, i, (1, 0.0), (2, 1.0))  # the O's left half, flat-topped to meet the E
    ce, ie, sbe = fn_of("E")(p)
    off = o.cx - p.VC * 0.5
    return [left] + translate(ce, off), off + ie, (p.SBCR, sbe[1])


def g_Thorn(p):
    V, v, h = p.VC, p.VC * 1.02, p.HC
    w = p.c(400, 0.9) + V + v
    return [rect(0, 0, V, CH)] + G.cap_bowl(0, w, CH * 0.20, CH * 0.80, V, v, h), w, (p.SBC, p.SBCR)


def g_thorn(p):
    c, w = G.b_parts(p, DSC, ASC)
    return c, w, (p.SB, p.SBR)


def g_eth(p):
    v, h = p.VR, p.HR
    w = p.c(296, 0.9) + 2 * v
    top = XH * 0.92
    o = Ellipse(0, -O, w, top + O, 0.6)
    i = Ellipse(v, -O + h, w - v, top + O - h, 0.62)
    # the ascending stroke leaves the bowl's upper right and curls up to the left
    s = stroke((w - v * 0.55, top * 0.62), (w * 0.34, ASC), p.D * 0.95, ("p",), ("h", ASC))
    bar = stroke((w * 0.30, ASC - 230), (w * 0.86, ASC - 130), p.H * 0.9)
    return ring(o, i) + [s, bar], w, (p.SBR, p.SBR)


def g_germandbls(p):
    V, v, h = p.V, p.VR, p.HR
    w = p.c(300, 0.9) + V + v
    ym = XH * 0.70
    top = ASC + O
    up_o = Ellipse(V * 0.3, ym - h / 2, w * 0.86, top, 0.6)
    up_i = Ellipse(V * 0.3 + V, ym + h / 2, w * 0.86 - v * 0.95, top - h, 0.62)
    upper = band(up_o, up_i, (3, 0.0), (1, 1.0))
    lo_o = Ellipse(w * 0.06, -O, w, ym + h / 2, 0.6)
    lo_i = Ellipse(w * 0.06 + v, -O + h, w - v, ym - h / 2, 0.62)
    yb = lo_o.cy - 0.38 * lo_o.ry
    lower = band(lo_o, lo_i, lo_o.at_y(2, yb), (5, 0.0), lo_i.at_y(2, yb), (5, 0.0))
    return [rect(0, 0, V, up_o.cy), upper, lower, rect(w * 0.30, ym - h / 2, lo_o.cx + 2, ym + h / 2)], w, (p.SB, p.SBR)


def g_kgreenlandic(p):
    c, w, sb = fn_of("k")(p)
    return [rect(0, 0, p.V, XH)] + c[1:], w, sb


def g_eng(p):
    c, w, sb = fn_of("n")(p)
    V = p.V
    rx, ry = 110 + V * 0.5, 110 + V * 0.4
    hook, cy = G.hook_down(w - V, V, p.H, DSC - O * 0.5, rx, ry)
    return c + [hook, rect(w - V, cy, w, XH * 0.6)], w, sb


def g_Eng(p):
    c, w, sb = fn_of("N")(p)
    V = p.VC
    rx, ry = 120 + V * 0.5, 120 + V * 0.4
    hook, cy = G.hook_down(w - V, V, p.HC, DSC - O * 0.5, rx, ry)
    return c + [hook, rect(w - V, cy, w, 10)], w, sb


def g_ij(p):
    ci, ii, si = fn_of("i")(p)
    cj, ij, sj = fn_of("j")(p)
    off = ii + si[1] + sj[0]
    return ci + translate(cj, off), off + ij, (si[0], sj[1])


def g_IJ(p):
    ci, ii, si = fn_of("I")(p)
    cj, ij, sj = fn_of("J")(p)
    off = ii + si[1] + sj[0]
    return ci + translate(cj, off), off + ij, (si[0], sj[1])


def g_ldot(p, base="l"):
    c, ink, (lsb, rsb) = fn_of(base)(p)
    d = dot_size(p)
    x = ink + 60 + p.dV * 0.2 if base == "l" else p.VC + 70
    y = XH * 0.45 if base == "l" else CH * 0.45
    c = c + [rect(x, y - d / 2, x + d, y + d / 2)]
    return c, max(ink, x + d), (lsb, rsb if base == "L" else p.SB * 0.8)


for nm, ch, fn in [
    ("lslash", "ł", g_lslash), ("Lslash", "Ł", g_Lslash), ("Eth", "Ð", g_Eth), ("Dcroat", "Đ", g_Eth),
    ("dcroat", "đ", g_dcroat), ("hbar", "ħ", g_hbar), ("Hbar", "Ħ", g_Hbar), ("tbar", "ŧ", g_tbar),
    ("Tbar", "Ŧ", g_Tbar), ("oslash", "ø", g_oslash), ("Oslash", "Ø", g_Oslash), ("AE", "Æ", g_AE),
    ("ae", "æ", g_ae), ("oe", "œ", g_oe), ("OE", "Œ", g_OE), ("Thorn", "Þ", g_Thorn), ("thorn", "þ", g_thorn),
    ("eth", "ð", g_eth), ("germandbls", "ß", g_germandbls), ("kgreenlandic", "ĸ", g_kgreenlandic),
    ("eng", "ŋ", g_eng), ("Eng", "Ŋ", g_Eng), ("ij", "ĳ", g_ij), ("IJ", "Ĳ", g_IJ),
    ("ldot", "ŀ", g_ldot), ("Ldot", "Ŀ", lambda p: g_ldot(p, "L")),
]:
    add(nm, ch, fn)
BASE.update({"lslash": "l", "Lslash": "L", "Eth": "D", "Dcroat": "D", "dcroat": "d", "oslash": "o",
             "Oslash": "O", "AE": "A", "Thorn": "P", "thorn": "p", "germandbls": "B", "ij": "i", "IJ": "I"})


def g_aeacute(p):  # not in range, but Æ/æ are common enough that their bases matter
    return None


# --- punctuation -------------------------------------------------------------------

def quote_r(p):
    c, w = comma_shape(p, 1.0)
    return translate(c, w / 2, CH), w


def quote_l(p):
    c, w = comma_shape(p, 1.0)
    c = rotate180(c, 0, 0)
    d = dot_size(p)
    return translate(c, w / 2, CH - d), w


def g_quoteright(p):
    c, w = quote_r(p)
    return c, w, (p.SB, p.SB)


def g_quoteleft(p):
    c, w = quote_l(p)
    return c, w, (p.SB, p.SB)


def double(fn):
    def g(p):
        c, w = fn(p)
        gap = 70 + p.dV * 0.25
        return c + translate(c, w + gap), 2 * w + gap, (p.SB, p.SB)
    return g


def g_quotesinglbase(p):
    c, d, sb = fn_of("comma")(p)
    return c, d, sb


def g_quotedblbase(p):
    c, d, sb = fn_of("comma")(p)
    gap = 70 + p.dV * 0.25
    return c + translate(c, d + gap), 2 * d + gap, sb


def dash(width, y=None, t=None):
    def g(p):
        yy = XH * 0.42 if y is None else y
        tt = p.H * 1.05 if t is None else t
        w = width(p)
        return [rect(0, yy, w, yy + tt)], w, (p.SBD + 22, p.SBD + 22)
    return g


def g_ellipsis(p):
    d = dot_size(p)
    gap = 120 + p.dV * 0.3
    return [rect(i * (d + gap), 0, i * (d + gap) + d, d) for i in range(3)], 3 * d + 2 * gap, (p.SB, p.SB)


def g_bullet(p):
    s = dot_size(p) * 1.9
    y = XH / 2 - s / 2 + 10
    return [Ellipse(0, y, s, y + s, 0.64).contour()], s, (p.SB, p.SB)


def g_periodcentered(p):
    d = dot_size(p)
    y = XH / 2 - d / 2 + 10
    return [rect(0, y, d, y + d)], d, (p.SB, p.SB)


def chevron(p, w, hh, t, cy, x0=0):
    tv = t * math.hypot(w, hh) / w
    up = poly((x0, cy - tv / 2), (x0 + w, cy + hh - tv), (x0 + w, cy + hh), (x0, cy + tv / 2))
    dn = poly((x0, cy - tv / 2), (x0 + w, cy - hh), (x0 + w, cy - hh + tv), (x0, cy + tv / 2))
    return [up, dn]


def g_guilsinglleft(p):
    w, hh = 200 + p.dV * 0.5, 185
    return chevron(p, w, hh, p.D * 0.80, XH / 2 - 10), w, (p.SBD + 16, p.SBD + 16)


def g_guilsinglright(p):
    c, w, sb = g_guilsinglleft(p)
    return mirror_x(c, w), w, sb


def g_guillemotleft(p):
    w, hh = 200 + p.dV * 0.5, 185
    off = w * 0.55 + p.D * 0.7
    return chevron(p, w, hh, p.D * 0.80, XH / 2 - 10) + chevron(p, w, hh, p.D * 0.80, XH / 2 - 10, off), w + off, (p.SBD + 16, p.SBD + 16)


def g_guillemotright(p):
    c, w, sb = g_guillemotleft(p)
    return mirror_x(c, w), w, sb


def g_exclamdown(p):
    c, w, sb = fn_of("exclam")(p)
    return translate(rotate180(c, w / 2, CH / 2), 0, -(CH - XH) - 10 * 0), w, sb


def g_questiondown(p):
    c, w, sb = fn_of("question")(p)
    return translate(rotate180(c, w / 2, CH / 2), 0, -(CH - XH)), w, sb


def g_dagger(p, double_=False):
    V, H = p.V * 0.92, p.H
    w = 330 + p.dV * 0.4
    c = [rect(w / 2 - V / 2, DSC + 40, w / 2 + V / 2, CH), rect(0, CH - 190, w, CH - 190 + H)]
    if double_:
        c.append(rect(0, 60, w, 60 + H))
    return c, w, (p.SBD + 20, p.SBD + 20)


def g_prime(p, n=1):
    t = p.D * 0.85
    one = stroke((20, CH - 230), (110, CH), t, ("h", CH - 230), ("h", CH))
    c = [one] + ([translate([one], 120 + p.dV * 0.4)[0]] if n == 2 else [])
    x0, _, x1, _ = bounds(c)
    return translate(c, -x0), x1 - x0, (p.SB * 0.8, p.SB * 0.8)


def g_brokenbar(p):
    t = p.V * 0.9
    return [rect(0, DSC + 30, t, 190), rect(0, 320, t, ASC + 20)], t, (p.SB * 1.3, p.SB * 1.3)


def g_section(p):
    v = p.VR * 0.9
    w = p.c(310, 0.6) + 2 * v
    h = p.HR * 0.95
    up = G.s_shape(w, CH * 0.20, CH + O, v, h, h * 1.04, 0.40, 0.36)
    lo = G.s_shape(w, DSC + 40, CH * 0.60, v, h, h * 1.04, 0.36, 0.40)
    return up + lo, w, (p.SBR, p.SBR)


def g_paragraph(p):
    V, h = p.V * 0.95, p.H
    w = 460 + p.dV * 0.5
    bw = w * 0.62
    o = Ellipse(0, CH * 0.36, bw + V * 0.6, CH, 0.62)
    bowl = [o.contour()]
    return bowl + [rect(bw, DSC + 40, bw + V, CH), rect(w - V, DSC + 40, w, CH), rect(bw, CH - h, w, CH)], w, (p.SBR, p.SB)


# --- currency ----------------------------------------------------------------------

def g_Euro(p):
    v, h = p.VC * 1.02, p.HC * 0.97
    w = p.c(420, 0.5) + 2 * v
    con, _, _ = G.c_shape(w, -O, CH + O, v, h, 0.50, 0.50)
    pad = 90 + p.dV * 0.3
    c = translate([con], pad)
    t = p.HC * 0.92
    c += [rect(0, CH * 0.56, pad + w * 0.62, CH * 0.56 + t), rect(0, CH * 0.36, pad + w * 0.56, CH * 0.36 + t)]
    return c, pad + w, (p.SBD + 10, p.SBCR * 0.9)


def g_sterling(p):
    V, H = p.VC, p.HC
    w = p.c(420, 0.6) + V
    xs = w * 0.22
    rx, ry = (w - xs) / 2 * 0.95, 160 + V * 0.3
    top = CH + O
    o = Ellipse(xs, top - 2 * ry, xs + 2 * rx, top, 0.6)
    i = Ellipse(xs + V, top - 2 * ry + H, xs + 2 * rx - V, top - H, 0.62)
    yt = o.cy - 0.10 * o.ry
    hook = band(o, i, o.at_y(4, yt), (1, 1.0), i.at_y(4, yt), (1, 1.0))
    return [hook, rect(xs, 50, xs + V, o.cy), rect(0, CH * 0.38, w * 0.74, CH * 0.38 + H),
            rect(0, 0, w, H), poly((xs - 20, H - 2), (xs + V, H - 2), (xs + V, 120), (xs + 10, 120))], w, (p.SBD + 20, p.SBD + 16)


def g_yen(p):
    c, w, sb = fn_of("Y")(p)
    t = p.HC * 0.9
    bw = 360 + p.dV * 0.6
    c = c + [rect(w / 2 - bw / 2, CH * 0.30, w / 2 + bw / 2, CH * 0.30 + t),
             rect(w / 2 - bw / 2, CH * 0.30 - t - 60, w / 2 + bw / 2, CH * 0.30 - 60)]
    return c, w, sb


def g_cent(p):
    c, w, sb = fn_of("c")(p)
    V = p.V * 0.8
    return c + [rect(w * 0.5 - V / 2, -110, w * 0.5 + V / 2, XH + 110)], w, sb


def g_currency(p):
    v, h = p.V * 0.9, p.H * 0.9
    s = 330 + p.dV * 0.4
    pad = 70
    cx = cy = s / 2 + pad
    c = ring(Ellipse(pad, pad + 40, pad + s, pad + s + 40, 0.6), Ellipse(pad + v, pad + 40 + h, pad + s - v, pad + s + 40 - h, 0.62))
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        p0 = (cx + math.cos(r) * s * 0.40, cy + 40 + math.sin(r) * s * 0.40)
        p1 = (cx + math.cos(r) * (s * 0.5 + pad), cy + 40 + math.sin(r) * (s * 0.5 + pad))
        c.append(stroke(p0, p1, p.D * 0.85))
    x0, _, x1, _ = bounds(c)
    return translate(c, -x0), x1 - x0, (p.SBR, p.SBR)


# --- math and arrows ------------------------------------------------------------------

MATH_CY = 300


def g_minus(p):
    w = math_width(p) - 50
    h = p.H
    return [rect(0, MATH_CY - h / 2, w, MATH_CY + h / 2)], w, (math_sb(p, w),) * 2


def g_plusminus(p):
    c, w, sb = fn_of("plus")(p)
    h = p.H
    c = translate(c, 0, 60)
    return c + [rect(0, MATH_CY - w / 2 + 60 - 60 - h, w, MATH_CY - w / 2 + 60 - 60)], w, sb


def g_multiply(p):
    w = math_width(p) - 110
    t = p.H * 1.02
    cy = MATH_CY
    a = stroke((0, cy - w / 2), (w, cy + w / 2), t)
    b = stroke((0, cy + w / 2), (w, cy - w / 2), t)
    c = [a, b]
    x0, _, x1, _ = bounds(c)
    c = translate(c, -x0)
    return c, x1 - x0, (math_sb(p, x1 - x0),) * 2


def g_divide(p):
    c, w, sb = g_minus(p)
    d = dot_size(p)
    g = 54 + p.dV * 0.2
    c += [rect(w / 2 - d / 2, MATH_CY + p.H / 2 + g, w / 2 + d / 2, MATH_CY + p.H / 2 + g + d),
          rect(w / 2 - d / 2, MATH_CY - p.H / 2 - g - d, w / 2 + d / 2, MATH_CY - p.H / 2 - g)]
    return c, w, sb


def g_notequal(p):
    c, w, sb = fn_of("equal")(p)
    s = stroke((w * 0.28, MATH_CY - 190), (w * 0.72, MATH_CY + 190), p.H * 1.0)
    return c + [s], w, sb


def g_lessequal(p, greater=False):
    c, w, sb = fn_of("greater" if greater else "less")(p)
    c = translate(c, 0, 50)
    h = p.H
    return c + [rect(0, MATH_CY - 210 + 50 - 70 - h, w, MATH_CY - 210 + 50 - 70)], w, sb


def g_approxequal(p):
    w = math_width(p) - 40
    t = p.H * 1.0
    a = tilde_shape(w, 40 + p.dV * 0.1, t, 0)
    c = [translate([a], w / 2, MATH_CY + 30)[0], translate([a], w / 2, MATH_CY - 130 - t * 0.5)[0]]
    return c, w, (math_sb(p, w),) * 2


def g_logicalnot(p):
    w = math_width(p) - 50
    h = p.H
    return [rect(0, MATH_CY + 40, w, MATH_CY + 40 + h), rect(w - p.V * 0.95, MATH_CY - 120, w, MATH_CY + 40 + h)], w, (math_sb(p, w),) * 2


def g_degree(p):
    s = 210 + p.dV * 0.4
    v, h = p.V * 0.82, p.H * 0.82
    return ring(Ellipse(0, CH - s, s, CH, 0.6), Ellipse(v, CH - s + h, s - v, CH - h, 0.62)), s, (p.SBR, p.SBR)


def g_fraction(p):
    w = 300 + p.dV * 0.3
    D = p.D * 0.88
    hw = diag_hw(w, CH, D)
    return [poly((0, 0), (hw, 0), (w, CH), (w - hw, CH))], w, (-60, -60)


def arrow(direction):
    def g(p):
        L = 760 + p.dV * 0.6
        t = p.H * 1.05
        head = 210 + p.dV * 0.3
        cy = MATH_CY
        shaft = rect(0, cy - t / 2, L - t * 0.6, cy + t / 2)
        hd = p.D * 0.92
        a = stroke((L - head, cy + head), (L, cy), hd, ("p",), ("p",))
        b = stroke((L - head, cy - head), (L, cy), hd, ("p",), ("p",))
        tip = poly((L - hd * 0.75, cy), (L - hd * 1.3, cy + hd * 0.6), (L + 0.01, cy + 0.01), (L - hd * 1.3, cy - hd * 0.6))
        c = [shaft, a, b]
        if direction == "left":
            c = mirror_x(c, L)
        elif direction in ("up", "down"):
            c = rotate(c, 90 if direction == "up" else -90, L / 2, cy)
        x0, y0, x1, y1 = bounds(c)
        if direction in ("up", "down"):
            c = translate(c, -x0, -y0 + (CH - (y1 - y0)) / 2 - 20)
        else:
            c = translate(c, -x0)
        x0, y0, x1, y1 = bounds(c)
        return c, x1 - x0, (p.SBR, p.SBR)
    return g


# --- superscripts, fractions, ordinals, marks ----------------------------------------

SUP = 0.60


def heavier(p):
    """Parameters for small forms: drawn heavier, then scaled down, so their
    strokes stay close to the main weight."""
    return P(p.wght, p.V * 1.45)


def small_fig(name, p, y):
    c, ink, sb = fn_of(name)(heavier(p))
    return scale(c, SUP, SUP, 0, y), ink * SUP


def sup(name):
    def g(p):
        c, w = small_fig(name, p, CH - CH * SUP)
        return c, w, (36, 36)
    return g


def fraction_glyph(num, den):
    def g(p):
        a, wa = small_fig(num, p, CH - CH * SUP)
        b, wb = small_fig(den, p, 0)
        s, ws, _ = g_fraction(p)
        gap = 10
        c = a + translate(s, wa + gap - 50) + translate(b, wa + gap + ws - 100 + gap)
        return c, wa + ws + wb + 2 * gap - 150, (p.SBR, p.SBR)
    return g


def ordinal(base):
    def g(p):
        c, ink, _ = fn_of(base)(heavier(p))
        c = scale(c, SUP, SUP, 0, CH - XH * SUP - 10)
        w = ink * SUP
        t = p.H * 0.95
        return c + [rect(0, CH * 0.28, w, CH * 0.28 + t)], w, (40, 40)
    return g


def circled(base, s=0.5):
    def g(p):
        D = 760 + p.dV * 0.3
        v, h = p.V * 0.62, p.H * 0.62
        cy = CH / 2
        c = ring(Ellipse(0, cy - D / 2, D, cy + D / 2, 0.58), Ellipse(v, cy - D / 2 + h, D - v, cy + D / 2 - h, 0.58))
        ic, ink, _ = fn_of(base)(heavier(p))
        ic = scale(ic, s, s)
        c += translate(ic, D / 2 - ink * s / 2, cy - CH * s / 2)
        return c, D, (p.SBR, p.SBR)
    return g


def g_trademark(p):
    t, wt, _ = fn_of("T")(heavier(p))
    m, wm, _ = fn_of("M")(heavier(p))
    s = 0.48
    y = CH - CH * s
    gap = 40
    c = scale(t, s, s, 0, y) + scale(m, s, s, wt * s + gap, y)
    return c, (wt + wm) * s + gap, (p.SBR, p.SBR)


def g_mu(p):
    c, w, sb = fn_of("u")(p)
    return c + [rect(0, DSC, p.V, XH * 0.5)], w, sb


# --- alternates for OpenType features ------------------------------------------------

def shifted(name, dy):
    def g(p):
        c, w, sb = fn_of(name)(p)
        return translate(c, 0, dy), w, sb
    return g


def g_l_tail(p):  # ss01: l with a tail, so it can't be confused with I or 1
    V = p.V
    rx = 92 + V * 0.5
    ry = 92 + V * 0.4
    o = Ellipse(0, -O, 2 * rx, -O + 2 * ry, 0.6)
    i = Ellipse(V, -O + p.H * 0.95, 2 * rx - V, -O + 2 * ry - p.H * 0.95, 0.62)
    w = rx + V * 0.6 + 30
    hook = band(o, i, (2, 0.0), o.at_x(3, w), (2, 0.0), i.at_x(3, w))
    return [rect(0, o.cy, V, ASC), hook], w, (p.SB, p.SBD + 10)


def g_I_serif(p):  # ss01: I with crossbars
    V, h = p.VC, p.HC
    w = 280 + p.dV * 0.6
    x = w / 2 - V / 2
    return [rect(x, 0, x + V, CH), rect(0, 0, w, h), rect(0, CH - h, w, CH)], w, (p.SBC * 0.8, p.SBC * 0.8)


def g_zero_slash(p, base="zero"):
    c, w, sb = fn_of(base)(p)
    s = stroke((w * 0.24, CH * 0.20), (w * 0.76, CH * 0.80), p.D * 0.85, ("p",), ("p",))
    return c + [s], w, sb


def g_one_prop(p):
    c, w, sb = fn_of("one")(p)
    return c, w, (p.SB * 0.9, p.SB * 1.1)


# --- registration --------------------------------------------------------------------

SPACE = lambda p: ([], 0, (136 + p.dV * 0.3,) * 2)

for nm, ch, fn in [
    ("uni00A0", " ", SPACE), ("uni2009", " ", lambda p: ([], 0, (85, 85))),
    ("figurespace", " ", lambda p: ([], 0, ((fig_width(p) + 2 * p.SBR) / 2,) * 2)),
    ("uni00AD", "­", fn_of("hyphen")),
    ("quoteright", "’", g_quoteright), ("quoteleft", "‘", g_quoteleft),
    ("quotedblright", "”", double(quote_r)), ("quotedblleft", "“", double(quote_l)),
    ("quotesinglbase", "‚", g_quotesinglbase), ("quotedblbase", "„", g_quotedblbase),
    ("endash", "–", dash(lambda p: 500 + p.dV * 0.3)), ("emdash", "—", dash(lambda p: 940)),
    ("ellipsis", "…", g_ellipsis), ("bullet", "•", g_bullet), ("periodcentered", "·", g_periodcentered),
    ("guilsinglleft", "‹", g_guilsinglleft), ("guilsinglright", "›", g_guilsinglright),
    ("guillemotleft", "«", g_guillemotleft), ("guillemotright", "»", g_guillemotright),
    ("exclamdown", "¡", g_exclamdown), ("questiondown", "¿", g_questiondown),
    ("dagger", "†", g_dagger), ("daggerdbl", "‡", lambda p: g_dagger(p, True)),
    ("minute", "′", g_prime), ("second", "″", lambda p: g_prime(p, 2)),
    ("brokenbar", "¦", g_brokenbar), ("section", "§", g_section), ("paragraph", "¶", g_paragraph),
    ("Euro", "€", g_Euro), ("sterling", "£", g_sterling), ("yen", "¥", g_yen), ("cent", "¢", g_cent),
    ("currency", "¤", g_currency),
    ("minus", "−", g_minus), ("plusminus", "±", g_plusminus), ("multiply", "×", g_multiply),
    ("divide", "÷", g_divide), ("notequal", "≠", g_notequal), ("lessequal", "≤", g_lessequal),
    ("greaterequal", "≥", lambda p: g_lessequal(p, True)), ("approxequal", "≈", g_approxequal),
    ("logicalnot", "¬", g_logicalnot), ("degree", "°", g_degree), ("fraction", "⁄", g_fraction),
    ("arrowleft", "←", arrow("left")), ("arrowright", "→", arrow("right")),
    ("arrowup", "↑", arrow("up")), ("arrowdown", "↓", arrow("down")),
    ("onesuperior", "¹", sup("one")), ("twosuperior", "²", sup("two")), ("threesuperior", "³", sup("three")),
    ("onequarter", "¼", fraction_glyph("one", "four")), ("onehalf", "½", fraction_glyph("one", "two")),
    ("threequarters", "¾", fraction_glyph("three", "four")),
    ("ordfeminine", "ª", ordinal("a")), ("ordmasculine", "º", ordinal("o")),
    ("copyright", "©", circled("C")), ("registered", "®", circled("R")), ("trademark", "™", g_trademark),
    ("mu", "µ", g_mu),
]:
    add(nm, ch, fn)

# case-sensitive forms: raise punctuation that's centred on the x-height so it
# centres on capitals instead
CASE = {
    "hyphen": 100, "endash": 100, "emdash": 100, "uni00AD": 100,
    "parenleft": 64, "parenright": 64, "bracketleft": 64, "bracketright": 64,
    "braceleft": 64, "braceright": 64, "guilsinglleft": 96, "guilsinglright": 96,
    "guillemotleft": 96, "guillemotright": 96, "bullet": 96, "periodcentered": 96,
    "colon": 96, "exclamdown": CH - XH, "questiondown": CH - XH,
}
for nm, dy in CASE.items():
    add(nm + ".case", None, shifted(nm, dy))
ALT["case"] = [(nm, nm + ".case") for nm in CASE]

add("l.ss01", None, g_l_tail)
add("I.ss01", None, g_I_serif)
add("zero.zero", None, g_zero_slash)
ALT["ss01"] = [("l", "l.ss01"), ("I", "I.ss01"), ("zero", "zero.zero")]
ALT["zero"] = [("zero", "zero.zero")]

# Figures: proportional by default, so a 1 inside "fra1" or a hash doesn't leave a gap,
# and tabular under `tnum` (CSS tabular-nums), which litt sets for values and counts.
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def proportional(fn, name):
    def g(p):
        c, ink, _ = fn(p)
        sb = p.SBR * (0.9 if name in ("four", "seven") else 1.15)
        return c, ink, (sb, sb)
    return g


for d in DIGITS:
    ch, fn = GLYPHS[d]
    add(d + ".tf", None, fn)
    GLYPHS[d] = (ch, proportional(fn, d))
add("zero.zero.tf", None, lambda p: g_zero_slash(p, "zero.tf"))
# every order of tnum, zero and ss01 lands on the right zero
ALT["tnum"] = [(d, d + ".tf") for d in DIGITS] + [("zero.zero", "zero.zero.tf")]
ALT["zero"] = [("zero", "zero.zero"), ("zero.tf", "zero.zero.tf")]
ALT["ss01"] = ALT["ss01"] + [("zero.tf", "zero.zero.tf")]


def ccmp_pairs():
    """(base glyph, combining mark glyph, precomposed glyph) for decomposed input."""
    out = []
    for nm, (ch, _) in GLYPHS.items():
        if not ch:
            continue
        d = unicodedata.decomposition(ch)
        if not d or d.startswith("<"):
            continue
        parts = [int(x, 16) for x in d.split()]
        if len(parts) != 2 or parts[1] not in ACCENTS:
            continue
        base = name_for(parts[0]) if parts[0] > 0x7F else G_NAME.get(chr(parts[0]))
        if base and base in GLYPHS:
            out.append((base, name_for(parts[1]), nm))
    return out


G_NAME = {ch: nm for nm, (ch, _) in GLYPHS.items() if ch and len(ch) == 1 and ord(ch) < 0x80}
