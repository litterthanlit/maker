"""Build Hypher: the variable font, static instances and web fonts.

    python3 families/hypher/build.py

Writes to families/hypher/fonts/:
    variable/Hypher[wght].ttf + .woff2
    static/Hypher-<Style>.ttf + .woff2
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "src"))
sys.path.insert(0, str(HERE))

from core.fontbuild import Family, build  # noqa: E402
import glyphs as G  # noqa: E402

# weight -> lowercase stem width, in Michroma's 2048 units. 400 is Michroma's own.
MASTERS = {300: 128, 400: 192, 700: 300}

# (left, right, value): the lockup's tracking is even, but e-r reads loose
# because both letters open to the right. 2.5 units at the lockup's x-height
# of 80 (to the e's round top) is 2.5 / 80 * 1174 here.
KERN_PAIRS = [("e", "r", -37)]


def features(wght):
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "feature kern {"]
    lines += [f"  pos {l} {r} {v};" for l, r, v in KERN_PAIRS]
    lines.append("} kern;")
    return "\n".join(lines)


HYPHER = Family(
    name="Hypher",
    file="Hypher",
    version="0.100",
    copyright="Copyright 2026 The Hypher Project Authors; outlines from Michroma, Copyright 2011 The Michroma Project Authors",
    glyphs=G.GLYPHS,
    params=lambda w: G.P(w, MASTERS[w]),
    masters=list(MASTERS),
    default=400,
    instances={300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"},
    ascent=2368,  # Michroma's own line box
    descent=-544,
    x_height=G.XH,
    cap_height=G.CH,
    features=features,
    out=HERE / "fonts",
    upm=G.UPM,
    hint=None,  # a display face: set large, where hinting does nothing
)

if __name__ == "__main__":
    build(HYPHER, HERE.parent.parent / "build")
