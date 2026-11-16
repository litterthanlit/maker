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
import kerning as K  # noqa: E402

# weight -> lowercase stem width; everything else derives from it.
MASTERS = {300: 60, 400: 92, 700: 150}


LETTERS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
QUOTES = ["quoteright", "quotedblright", "quoteleft", "quotedblleft", "quotesingle", "quotedbl"]
KERN_GLYPHS = LETTERS + ["period", "comma", "hyphen"] + QUOTES
OVERHANG = list("AFLPTVWYr")  # letters that leave room for punctuation beside them, by convention


def auto_candidates():
    """Letters kern with letters; punctuation only beside the letters that overhang it."""
    out = [(l, r) for l in LETTERS for r in LETTERS]
    out += [(l, p) for l in OVERHANG for p in ["period", "comma", "hyphen"] + QUOTES]
    out += [(p, r) for r in "ATVWYJ" for p in ["hyphen"] + QUOTES]
    return out


def kern_pairs():
    """Every kerning pair for the current version, accented letters kerning like their base."""
    if G.STYLE.get("kerning") == "auto":  # measured from this version's own outlines
        import autokern
        pairs = autokern.pairs(
            {n: f for n, (_, f) in G.GLYPHS.items()}, G.P(400, MASTERS[400]), None, depth=0.35 * G.XH,
            refs={"left": {"S": "n", "R": "o", "T": "f", "D": "v", "F": "z"},
                  "right": {"S": "n", "R": "o", "T": "c", "D": "v", "F": "z"}},
            types=G.STYLE["types"], candidates=auto_candidates())
        pairs = {k: round(v * 0.8) for k, v in pairs.items() if v * 0.8 <= -10}  # measured space over-closes; soften
    else:
        scale = G.STYLE.get("kern_scale", 1.0 if G.STYLE["name"] == "Wordmark" else 0.92)
        pairs = {k: round(v * scale) for k, v in K.PAIRS.items()}
    pairs.update({(l, r): v for l, r, v in G.STYLE["kern"]})
    family = {}  # base glyph -> itself and its accented forms
    for name in G.GLYPHS:
        family.setdefault(G.BASE.get(name, name), []).append(name)
    out = {}
    for (l, r), v in pairs.items():
        for ll in family.get(l, [l]):
            for rr in family.get(r, [r]):
                out[(ll, rr)] = v
    return out


def features(wght):
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "feature kern {"]
    lines += [f"  pos {l} {r} {v};" for (l, r), v in sorted(kern_pairs().items()) if l in G.GLYPHS and r in G.GLYPHS]
    lines.append("} kern;")
    return "\n".join(lines)


def family(style):
    """The Family for one version; the default version is plain Hypher Display."""
    G.set_style(style)
    default = style == G.DEFAULT_STYLE
    return Family(
        name="Hypher Display" if default else f"Hypher Display {G.LABELS.get(style, style)}",
        file="HypherDisplay" if default else f"HypherDisplay{style}",
        version="0.560",
        copyright="Copyright 2026 The Hypher Project Authors; proportions and kerning after Michroma, Copyright 2011 The Michroma Project Authors",
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
