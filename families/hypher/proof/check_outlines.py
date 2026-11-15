"""List every glyph whose offset outline crosses itself, at each master.

    python3 families/hypher/proof/check_outlines.py

Michroma's own contours don't overlap, so a clean glyph's signed area equals
the area of its outline with overlaps removed. Less area means a loop runs
backwards (a bowtie), which renders as a notch or a stray tick: that fails.
More area means the outline covers some ink twice, as Bold's arches do where
they run into their stems; that fills the same pixels, but a hook outside the
letter shows up the same way, so those are listed for a look at lockup.html.
Exit status 1 if any glyph fails.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent.parent / "src"))
sys.path.insert(0, str(HERE))

import pathops  # noqa: E402

import build  # noqa: E402
import glyphs as G  # noqa: E402


def to_path(contours):
    p = pathops.Path()
    pen = p.getPen()
    for c in contours:
        pen.moveTo(c[0])
        for seg in c[1:]:
            if seg[0] == "l":
                pen.lineTo(seg[1])
            else:
                pen.curveTo(*seg[1:])
        pen.closePath()
    return p


def signed(contours):
    total = 0
    for c in contours:
        p = to_path([c])
        total += p.area if not p.clockwise else -p.area
    return total


bad = []
for w, stem in build.MASTERS.items():
    params = G.P(w, stem)
    for name, (char, fn) in G.GLYPHS.items():
        contours = fn(params)[0]
        if not contours:
            continue
        clean = to_path(contours)
        clean.simplify(fix_winding=True)
        if abs(abs(signed(contours)) - clean.area) > 1:
            bad.append((w, name, round(abs(signed(contours)) - clean.area)))

fail = [b for b in bad if b[2] < 0]
for w, name, delta in bad:
    print(f"{w} {name}: {'reversed loop' if delta < 0 else 'overlap'}, {abs(delta)} units²")
print(f"{len(fail)} reversed loops, {len(bad) - len(fail)} overlaps in {len(G.GLYPHS) * len(build.MASTERS)} glyph-masters")
sys.exit(1 if fail else 0)
