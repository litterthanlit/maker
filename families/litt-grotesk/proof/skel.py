"""Draw a glyph's outline (grey) with its pen skeleton (red) to an SVG, for tuning.
    python3 families/litt-grotesk/proof/skel.py S 400 out.svg"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core import geometry
captured = []
_orig = geometry.pen
def spy(sk, *a, **k):
    captured.append(sk); return _orig(sk, *a, **k)
geometry.pen = spy
import glyphs as G, penglyphs
penglyphs.pen = spy
import extended  # noqa
name, wght, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
p = G.P(wght, {300: 46, 400: 84, 700: 140}.get(wght, 84))
c, ink, sb = G.GLYPHS[name][1](p)
def path(con):
    d = f"M{con[0][0]:.1f},{-con[0][1]:.1f}"
    for s in con[1:]:
        if s[0] == "l": d += f"L{s[1][0]:.1f},{-s[1][1]:.1f}"
        else: d += "C" + " ".join(f"{q[0]:.1f},{-q[1]:.1f}" for q in s[1:])
    return d + "Z"
sk = "".join(f'<path d="M{c[0][0]:.1f},{-c[0][1]:.1f}C{c[1][0]:.1f},{-c[1][1]:.1f} {c[2][0]:.1f},{-c[2][1]:.1f} {c[3][0]:.1f},{-c[3][1]:.1f}" fill="none" stroke="red" stroke-width="4"/>'
             f'<circle cx="{c[0][0]:.1f}" cy="{-c[0][1]:.1f}" r="9" fill="red"/>' for s in captured for c in s)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-60 {-1000} {ink+120} 1300" width="{(ink+120)/2.2:.0f}" height="590">
<rect x="-60" y="-1000" width="{ink+120}" height="1300" fill="#fff"/>
<line x1="-60" x2="{ink+60}" y1="0" y2="0" stroke="#9cf"/><line x1="-60" x2="{ink+60}" y1="-720" y2="-720" stroke="#9cf"/><line x1="-60" x2="{ink+60}" y1="-540" y2="-540" stroke="#9cf"/>
<path d="{''.join(path(x) for x in c)}" fill="#ccc" fill-rule="nonzero"/>{sk}</svg>'''
open(out, "w").write(svg)
