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


TOP_MARKS = ["uni0300", "uni0301", "uni0302", "uni0303", "uni0304", "uni0306", "uni0307", "uni0308", "uni030A",
             "uni030B", "uni030C"]
BOTTOM_MARKS = ["uni0326", "uni0327"]
MARK_X = -300  # where combining marks are drawn, so unpositioned they still sit over the letter before


def anchors(wght):
    """Per base letter at this weight: (top, bottom, ogonek) anchors, in final font units."""
    p = G.P(wght, MASTERS[wght])
    out = {}
    for name in LETTERS + ["dotlessi", "dotlessj", "uni25CC"]:
        _, W, (lsb, _) = G.GLYPHS[name][1](p)
        cap = name[0].isupper()
        top = G.CH if cap else {"b": G.ASC, "d": G.ASC, "h": G.ASC, "k": G.ASC, "l": G.ASC,
                                "f": G.XH * G.lm("f_top", 1.40), "t": G.XH * G.lm("t_top", 1.273)}.get(name, G.XH)
        cx = lsb + (W * 0.3 if name == "L" else W / 2)
        og = G.OGONEK_AT.get(name, lambda p, W: W - p.V / 2)(p, W) + lsb
        out[name] = ((round(cx), round(top)), (round(lsb + W / 2), 0), (round(og), 0))
    # accented letters take a second accent above the one they carry, or below it
    kinds = {f"uni{ord(ch):04X}": kind for base, marks in G.ACCENTS.items() for ch, kind in marks}
    for name, base in G.BASE.items():
        if base not in out:
            continue
        (tx, ty), bottom, og = out[base]
        kind = kinds.get(name)
        if kind and kind not in G.BELOW and kind != "caronv":
            h = G.mark(p, kind, base[0].isupper())[1]
            lift = (G.CH * 0.06) if base[0].isupper() else (G.XH * 0.13)
            ty = round(ty + lift + h)
        out[name] = ((tx, ty), bottom, og)
    return out


def features(wght):
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;"]
    # i and j lose their dot under an accent typed after them (soft dotted)
    lines += [f"@TOP_MARKS = [{' '.join(TOP_MARKS)}];", f"@BELOW = [{' '.join(BOTTOM_MARKS)} uni0328];",
              "feature ccmp {", "  lookup soft_dotted {",
              "    sub i' @TOP_MARKS by dotlessi;", "    sub j' @TOP_MARKS by dotlessj;",
              "    sub i' @BELOW @TOP_MARKS by dotlessi;", "    sub j' @BELOW @TOP_MARKS by dotlessj;",
              "    sub uni012F' @TOP_MARKS by uni012F.dotless;", "    sub uni012F' @BELOW @TOP_MARKS by uni012F.dotless;",
              "  } soft_dotted;", "} ccmp;"]
    lines.append("feature kern {")
    lines += [f"  pos {l} {r} {v};" for (l, r), v in sorted(kern_pairs().items()) if l in G.GLYPHS and r in G.GLYPHS]
    lines.append("} kern;")
    # accents typed after a letter attach to it
    lines += [f"markClass [{' '.join(TOP_MARKS)}] <anchor {MARK_X} {G.XH}> @TOP;",
              f"markClass [{' '.join(BOTTOM_MARKS)}] <anchor {MARK_X} 0> @BOTTOM;",
              f"markClass [uni0328] <anchor {MARK_X} 0> @OGONEK;", "feature mark {"]
    for name, ((tx, ty), (bx, by), (ox, oy)) in anchors(wght).items():
        lines.append(f"  pos base {name} <anchor {tx} {ty}> mark @TOP <anchor {bx} {by}> mark @BOTTOM <anchor {ox} {oy}> mark @OGONEK;")
    lines.append("} mark;")
    return "\n".join(lines)


def family(style):
    """The Family for one version; the default version is plain Hypher Display."""
    G.set_style(style)
    default = style == G.DEFAULT_STYLE
    return Family(
        name="Hypher Display" if default else f"Hypher Display {G.LABELS.get(style, style)}",
        file="HypherDisplay" if default else f"HypherDisplay{style}",
        version="0.610",
        copyright="Copyright 2026 The Hypher Display Project Authors (https://github.com/litterthanlit/maker)",
        description="Display face for the Hypher wordmark. Proportions and kerning measured from Michroma (OFL).",
        fs_type=0,  # installable: an open font sets no embedding restrictions
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
        code_pages=(0, 1, 4),  # Latin 1, Latin 2 (Central Europe), Turkish: what Latin Core covers
        windows_names_only=True,
        smart_dropout=True,
        win_all_masters=True,
        meta_scripts="Latn",
    )


if __name__ == "__main__":
    tmp = HERE.parent.parent / "build"
    styles = list(G.STYLES) if "--versions" in sys.argv else [G.DEFAULT_STYLE]
    for style in sorted(styles, key=lambda s: s == G.DEFAULT_STYLE):  # the default last
        build(family(style), tmp)
