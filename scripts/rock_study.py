"""Study scanline-coherent rock shading before changing the live artwork."""
import sys
from pathlib import Path
from PIL import Image
from beast_art import make_rgb,asset
from dither import quantize,PALETTE,mix
root=Path(__file__).resolve().parents[1]
rock=asset('montagnes',(256,60))
out=Image.new('RGB',(256,60));pairs=[]
for y in range(60):
    pair=(3,7)
    pairs.append(pair)
    for x in range(256):
        r,g,b,alpha=rock.getpixel((x,y))
        lum=.299*r+.587*g+.114*b
        shade=max(.03,min(.8,(lum-45)/170))
        sky=.70+.22*y/59
        coverage=sky*(1-alpha/255)+shade*alpha/255
        out.putpixel((x,y),mix(PALETTE[pair[0]],PALETTE[pair[1]],coverage))
pixels,attrs=quantize(out,row_pairs=pairs,serpentine=True)
im=Image.new('RGB',(256,60))
for y in range(60):
    for x in range(256):im.putpixel((x,y),PALETTE[pairs[y][pixels[y][x]]])
im.resize((1024,240),Image.Resampling.NEAREST).save(root/'build/rock-row-study.png')
