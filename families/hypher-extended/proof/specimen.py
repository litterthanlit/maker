from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
f=str(Path(__file__).parent.parent / "fonts/variable/HypherExtended[wght].ttf")
lines=[("ABCDEFGHIJKLM",400),("NOPQRSTUVWXYZ",400),("0123456789 &%",400),('.,:;!?-–—\'"‘’“”()[]/+=_',400),("Nitrous Hypher",300),("NITROUS HYPHER",700)]
img=Image.new("L",(2600,1500),245); d=ImageDraw.Draw(img); y=30
for t,w in lines:
    ft=ImageFont.truetype(f,150); ft.set_variation_by_axes([w]); d.text((40,y),t,font=ft,fill=30); y+=240
img.save(str(Path(__file__).parent / "specimen.png"))
