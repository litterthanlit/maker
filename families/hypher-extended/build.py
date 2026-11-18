"""Build Hypher Extended: the variable font, static instances and web fonts.

    python3 families/hypher-extended/build.py

Writes to families/hypher-extended/fonts/:
    variable/HypherExtended[wght].ttf + .woff2, static/HypherExtended-<Style>.ttf + .woff2
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "src"))
sys.path.insert(0, str(HERE))

from core.fontbuild import Family, build  # noqa: E402
import glyphs as G  # noqa: E402

# weight -> stem width at a 700 cap height; everything else derives from it.
# The reference wordmark's stem (165) falls near SemiBold.
MASTERS = {300: 70, 400: 104, 700: 180}

SHUT = ["period", "comma", "quoteright", "quotedblright"]  # marks that tuck under an overhang
PAIRS = {
    **{("T", m): -110 for m in SHUT[:2]}, **{(l, m): -120 for l in "VWY" for m in SHUT[:2]},
    **{(l, m): -90 for l in "FP" for m in SHUT[:2]},
    ("L", "T"): -110, ("L", "V"): -120, ("L", "W"): -90, ("L", "Y"): -120,
    ("L", "quoteright"): -140, ("L", "quotedblright"): -140,
    ("T", "hyphen"): -60, ("V", "hyphen"): -40, ("Y", "hyphen"): -50,
    ("K", "O"): -30, ("K", "C"): -30, ("K", "G"): -30, ("K", "Q"): -30,
    ("X", "O"): -30, ("X", "C"): -30, ("X", "G"): -30, ("X", "Q"): -30,
    ("quoteleft", "J"): -60, ("quotedblleft", "J"): -60, ("T", "J"): -60,
}


def features(wght):
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "feature kern {"]
    lines += [f"  pos {l} {r} {v};" for (l, r), v in sorted(PAIRS.items())]
    lines.append("} kern;")
    return "\n".join(lines)


FAMILY = Family(
    name="Hypher Extended",
    file="HypherExtended",
    version="0.100",
    copyright="Copyright 2026 The Hypher Project Authors",
    glyphs=G.GLYPHS,
    params=lambda w: G.P(w, MASTERS[w]),
    masters=list(MASTERS),
    default=400,
    instances={300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"},
    ascent=920,
    descent=-260,
    x_height=G.CH,  # caps only: the lowercase keys type the capitals
    cap_height=G.CH,
    features=features,
    out=HERE / "fonts",
    hint=None,  # a display face: set large, where hinting does nothing
)


if __name__ == "__main__":
    build(FAMILY, HERE.parent.parent / "build")
