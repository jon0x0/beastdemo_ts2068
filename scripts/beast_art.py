"""Resize the supplied reference assets and encode legal TS2068 8x1 cells.

Source assets are pinned in references/beast; see THIRD_PARTY.md.
"""
from pathlib import Path
from PIL import Image, ImageEnhance
from dither import quantize, gradient, PALETTE, mix

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references/beast'
# Each band is a separate scroll plane. Negative shift means wind-driven.
BANDS = [('cloud0',0,20,-1),('cloud1',20,32,-2),
         ('cloud2',58,18,-3),('cloud3',76,8,-4),('cloud4',84,8,-5),
         ('hill',92,60,0),('grass0',152,4,1),('grass1',156,4,2),
         ('grass2',160,4,3),('grass3',164,6,4),
         ('fence',170,14,5),('grass4',184,8,6),('sky_gap',52,6,0)]

def asset(name, size):
    return Image.open(REF / (name+'.png')).convert('RGBA').resize(size, Image.Resampling.LANCZOS)

def make_rgb():
    sky=Image.new('RGB',(256,192))
    for y in range(192):
        c=gradient([(0,(92,55,125)),(48,(177,110,160)),(92,(224,150,178)),(151,(241,169,184)),(191,(55,75,16))],y)
        for x in range(256):sky.putpixel((x,y),c)
    bands=[]
    for name,y,h,rate in BANDS:
        im=sky.crop((0,y,256,y+h)).convert('RGBA')
        if name=='sky_gap':
            bands.append(im.convert('RGB'));continue
        if name.startswith('cloud'):
            overlay=asset('nuages'+name[-1],(256,h))
        elif name=='hill':
            overlay=asset('montagnes',(256,h))
        else:
            idx=int(name[-1]) if name.startswith('grass') else 4
            im=Image.new('RGBA',(256,h),(49,62,9,255))
            overlay=asset('herbe'+str(idx),(256,h))
        im.alpha_composite(overlay)
        if name.startswith('grass') or name=='fence':
            im=ImageEnhance.Brightness(im).enhance(1.7)
        if name=='fence':
            fence=asset('barriere',(256,h))
            lit=ImageEnhance.Brightness(fence.convert('RGB')).enhance(2.3)
            lit.putalpha(fence.getchannel('A'))
            im.alpha_composite(lit)
        bands.append(im.convert('RGB'))
    sheet=Image.open(REF/'aarbonRun.png').convert('RGBA')
    sprites=[]
    for i in range(6):
        frame=sheet.crop((i*78,0,(i+1)*78,100)).resize((32,40),Image.Resampling.LANCZOS)
        # Sharper, brighter body survives the small ECM conversion.
        rgb=ImageEnhance.Brightness(frame.convert('RGB')).enhance(1.35)
        rgb.putalpha(frame.getchannel('A'))
        sprites.append(rgb)
    return bands,sprites

def encode():
    bands,sprites=make_rgb(); encoded=[]
    for spec,im in zip(BANDS,bands):
        name=spec[0]
        if name=='hill':
            # A common palette across each complete scanline removes 8-pixel
            # hue decisions at the silhouette. A consistent scanline pair gives
            # the shaded rock a consistent rose tone against pale pink sky.
            rock=asset('montagnes',im.size)
            pairs=[(3,7)]*im.height
            for y in range(im.height):
                paper,ink=[PALETTE[c] for c in pairs[y]]
                for x in range(256):
                    r,g,b,alpha=rock.getpixel((x,y))
                    lum=.299*r+.587*g+.114*b
                    shade=max(.03,min(.8,(lum-45)/170))
                    sky=.70+.22*y/(im.height-1)
                    coverage=sky*(1-alpha/255)+shade*alpha/255
                    im.putpixel((x,y),mix(paper,ink,coverage))
        elif name.startswith('grass'):
            from collections import Counter
            _, fitted=quantize(im,allowed_pairs=[(0,4),(0,6),(4,6),(0,7)],serpentine=True)
            colors=[Counter(row).most_common(1)[0][0] for row in fitted]
            pairs=[((a>>3)&7,a&7) for a in colors]
        elif name=='fence':pairs=[(0,7)]*im.height
        else:pairs=[(1,7) if name=='cloud0' else (3,7)]*im.height
        pixels,attrs=quantize(im,row_pairs=pairs,serpentine=True)
        phases=[]
        step=1 if spec[0]=='hill' else 2
        for p in range(8//step):
            offset=p*step
            # Shift the already-dithered artwork; do not re-quantize each phase.
            if name=='hill' or name.startswith('grass') or name=='fence':
                phases.append(dict(pixels=[r[offset:]+r[:offset] for r in pixels],attrs=attrs))
            else:
                # Preserve the accepted non-rock artwork and its per-cell colors.
                original=bands[BANDS.index(spec)]
                shifted=Image.new('RGB',original.size)
                shifted.paste(original.crop((offset,0,256,original.height)),(0,0))
                if offset:shifted.paste(original.crop((0,0,offset,original.height)),(256-offset,0))
                candidates=[(0,3),(3,7),(1,7),(0,7)] if name.startswith('cloud') or name=='sky_gap' else [(0,4),(0,6),(4,6),(0,7)]
                def preserve_hue(samples,choices):
                    if name.startswith('cloud') or name=='sky_gap':
                        r,g,b=[sum(c[k] for c in samples)/len(samples) for k in range(3)]
                        return [(0,3),(3,7)] if r>g*1.15 and b>g*1.15 else [(0,7)]
                    return choices
                bp,ba=quantize(shifted,allowed_pairs=candidates,serpentine=True,pair_filter=preserve_hue)
                phases.append(dict(pixels=bp,attrs=ba))
        encoded.append(dict(name=spec[0],y=spec[1],height=spec[2],rate=spec[3],phase_step=step,phases=phases))
        print('Encoded',spec[0],flush=True)
    frames=[]
    for im in sprites:
        # Transparent cells retain the scenery. Body cells use per-cell ECM pairs.
        rgb=Image.new('RGB',im.size,(20,15,25));rgb.paste(im,mask=im.getchannel('A'))
        pixels,attrs=quantize(rgb,allowed_pairs=[(1,7)],serpentine=True)
        mask=[[int(im.getpixel((x,y))[3]<100) for x in range(32)] for y in range(40)]
        frames.append(dict(pixels=pixels,attrs=attrs,mask=mask))
    return dict(bands=encoded,sprites=frames)
