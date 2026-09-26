"""Verify a lossless runner shift and compare all six poses against rev10."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
from dither import PALETTE
r=Path(__file__).resolve().parents[1]
old=json.loads((r/'revisions/rev10/build/beast-art.json').read_text());new=json.loads((r/'build/beast-art.json').read_text())
assert old['bands']==new['bands'],'Background graphics/palettes must remain identical'
for a,b in zip(old['sprites'],new['sprites']):
    assert a['attrs']==b['attrs']
    for y in range(40):
        assert all(a['mask'][y][27:])
        assert b['mask'][y]==[1]*5+a['mask'][y][:27]
        for x in range(27):
            if not a['mask'][y][x]:assert a['pixels'][y][x]==b['pixels'][y][x+5]
def spill(art):
    return sum(7-max(x for x,v in enumerate(row) if not v)%8 for s in art['sprites'] for row in s['mask'][:32] if 0 in row)
before,after=spill(old),spill(new);assert after<before
im=Image.new('RGB',(1008,360),(18,15,24));d=ImageDraw.Draw(im)
for variant,(art,x0,label) in enumerate([(old,112,'REV10 / original'),(new,104,'REV14 / shifted 3 pixels left; unchanged palette')]):
    d.text((8,variant*180+5),label,fill='white')
    for i,s in enumerate(art['sprites']):
        view=Image.new('RGB',(56,48))
        for y in range(48):
            sy=116+y;band=next(b for b in art['bands'] if b['y']<=sy<b['y']+b['height']);p=band['phases'][0];yy=sy-band['y']
            for x in range(56):
                sx=96+x;bit=p['pixels'][yy][sx];a=p['attrs'][yy][sx//8]
                if 120<=sy<160 and x0<=sx<x0+32:
                    ry=sy-120;rx=sx-x0;c=rx//8
                    if not s['mask'][ry][rx]:bit=s['pixels'][ry][rx]
                    if not all(s['mask'][ry][c*8:c*8+8]):a=s['attrs'][ry][c]
                view.putpixel((x,y),PALETTE[((a&7) if bit else (a>>3)&7)+(8 if a&64 else 0)])
        im.paste(view.resize((168,144),Image.Resampling.NEAREST),(i*168,variant*180+27))
im.save(r/'build/runner-alignment-comparison.png')
report={'backgroundIdentical':True,'visibleSpritePixelsPreserved':True,'screenShiftPixels':-3,'rightEdgeExposedPixelsAcrossSixPoses':{'before':before,'after':after},'reductionPercent':round(100*(before-after)/before,2),'scope':'Upper 32 sprite rows against rocks; geometric exposure, not a claim of zero clash','dck_sha256':json.loads((r/'build/manifest.json').read_text())['sha256']['dck']}
(r/'build/alignment-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
