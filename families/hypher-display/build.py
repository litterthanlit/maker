"""Build Hypher Display: the variable font, static instances and web fonts.

    python3 families/hypher-display/build.py              # Hypher Display (the Wordmark design)
    python3 families/hypher-display/build.py --versions   # also every named version

Writes to families/hypher-display/fonts/:
    variable/HypherDisplay[wght].ttf + .woff2, static/HypherDisplay-<Style>.ttf + .woff2
    versions/<Name>/variable/HypherDisplay<Name>[wght].ttf + .woff2, and statics
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "src"))
sys.path.insert(0, str(HERE))

from core.fontbuild import Family, build  # noqa: E402
import glyphs as G  # noqa: E402

# weight -> lowercase stem width; everything else derives from it.
MASTERS = {300: 60, 400: 92, 700: 150}


def features(wght):
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "feature kern {"]
    lines += [f"  pos {l} {r} {v};" for l, r, v in G.STYLE["kern"]]
    lines.append("} kern;")
    return "\n".join(lines)


def family(style):
    """The Family for one version; the default version is plain Hypher Display."""
    G.set_style(style)
    default = style == G.DEFAULT_STYLE
    return Family(
        name="Hypher Display" if default else f"Hypher Display {style}",
        file="HypherDisplay" if default else f"HypherDisplay{style}",
        version="0.310",
        copyright="Copyright 2026 The Hypher Project Authors",
        glyphs=G.GLYPHS,
        params=lambda w: G.P(w, MASTERS[w]),
        masters=list(MASTERS),
        default=400,
        instances={300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"},
        ascent=1000,
        descent=-260,
        x_height=G.XH,
        cap_height=G.CH,
        features=features,
        out=HERE / "fonts" if default else HERE / "fonts" / "versions" / style,
        hint=None,  # a display face: set large, where hinting does nothing
    )


if __name__ == "__main__":
    tmp = HERE.parent.parent / "build"
    styles = list(G.STYLES) if "--versions" in sys.argv else [G.DEFAULT_STYLE]
    for style in sorted(styles, key=lambda s: s == G.DEFAULT_STYLE):  # the default last
        build(family(style), tmp)
