"""Hypher's glyphs: machined letters, drawn in code.

Every letter is built from flat-sided polygons with rounded corners, after the
Hypher mark: sides are straight and curves happen only in corners. Each
function takes the weight parameters and returns (contours, ink, (lsb, rsb)).

How round the letters are is a style: a named set of numbers in STYLES. Each
style is a version of Hypher; set_style() picks one before drawing.
"""

import os

from core import geometry
from core.geometry import diag_hw, mirror_x, rect, rotate, rotate180, translate

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
# Figures and symbols, measured the same way.
WM_WIDTHS.update({
    "zero": 822, "one": 662, "two": 808, "three": 819, "four": 871, "five": 799, "six": 819,
    "seven": 840, "eight": 819, "nine": 819, "question": 700, "hyphen": 373, "endash": 404,
    "emdash": 529, "parenleft": 249, "parenright": 249, "bracketleft": 280, "bracketright": 280,
    "slash": 436, "plus": 529, "equal": 489, "asterisk": 563, "underscore": 529, "numbersign": 690,
})
WM_SIDES.update({
    "zero": (102, 102), "one": (219, 146), "two": (121, 98), "three": (104, 104), "four": (102, 102),
    "five": (126, 102), "six": (115, 93), "seven": (102, 102), "eight": (104, 104), "nine": (104, 122),
    "period": (102, 102), "comma": (71, 102), "colon": (102, 102), "semicolon": (71, 102),
    "exclam": (131, 131), "question": (146, 137), "hyphen": (102, 102), "endash": (102, 102),
    "emdash": (40, 40), "quotesingle": (102, 102), "quotedbl": (102, 102), "quoteleft": (102, 102),
    "quoteright": (102, 102), "quotedblleft": (102, 102), "quotedblright": (102, 102),
    "parenleft": (102, 102), "parenright": (102, 102), "bracketleft": (102, 102),
    "bracketright": (102, 102), "slash": (71, 71), "plus": (116, 116), "equal": (136, 136),
    "asterisk": (102, 102), "underscore": (40, 40), "numbersign": (91, 91),
})
# Capitals and the last symbols, measured the same way.
WM_WIDTHS.update({
    "A": 996, "B": 871, "C": 917, "D": 915, "E": 747, "F": 704, "G": 917, "H": 871, "I": 93, "J": 684,
    "K": 856, "L": 684, "M": 1174, "N": 942, "O": 918, "P": 836, "Q": 918, "R": 836, "S": 917, "T": 840,
    "U": 898, "V": 928, "W": 1543, "X": 996, "Y": 933, "Z": 871, "ampersand": 1000, "at": 964,
    "percent": 920,
})
WM_SIDES.update({
    "A": (71, 71), "B": (133, 102), "C": (102, 104), "D": (135, 102), "E": (133, 71), "F": (133, 83),
    "G": (102, 119), "H": (135, 135), "I": (133, 133), "J": (102, 127), "K": (133, 71), "L": (133, 71),
    "M": (135, 135), "N": (133, 133), "O": (102, 102), "P": (135, 76), "Q": (102, 40), "R": (135, 123),
    "S": (105, 100), "T": (86, 86), "U": (106, 106), "V": (73, 75), "W": (77, 77), "X": (71, 71),
    "Y": (102, 102), "Z": (102, 101), "ampersand": (102, 90), "at": (102, 102), "percent": (102, 102),
})
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
# Lathe: the Wordmark's landmarks, spacing and kerning with Hypher's own details
# (machined corners, the straight y) and its own width. Corners alone barely move
# a design away from Michroma (88% -> 86% overlap); width does, so each Lathe
# sits about 75% from Michroma: related to the logo, but its own.
_LATHE = {**STYLES["Wordmark"], "radius": 0.215, "smooth": 0.6, "inner_smooth": 0.6, "inner": 0.55, "term": 0.02,
          "y_tail": "straight"}
STYLES["LatheWide"] = {**_LATHE, "widths": {c: round(w * 1.06) for c, w in WM_WIDTHS.items()}, "kern_scale": 1.06}
STYLES["LatheNarrow"] = {**_LATHE, "widths": {c: round(w * 0.95) for c, w in WM_WIDTHS.items()}, "kern_scale": 0.95}

# Billet: Hypher's own proportion system, with a fifth of the wordmark font in it.
# Widths come from rules (one width per family of shapes, as multiples of the
# x-height or cap height), sidebearings from the shape of each side, and
# landmarks from shared heights (terminals at 0.30 and 0.70, bars in the
# middle, the f at the ascender, the g at the descender). Each number is then
# blended: 80% Hypher's rule, 20% the wordmark font's measurement.
MICHROMA_SHARE = 0.2

_X, _C = XH, ASC
_OWN_W = {
    **dict.fromkeys("oce", 1.14 * _X), **dict.fromkeys("bdpqg", 1.16 * _X), "a": 1.08 * _X,
    **dict.fromkeys("nhu", 1.06 * _X), "m": 2 * 1.06 * _X - REGULAR_STEM, "r": 0.62 * _X, "f": 0.74 * _X,
    "t": 0.76 * _X, "i": 93, "l": 93, "j": 0.42 * _X, "k": 1.04 * _X, "s": 1.08 * _X,
    **dict.fromkeys("vy", 1.14 * _X), "x": 1.12 * _X, "z": 1.02 * _X, "w": 1.74 * _X,
    **dict.fromkeys("OCGQD", 1.15 * _C), **dict.fromkeys("BPR", 1.06 * _C), **dict.fromkeys("HNU", 1.10 * _C),
    "E": 0.95 * _C, "F": 0.92 * _C, "L": 0.88 * _C, **dict.fromkeys("AVX", 1.22 * _C), "Y": 1.15 * _C,
    "M": 1.45 * _C, "W": 1.95 * _C, "K": 1.08 * _C, "S": 1.12 * _C, "T": 1.05 * _C, "Z": 1.08 * _C,
    "J": 0.90 * _C, "I": 93,
    **dict.fromkeys(["zero", "two", "three", "five", "six", "seven", "eight", "nine"], 0.98 * _C),
    "one": 0.80 * _C, "four": 1.05 * _C,
}
# Sidebearing by the shape of the side: straight, round, open (a terminal), diagonal.
_SIDE = {"S": 0.18 * _X, "R": 0.15 * _X, "T": 0.10 * _X, "D": 0.08 * _X, "F": 0.12 * _X}
_TYPES = {
    "a": "RS", "b": "SR", "c": "RT", "d": "RS", "e": "RR", "f": "TD", "g": "RS", "h": "SS", "i": "SS",
    "j": "DS", "k": "SD", "l": "SS", "m": "SS", "n": "SS", "o": "RR", "p": "SR", "q": "RS", "r": "ST",
    "s": "RR", "t": "ST", "u": "SS", "v": "DD", "w": "DD", "x": "DD", "y": "DD", "z": "FF",
    "A": "DD", "B": "SR", "C": "RT", "D": "SR", "E": "ST", "F": "ST", "G": "RS", "H": "SS", "I": "SS",
    "J": "TS", "K": "SD", "L": "SD", "M": "SS", "N": "SS", "O": "RR", "P": "SR", "Q": "RR", "R": "SD",
    "S": "RR", "T": "DD", "U": "SS", "V": "DD", "W": "DD", "X": "DD", "Y": "DD", "Z": "FF",
    **dict.fromkeys(["zero", "two", "three", "five", "six", "seven", "eight", "nine", "four"], "RR"),
    "one": "SS",
}
_OWN_LM = {
    "a_bowl": 0.55, "a_hook": 0.70, "c_t0": 0.30, "c_t1": 0.70, "f_top": ASC / XH, "g_deep": DSC,
    "k_ya": 0.56, "k_yl": 0.50, "s_mid": 0.50, "s_t0": 0.30, "s_t1": 0.70, "t_top": 1.20, "t_foot": 0.30,
    "two_bar": 0.447, "two_t": 0.70, "three_tb": 0.30, "three_tt": 0.70, "three_mid": 0.50, "four_bar": 0.25,
    "five_bowl": 0.60, "five_t": 0.30, "six_bowl": 0.55, "six_t": 0.70, "A_bar": 0.25, "B_mid": 0.50,
    "C_t0": 0.30, "C_t1": 0.70, "EFH_mid": 0.50, "G_bar": 0.50, "G_t1": 0.70, "J_t": 0.30, "M_dip": 0.0,
    "P_bowl": 0.40, "R_bowl": 0.40, "S_mid": 0.50, "S_t0": 0.30, "S_t1": 0.70, "Y_join": 0.45,
}
_MICH_LM = {  # the defaults lm() falls back to, from the wordmark font
    "a_bowl": 0.58, "a_hook": 0.73, "c_t0": 0.334, "c_t1": 0.686, "f_top": 1.40, "g_deep": -213,
    "k_ya": 0.563, "k_yl": 0.513, "s_mid": 0.523, "s_t0": 0.29, "s_t1": 0.72, "t_top": 1.273, "t_foot": 0.436,
    "two_bar": 0.446, "two_t": 0.736, "three_tb": 0.29, "three_tt": 0.736, "three_mid": 0.518, "four_bar": 0.209,
    "five_bowl": 0.636, "five_t": 0.29, "six_bowl": 0.57, "six_t": 0.736, "A_bar": 0.229, "B_mid": 0.532,
    "C_t0": 0.337, "C_t1": 0.656, "EFH_mid": 0.510, "G_bar": 0.526, "G_t1": 0.70, "J_t": 0.375, "M_dip": 0.066,
    "P_bowl": 0.386, "R_bowl": 0.404, "S_mid": 0.515, "S_t0": 0.33, "S_t1": 0.70, "Y_join": 0.416,
}


def _mix(own, michroma):
    return own * (1 - MICHROMA_SHARE) + michroma * MICHROMA_SHARE


STYLES["Billet"] = {
    **STYLES["Finish"],
    "y_tail": "straight", "stem_tops": "round", "e_bar": _mix(0.43, 0.454), "e_term": _mix(0.30, 0.297),
    "widths": {**WM_WIDTHS, **{c: round(_mix(w, WM_WIDTHS[c])) for c, w in _OWN_W.items()}},
    "sides": {**WM_SIDES, **{c: (round(_mix(_SIDE[t[0]] * (1.15 if c[0].isupper() else 1), WM_SIDES[c][0])),
                                 round(_mix(_SIDE[t[1]] * (1.15 if c[0].isupper() else 1), WM_SIDES[c][1])))
                             for c, t in _TYPES.items()}},
    "lm": {k: _mix(v, _MICH_LM[k]) for k, v in _OWN_LM.items()},
    "kern_scale": 0.95,
}
# Datum: none of the wordmark font. Every width, sidebearing and landmark is
# Hypher's own rule; the remaining placements (the K's arm, the 4's stem, the
# colon's dots, the bars of E and F, punctuation widths) are Hypher's too, and
# kerning is measured from Datum's own outlines (autokern.py).
_OWN_SYM_W = {
    "question": 1.12 * _X, "hyphen": 0.62 * _X, "endash": 0.80 * _X, "emdash": 1.40 * _X,
    "parenleft": 0.40 * _X, "parenright": 0.40 * _X, "bracketleft": 0.45 * _X, "bracketright": 0.45 * _X,
    "slash": 0.72 * _X, "plus": 0.90 * _X, "equal": 0.90 * _X, "asterisk": 0.90 * _X, "underscore": 1.00 * _X,
    "numbersign": 1.15 * _X, "ampersand": 1.70 * _X, "at": 1.65 * _X, "percent": 1.55 * _X,
}
_SYM_TYPES = {
    **dict.fromkeys(["period", "comma", "colon", "semicolon", "exclam", "quotesingle", "quotedbl", "quoteleft",
                     "quoteright", "quotedblleft", "quotedblright"], "SS"),
    **dict.fromkeys(["hyphen", "endash", "emdash", "underscore", "plus", "equal", "asterisk", "numbersign"], "FF"),
    "question": "TR", "parenleft": "RT", "parenright": "TR", "bracketleft": "ST", "bracketright": "TS",
    "slash": "DD", "ampersand": "RD", "at": "RR", "percent": "RR",
}
STYLES["Datum"] = {
    **STYLES["Finish"],
    "y_tail": "straight", "stem_tops": "round", "e_bar": 0.43, "e_term": 0.30,
    "widths": {**WM_WIDTHS, **_OWN_W, **_OWN_SYM_W},
    "sides": {**WM_SIDES, **{c: (round(_SIDE[t[0]] * (1.15 if c[0].isupper() else 1)),
                                 round(_SIDE[t[1]] * (1.15 if c[0].isupper() else 1)))
                             for c, t in {**_TYPES, **_SYM_TYPES}.items()}},
    "lm": {
        **_OWN_LM, "g_tip": 0.15, "g_xt": 0.0, "k_xt": 0.70, "k_xb": 0.74, "t_bar": 1.0, "f_x0": 0.25,
        "one_xs": 0.42, "one_drop": 0.12, "three_xm": 0.35, "four_xs": 0.70, "seven_xb": 0.25, "eight_mid": 0.50,
        "colon_lo": 0.25, "colon_hi": 0.75, "q_xs": 0.40, "q_bar": 0.45, "q_t": 0.70, "dash": 0.50, "plus": 0.50,
        "equal": 0.50, "equal_gap": 0.25, "B_upper": 0.95, "E_top": 1.0, "E_mid": 0.88, "F_mid": 0.88,
        "K_xj": 0.22, "K_xa": 0.78, "K_xl": 0.80, "R_x0": 0.62, "R_x1": 1.0, "Z_l": 0.0, "Z_r": 1.0,
        "G_xb": 0.55, "at_b": -0.16, "at_t": 1.16,
    },
    "kerning": "auto",
    "types": {**_TYPES, **_SYM_TYPES},
}

# Chamfer: as far from the wordmark font as Hypher goes. Datum's own rules and
# kerning, every corner cut with a straight chamfer instead of a curve, and
# letters at 86% of Datum's width: Michroma is wide and round; this is
# neither.
STYLES["Chamfer"] = {**STYLES["Datum"], "chamfer": True, "smooth": 0.0, "inner_smooth": 0.0, "radius": 0.17,
                     "inner": 0.55, "term": 0.0,
                     "widths": {c: round(w * 0.86) for c, w in STYLES["Datum"]["widths"].items()}}

# Datum 20: Datum at 93% width. Fonts of the same genre share about 47% of
# their letter area with the wordmark font whatever their design (the floor);
# measured above that floor, this one resembles it by 20%.
STYLES["Datum20"] = {**STYLES["Datum"], "widths": {c: round(w * 0.93) for c, w in STYLES["Datum"]["widths"].items()}}

# Weld: Datum's corners, proportions and own kerning, with the wordmark's
# construction: the y's tail hooking into a flat foot, and stems that rise
# square to the x-height in r, n, m, p and u.
STYLES["Weld"] = {**STYLES["Datum"], "y_tail": "hook", "y_tail_end": 0.19, "stem_tops": "square"}

# Billet Compact: Billet at 90% width, out of the wordmark font's wide stance.
STYLES["BilletCompact"] = {**STYLES["Billet"], "widths": {c: round(w * 0.90) for c, w in STYLES["Billet"]["widths"].items()},
                           "kern_scale": 0.86}
# The Wordmark design draws its e as Datum does (lower crossbar, softer cut
# ends, a little narrower), keeping the wordmark's spacing around it. Set
# after Lathe copies the Wordmark, so only the Wordmark itself borrows it.
STYLES["Wordmark"]["e_from"] = "Datum"
# Every curve follows that e: its corners (radius 0.215, eased 0.6, inside and
# out), its softly rounded cut ends, and its counters, half again as round as
# the bowls'. The Wordmark keeps its own widths, spacing and construction.
STYLES["Wordmark"].update(radius=0.215, smooth=0.6, inner_smooth=0.6, inner=0.55, term=0.02, counter=1.5,
                          notch=True)  # the shoulder notch beside square stem ends, kept by choice
DEFAULT_STYLE = "Wordmark"
LABELS = {"LatheWide": "Lathe Wide", "LatheNarrow": "Lathe Narrow", "BilletCompact": "Billet Compact", "Datum20": "Datum 20"}  # family-name spelling, where it differs from the key



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
        if "counter" in STYLE:  # rounder counters, but never rounder than the outside, or corners go heavy at Light
            self.ri = min(self.ri * STYLE["counter"], 0.85 * self.ro, 1.2 * stem)  # and at most 1.2 stems, or a thin stem goes heavy beside a square corner
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


def lm(key, default):
    """A landmark height (or the g's depth): the version's own, or the wordmark font's."""
    return STYLE.get("lm", {}).get(key, default)


def rounded(*corners):
    return geometry.rounded(*corners, smooth=STYLE["smooth"], chamfer=STYLE.get("chamfer", False))


def box(x0, y0, x1, y1, bl, br, tr, tl):
    """A rectangle with its own radius at each corner, counter-clockwise."""
    return rounded((x0, y0, bl), (x1, y0, br), (x1, y1, tr), (x0, y1, tl))


def hole(x0, y0, x1, y1, r, bottom=None, top=None):
    """A counter: a rounded rectangle running clockwise; bottom and top override those corners' radius."""
    b = r if bottom is None else bottom
    t = r if top is None else top
    return geometry.rounded((x0, y0, b), (x0, y1, t), (x1, y1, t), (x1, y0, b), smooth=STYLE["inner_smooth"],
                            chamfer=STYLE.get("chamfer", False))


def waist(p, side):
    """The corner radius where two stacked bowls meet (the 3's, the 8's): up to
    twice the outer corner, so the side pinches in about as deep as Michroma's,
    but only as much as the side has room for beside the outer corner, so the
    outer corner keeps its full size."""
    room = (side - 1) / (1 + 0.6 * STYLE["smooth"]) - p.ro
    return max(min(STYLE.get("waist", 2.0) * p.ro, room), 4)


def tee(p, r):
    """A counter's corner where three strokes meet (the B's middle bar at its stem,
    the m's middle stem, the 6's bowl at its stem): no rounder than a stem, so the
    joint stays as light as the e's at Light."""
    return min(joint(p, r), p.V)


def joint(p, r):
    """A counter's corner against a crossbar: no rounder than 1.3 bars, so two corners
    back to back across a thin bar (the e's, the 8's) do not swell into a blob at Light."""
    return min(r, 1.3 * p.H)


def stem_top(p, x0, bottom):
    """With square stem tops (the wordmark's), a stem whose flat top sits at the x-height."""
    if STYLE["stem_tops"] != "square":
        return []
    return [box(x0, bottom, x0 + p.V, XH, p.rt, p.rt, 0, p.rt)]


def arch(p, x0, x1, top, bottom=0, left_bottom=None, on_stem=()):
    """The n's arch: two stems joined by a flat top, open at the bottom.

    left_bottom ends the left leg higher, as a terminal (the a's hook). on_stem
    names the top corners ("left", "right") that sit on a stem with a square top:
    those are square too, or the arch's curve would leave a notch beside it."""
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    lb = bottom if left_bottom is None else left_bottom
    tl = shoulder(p, ro) if "left" in on_stem else ro
    tr = shoulder(p, ro) if "right" in on_stem else ro
    il = tee(p, ri) if "left" in on_stem else ri  # the counter's corner where the arch meets the stem
    ir = tee(p, ri) if "right" in on_stem else ri
    return rounded(
        (x0, lb, rt), (x0 + V, lb, rt), (x0 + V, top - H, il), (x1 - V, top - H, ir),
        (x1 - V, bottom, rt), (x1, bottom, rt), (x1, top, tr), (x0, top, tl),
    )


def rpoly(*corners):
    """rounded(), with the points put in counter-clockwise order first."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(corners, corners[1:] + corners[:1]))
    return rounded(*(corners if area > 0 else corners[::-1]))


def square(p, c):
    """A corner that is square on the wordmark (where its stems run straight into a bowl), round elsewhere."""
    return p.rt if STYLE["stem_tops"] == "square" else c


def shoulder(p, c):
    """A bowl's or arch's corner beside a square-ended stem. With "notch" (the
    wordmark's) it stays round, so the curve starts just past the stem's square
    end and leaves a small step there: the wordmark's shoulder. Without it, the
    corner squares off to run flush with the stem."""
    return c if STYLE.get("notch") else square(p, c)


def dot(p, x0):
    """The i's and j's dot: a stem-wide square whose top sits on the ascender."""
    return box(x0, ASC - p.V, x0 + p.V, ASC, p.rt, p.rt, p.rt, p.rt)


def bowl(p, x0, x1, bottom=0, top=XH, stem=None):
    """A closed bowl; stem ("left" or "right") squares the corners on that side,
    where they meet a square-ended stem, so no notch opens between them."""
    lft = shoulder(p, p.ro) if stem == "left" else p.ro
    rgt = shoulder(p, p.ro) if stem == "right" else p.ro
    return [box(x0, bottom, x1, top, lft, rgt, rgt, lft),
            hole(x0 + p.V, bottom + p.H, x1 - p.V, top - p.H, p.ri)]


@glyph("space", " ")
def g_space(p):
    return [], 0, (150, 150)


@glyph("n", "n")
def g_n(p):
    W = p.w("n")
    return stem_top(p, 0, 0) + [arch(p, 0, W, XH, on_stem=("left",))], W, p.sides("n")


@glyph("h", "h")
def g_h(p):
    W = p.w("h")
    stem = box(0, 0, p.V, ASC, p.rt, p.rt, p.rt, p.rt)
    return [stem, arch(p, 0, W, XH, on_stem=("left",))], W, p.sides("h")


@glyph("o", "o")
def g_o(p):
    W = p.w("o")
    return bowl(p, 0, W), W, p.sides("o")


@glyph("p", "p")
def g_p(p):
    W = p.w("p")
    tl = p.rt if STYLE["stem_tops"] == "square" else p.ro
    stem = box(0, DSC, p.V, XH, p.rt, p.rt, 0, tl)
    return [stem] + bowl(p, 0, W, stem="left"), W, p.sides("p")


@glyph("e", "e")
def g_e(p):
    """A bowl with a crossbar; the lower right opens above a flat terminal.

    The inner corner under the terminal is rounded twice as much as the rest,
    so the bottom stroke sweeps up into the terminal as the wordmark's e does,
    and the counters are rounded half again as much as the bowls'.
    The crossbar moves down a little as the strokes thicken, so Bold keeps an
    open eye."""
    if STYLE.get("e_from"):  # another version's e, in this version's spacing
        saved, sides = dict(STYLE), p.sides("e")
        set_style(STYLE["e_from"])
        try:
            contours, W, _ = g_e(P(p.wght, p.V))
        finally:
            STYLE.clear()
            STYLE.update(saved)
        return contours, W, sides
    W = p.w("e")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    bar0 = XH * STYLE["e_bar"] - (H - 79) * 0.5  # bottom of the crossbar
    bar1 = bar0 + H
    term = XH * STYLE["e_term"]  # top of the lower terminal
    rc = ri * 1.5  # the e's counters are softer than the bowls', as in the wordmark's e
    outer = rounded(
        (0, 0, ro), (W, 0, ro), (W, term, rt), (W - V, term, rt), (W - V, H, ri * 2), (V, H, rc),
        (V, bar0, joint(p, rc)), (W, bar0, rt), (W, XH, ro), (0, XH, ro),
    )
    eye = hole(V, bar1, W - V, XH - H, rc, bottom=joint(p, rc))
    return [outer, eye], W, p.sides("e")


@glyph("r", "r")
def g_r(p):
    """A stem and a flat arm, cut square at the right."""
    W = p.w("r")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    c = rounded(
        (0, 0, rt), (V, 0, rt), (V, XH - H, ri), (W, XH - H, rt), (W, XH, ro), (0, XH, shoulder(p, ro)),
    )
    return stem_top(p, 0, 0) + [c], W, p.sides("r")


@glyph("y", "y")
def g_y(p):
    """A symmetric V meeting on the baseline; the right arm runs on into the descender.

    Its tops are cut flat, as the v's and x's are."""
    W = p.w("y")
    V, rt = p.V, p.rt
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
            (xt, DSC, rt), (edge_x(DSC, hw / 2), DSC, ro * STYLE["y_bend"]), (W, XH, rt), (W - hw, XH, rt),
            (edge_x(DSC + H, -hw / 2), DSC + H, p.ri * STYLE["y_bend"]), (xt, DSC + H, rt),
        )
    else:
        right = rounded(
            (xd - hw / 2, DSC, rt), (xd + hw / 2, DSC, rt), (W, XH, rt), (W - hw, XH, rt),
        )

    # The left arm mirrors the right and stops on the right arm's centre line,
    # so the join has no foot. Left centre: x = cx - slope*y; right: x = cx + slope*y.
    def meet(edge):
        y = edge / (2 * slope)
        return (cx + slope * y, y, 0)

    left = rounded((0, XH, rt), meet(-hw / 2), meet(hw / 2), (hw, XH, rt))
    return [right, left], W, p.sides("y")



@glyph("a", "a")
def g_a(p):
    """A hook over a bowl: the hook's right leg is the stem; the bowl tucks under it."""
    W = p.w("a")
    top = XH * lm("a_bowl", 0.58) + (p.H - 79) * 0.6  # top of the bowl, raised with weight so its counter stays open
    hook = arch(p, 0, W, XH, left_bottom=XH * lm("a_hook", 0.73))
    return [hook] + bowl(p, 0, W, top=top, stem="right"), W, p.sides("a")


@glyph("b", "b")
def g_b(p):
    W = p.w("b")
    stem = box(0, 0, p.V, ASC, square(p, p.ro), 0, p.rt, p.rt)
    return [stem] + bowl(p, 0, W, stem="left"), W, p.sides("b")


@glyph("c", "c")
def g_c(p):
    """A bowl opened on the right between two flat terminals."""
    W = p.w("c")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    t0, t1 = XH * lm("c_t0", 0.334), XH * lm("c_t1", 0.686)
    c = rounded(
        (0, 0, ro), (W, 0, ro), (W, t0, rt), (W - V, t0, rt), (W - V, H, ri), (V, H, ri),
        (V, XH - H, ri), (W - V, XH - H, ri), (W - V, t1, rt), (W, t1, rt), (W, XH, ro), (0, XH, ro),
    )
    return [c], W, p.sides("c")


@glyph("d", "d")
def g_d(p):
    W = p.w("d")
    stem = box(W - p.V, 0, W, ASC, 0, square(p, p.ro), p.rt, p.rt)
    return [stem] + bowl(p, 0, W, stem="right"), W, p.sides("d")


@glyph("f", "f")
def g_f(p):
    """The r's arm raised above the ascender, with a crossbar at the x-height."""
    W = p.w("f")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    x0, top = W * lm("f_x0", 0.208), XH * lm("f_top", 1.40)
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
    deep, xt = lm("g_deep", -213), W * lm("g_xt", 0.037)  # the g's tail goes below the other descenders
    tip = min(deep + H + XH * lm("g_tip", 0.12), -30)  # the terminal stands 0.12 x-heights above the tail, clear of the bowl
    tail = rounded(
        (xt, tip, rt), (xt, deep, ro), (W, deep, ro), (W, XH, square(p, ro)), (W - V, XH, rt),
        (W - V, deep + H, ri), (xt + V, deep + H, ri), (xt + V, tip, rt),
    )
    return [tail] + bowl(p, 0, W, stem="right"), W, p.sides("g")


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
    ya, yl = XH * lm("k_ya", 0.563), XH * lm("k_yl", 0.513)  # where the arm's upper and the leg's lower edge leave the stem
    xt, xb = W * lm("k_xt", 0.748), W * lm("k_xb", 0.777)  # the arm's top-left and the leg's bottom-left
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
    # without the shoulder notch, the middle stem rises square between the arches;
    # with it, the arches meet over the middle stem in a small dip, as the n's shoulder steps
    middle = [] if STYLE.get("notch") else stem_top(p, W1 - p.V, 0)
    return stem_top(p, 0, 0) + middle + [arch(p, 0, W1, XH, on_stem=("left", "right")),
                                         arch(p, W1 - p.V, W, XH, on_stem=("left",))], W, p.sides("m")


@glyph("q", "q")
def g_q(p):
    W = p.w("q")
    stem = box(W - p.V, DSC, W, XH, p.rt, p.rt, square(p, p.ro), 0)
    return [stem] + bowl(p, 0, W, stem="right"), W, p.sides("q")


@glyph("s", "s")
def g_s(p):
    """Two bowls sharing a middle bar, each opening onto a flat terminal."""
    W = p.w("s")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    m0 = XH * lm("s_mid", 0.523) - H / 2  # bottom of the middle bar
    m1 = m0 + H
    t0, t1 = XH * lm("s_t0", 0.29), XH * lm("s_t1", 0.72)  # tops of the lower terminal, bottom of the upper
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
    top, foot = XH * lm("t_top", 1.273), XH * lm("t_foot", 0.436)
    c = rounded(
        (0, top, rt), (0, 0, ro), (W, 0, ro), (W, foot, rt), (W - V, foot, rt), (W - V, H, ri),
        (V, H, ri), (V, top, rt),
    )
    bar = box(0, XH - H, W * lm("t_bar", 0.932), XH, rt, rt, rt, rt)
    return [c, bar], W, p.sides("t")


@glyph("u", "u")
def g_u(p):
    """The n turned upside down: its square stem foot lands on the right."""
    contours, W, _ = g_n(p)
    return rotate180(contours, W / 2, XH / 2), W, p.sides("u")


def v_shape(p, x0, W, top=XH, bottom=0, foot=None, r_top=None):
    """Two diagonals meeting at the bottom on a flat foot (b wide, 0.85 of an arm by default).

    Every end is cut like the x's, flat and square to the line."""
    V, rt = p.V, p.rt
    r = rt if r_top is None else r_top
    t = V * 0.98
    cx = x0 + W / 2
    h = top - bottom
    hw = t
    for _ in range(4):  # the foot's width and the arms' slope depend on each other
        b = 0.85 * hw if foot is None else foot
        slope = (W / 2 - b / 2) / h
        hw = diag_hw(W / 2 - b / 2, h, t)
    y_in = top - (W / 2 - hw) / slope  # where the inner edges meet
    return rpoly(
        (x0, top, r), (cx - b / 2, bottom, rt), (cx + b / 2, bottom, rt), (x0 + W, top, r), (x0 + W - hw, top, rt),
        (cx, y_in, 0), (x0 + hw, top, rt),
    ), hw


@glyph("v", "v")
def g_v(p):
    W = p.w("v")
    return [v_shape(p, 0, W)[0]], W, p.sides("v")


def w_shape(p, W, top=XH):
    """Two v's sharing their middle arms, drawn as one outline, every end cut flat.

    The middle peak is flat at the top, cut like the terminals; laying two
    v's over each other left each one's rounded outer corner as a notch there."""
    V, rt = p.V, p.rt
    t = V * 0.98
    hw = V * 1.3
    for _ in range(6):  # each v's width and its arms' width depend on each other
        Wv = (W + hw) / 2
        b = 0.85 * hw
        slope = (Wv / 2 - b / 2) / top
        hw = diag_hw(Wv / 2 - b / 2, top, t)
    Wv = (W + hw) / 2
    c1, c2 = Wv / 2, W - Wv / 2
    y_in = top - (Wv / 2 - hw) / slope  # where each v's inner edges meet

    def cross(a, b, c, d):  # where line ab meets line cd
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = a, b, c, d
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        u = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return x1 + u * (x2 - x1), y1 + u * (y2 - y1)

    mx, my = cross((c1 + b / 2, 0), (Wv, top), (W - Wv, top), (c2 - b / 2, 0))  # under the middle peak
    return rpoly(
        (0, top, rt), (c1 - b / 2, 0, rt), (c1 + b / 2, 0, rt), (mx, my, 0), (c2 - b / 2, 0, rt), (c2 + b / 2, 0, rt),
        (W, top, rt), (W - hw, top, rt), (c2, y_in, 0), (Wv, top, rt), (W - Wv, top, rt), (c1, y_in, 0), (hw, top, rt),
    )


@glyph("w", "w")
def g_w(p):
    W = p.w("w")
    return [w_shape(p, W)], W, p.sides("w")


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
    top = box(0, XH - H, W, XH, rt, 0, rt, rt)  # sharp where the diagonal leaves, so its corner does not poke out past a soft one
    bottom = box(0, 0, W, H, rt, rt, rt, 0)
    diagonal = rpoly((W - hw, XH - H, 0), (W, XH - H, 0), (hw, H, 0), (0, H, 0))
    return [top, bottom, diagonal], W, p.sides("z")


# --- Figures --------------------------------------------------------------
# Lining figures at cap height, as wide as the bowls of the lowercase. Their
# landmark heights are fractions of FH, measured from the lockup's font.

FH = ASC


@glyph("zero", "0")
def g_zero(p):
    W = p.w("zero")
    return bowl(p, 0, W, top=FH), W, p.sides("zero")


@glyph("one", "1")
def g_one(p):
    """A stem on a full-width base, with a flag falling to the left."""
    W = p.w("one")
    V, H, rt = p.V, p.H, p.rt
    xs = W * lm("one_xs", 0.465) - (V - REGULAR_STEM) / 2  # the stem stays centred on the same line as it thickens
    drop = FH * lm("one_drop", 0.10)  # how far the flag falls across its length
    flag = rpoly((xs + 2, FH, 0), (0, FH - drop, rt), (0, FH - drop - H * 1.05, rt), (xs + 2, FH - H * 1.05, 0))
    stem = box(xs, 0, xs + V, FH, 0, 0, rt, 0 if STYLE["stem_tops"] == "square" else p.ro)  # the flag runs on from a sharp corner
    base = box(0, 0, W, H, rt, rt, rt, rt)
    return [stem, flag, base], W, p.sides("one")


@glyph("two", "2")
def g_two(p):
    W = p.w("two")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    m0 = FH * lm("two_bar", 0.446)  # bottom of the middle bar
    m1, t = m0 + H, FH * lm("two_t", 0.736)  # top of the middle bar; the hook's terminal
    c = rounded(
        (0, 0, rt), (W, 0, rt), (W, H, rt), (V, H, ri), (V, m0, ri), (W, m0, ro), (W, FH, ro), (0, FH, ro),
        (0, t, rt), (V, t, rt), (V, FH - H, ri), (W - V, FH - H, ri), (W - V, m1, ri), (0, m1, ro),
    )
    return [c], W, p.sides("two")


@glyph("three", "3")
def g_three(p):
    """Two bowls open to the left, stacked on a short middle bar.

    Each bowl rounds its own corner at the middle, so the right side pinches in
    there, as Michroma's 3 does; one straight side read as a block."""
    W = p.w("three")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    tb, tt = FH * lm("three_tb", 0.29), FH * lm("three_tt", 0.736)  # terminal heights
    m0 = FH * lm("three_mid", 0.518) - H / 2
    m1, xm = m0 + H, W * lm("three_xm", 0.405)  # the middle bar starts here
    rw_up, rw_lo = waist(p, FH - m0), waist(p, m1)
    upper = rpoly(
        (0, FH, ro), (0, tt, rt), (V, tt, rt), (V, FH - H, ri), (W - V, FH - H, ri), (W - V, m1, joint(p, ri)),
        (xm, m1, rt), (xm, m0, rt), (W, m0, rw_up), (W, FH, ro),
    )
    lower = rpoly(
        (0, 0, ro), (W, 0, ro), (W, m1, rw_lo), (xm, m1, rt), (xm, m0, rt), (W - V, m0, joint(p, ri)),
        (W - V, H, ri), (V, H, ri), (V, tb, rt), (0, tb, rt),
    )
    return [upper, lower], W, p.sides("three")


@glyph("four", "4")
def g_four(p):
    """One outline, as Michroma's: the diagonal's outer edge runs from the crossbar's
    top left corner to the top, where it meets the stem flush, so nothing steps out."""
    W = p.w("four")
    V, H, rt = p.V, p.H, p.rt
    xs = W * lm("four_xs", 0.751)  # the stem's left edge
    b0 = FH * lm("four_bar", 0.209)  # bottom of the crossbar
    b1 = b0 + H
    ox = xs - 0.34 * V  # the diagonal's outer edge at the top
    hw = diag_hw(ox, FH - b1, V * 0.98)  # its horizontal width
    yin = b1 + (xs - hw) * (FH - b1) / ox  # where its inner edge meets the stem
    outer = rpoly(
        (xs, 0, rt), (xs + V, 0, rt), (xs + V, b0, 0), (W, b0, rt), (W, b1, rt), (xs + V, b1, 0),
        (xs + V, FH, rt), (ox, FH, rt), (0, b1, rt), (0, b0, rt), (xs, b0, 0),
    )
    counter = rounded((hw, b1, 0), (xs, yin, 0), (xs, b1, 0))
    return [outer, counter], W, p.sides("four")


@glyph("five", "5")
def g_five(p):
    W = p.w("five")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    bt, tb = FH * lm("five_bowl", 0.636), FH * lm("five_t", 0.29)  # top of the bowl; its terminal
    c = rounded(
        (0, tb, rt), (0, 0, ro), (W, 0, ro), (W, bt, ro), (V, bt, ri), (V, FH - H, ri), (W, FH - H, rt),
        (W, FH, rt), (0, FH, rt), (0, bt - H, rt), (W - V, bt - H, ri), (W - V, H, ri), (V, H, ri), (V, tb, rt),
    )
    return [c], W, p.sides("five")


@glyph("six", "6")
def g_six(p):
    """A closed lower bowl whose left side runs up into a hook."""
    W = p.w("six")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    bt, t = FH * lm("six_bowl", 0.57), FH * lm("six_t", 0.736)
    c = rounded(
        (0, 0, ro), (W, 0, ro), (W, bt, ro), (V, bt, tee(p, ri)), (V, FH - H, ri), (W - V, FH - H, ri),
        (W - V, t, rt), (W, t, rt), (W, FH, ro), (0, FH, ro),
    )
    return [c, hole(V, H, W - V, bt - H, ri, top=tee(p, ri))], W, p.sides("six")  # three strokes meet here


@glyph("seven", "7")
def g_seven(p):
    """One outline, as Michroma's: the diagonal's outer edge leaves the bar at its
    lower right corner, so the bar does not stick out past it."""
    W = p.w("seven")
    V, H, rt = p.V, p.H, p.rt
    xb = W * lm("seven_xb", 0.186)  # where the diagonal lands
    h = FH - H
    hw = V * 1.2
    for _ in range(6):
        hw = diag_hw(W - xb - hw, h, V * 0.98)
    xi = xb + (W - xb - hw)  # the inner edge under the bar, parallel to the outer
    return [rpoly(
        (0, h, rt), (xi, h, 0), (xb, 0, rt), (xb + hw, 0, rt), (W, h, 0), (W, FH, rt), (0, FH, rt),
    )], W, p.sides("seven")


@glyph("eight", "8")
def g_eight(p):
    """Two bowls stacked on the middle bar, each with its own corners, so both
    sides pinch in at the middle, as Michroma's 8 does."""
    W = p.w("eight")
    V, H, ro, ri = p.V, p.H, p.ro, p.ri
    m0 = FH * lm("eight_mid", 0.518) - H / 2
    rw_up, rw_lo = waist(p, FH - m0), waist(p, m0 + H)
    upper = box(0, m0, W, FH, rw_up, rw_up, ro, ro)
    lower = box(0, 0, W, m0 + H, ro, ro, rw_lo, rw_lo)
    return [upper, lower, hole(V, H, W - V, m0, ri, top=joint(p, ri)), hole(V, m0 + H, W - V, FH - H, ri, bottom=joint(p, ri))], W, p.sides("eight")


@glyph("nine", "9")
def g_nine(p):
    """The six turned upside down."""
    W = p.w("nine")
    contours = g_six(p)[0]
    return rotate180(contours, p.w("six") / 2, FH / 2), W, p.sides("nine")


# --- Punctuation and symbols ---------------------------------------------

def dot_at(p, x0, y0):
    return box(x0, y0, x0 + p.V, y0 + p.V, p.rt, p.rt, p.rt, p.rt)


def comma_at(p, x0, top, tail=None):
    """A wedge leaning down to the left: a stem wide at the top, two thirds of that at the tip."""
    V, rt = p.V, p.rt
    tail = V * 2.0 if tail is None else tail  # from top to tip
    return rpoly((x0 + V / 3, top, rt), (x0 + V / 3 + V, top, rt), (x0 + V * 0.67, top - tail, rt), (x0, top - tail, rt))


@glyph("period", ".")
def g_period(p):
    return [dot_at(p, 0, 0)], p.V, p.sides("period")


@glyph("comma", ",")
def g_comma(p):
    return [comma_at(p, 0, p.V * 0.67)], p.V * 4 / 3, p.sides("comma")


@glyph("colon", ":")
def g_colon(p):
    """Two dots floating on the x-height, centred at a quarter and three quarters."""
    V = p.V
    return [dot_at(p, 0, XH * lm("colon_lo", 0.249) - V / 2), dot_at(p, 0, XH * lm("colon_hi", 0.75) - V / 2)], V, p.sides("colon")


@glyph("semicolon", ";")
def g_semicolon(p):
    V = p.V
    return [comma_at(p, 0, V * 0.67), dot_at(p, V / 3, XH * lm("colon_hi", 0.75) - V / 2)], V * 4 / 3, p.sides("semicolon")


@glyph("exclam", "!")
def g_exclam(p):
    V, rt = p.V, p.rt
    return [box(0, V * 1.7, V, FH, rt, rt, rt, rt), dot_at(p, 0, 0)], V, p.sides("exclam")


@glyph("question", "?")
def g_question(p):
    """The two's hook, whose middle bar drops into a short stem over a dot."""
    W = p.w("question")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    xs = W * lm("q_xs", 0.323) - (V - REGULAR_STEM) / 2
    m0, t = FH * lm("q_bar", 0.479), FH * lm("q_t", 0.73)  # bar bottom, terminal
    sb = V * 1.68  # the stem stops 0.68 of a stroke above the dot, at any weight
    m1 = m0 + H
    c = rounded(
        (0, t, rt), (V, t, rt), (V, FH - H, ri), (W - V, FH - H, ri), (W - V, m1, ri), (xs, m1, ro),
        (xs, sb, rt), (xs + V, sb, rt), (xs + V, m0, ri), (W, m0, ro), (W, FH, ro), (0, FH, ro),
    )
    return [c, dot_at(p, xs, 0)], W, p.sides("question")


def dash(p, name, width=None):
    W = width if width is not None else p.w(name)
    c = XH * lm("dash", 0.514)  # the dashes sit on the middle of the x-height
    return [box(0, c - p.H / 2, W, c + p.H / 2, p.rt, p.rt, p.rt, p.rt)], W, p.sides(name)


@glyph("hyphen", "-")
def g_hyphen(p):
    return dash(p, "hyphen")


@glyph("endash", "\u2013")
def g_endash(p):
    return dash(p, "endash")


@glyph("emdash", "\u2014")
def g_emdash(p):
    return dash(p, "emdash")


@glyph("underscore", "_")
def g_underscore(p):
    W = p.w("underscore")
    return [box(0, -p.H, W, 0, p.rt, p.rt, p.rt, p.rt)], W, p.sides("underscore")


@glyph("quotesingle", "'")
def g_quotesingle(p):
    V, rt = p.V, p.rt
    return [box(0, XH, V, FH, rt, rt, rt, rt)], V, p.sides("quotesingle")


@glyph("quotedbl", '"')
def g_quotedbl(p):
    V, rt = p.V, p.rt
    gap = V * 0.68
    return [box(0, XH, V, FH, rt, rt, rt, rt), box(V + gap, XH, 2 * V + gap, FH, rt, rt, rt, rt)], 2 * V + gap, p.sides("quotedbl")


def quote(p, n, turned):
    """One or two commas hung from cap height; turned for the opening quotes, so their wide end is low."""
    V = p.V
    w1, gap = V * 4 / 3, V * 0.5
    marks = [comma_at(p, i * (w1 + gap), FH) for i in range(n)]
    W = n * w1 + (n - 1) * gap
    if turned:
        marks = rotate180(marks, W / 2, FH - V)
    return marks, W


@glyph("quoteright", "\u2019")
def g_quoteright(p):
    m, W = quote(p, 1, False)
    return m, W, p.sides("quoteright")


@glyph("quoteleft", "\u2018")
def g_quoteleft(p):
    m, W = quote(p, 1, True)
    return m, W, p.sides("quoteleft")


@glyph("quotedblright", "\u201d")
def g_quotedblright(p):
    m, W = quote(p, 2, False)
    return m, W, p.sides("quotedblright")


@glyph("quotedblleft", "\u201c")
def g_quotedblleft(p):
    m, W = quote(p, 2, True)
    return m, W, p.sides("quotedblleft")


def bracket(p, W, r_out, r_in):
    """An opening bracket: a stroke with arms at top and bottom."""
    V, H, rt = p.V, p.H, p.rt
    bot, top = DSC * 0.61, FH + 34  # below the baseline and above cap height, as in the wordmark's font
    return rounded(
        (0, bot, r_out), (W, bot, rt), (W, bot + H, rt), (V, bot + H, r_in), (V, top - H, r_in),
        (W, top - H, rt), (W, top, rt), (0, top, r_out),
    )


@glyph("parenleft", "(")
def g_parenleft(p):
    W = p.w("parenleft")
    return [bracket(p, W, p.ro * 1.6, p.ri * 1.6)], W, p.sides("parenleft")


@glyph("parenright", ")")
def g_parenright(p):
    W = p.w("parenright")
    return mirror_x([bracket(p, W, p.ro * 1.6, p.ri * 1.6)], W), W, p.sides("parenright")


@glyph("bracketleft", "[")
def g_bracketleft(p):
    W = p.w("bracketleft")
    return [bracket(p, W, p.rt, p.rt)], W, p.sides("bracketleft")


@glyph("bracketright", "]")
def g_bracketright(p):
    W = p.w("bracketright")
    return mirror_x([bracket(p, W, p.rt, p.rt)], W), W, p.sides("bracketright")


@glyph("slash", "/")
def g_slash(p):
    W = p.w("slash")
    hw = diag_hw(W, FH, p.V * 0.98)
    return [rpoly((0, 0, p.rt), (hw, 0, p.rt), (W, FH, p.rt), (W - hw, FH, p.rt))], W, p.sides("slash")


@glyph("plus", "+")
def g_plus(p):
    W = p.w("plus")
    V, H, rt = p.V, p.H, p.rt
    c = XH * lm("plus", 0.62)  # centred a little above the middle of the x-height, as the wordmark's font has it
    return [box(W / 2 - V / 2, c - W / 2, W / 2 + V / 2, c + W / 2, rt, rt, rt, rt),
            box(0, c - H / 2, W, c + H / 2, rt, rt, rt, rt)], W, p.sides("plus")


@glyph("equal", "=")
def g_equal(p):
    W = p.w("equal")
    H, rt = p.H, p.rt
    c, gap = XH * lm("equal", 0.657), XH * lm("equal_gap", 0.236)  # centre, and the space between the bars
    return [box(0, c - gap / 2 - H, W, c - gap / 2, rt, rt, rt, rt),
            box(0, c + gap / 2, W, c + gap / 2 + H, rt, rt, rt, rt)], W, p.sides("equal")


@glyph("asterisk", "*")
def g_asterisk(p):
    """Three bars crossing at sixty degrees, hung from cap height."""
    W = p.w("asterisk")
    t = p.V * 0.9
    cx, cy = W / 2, FH - W / 2
    bar = [rect(cx - t / 2, cy - W / 2, cx + t / 2, cy + W / 2)]
    return bar + rotate(bar, 60, cx, cy) + rotate(bar, -60, cx, cy), W, p.sides("asterisk")


@glyph("numbersign", "#")
def g_numbersign(p):
    W = p.w("numbersign")
    V, H, rt = p.V, p.H, p.rt
    x1, x2 = W * 0.27, W * 0.73 - V  # the two uprights
    y1, y2 = FH * 0.30, FH * 0.70 - H  # the two crossbars
    up = [box(x, 0, x + V, FH, rt, rt, rt, rt) for x in (x1, x2)]
    across = [box(0, y, W, y + H, rt, rt, rt, rt) for y in (y1, y2)]
    return up + across, W, p.sides("numbersign")


# --- Capitals -------------------------------------------------------------
# Cap height is the ascender. Widths, spacing and landmark heights are
# measured from the lockup's font, as for the lowercase.

CH = ASC


def capbowl(p, x0, x1, y0, y1, left="round", bar=None):
    """A bowl for B, D, P and R: square on the left, where it meets the stem.
    bar ("top" or "bottom") is the side that is a shared middle bar, whose counter
    corners are capped like the e's (joint())."""
    ro, ri, rt = p.ro, p.ri, p.rt
    l = ro if left == "round" else rt
    return [box(x0, y0, x1, y1, l, ro, ro, l),
            hole(x0 + p.V, y0 + p.H, x1 - p.V, y1 - p.H, ri,
                 top=tee(p, ri) if bar == "top" else None, bottom=tee(p, ri) if bar == "bottom" else None)]


def stem(p, x0, y0=0, y1=CH):
    return box(x0, y0, x0 + p.V, y1, p.rt, p.rt, p.rt, p.rt)


def bar(p, x0, x1, y0):
    return box(x0, y0, x1, y0 + p.H, p.rt, p.rt, p.rt, p.rt)


def stroke(p, a, b, t):
    """A straight stroke of thickness t from a to b, cut square at both ends."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / L * t / 2, dx / L * t / 2
    return rpoly((a[0] + nx, a[1] + ny, p.rt), (b[0] + nx, b[1] + ny, p.rt), (b[0] - nx, b[1] - ny, p.rt),
                 (a[0] - nx, a[1] - ny, p.rt))


@glyph("A", "A")
def g_A(p):
    """The V turned over, with a flat apex, and a crossbar low in the counter."""
    W = p.w("A")
    vee, hw = v_shape(p, 0, W, top=CH, r_top=p.rt)
    legs = rotate180([vee], W / 2, CH / 2)
    apex = (W - 0.85 * hw) / 2  # the outer edges' run, from foot to apex
    y0 = CH * lm("A_bar", 0.229)
    x = (y0 + p.H) / CH * apex + 2  # inside both legs over the whole bar
    return legs + [bar(p, x, W - x, y0)], W, p.sides("A")


@glyph("B", "B")
def g_B(p):
    W = p.w("B")
    m0 = CH * lm("B_mid", 0.532) - p.H / 2  # bottom of the middle bar
    return [stem(p, 0)] + capbowl(p, 0, W, 0, m0 + p.H, "square", bar="top") + capbowl(p, 0, W * lm("B_upper", 0.965), m0, CH, "square", bar="bottom"), W, p.sides("B")


def c_shape(p, W, h, t0, t1):
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    return rounded(
        (0, 0, ro), (W, 0, ro), (W, t0, rt), (W - V, t0, rt), (W - V, H, ri), (V, H, ri),
        (V, h - H, ri), (W - V, h - H, ri), (W - V, t1, rt), (W, t1, rt), (W, h, ro), (0, h, ro),
    )


@glyph("C", "C")
def g_C(p):
    W = p.w("C")
    return [c_shape(p, W, CH, CH * lm("C_t0", 0.337), CH * lm("C_t1", 0.656))], W, p.sides("C")


@glyph("D", "D")
def g_D(p):
    W = p.w("D")
    return [stem(p, 0)] + capbowl(p, 0, W, 0, CH, "square"), W, p.sides("D")


@glyph("E", "E")
def g_E(p):
    W = p.w("E")
    m0 = CH * lm("EFH_mid", 0.510) - p.H / 2
    return [stem(p, 0), bar(p, 0, W * lm("E_top", 0.981), CH - p.H), bar(p, 0, W * lm("E_mid", 0.945), m0), bar(p, 0, W, 0)], W, p.sides("E")


@glyph("F", "F")
def g_F(p):
    W = p.w("F")
    m0 = CH * lm("EFH_mid", 0.510) - p.H / 2
    return [stem(p, 0), bar(p, 0, W, CH - p.H), bar(p, 0, W * lm("F_mid", 0.96), m0)], W, p.sides("F")


@glyph("G", "G")
def g_G(p):
    """The C, whose lower terminal turns into a bar reaching back into the counter."""
    W = p.w("G")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    gt, xb, t1 = CH * lm("G_bar", 0.526), W * lm("G_xb", 0.508), CH * lm("G_t1", 0.70)
    c = rounded(
        (0, 0, ro), (W, 0, ro), (W, gt, rt), (xb, gt, rt), (xb, gt - H, rt), (W - V, gt - H, ri),
        (W - V, H, ri), (V, H, ri), (V, CH - H, ri), (W - V, CH - H, ri), (W - V, t1, rt), (W, t1, rt),
        (W, CH, ro), (0, CH, ro),
    )
    return [c], W, p.sides("G")


@glyph("H", "H")
def g_H(p):
    W = p.w("H")
    return [stem(p, 0), stem(p, W - p.V), bar(p, 0, W, CH * lm("EFH_mid", 0.510) - p.H / 2)], W, p.sides("H")


@glyph("I", "I")
def g_I(p):
    return [stem(p, 0)], p.V, p.sides("I")


@glyph("J", "J")
def g_J(p):
    """A stem that turns left at the baseline into a short upturned terminal."""
    W = p.w("J")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    jt = CH * lm("J_t", 0.375)
    c = rounded((0, jt, rt), (0, 0, ro), (W, 0, ro), (W, CH, rt), (W - V, CH, rt), (W - V, H, ri), (V, H, ri), (V, jt, rt))
    return [c], W, p.sides("J")


@glyph("K", "K")
def g_K(p):
    """A stem with a short stub, from which an arm rises and a leg falls."""
    W = p.w("K")
    V, H, rt = p.V, p.H, p.rt
    t = V * 0.98
    m0 = CH * lm("EFH_mid", 0.510) - H / 2  # the stub, level with the H's bar
    m1, xj = m0 + H, W * lm("K_xj", 0.253)  # its top; where it ends
    xa, xl = W * lm("K_xa", 0.818), W * lm("K_xl", 0.836)  # the arm's top-left, the leg's bottom-left
    ha = diag_hw(xa - xj, CH - m1, t)
    hl = diag_hw(xl - xj, m0, t)

    def line(p0, p1):  # x = a + b*y
        b = (p1[0] - p0[0]) / (p1[1] - p0[1])
        return (p0[0] - b * p0[1], b)

    def cross(l1, l2):
        y = (l2[0] - l1[0]) / (l1[1] - l2[1])
        return (l1[0] + l1[1] * y, y)

    crotch = cross(line((xj + ha, m1), (xa + ha, CH)), line((xj + hl, m0), (xl + hl, 0)))
    diagonals = rounded(
        (V - 2, m0, 0), (xj, m0, 0), (xl, 0, rt), (xl + hl, 0, rt), crotch + (0,), (xa + ha, CH, rt), (xa, CH, rt),
        (xj, m1, 0), (V - 2, m1, 0),
    )
    return [stem(p, 0), diagonals], W, p.sides("K")


@glyph("L", "L")
def g_L(p):
    W = p.w("L")
    return [stem(p, 0), bar(p, 0, W, 0)], W, p.sides("L")


@glyph("M", "M")
def g_M(p):
    """Two stems and a V between them that dips almost to the baseline."""
    W = p.w("M")
    vee = v_shape(p, 0, W, top=CH, bottom=CH * lm("M_dip", 0.066), r_top=p.rt)[0]
    return [stem(p, 0), stem(p, W - p.V), vee], W, p.sides("M")


@glyph("N", "N")
def g_N(p):
    W = p.w("N")
    hw = diag_hw(W, CH, p.V * 0.98)
    diagonal = rpoly((0, CH, p.rt), (hw, CH, p.rt), (W, 0, p.rt), (W - hw, 0, p.rt))
    return [stem(p, 0), stem(p, W - p.V), diagonal], W, p.sides("N")


@glyph("O", "O")
def g_O(p):
    W = p.w("O")
    return bowl(p, 0, W, top=CH), W, p.sides("O")


@glyph("P", "P")
def g_P(p):
    W = p.w("P")
    return [stem(p, 0)] + capbowl(p, 0, W, CH * lm("P_bowl", 0.386), CH, "square"), W, p.sides("P")


@glyph("Q", "Q")
def g_Q(p):
    """The O, with a tail crossing its lower right."""
    W = p.w("Q")
    tail = stroke(p, (W * 0.52, CH * 0.37), (W * 1.04, -CH * 0.10), p.H * 0.98)
    return bowl(p, 0, W, top=CH) + [tail], W, p.sides("Q")


@glyph("R", "R")
def g_R(p):
    W = p.w("R")
    pb = CH * lm("R_bowl", 0.404)  # bottom of the bowl
    x0, x1 = W * lm("R_x0", 0.672), W * lm("R_x1", 0.975)  # the leg leaves the bowl here and lands here
    hw = diag_hw(x1 - x0, pb, p.V * 0.98)
    leg = rpoly((x0, pb + p.H / 2, 0), (x0 + hw, pb + p.H / 2, 0), (x1, 0, p.rt), (x1 - hw, 0, p.rt))
    return [stem(p, 0)] + capbowl(p, 0, W, pb, CH, "square") + [leg], W, p.sides("R")


@glyph("S", "S")
def g_S(p):
    W = p.w("S")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    m0 = CH * lm("S_mid", 0.515) - H / 2
    m1 = m0 + H
    t0, t1 = CH * lm("S_t0", 0.33), CH * lm("S_t1", 0.70)
    c = rounded(
        (0, t0, rt), (0, 0, ro), (W, 0, ro), (W, m1, ro), (V, m1, ri), (V, CH - H, ri),
        (W - V, CH - H, ri), (W - V, t1, rt), (W, t1, rt), (W, CH, ro), (0, CH, ro), (0, m0, ro),
        (W - V, m0, ri), (W - V, H, ri), (V, H, ri), (V, t0, rt),
    )
    return [c], W, p.sides("S")


@glyph("T", "T")
def g_T(p):
    W = p.w("T")
    return [bar(p, 0, W, CH - p.H), stem(p, W / 2 - p.V / 2)], W, p.sides("T")


@glyph("U", "U")
def g_U(p):
    W = p.w("U")
    return rotate180([arch(p, 0, W, CH)], W / 2, CH / 2), W, p.sides("U")


@glyph("V", "V")
def g_V(p):
    W = p.w("V")
    return [v_shape(p, 0, W, top=CH, r_top=p.rt)[0]], W, p.sides("V")


@glyph("W", "W")
def g_W(p):
    W = p.w("W")
    return [w_shape(p, W, top=CH)], W, p.sides("W")


@glyph("X", "X")
def g_X(p):
    W = p.w("X")
    rt = p.rt
    hw = diag_hw(W, CH, p.V * 0.98)
    return [rpoly((0, CH, rt), (hw, CH, rt), (W, 0, rt), (W - hw, 0, rt)),
            rpoly((W - hw, CH, rt), (W, CH, rt), (hw, 0, rt), (0, 0, rt))], W, p.sides("X")


@glyph("Y", "Y")
def g_Y(p):
    """A V whose foot is a stem's width, standing on a stem."""
    W = p.w("Y")
    yj = CH * lm("Y_join", 0.416)
    vee = v_shape(p, 0, W, top=CH, bottom=yj, foot=p.V, r_top=p.rt)[0]
    return [vee, stem(p, W / 2 - p.V / 2, 0, yj + p.H)], W, p.sides("Y")


@glyph("Z", "Z")
def g_Z(p):
    W = p.w("Z")
    H = p.H
    xr = W * lm("Z_r", 0.983)  # the top bar's right end: the diagonal starts under it, not past it
    hw = diag_hw(xr, CH - 2 * H, p.V * 0.98)
    diagonal = rpoly((xr - hw, CH - H, 0), (xr, CH - H, 0), (hw, H, 0), (0, H, 0))
    top = box(W * lm("Z_l", 0.036), CH - H, xr, CH, p.rt, 0, p.rt, p.rt)  # sharp where the diagonal leaves
    bottom = box(0, 0, W, H, p.rt, p.rt, p.rt, 0)
    return [top, bottom, diagonal], W, p.sides("Z")


# --- & @ % ----------------------------------------------------------------

@glyph("ampersand", "&")
def g_ampersand(p):
    """Michroma's construction, in Hypher's corners: the lower bowl's left side rises
    and runs on as the diagonal, out past the bowl to a cut at the right; the upper
    loop's stem comes down into the same diagonal, and the loop is open at the
    lower right like a 3's top, ending in a terminal. The lower bowl's right side
    rises through the diagonal to its own terminal."""
    W = p.w("ampersand")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    t = V * 0.98
    top0 = FH * 0.88  # the diagonal's upper edge, carried back to x = 0
    end = FH * 0.03  # its lower edge at the cut
    d0 = t * 1.12  # its height, measured upright (it runs at about 1 in 2)
    for _ in range(4):
        sl = (top0 - d0 - end) / W  # fall per unit across
        d0 = t * (1 + sl * sl) ** 0.5
    up = lambda x: top0 - sl * x  # noqa: E731  upper edge
    lo = lambda x: top0 - d0 - sl * x  # noqa: E731  lower edge
    wb, tr = W * 0.87, FH * 0.50  # the lower bowl's right side and terminal
    xr, tt = W * 0.82, FH * 0.68  # the upper loop's right side and terminal
    x1 = 0.6 * V  # the upper stem's outer edge: set into the lower bowl's side, so the two do not stand side by side as one heavy block at Bold
    x2 = x1 + V  # its inner edge
    lower = rpoly(
        (0, 0, ro), (wb, 0, ro), (wb, tr, rt), (wb - V, tr, rt), (wb - V, H, ri), (V, H, ri),
        (V, lo(V), joint(p, ri)), (W, lo(W), rt), (W, up(W), rt), (x2, up(x2), 0), (0, up(x2), ro),
    )
    j = 0.9 * V  # room along the diagonal for the fillet under the upper stem
    upper = rpoly(
        (x1, lo(V) + 0.5 * (up(x2) - lo(V)), 0), (x2 + j, up(x2 + j) - d0 / 2, 0), (x2 + j, up(x2 + j), 0),
        (x2, up(x2), 0.8 * V), (x2, FH - H, ri), (xr - V, FH - H, ri), (xr - V, tt, rt), (xr, tt, rt),
        (xr, FH, ro), (x1, FH, ro),
    )
    return [lower, upper], W, p.sides("ampersand")


@glyph("at", "@")
def g_at(p):
    """A small a inside a larger bowl that opens at the lower right."""
    W = p.w("at")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    b, t = XH * lm("at_b", -0.195), XH * lm("at_t", 1.195)  # the outer bowl reaches below the baseline, as the wordmark's font has it
    xi0, xi1 = W * 0.26, W * 0.74  # the inner a
    yi0, yi1 = b + H + (t - b) * 0.12, t - H - (t - b) * 0.12
    outer = rounded(
        (0, b, ro), (xi1, b, rt), (xi1, b + H, rt), (V, b + H, ri), (V, t - H, ri), (W - V, t - H, ri),
        (W - V, yi0, rt), (W, yi0, rt), (W, t, ro), (0, t, ro),
    )
    # the inner bowl is square at the top right, where the stem rises through it
    inner = [box(xi0, yi0, xi1, yi1, ro * 0.6, rt, rt, ro * 0.6), hole(xi0 + V, yi0 + H, xi1 - V, yi1 - H, ri * 0.6),
             box(xi1 - V, b, xi1, yi1, rt, rt, rt, rt)]
    return [outer] + inner, W, p.sides("at")


@glyph("percent", "%")
def g_percent(p):
    """Two small rings either side of a slash."""
    W = p.w("percent")
    V, H, ri = p.V, p.H, p.ri
    rw, rh = W * 0.38, CH * 0.44  # each ring, big enough that Bold keeps a counter
    r = min(p.ro, rh / 2)

    def ring(x0, y0):
        return [box(x0, y0, x0 + rw, y0 + rh, r, r, r, r), hole(x0 + V, y0 + H, x0 + rw - V, y0 + rh - H, min(ri, r))]

    hw = diag_hw(W * 0.62, CH, V * 0.98)
    slash = rpoly((W * 0.19, 0, p.rt), (W * 0.19 + hw, 0, p.rt), (W * 0.81, CH, p.rt), (W * 0.81 - hw, CH, p.rt))
    return ring(0, CH - rh) + ring(W - rw, 0) + [slash], W, p.sides("percent")


# --- Accents --------------------------------------------------------------
# Marks are drawn once, centred on x = 0 with their bottom at y = 0, then
# hung over a base letter: above the x-height for lowercase, above cap height
# for capitals.

@glyph("dotlessi", "\u0131")
def g_dotlessi(p):
    return [box(0, 0, p.V, XH, p.rt, p.rt, p.rt, p.rt)], p.V, p.sides("i")


def mark(p, kind, cap=False):
    """(contours, height) for one mark."""
    V, H, rt = p.V, p.H, p.rt
    s = 0.9 if cap else 1.0  # marks on capitals sit lower and a touch smaller
    mh = V * 0.9 + 73  # a mark's height: 1.7 stems at Regular, growing more slowly than the stroke so Bold's stay in the line
    if kind in ("acute", "grave"):
        w, h = V * 1.9 * s, mh * s
        c = rpoly((-w / 2, 0, rt), (-w / 2 + V * 1.1, 0, rt), (w / 2, h, rt), (w / 2 - V * 1.1, h, rt))
        return ([c] if kind == "acute" else mirror_x([c], 0)), h
    if kind == "circumflex":
        w, h = (V * 2.2 + 184) * s, mh * s
        vee = v_shape(p, -w / 2, w, top=h, foot=V * 1.2, r_top=rt)[0]
        return rotate180([vee], 0, h / 2), h
    if kind == "dieresis":
        g = V * 0.9
        return [dot_at(p, -g / 2 - V, 0), dot_at(p, g / 2, 0)], V
    if kind == "ring":
        w = (V * 1.6 + 130) * s  # grows less than the stroke, so Bold's ring stays in proportion
        r = min(p.ri, w / 3)
        return [box(-w / 2, 0, w / 2, w * 0.8, r, r, r, r), hole(-w / 2 + V * 0.8, H * 0.8, w / 2 - V * 0.8, w * 0.8 - H * 0.8, r / 2)], w * 0.8
    if kind == "tilde":
        # A wave: low on the left, high on the right, the bends rounded so it reads as one
        # stroke and not as a slash between two bars.
        w, d = V * 4.4 * s, max(V * 1.1 * s, H * 1.3)
        a, b = -w / 2 + w * 0.30, -w / 2 + w * 0.70
        rr = H * 1.4
        c = rounded((-w / 2, 0, rt), (a, 0, rr), (b, d, rr), (w / 2, d, rt), (w / 2, d + H, rt), (b, d + H, rr),
                    (a, H, rr), (-w / 2, H, rt))
        return [c], d + H
    if kind == "cedilla":  # a small hook hanging below the baseline from y = 0, like the j's tail
        h, xl = XH * 0.30 + H * 0.6, -V * 1.7  # about as deep at every weight
        c = rounded((xl, -h + H, rt), (xl, -h, rt), (V / 2, -h, p.ro * 0.4), (V / 2, rt + 2, 0), (-V / 2, rt + 2, 0),
                    (-V / 2, -h + H, p.ri * 0.4))
        return [c], 0
    if kind == "macron":
        w = V * 3.6 * s
        return [box(-w / 2, 0, w / 2, H, rt, rt, rt, rt)], H
    if kind == "breve":  # a small cup
        w, h = V * 3.8 * s, V * 1.4 * s
        v, hh = V * 0.85, H * 0.8
        r = min(p.ro * 0.5, h * 0.8)
        cup = rounded((-w / 2, 0, r), (w / 2, 0, r), (w / 2, h, rt), (w / 2 - v, h, rt), (w / 2 - v, hh, r * 0.5),
                      (-w / 2 + v, hh, r * 0.5), (-w / 2 + v, h, rt), (-w / 2, h, rt))
        return [cup], h
    if kind == "dotaccent":
        return [dot_at(p, -V / 2, 0)], V
    if kind == "caron":
        w, h = (V * 2.2 + 184) * s, mh * s
        return [v_shape(p, -w / 2, w, top=h, foot=V * 1.2, r_top=rt)[0]], h
    if kind == "hungarumlaut":
        a, h = mark(p, "acute", cap)
        off = V * 1.15
        return translate(a, -off) + translate(a, off), h
    if kind == "ogonek":  # the cedilla's hook turned to hang from a letter's right foot, its tail to the right
        h, xl = XH * 0.30 + H * 0.6, -V * 1.3
        c = rounded((xl, -h + H, rt), (xl, -h, rt), (V / 2, -h, p.ro * 0.4), (V / 2, rt + 2, 0), (-V / 2, rt + 2, 0),
                    (-V / 2, -h + H, p.ri * 0.4))  # its top tucks just past the letter's soft corner, square, so the two run on as one
        return mirror_x([c], 0), 0
    if kind == "commaaccent":  # a comma hung below the baseline
        return [comma_at(p, -V * 2 / 3, -H * 0.5, tail=V * 0.9 + 100)], 0  # shorter than a comma, so Bold does not hang deep
    if kind == "commaturned":  # a comma turned over, above (the ģ's)
        return rotate180([comma_at(p, -V * 2 / 3, V * 2)], 0, V), V * 2
    raise ValueError(kind)


ACCENTS = {  # base: [(char, mark), ...]
    "a": [("à", "grave"), ("á", "acute"), ("â", "circumflex"), ("ã", "tilde"), ("ä", "dieresis"), ("å", "ring")],
    "e": [("è", "grave"), ("é", "acute"), ("ê", "circumflex"), ("ë", "dieresis")],
    "dotlessi": [("ì", "grave"), ("í", "acute"), ("î", "circumflex"), ("ï", "dieresis")],
    "o": [("ò", "grave"), ("ó", "acute"), ("ô", "circumflex"), ("õ", "tilde"), ("ö", "dieresis")],
    "u": [("ù", "grave"), ("ú", "acute"), ("û", "circumflex"), ("ü", "dieresis")],
    "n": [("ñ", "tilde")], "y": [("ý", "acute"), ("ÿ", "dieresis")], "c": [("ç", "cedilla")],
    "A": [("À", "grave"), ("Á", "acute"), ("Â", "circumflex"), ("Ã", "tilde"), ("Ä", "dieresis"), ("Å", "ring")],
    "E": [("È", "grave"), ("É", "acute"), ("Ê", "circumflex"), ("Ë", "dieresis")],
    "I": [("Ì", "grave"), ("Í", "acute"), ("Î", "circumflex"), ("Ï", "dieresis")],
    "O": [("Ò", "grave"), ("Ó", "acute"), ("Ô", "circumflex"), ("Õ", "tilde"), ("Ö", "dieresis")],
    "U": [("Ù", "grave"), ("Ú", "acute"), ("Û", "circumflex"), ("Ü", "dieresis")],
    "N": [("Ñ", "tilde")], "Y": [("Ý", "acute")], "C": [("Ç", "cedilla")],
}
BASE = {}  # accented glyph name -> base glyph name, for kerning


BELOW = ("cedilla", "ogonek", "commaaccent")
OGONEK_AT = {"a": lambda p, W: W - p.V / 2, "A": lambda p, W: W - p.V * 0.75, "e": lambda p, W: W * 0.62,
             "E": lambda p, W: W * 0.8, "i": lambda p, W: p.V / 2, "dotlessi": lambda p, W: p.V / 2, "I": lambda p, W: p.V / 2,
             "u": lambda p, W: W - p.V / 2, "U": lambda p, W: W * 0.72}


def accented(base, kind):
    def fn(p):
        ch = GLYPHS[base][0]  # looked up when drawn: some bases (ǯ's, ǿ's) are defined further down
        cap = (ch or base)[0].isupper()  # by the character where there is one: uni01B7 is a capital
        contours, W, sides = GLYPHS[base][1](p)
        if kind == "caronv":  # ď ľ Ľ ť: the caron as a comma beside the stem's top
            x0, top = {"d": (W + p.V * 0.35, ASC), "l": (p.V * 1.35, ASC), "L": (p.V * 1.4, CH),
                       "t": (p.V * 1.35, XH * lm("t_top", 1.273))}[base]
            return contours + [comma_at(p, x0, top)], max(W, x0 + p.V * 4 / 3), sides
        m, h = mark(p, kind, cap)
        if kind in BELOW:
            y = 0
            if kind == "cedilla" and base in ("t", "T"):  # under a stem it hangs free, or the stem reads as running on into a hook
                y = -(p.rt + 2) - p.H * 0.45
        elif base in ("l", "h", "k"):  # over the ascender
            y = ASC + XH * 0.13
        else:
            y = (CH + CH * 0.06) if cap else (XH + XH * 0.13)
            if kind == "ring":  # a closed ring reads as touching sooner than an open mark
                y += p.V * 0.4
        cx = W / 2
        if kind == "ogonek":
            cx = OGONEK_AT[base](p, W)
        elif base == "L" and kind not in BELOW:
            cx = W * 0.3  # over the stem side
        elif base in ("r", "R") and kind == "commaaccent":
            cx = p.V / 2
        return contours + translate(m, cx, y), W, sides
    return fn


# Google Fonts Latin Core: the rest of Western and Central Europe.
for _base, _more in {
    "a": [("ā", "macron"), ("ă", "breve"), ("ą", "ogonek")], "A": [("Ā", "macron"), ("Ă", "breve"), ("Ą", "ogonek")],
    "c": [("ć", "acute"), ("ċ", "dotaccent"), ("č", "caron")], "C": [("Ć", "acute"), ("Ċ", "dotaccent"), ("Č", "caron")],
    "d": [("ď", "caronv")], "D": [("Ď", "caron")],
    "e": [("ē", "macron"), ("ė", "dotaccent"), ("ę", "ogonek"), ("ě", "caron")],
    "E": [("Ē", "macron"), ("Ė", "dotaccent"), ("Ę", "ogonek"), ("Ě", "caron")],
    "g": [("ğ", "breve"), ("ġ", "dotaccent"), ("ģ", "commaturned")],
    "G": [("Ğ", "breve"), ("Ġ", "dotaccent"), ("Ģ", "commaaccent")],
    "dotlessi": [("ī", "macron")], "i": [("į", "ogonek")],
    "I": [("Ī", "macron"), ("Į", "ogonek"), ("İ", "dotaccent")],
    "k": [("ķ", "commaaccent")], "K": [("Ķ", "commaaccent")],
    "l": [("ĺ", "acute"), ("ļ", "commaaccent"), ("ľ", "caronv")],
    "L": [("Ĺ", "acute"), ("Ļ", "commaaccent"), ("Ľ", "caronv")],
    "n": [("ń", "acute"), ("ņ", "commaaccent"), ("ň", "caron")],
    "N": [("Ń", "acute"), ("Ņ", "commaaccent"), ("Ň", "caron")],
    "o": [("ő", "hungarumlaut")], "O": [("Ő", "hungarumlaut")],
    "r": [("ŕ", "acute"), ("ř", "caron")], "R": [("Ŕ", "acute"), ("Ř", "caron")],
    "s": [("ś", "acute"), ("ş", "cedilla"), ("š", "caron"), ("ș", "commaaccent")],
    "S": [("Ś", "acute"), ("Ş", "cedilla"), ("Š", "caron"), ("Ș", "commaaccent")],
    "t": [("ť", "caronv"), ("ț", "commaaccent")], "T": [("Ť", "caron"), ("Ț", "commaaccent")],
    "u": [("ū", "macron"), ("ů", "ring"), ("ű", "hungarumlaut"), ("ų", "ogonek")],
    "U": [("Ū", "macron"), ("Ů", "ring"), ("Ű", "hungarumlaut"), ("Ų", "ogonek")],
    "w": [("ŵ", "circumflex"), ("ẁ", "grave"), ("ẃ", "acute"), ("ẅ", "dieresis")],
    "W": [("Ŵ", "circumflex"), ("Ẁ", "grave"), ("Ẃ", "acute"), ("Ẅ", "dieresis")],
    "y": [("ŷ", "circumflex"), ("ỳ", "grave")], "Y": [("Ŷ", "circumflex"), ("Ÿ", "dieresis"), ("Ỳ", "grave")],
    "z": [("ź", "acute"), ("ż", "dotaccent"), ("ž", "caron")], "Z": [("Ź", "acute"), ("Ż", "dotaccent"), ("Ž", "caron")],
}.items():
    ACCENTS.setdefault(_base, []).extend(_more)
# The auxiliary letters these languages' orthographies list (Fontbakery's language check)
for _base, _more in {
    "o": [("ō", "macron"), ("ŏ", "breve")], "O": [("Ō", "macron"), ("Ŏ", "breve")],
    "e": [("ĕ", "breve"), ("ẽ", "tilde")], "E": [("Ĕ", "breve"), ("Ẽ", "tilde")],
    "dotlessi": [("ĭ", "breve"), ("ĩ", "tilde")], "I": [("Ĭ", "breve"), ("Ĩ", "tilde")], "u": [("ŭ", "breve"), ("ǔ", "caron"), ("ũ", "tilde")],
    "U": [("Ŭ", "breve"), ("Ǔ", "caron"), ("Ũ", "tilde")],
    "t": [("ţ", "cedilla")], "T": [("Ţ", "cedilla")],
    "a": [("ǎ", "caron")], "A": [("Ǎ", "caron")], "r": [("ŗ", "commaaccent")],
    "R": [("Ŗ", "commaaccent")],
    "g": [("ǧ", "caron"), ("ĝ", "circumflex")], "G": [("Ǧ", "caron"), ("Ĝ", "circumflex")],
    "k": [("ǩ", "caron")], "K": [("Ǩ", "caron")],
    "h": [("ȟ", "caron"), ("ĥ", "circumflex")], "H": [("Ȟ", "caron"), ("Ĥ", "circumflex")],
    "c": [("ĉ", "circumflex")], "C": [("Ĉ", "circumflex")], "s": [("ŝ", "circumflex")], "S": [("Ŝ", "circumflex")],
    "dotlessj": [("ĵ", "circumflex")], "J": [("Ĵ", "circumflex")],
    "uni0292": [("ǯ", "caron")], "uni01B7": [("Ǯ", "caron")], "oslash": [("ǿ", "acute")], "Oslash": [("Ǿ", "acute")],
}.items():
    ACCENTS.setdefault(_base, []).extend(_more)

for _base, _marks in ACCENTS.items():
    for _char, _kind in _marks:
        _name = f"uni{ord(_char):04X}"
        GLYPHS[_name] = (_char, accented(_base, _kind))
        BASE[_name] = _base

# --- Google Fonts Latin Core: the remaining symbols and letters -------------
# Widths and sidebearings are measured from Michroma like the rest of the
# wordmark (ink x1.01, sides +41 units); every shape is built from the same
# parts as the letters above: bars, bowls, stems, the v, the marks.

WM_WIDTHS.update({
    "dollar": 918, "less": 436, "greater": 436, "backslash": 436, "asciicircum": 467, "grave": 338,
    "braceleft": 343, "bar": 93, "braceright": 343, "asciitilde": 436, "cent": 654, "sterling": 716,
    "yen": 934, "copyright": 810, "registered": 810, "degree": 330, "periodcentered": 93, "multiply": 441,
    "divide": 498, "bullet": 249, "ellipsis": 529, "Euro": 868, "trademark": 1215, "minus": 499,
    "exclamdown": 93, "section": 607, "dieresis": 438, "ordfeminine": 612, "guillemotleft": 529,
    "macron": 374, "acute": 338, "paragraph": 841, "cedilla": 187, "ordmasculine": 685,
    "guillemotright": 529, "questiondown": 700, "AE": 1433, "Eth": 965, "Oslash": 919, "Thorn": 841,
    "germandbls": 720, "eth": 686, "oslash": 686, "thorn": 685, "Hbar": 872, "Lslash": 747,
    "dotlessj": 171, "uni1E9E": 840, "quotesinglbase": 125, "quotedblbase": 280, "guilsinglleft": 311,
    "guilsinglright": 311,
})
WM_SIDES.update({
    "dollar": (105, 100), "less": (162, 162), "greater": (162, 162), "backslash": (72, 71),
    "asciicircum": (72, 72), "grave": (107, 103), "braceleft": (103, 103), "bar": (103, 103),
    "braceright": (103, 103), "asciitilde": (162, 162), "cent": (87, 87), "sterling": (72, 102),
    "yen": (72, 72), "copyright": (103, 103), "registered": (103, 103), "degree": (103, 103),
    "periodcentered": (103, 103), "multiply": (160, 160), "divide": (132, 132), "bullet": (160, 160),
    "ellipsis": (103, 103), "Euro": (103, 103), "trademark": (103, 103), "minus": (131, 131),
    "exclamdown": (132, 132), "section": (103, 103), "dieresis": (86, 86), "ordfeminine": (103, 124),
    "guillemotleft": (103, 103), "macron": (103, 103), "acute": (103, 107), "paragraph": (103, 103),
    "cedilla": (103, 103), "ordmasculine": (103, 103), "guillemotright": (103, 103),
    "questiondown": (146, 137), "AE": (71, 71), "Eth": (60, 102), "Oslash": (102, 102), "Thorn": (135, 76),
    "germandbls": (104, 87), "ae": (103, 98), "eth": (87, 87), "oslash": (87, 87), "thorn": (104, 87),
    "OE": (102, 71), "oe": (87, 98), "Dcroat": (60, 102), "dcroat": (87, 60), "Hbar": (90, 90),
    "hbar": (60, 101), "Lslash": (72, 71), "lslash": (60, 60), "dotlessj": (22, 133), "uni1E9E": (133, 102),
    "quotesinglbase": (71, 102), "quotedblbase": (102, 102), "guilsinglleft": (103, 103),
    "guilsinglright": (103, 103),
})
for _n in list(WM_WIDTHS):
    WIDTHS.setdefault(_n, round(WM_WIDTHS[_n] * 0.92))
for _n in list(WM_SIDES):
    SIDES.setdefault(_n, tuple(v * 0.93 for v in WM_SIDES[_n]))

MATH = XH * 0.62  # the centre line of + - x / = and their kin, as the plus has it


def scaled(contours, k, dx=0, dy=0):
    return geometry.transform(contours, a=k, d=k, e=dx, f=dy)


def small(p, k, thin=0.62):
    """Weight parameters for a letter drawn full size and then scaled by k, so its
    stems come out `thin` stems thick: the © and ® letters, ™, ª and º."""
    return P(p.wght, p.V * thin / k)


def chevron(p, W, h, cy, opening="right"):
    """A < with flat cut ends: a v laid on its side, apex at the left."""
    vee = v_shape(p, 0, h, top=W, foot=p.V * 0.5, r_top=p.rt)[0]  # opens up, h wide, W tall
    c = rotate([vee], -90, 0, 0)  # apex now at the left, opening right
    c = translate(c, 0, cy + h / 2)
    return c if opening == "right" else mirror_x(c, W)


def s_shape(p, W, h, mid=0.515, t0=0.33, t1=0.70):
    """The S's outline, any size."""
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    m0 = h * mid - H / 2
    m1 = m0 + H
    return rounded(
        (0, h * t0, rt), (0, 0, ro), (W, 0, ro), (W, m1, ro), (V, m1, ri), (V, h - H, ri),
        (W - V, h - H, ri), (W - V, h * t1, rt), (W, h * t1, rt), (W, h, ro), (0, h, ro), (0, m0, ro),
        (W - V, m0, ri), (W - V, H, ri), (V, H, ri), (V, h * t0, rt),
    )


@glyph("dollar", "$")
def g_dollar(p):
    """The S at figure height with a line through it, out past top and bottom."""
    W = p.w("dollar")
    t = p.V * 0.8
    line = box(W / 2 - t / 2, -FH * 0.13, W / 2 + t / 2, FH * 1.13, p.rt, p.rt, p.rt, p.rt)
    return [s_shape(p, W, FH), line], W, p.sides("dollar")


@glyph("less", "<")
def g_less(p):
    W = p.w("less")
    return chevron(p, W, W * 1.2, MATH, "right"), W, p.sides("less")


@glyph("greater", ">")
def g_greater(p):
    W = p.w("greater")
    return chevron(p, W, W * 1.2, MATH, "left"), W, p.sides("greater")


@glyph("backslash", "\\")
def g_backslash(p):
    W = p.w("backslash")
    return mirror_x(g_slash(p)[0], W), W, p.sides("backslash")


@glyph("asciicircum", "^")
def g_asciicircum(p):
    """A v turned over, hung from cap height."""
    W = p.w("asciicircum")
    h = FH * 0.42
    vee = v_shape(p, 0, W, top=h, foot=p.V * 1.1, r_top=p.rt)[0]
    return translate(rotate180([vee], W / 2, h / 2), 0, FH - h), W, p.sides("asciicircum")


def spacing_mark(p, name, kind, y=None):
    """A mark on its own: centred in its width, where it sits over a lowercase letter."""
    W = p.w(name)
    m, _ = mark(p, kind)
    return translate(m, W / 2, XH * 1.13 if y is None else y), W, p.sides(name)


@glyph("grave", "`")
def g_grave(p):
    return spacing_mark(p, "grave", "grave")


@glyph("acute", "´")
def g_acute(p):
    return spacing_mark(p, "acute", "acute")


@glyph("dieresis", "¨")
def g_dieresis(p):
    return spacing_mark(p, "dieresis", "dieresis")


@glyph("macron", "¯")
def g_macron(p):
    return spacing_mark(p, "macron", "macron")


@glyph("cedilla", "¸")
def g_cedilla(p):
    return spacing_mark(p, "cedilla", "cedilla", y=0)


def brace(p, W):
    """An opening brace: the bracket, stepped in, with a tooth out to the left at its middle."""
    xs = W * 0.36
    mid = (DSC * 0.61 + FH + 34) / 2
    b = translate([bracket(p, W - xs, p.ro * 1.2, p.ri * 1.2)], xs)
    tooth = box(0, mid - p.H / 2, xs + p.V / 2, mid + p.H / 2, p.rt, 0, 0, p.rt)
    return b + [tooth]


@glyph("braceleft", "{")
def g_braceleft(p):
    W = p.w("braceleft")
    return brace(p, W), W, p.sides("braceleft")


@glyph("braceright", "}")
def g_braceright(p):
    W = p.w("braceright")
    return mirror_x(brace(p, W), W), W, p.sides("braceright")


@glyph("bar", "|")
def g_bar(p):
    return [box(0, DSC * 0.61, p.V, FH + 34, p.rt, p.rt, p.rt, p.rt)], p.V, p.sides("bar")


def wave(p, w, cy, d=None):
    """The tilde's wave, w wide, centred on cy; d is its rise."""
    V, H, rt = p.V, p.H, p.rt
    d = max(V * 1.1, H * 1.3) if d is None else d
    a, b = w * 0.30, w * 0.70
    rr = H * 1.4
    y0 = cy - (d + H) / 2
    return rounded((0, y0, rt), (a, y0, rr), (b, y0 + d, rr), (w, y0 + d, rt), (w, y0 + d + H, rt),
                   (b, y0 + d + H, rr), (a, y0 + H, rr), (0, y0 + H, rt))


@glyph("asciitilde", "~")
def g_asciitilde(p):
    W = p.w("asciitilde")
    return [wave(p, W, MATH, d=max(W * 0.45, p.H * 1.3))], W, p.sides("asciitilde")


@glyph("uni00A0", " ")
def g_nbspace(p):
    return [], 0, (150, 150)


@glyph("cent", "¢")
def g_cent(p):
    """The c with a line through it, out past the x-height and the baseline."""
    W = p.w("cent")
    t = p.V * 0.8
    c = c_shape(p, W, XH, XH * lm("c_t0", 0.334), XH * lm("c_t1", 0.686))
    line = box(W / 2 - t / 2, -XH * 0.16, W / 2 + t / 2, XH * 1.16, p.rt, p.rt, p.rt, p.rt)
    return [c, line], W, p.sides("cent")


@glyph("sterling", "£")
def g_sterling(p):
    """A stem rising from a full-width base into the f's arm, crossed by a bar."""
    W = p.w("sterling")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    xs, t = W * 0.22, FH * 0.70  # stem, and the arm's terminal
    arm = rounded(
        (xs, H, rt), (xs + V, H, rt), (xs + V, FH - H, ri), (W - V, FH - H, ri), (W - V, t, rt), (W, t, rt),
        (W, FH, ro), (xs, FH, ro),
    )
    cross = box(0, FH * 0.44 - H / 2, W * 0.70, FH * 0.44 + H / 2, rt, rt, rt, rt)
    base = box(0, 0, W, H, rt, rt, rt, rt)
    return [arm, cross, base], W, p.sides("sterling")


@glyph("yen", "¥")
def g_yen(p):
    """The Y, with two bars across its stem."""
    W = p.w("yen")
    yj = FH * lm("Y_join", 0.416)
    vee = v_shape(p, 0, W, top=FH, bottom=yj, foot=p.V, r_top=p.rt)[0]
    bw = W * 0.62
    b1 = yj - p.H * 0.4
    bars = [box(W / 2 - bw / 2, y, W / 2 + bw / 2, y + p.H, p.rt, p.rt, p.rt, p.rt) for y in (b1 - p.H * 2.0, b1)]
    return [vee, stem(p, W / 2 - p.V / 2, 0, yj + p.H)] + bars, W, p.sides("yen")


def ring_box(p, W, h, y0, thin=0.62):
    """A round-cornered ring, strokes `thin` stems thick: the ©'s and ®'s frame."""
    v, hh = p.V * thin, p.H * thin
    r = min(p.ro * 1.6, h / 2)
    return [box(0, y0, W, y0 + h, r, r, r, r), hole(v, y0 + hh, W - v, y0 + h - hh, max(r - v * 0.8, 4))]


def framed(p, name, letter_fn):
    """© and ®: a capital, small, centred in a ring at cap height. letter_fn(q) -> (contours, width)."""
    W = p.w(name)
    h = W * 0.96
    y0 = (FH - h) / 2
    k = 0.46
    q = small(p, k, thin=0.66)
    c, lw = letter_fn(q)
    lw *= k
    return ring_box(p, W, h, y0) + scaled(c, k, (W - lw) / 2, y0 + (h - CH * k) / 2), W, p.sides(name)


@glyph("copyright", "©")
def g_copyright(p):
    def letter(q):
        w = WM_WIDTHS["C"] * 0.95
        return [c_shape(q, w, CH, CH * 0.36, CH * 0.64)], w
    return framed(p, "copyright", letter)


@glyph("registered", "®")
def g_registered(p):
    def letter(q):
        c, w, _ = g_R(q)
        return c, w
    return framed(p, "registered", letter)


@glyph("degree", "°")
def g_degree(p):
    W = p.w("degree")
    return translate(ring_box(p, W, W * 0.92, 0, thin=0.8), 0, FH - W * 0.92), W, p.sides("degree")


@glyph("periodcentered", "·")
def g_periodcentered(p):
    return [dot_at(p, 0, XH * lm("dash", 0.514) - p.V / 2)], p.V, p.sides("periodcentered")


@glyph("multiply", "×")
def g_multiply(p):
    """The x, square, on the centre line."""
    W = p.w("multiply")
    rt, y0 = p.rt, MATH - W / 2
    hw = diag_hw(W, W, p.V * 0.98)
    down = rpoly((0, y0 + W, rt), (hw, y0 + W, rt), (W, y0, rt), (W - hw, y0, rt))
    up = rpoly((W - hw, y0 + W, rt), (W, y0 + W, rt), (hw, y0, rt), (0, y0, rt))
    return [down, up], W, p.sides("multiply")


@glyph("divide", "÷")
def g_divide(p):
    W = p.w("divide")
    V, H, rt = p.V, p.H, p.rt
    gap = V * 0.9
    line = box(0, MATH - H / 2, W, MATH + H / 2, rt, rt, rt, rt)
    return [line, dot_at(p, W / 2 - V / 2, MATH + H / 2 + gap), dot_at(p, W / 2 - V / 2, MATH - H / 2 - gap - V)], W, p.sides("divide")


@glyph("minus", "−")
def g_minus(p):
    W = p.w("minus")
    return [box(0, MATH - p.H / 2, W, MATH + p.H / 2, p.rt, p.rt, p.rt, p.rt)], W, p.sides("minus")


@glyph("bullet", "•")
def g_bullet(p):
    W = max(p.w("bullet"), p.V * 2.2)
    c = XH * lm("dash", 0.514)
    r = W * 0.3
    return [box(0, c - W / 2, W, c + W / 2, r, r, r, r)], W, p.sides("bullet")


@glyph("ellipsis", "…")
def g_ellipsis(p):
    V = p.V
    gap = V * 1.25
    return [dot_at(p, i * (V + gap), 0) for i in range(3)], 3 * V + 2 * gap, p.sides("ellipsis")


@glyph("Euro", "€")
def g_Euro(p):
    """The C, stepped right, with two bars through its back."""
    W = p.w("Euro")
    V, H, rt = p.V, p.H, p.rt
    xo = W * 0.14
    c = translate([c_shape(p, W - xo, FH, FH * lm("C_t0", 0.337), FH * lm("C_t1", 0.656))], xo)
    x1 = xo + (W - xo) * 0.55
    bars = [box(0, y - H / 2, x1, y + H / 2, rt, rt, rt, rt) for y in (FH * 0.35, FH * 0.63)]
    return c + bars, W, p.sides("Euro")


@glyph("trademark", "™")
def g_trademark(p):
    """T and M, small, hung from cap height."""
    k = 0.42
    q = small(p, k, thin=0.75)
    T, M = g_T(q), g_M(q)
    gap = p.V * 0.8
    wt, wm = T[1] * k, M[1] * k
    y = FH - CH * k
    c = scaled(T[0], k, 0, y) + scaled(M[0], k, wt + gap, y)
    return c, wt + gap + wm, p.sides("trademark")


@glyph("exclamdown", "¡")
def g_exclamdown(p):
    c, W, _ = g_exclam(p)
    return translate(rotate180(c, W / 2, FH / 2), 0, XH - FH), W, p.sides("exclamdown")


@glyph("questiondown", "¿")
def g_questiondown(p):
    c, W, _ = g_question(p)
    return translate(rotate180(c, W / 2, FH / 2), 0, XH - FH), W, p.sides("questiondown")


@glyph("section", "\u00a7")
def g_section(p):
    """A closed loop in the middle, a hook rising from its left side to a terminal at
    the top right, and the same hook turned over below it."""
    W = p.w("section")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    l0, l1 = FH * 0.29, FH * 0.71  # the loop
    t1 = FH * 0.80  # the hooks' terminals
    r = min(ro, (l1 - l0) / 2)
    loop = [box(0, l0, W, l1, r, r, r, r), hole(V, l0 + H, W - V, l1 - H, min(ri, r / 2), )]
    ym = (l0 + l1) / 2  # the hook starts on the loop's straight side, so the two sides run on as one
    hook = rpoly(
        (0, ym, 0), (V, ym, 0), (V, FH - H, ri), (W - V, FH - H, ri), (W - V, t1, rt), (W, t1, rt),
        (W, FH, ro), (0, FH, ro),
    )
    return loop + [hook] + rotate180([hook], W / 2, FH / 2), W, p.sides("section")


@glyph("paragraph", "¶")
def g_paragraph(p):
    """A solid bowl on the left, two stems hanging from a bar across the top."""
    W = p.w("paragraph")
    V, H, ro, rt = p.V, p.H, p.ro, p.rt
    x1, x2 = W * 0.52, W - V
    bowl_ = box(0, FH * 0.40, x1 + V, FH, ro, 0, 0, ro)
    stems = [box(x1, 0, x1 + V, FH, rt, rt, 0, 0), box(x2, 0, W, FH, rt, rt, rt, 0)]
    top = box(x1, FH - H, W, FH, 0, 0, rt, 0)
    return [bowl_, top] + stems, W, p.sides("paragraph")


def ordinal(p, name, letter):
    """ª and º: the a or o, small, raised to cap height, over a short bar."""
    k = 0.52
    q = small(p, k, thin=0.72)
    c, w, _ = letter(q)
    wk = w * k
    y = FH - XH * k
    bar_y = y - p.H * 0.75 - p.V * 0.7
    return scaled(c, k, 0, y) + [box(0, bar_y, wk, bar_y + p.H * 0.75, p.rt, p.rt, p.rt, p.rt)], wk, p.sides(name)


@glyph("ordfeminine", "ª")
def g_ordfeminine(p):
    return ordinal(p, "ordfeminine", g_a)


@glyph("ordmasculine", "º")
def g_ordmasculine(p):
    return ordinal(p, "ordmasculine", g_o)


def guillemets(p, name, n, opening):
    W1 = XH * 0.27 + p.V * 1.15  # grows with the stroke, so Bold keeps the inside of each chevron open
    h = W1 * 1.45
    gap = p.V * 0.45
    c = []
    for i in range(n):
        c += translate(chevron(p, W1, h, XH * lm("dash", 0.514), opening), i * (W1 + gap))
    return c, n * W1 + (n - 1) * gap, p.sides(name)


@glyph("guillemotleft", "«")
def g_guillemotleft(p):
    return guillemets(p, "guillemotleft", 2, "right")


@glyph("guillemotright", "»")
def g_guillemotright(p):
    return guillemets(p, "guillemotright", 2, "left")


@glyph("guilsinglleft", "‹")
def g_guilsinglleft(p):
    return guillemets(p, "guilsinglleft", 1, "right")


@glyph("guilsinglright", "›")
def g_guilsinglright(p):
    return guillemets(p, "guilsinglright", 1, "left")


@glyph("quotesinglbase", "‚")
def g_quotesinglbase(p):
    return [comma_at(p, 0, p.V * 0.67)], p.V * 4 / 3, p.sides("quotesinglbase")


@glyph("quotedblbase", "„")
def g_quotedblbase(p):
    V = p.V
    w1, gap = V * 4 / 3, V * 0.5
    return [comma_at(p, i * (w1 + gap), V * 0.67) for i in range(2)], 2 * w1 + gap, p.sides("quotedblbase")


# Letters

@glyph("AE", "Æ")
def g_AE(p):
    """The A's left leg running up into the E's stem, with the A's bar between them."""
    W = p.w("AE")
    V, H, rt = p.V, p.H, p.rt
    xs = W * 0.40  # the E's stem
    hw = diag_hw(xs, CH, V * 0.98)
    leg = rpoly((0, 0, rt), (hw, 0, rt), (xs + V * 0.5, CH, 0), (xs + V * 0.5 - hw, CH, 0))
    m0 = CH * lm("EFH_mid", 0.510) - H / 2
    ab = CH * lm("A_bar", 0.229)
    we = W - xs
    xl = (ab + H / 2) / CH * (xs + V * 0.5 - hw) + hw * 0.5  # the bar starts inside the leg
    parts = [stem(p, xs), bar(p, xs, xs + we * lm("E_top", 0.981), CH - H), bar(p, xs, xs + we * lm("E_mid", 0.945), m0),
             bar(p, xs, W, 0), box(xl, ab, xs + V / 2, ab + H, 0, 0, 0, 0)]
    return [leg] + parts, W, p.sides("AE")


def crossbar(p, x0, x1, y):
    return box(x0, y - p.H / 2, x1, y + p.H / 2, p.rt, p.rt, p.rt, p.rt)


@glyph("Eth", "Ð")
def g_Eth(p):
    """The D, stepped right, with a bar through its stem."""
    xo = p.V * 0.9
    c, W, _ = g_D(p)
    return translate(c, xo) + [crossbar(p, 0, xo + p.V * 2.3, CH * 0.5)], W + xo, p.sides("Eth")


@glyph("Dcroat", "Đ")
def g_Dcroat(p):
    c, W, _ = g_Eth(p)
    return c, W, p.sides("Dcroat")


def slashed(p, contours, W, h, below, above):
    """A letter with a diagonal through it, out past its top and bottom (Ø, ø)."""
    t = p.V * 0.9
    y0, y1 = -h * below, h * (1 + above)
    hw = diag_hw(W * 0.84, y1 - y0, t)
    x0 = W * 0.08
    s = rpoly((x0, y0, p.rt), (x0 + hw, y0, p.rt), (W - x0, y1, p.rt), (W - x0 - hw, y1, p.rt))
    return contours + [s]


@glyph("Oslash", "Ø")
def g_Oslash(p):
    c, W, _ = GLYPHS["O"][1](p)  # with its overshoot
    return slashed(p, c, W, CH, 0.14, 0.14), W, p.sides("Oslash")


@glyph("oslash", "ø")
def g_oslash(p):
    c, W, _ = GLYPHS["o"][1](p)
    return slashed(p, c, W, XH, 0.18, 0.18), W, p.sides("oslash")


@glyph("Thorn", "Þ")
def g_Thorn(p):
    W = p.w("Thorn")
    return [stem(p, 0)] + capbowl(p, 0, W, CH * 0.20, CH * 0.82, "square"), W, p.sides("Thorn")


@glyph("thorn", "þ")
def g_thorn(p):
    """The p with its stem run up to the ascender."""
    W = p.w("thorn")
    stem_ = box(0, DSC, p.V, ASC, p.rt, p.rt, p.rt, p.rt)
    return [stem_] + bowl(p, 0, W, stem="left"), W, p.sides("thorn")


def eszett(p, W, top, round_top=True):
    """ß: a stem and a top bowl open below, its bar handing over to a lower bowl like the 3's."""
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    W1, xm, xb = W * 0.86, W * 0.36, W * 0.30
    m0 = XH * 0.60 - H / 2
    m1 = m0 + H
    rw = waist(p, m1)
    upper = rpoly(
        (0, 0, rt), (V, 0, rt), (V, top - H, ri), (W1 - V, top - H, ri), (W1 - V, m1, joint(p, ri)),
        (xm, m1, rt), (xm, m0, rt), (W1, m0, waist(p, top - m0)), (W1, top, ro), (0, top, ro if round_top else rt),
    )
    lower = rpoly(
        (xb, 0, rt), (W, 0, ro), (W, m1, rw), (xm, m1, rt), (xm, m0, rt), (W - V, m0, joint(p, ri)),
        (W - V, H, ri), (xb, H, rt),
    )
    return [upper, lower]


@glyph("germandbls", "ß")
def g_germandbls(p):
    W = p.w("germandbls")
    return eszett(p, W, ASC), W, p.sides("germandbls")


@glyph("uni1E9E", "ẞ")
def g_Germandbls(p):
    W = p.w("uni1E9E")
    return eszett(p, W, CH, round_top=False), W, p.sides("uni1E9E")


@glyph("eth", "\u00f0")
def g_eth(p):
    """Michroma's construction: the bowl's right side runs on up to the ascender and over
    to a terminal on the left, and a short stroke rises across the shoulder."""
    W = p.w("eth")
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    t = XH + (ASC - XH) * 0.35  # the top's left terminal
    hook = rpoly(
        (W - V, XH * 0.5, rt), (W, XH * 0.5, rt), (W, ASC, ro), (0, ASC, ro), (0, t, rt), (V, t, rt),
        (V, ASC - H, ri), (W - V, ASC - H, ri),
    )
    w, rise, th = V * 2.4, V * 0.45, H * 0.8
    cx, cy = W - V * 0.3, ASC - H * 1.25
    cross = rpoly((cx - w / 2, cy - rise / 2 - th / 2, rt), (cx + w / 2, cy + rise / 2 - th / 2, rt),
                  (cx + w / 2, cy + rise / 2 + th / 2, rt), (cx - w / 2, cy - rise / 2 + th / 2, rt))
    return GLYPHS["o"][1](p)[0] + [hook, cross], W + V * 0.9, p.sides("eth")


def joined(first, second, overlap):
    """Two letters run together, the second starting `overlap` before the first ends (æ, œ, Œ)."""
    a, wa, (lsb, _) = first
    b, wb, (_, rsb) = second
    return a + translate(b, wa - overlap), wa + wb - overlap, (lsb, rsb)


@glyph("ae", "æ")
def g_ae(p):
    return joined(g_a(p), g_e(p), p.V)  # neither overshoots: the a has a flat stem at the line


@glyph("oe", "œ")
def g_oe(p):
    return joined(GLYPHS["o"][1](p), GLYPHS["e"][1](p), p.V)


@glyph("OE", "Œ")
def g_OE(p):
    return joined(GLYPHS["O"][1](p), g_E(p), p.V)


@glyph("dcroat", "đ")
def g_dcroat(p):
    c, W, _ = g_d(p)
    return c + [crossbar(p, W - p.V * 2.4, W + p.V * 0.9, ASC * 0.84)], W + p.V * 0.9, p.sides("dcroat")


@glyph("Hbar", "Ħ")
def g_Hbar(p):
    xo = p.V * 0.5
    c, W, _ = g_H(p)
    return translate(c, xo) + [crossbar(p, 0, W + 2 * xo, CH * 0.78)], W + 2 * xo, p.sides("Hbar")


@glyph("hbar", "ħ")
def g_hbar(p):
    xo = p.V * 0.7
    c, W, _ = g_h(p)
    return translate(c, xo) + [crossbar(p, 0, xo + p.V * 2.6, ASC * 0.84)], W + xo, p.sides("hbar")


def lslash_bar(p, cx, cy):
    """The stroke through Ł and ł: short, rising to the right, cut flat."""
    w, rise, t = p.V * 2.6, p.V * 1.0, p.H * 0.95
    x0, x1 = cx - w / 2, cx + w / 2
    return rpoly((x0, cy - rise / 2 - t / 2, p.rt), (x1, cy + rise / 2 - t / 2, p.rt), (x1, cy + rise / 2 + t / 2, p.rt),
                 (x0, cy - rise / 2 + t / 2, p.rt))


@glyph("Lslash", "Ł")
def g_Lslash(p):
    xo = p.V * 0.8
    c, W, _ = g_L(p)
    return translate(c, xo) + [lslash_bar(p, xo + p.V / 2, CH * 0.46)], W + xo, p.sides("Lslash")


@glyph("lslash", "ł")
def g_lslash(p):
    xo = p.V * 0.8
    c, W, _ = g_l(p)
    return translate(c, xo) + [lslash_bar(p, xo + p.V / 2, ASC * 0.52)], W + 2 * xo, p.sides("lslash")


@glyph("dotlessj", "ȷ")
def g_dotlessj(p):
    c, W, _ = g_j(p)
    return c[:1], W, p.sides("j")


GLYPHS["uni012F.dotless"] = (None, accented("dotlessi", "ogonek"))  # į under an accent: the ccmp feature swaps it in
BASE["uni012F.dotless"] = "i"


@glyph("ldot", "\u0140")
def g_ldot(p):
    """ŀ (Catalan l·l): the l with a dot beside it at the middle of the x-height."""
    V = p.V
    return [box(0, 0, V, ASC, p.rt, p.rt, p.rt, p.rt), dot_at(p, V * 1.9, XH * 0.5 - V / 2)], V * 2.9, p.sides("l")


@glyph("Ldot", "\u013f")
def g_Ldot(p):
    c, W, _ = g_L(p)
    return c + [dot_at(p, W * 0.5, CH * 0.5 - p.V / 2)], W, p.sides("L")


@glyph("ij", "\u0133")
def g_ij(p):
    """The Dutch ij: i and j set as one letter."""
    i, Wi, _ = g_i(p)
    j, Wj, _ = g_j(p)
    gap = p.V * 1.1
    return i + translate(j, Wi + gap), Wi + gap + Wj, p.sides("i")


@glyph("IJ", "\u0132")
def g_IJ(p):
    I, Wi, _ = g_I(p)
    J, Wj, _ = g_J(p)
    gap = p.V * 1.2
    return I + translate(J, Wi + gap), Wi + gap + Wj, (p.sides("I")[0], p.sides("J")[1])


def ezh(p, W, top, bottom):
    """ʒ: the z's top bar and diagonal, landing on a middle bar that hands over to the 3's lower bowl."""
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    h = top - bottom
    m0 = bottom + h * 0.40 - H / 2  # the middle bar, low enough that the diagonal stays steep at Bold
    m1 = m0 + H
    xm = W * 0.40  # where the diagonal lands
    tb = bottom + h * 0.20  # the bowl's terminal
    hw = diag_hw(W - xm, top - H - m1, V * 0.98)
    bar = box(0, top - H, W, top, rt, 0, rt, rt)
    diagonal = rpoly((W - hw, top - H, 0), (W, top - H, 0), (xm + hw, m1, 0), (xm, m1, 0))
    rw = min(waist(p, m1 - bottom), ro * 0.6)  # shallower than a plain corner: the bowl here is shallow, and at Bold the diagonal lands close by
    lower = rpoly(
        (0, tb, rt), (0, bottom, ro), (W, bottom, ro), (W, m1, rw), (xm, m1, 0), (xm, m0, rt),
        (W - V, m0, ri), (W - V, bottom + H, ri), (V, bottom + H, ri), (V, tb, rt),
    )  # sharp where the diagonal lands, so its corner does not poke out past a soft one
    return [bar, diagonal, lower]


@glyph("uni0292", "\u0292")
def g_ezh(p):
    W = p.w("z")
    return ezh(p, W, XH, DSC * 0.9), W, p.sides("z")


@glyph("uni01B7", "\u01b7")
def g_Ezh(p):
    W = p.w("Z")
    return ezh(p, W, CH, 0), W, p.sides("Z")


@glyph("uni01E5", "\u01e5")
def g_gstroke(p):
    """ǥ: the g with a bar through its tail."""
    c, W, _ = GLYPHS["g"][1](p)
    return c + [crossbar(p, W - p.V * 1.8, W + p.V * 0.7, XH * 0.30)], W + p.V * 0.7, p.sides("g")  # across the stem, above the tail


@glyph("uni01E4", "\u01e4")
def g_Gstroke(p):
    c, W, _ = GLYPHS["G"][1](p)
    return c + [crossbar(p, W * 0.55, W + p.V * 0.3, CH * 0.26)], W + p.V * 0.3, p.sides("G")


@glyph("eng", "\u014b")
def g_eng(p):
    """The n whose right leg runs on below the baseline into the j's hook."""
    c, W, _ = g_n(p)
    hook, Wj, _ = g_j(p)
    return c + translate(hook[:1], W - Wj), W, p.sides("n")


@glyph("Eng", "\u014a")
def g_Eng(p):
    """The N whose right stem runs on below the baseline and hooks left."""
    c, W, _ = g_N(p)
    V, H, ro, ri, rt = p.V, p.H, p.ro, p.ri, p.rt
    xh = W * 0.55
    hook = rounded((xh, DSC + H, rt), (xh, DSC, rt), (W, DSC, ro), (W, CH * 0.5, rt), (W - V, CH * 0.5, rt), (W - V, DSC + H, ri))
    return c + [hook], W, p.sides("N")


@glyph("tbar", "\u0167")
def g_tbar(p):
    c, W, _ = g_t(p)
    y = (XH * lm("t_foot", 0.436) + XH - p.H) / 2  # centred between the foot and the crossbar
    t = p.H * 0.8
    return c + [box(0, y - t / 2, W * 0.72, y + t / 2, p.rt, p.rt, p.rt, p.rt)], W, p.sides("t")


@glyph("Tbar", "\u0166")
def g_Tbar(p):
    c, W, _ = g_T(p)
    return c + [crossbar(p, W * 0.22, W * 0.78, CH * 0.48)], W, p.sides("T")


@glyph("longs", "\u017f")
def g_longs(p):
    """ſ: the f without its crossbar."""
    c, W, _ = g_f(p)
    return c[:1], W, p.sides("f")


@glyph("uni02BB", "\u02bb")
def g_turnedcomma(p):
    m, W = quote(p, 1, True)
    return m, W, p.sides("quoteleft")


@glyph("uni25CC", "\u25cc")
def g_dottedcircle(p):
    """◌: where an accent typed on its own is shown. Twelve dots on a circle."""
    import math
    d = p.V * 0.62
    R = XH * 0.42
    cy = XH * 0.5
    dots = [box(R + R * math.cos(a) - d / 2, cy + R * math.sin(a) - d / 2, R + R * math.cos(a) + d / 2,
                cy + R * math.sin(a) + d / 2, d * 0.3, d * 0.3, d * 0.3, d * 0.3)
            for a in (2 * math.pi * i / 12 for i in range(12))]
    return dots, 2 * R + d, (80, 80)


def free_mark(p, kind, y):
    """A spacing modifier: the mark alone, as wide as its ink."""
    m, _ = mark(p, kind)
    xs = [pt[0] for c in m for seg in [[c[0]]] + [s[1:] for s in c[1:]] for pt in seg]
    return translate(m, -min(xs), y), max(xs) - min(xs), (86, 86)


def combining(kind, y):
    """A combining mark: no width of its own, hung over the letter before it."""
    def fn(p):
        m, _ = mark(p, kind)
        return translate(m, -300, y), 0, (0, 0)
    return fn


for _cp, _kind, _top in [(0x02C6, "circumflex", True), (0x02C7, "caron", True), (0x02D8, "breve", True),
                         (0x02D9, "dotaccent", True), (0x02DA, "ring", True), (0x02DB, "ogonek", False),
                         (0x02DC, "tilde", True), (0x02DD, "hungarumlaut", True)]:
    GLYPHS[f"uni{_cp:04X}"] = (chr(_cp), (lambda k, t: lambda p: free_mark(p, k, XH * 1.13 if t else 0))(_kind, _top))

for _cp, _kind in [(0x0300, "grave"), (0x0301, "acute"), (0x0302, "circumflex"), (0x0303, "tilde"), (0x0304, "macron"),
                   (0x0306, "breve"), (0x0307, "dotaccent"), (0x0308, "dieresis"), (0x030A, "ring"),
                   (0x030B, "hungarumlaut"), (0x030C, "caron")]:
    GLYPHS[f"uni{_cp:04X}"] = (chr(_cp), combining(_kind, XH * 1.13))
for _cp, _kind in [(0x0326, "commaaccent"), (0x0327, "cedilla"), (0x0328, "ogonek")]:
    GLYPHS[f"uni{_cp:04X}"] = (chr(_cp), combining(_kind, 0))


# Overshoot: a round top or bottom has to pass the line a little to look as tall
# as a flat one. Michroma's go 1.9% of the x-height past it on the lowercase and
# 2.1% on capitals and figures. Only the round extremes move: points within a
# horizontal stroke of the top (or bottom) line, so the stroke keeps its
# thickness and the corner curves stretch to meet it; terminals, bars and
# crossbars further in stay where they are. Letters with a flat stem at the
# line (n, b, d, p, a, u) do not overshoot, or their stems would step.
OVERSHOOT = {
    **dict.fromkeys(["o", "c", "e", "s"], ("XH", "tb")),
    **dict.fromkeys(["O", "C", "G", "Q", "S"], ("CH", "tb")),
    **dict.fromkeys(["zero", "three", "six", "eight", "nine", "ampersand"], ("FH", "tb")),
    "two": ("FH", "t"), "five": ("FH", "b"),
}


def overshot(fn, height, where):
    def wrapped(p):
        contours, W, sides = fn(p)
        top = {"XH": XH, "CH": CH, "FH": FH}[height]
        ov = top * (0.019 if height == "XH" else 0.021)
        zone = p.H + 2

        def move(pt):
            x, y = pt
            if "t" in where and y >= top - zone:
                return (x, y + ov)
            if "b" in where and y <= zone:
                return (x, y - ov)
            return pt

        out = [[move(c[0])] + [(seg[0], *[move(q) for q in seg[1:]]) for seg in c[1:]] for c in contours]
        return out, W, sides
    return wrapped


for _name, (_height, _where) in OVERSHOOT.items():
    GLYPHS[_name] = (GLYPHS[_name][0], overshot(GLYPHS[_name][1], _height, _where))

# Math signs share one advance, the plus's, so sums set in columns line up;
# each sits centred in it.
MATH_SIGNS = ["plus", "minus", "multiply", "divide", "equal", "less", "greater", "asciitilde"]


def math_width(fn):
    def wrapped(p):
        contours, W, _ = fn(p)
        _, wp, (lp, rp) = GLYPHS["plus"][1](p)
        side = (lp + wp + rp - W) / 2
        return contours, W, (side, side)
    return wrapped


for _name in MATH_SIGNS[1:]:
    GLYPHS[_name] = (GLYPHS[_name][0], math_width(GLYPHS[_name][1]))

set_style(os.environ.get("HYPHER_STYLE", DEFAULT_STYLE))
