"""Rev 05: gradient sky, moving mountains, palms, calm water, and speedboat."""
import math,random
from PIL import Image,ImageDraw,ImageFont
from dither import PALETTE,mix,quantize,quantize_rgb,gradient

def bits(im):return [[int(im.getpixel((x,y))) for x in range(im.width)] for y in range(im.height)]
def make_art():
    # Sky and mountain pixels are immutable. Moving objects never carry them.
    base=Image.new('RGB',(256,152));d=ImageDraw.Draw(base)
    pairs=[]
    for y in range(152):
        if y<40: pair=(1,7)
        elif y<62: pair=(1,3)
        elif y<82: pair=(1,3)
        elif y<104: pair=(1,5)
        else:pair=(1,7) if y<117 or y>=137 else (1,5)
        pairs.append(pair)
        p,q=[PALETTE[c] for c in pair]
        coverage=.025+.065*y/40 if y<40 else .62 if y<82 else .26 if y<104 else .26
        for x in range(256):
            color=mix(p,q,coverage)
            if 32<=y<104:color=mix((67,34,119),(213,126,156),min(1,(y-32)/55))
            base.putpixel((x,y),color)
    # Warm sun lies below the moving-cloud zone and stays anchored to the sky.
    for y in range(34,62):
        half=int(math.sqrt(max(0,14**2-(y-48)**2)))
        if y<53 or y%3:
            d.line((199-half,y,199+half,y),fill=(242,151,126))
    # A single asymmetric, screen-wide range, with foothills in the same view.
    ridge=[(0,89),(23,77),(43,84),(79,52),(101,65),(121,86),(151,67),(181,88),(213,61),(237,77),(256,87)]
    crest=[];slope=[]
    for x in range(256):
        for (x0,y0),(x1,y1) in zip(ridge,ridge[1:]):
            if x0<=x<x1:
                t=(x-x0)/(x1-x0);crest.append(y0+(y1-y0)*t+math.sin(t*math.pi)*(.6*math.sin(x*1.2)+.6*math.sin(x*.46)))
                slope.append((y1-y0)/(x1-x0));break
    for y in range(48,152):
        p,q=[PALETTE[c] for c in pairs[y]]
        for x in range(256):
            if y>=crest[x]:
                if y<104:
                    depth=(y-crest[x])/max(1,104-crest[x])
                    coverage=.32-.21*slope[x]-.09*depth+.045*math.sin(x*.77+y*.53)
                    coverage-=.12*max(0,math.sin(x*.14+y*.21))**6
                    if y-crest[x]<1.7:coverage+=.28
                else:
                    # Light valley mist makes dark passing branches readable.
                    coverage=.42+.055*math.sin(x*.026+y*.10)
                coverage=max(.08,min(.8,coverage))
                color=mix(p,q,coverage)
                if y<104:
                    color=mix((16,27,74),(133,166,180),coverage)
                    # Blend continuously into cooler foothills, never split
                    # the ridge into two horizontal color/motion bands.
                    haze=max(0,(y-78)/40)
                    color=mix(color,(33,101,111),haze)
                base.putpixel((x,y),color)
    background,attrs=quantize(base,pairs)
    # The whole distant view is fixed, so it can use full per-cell ECM colors.
    # This paints one ridge against a continuous sky, without broad color bands.
    landscape,landattrs=quantize(base.crop((0,32,256,104)))
    background[32:104]=landscape;attrs[32:104]=landattrs
    # Rev 04 replaces the fixed ridge with an independently masked slow layer.
    # Row palettes are shared with a stationary dusk gradient at its edge.
    mountain=[];mountmask=[]
    mountain_rgb=Image.new('RGB',(128,32));sky_rgb=Image.new('RGB',(256,32))
    mountain_pairs=[]
    knots=[(0,25),(17,17),(37,1),(63,26),(92,8),(111,20),(128,25)]
    for y in range(32):
        pair=(1,7) if y<14 else (1,5) if y<25 else (0,4)
        mountain_pairs.append(pair);p,q=[PALETTE[c] for c in pair]
        for x in range(256):sky_rgb.putpixel((x,y),mix(p,q,.68-y*.008))
        mr=[]
        for x in range(128):
            for (x0,y0),(x1,y1) in zip(knots,knots[1:]):
                if x0<=x<x1:crest=y0+(y1-y0)*(x-x0)/(x1-x0);slope=(y1-y0)/(x1-x0);break
            opaque=y>=crest;mr.append(int(not opaque))
            light=max(.10,min(.82,.40-.24*slope+.08*math.sin(x*.61+y*.51)))
            if y-crest<2:light=min(.95,light+.2)
            mountain_rgb.putpixel((x,y),mix(p,q,light if opaque else 0))
        mountmask.append(mr)
    mountain,_=quantize(mountain_rgb,mountain_pairs)
    mountain=[[p if not mountmask[y][x] else 0 for x,p in enumerate(row)] for y,row in enumerate(mountain)]
    skybits,skyattrs=quantize(sky_rgb,mountain_pairs)
    background[72:104]=skybits;attrs[72:104]=skyattrs
    # Continuous RGB sunset, globally error-diffused across ECM cells.
    sky=Image.new('RGB',(256,72))
    for y in range(72):
        for x in range(256):
            color=gradient([(0,(100,120,205)),(32,(145,155,205)),(50,(189,170,190)),(71,(220,185,155))],y)
            glow=math.exp(-((x-199)/52)**2-((y-57)/23)**2)*.23
            sky.putpixel((x,y),mix(color,(239,190,139),glow))
    ImageDraw.Draw(sky).ellipse((187,43,211,67),fill=(238,208,155))
    # Adjacent white-based pairs avoid neon complementary-color speckling.
    # Cloud rows retain white ink, while diffusion continues through the sky.
    skybits,skyattrs=quantize_rgb(sky,[(1,7)]*32+[None]*40,[(p,7) for p in [0,1,2,3,5,6]])
    background[:72]=skybits;attrs[:72]=skyattrs
    # 24 scanlines of cloud-only coverage, periodic over 128 pixels.
    # OR compositing adds light without moving or replacing sky texture.
    cloud_rgb=Image.new('RGB',(128,24));coverage=[]
    for y in range(24):
        row=[]
        for x in range(128):
            density=0
            for cx,cy,sx,sy in [(24,8,18,4),(85,17,25,4.5)]:
                for wrap in [-128,0,128]:
                    for dx,dy,scale in [(-9,1,.7),(0,-1,.95),(12,1,.7)]:
                        v=math.exp(-((x-(cx+wrap+dx))/(sx*scale))**2-((y-(cy+dy))/(sy*scale))**2)
                        if v>.28:density=max(density,min(1,(v-.28)*2))
            row.append(density)
            cloud_rgb.putpixel((x,y),(int(density*205),)*3)
        coverage.append(row)
    clouds,_=quantize(cloud_rgb,[(0,7)]*24)
    # Remove diffusion spill outside the actual cloud footprint.
    clouds=[[p if coverage[y][x]>0 else 0 for x,p in enumerate(row)] for y,row in enumerate(clouds)]
    # Forest silhouettes, with distinct trunks, crowns, and gaps. These are
    # foreground objects, not complete scrolling pictures of a background.
    tree=Image.new('1',(128,32));td=ImageDraw.Draw(tree)
    for cx,top,lean in [(19,5,5),(60,1,-5),(101,10,4)]:
        td.line([(cx-lean,31),(cx-lean//2,18),(cx,top+3)],fill=1,width=2)
        for dx,dy in [(-16,6),(-13,0),(-8,-3),(7,-3),(14,0),(17,7),(-9,11),(10,12)]:
            td.line([(cx,top+3),(cx+dx//2,top+dy//3),(cx+dx,top+dy)],fill=1,width=2)
            td.line((cx+dx//2,top+dy//3,cx+dx//2-2,top+dy//3+4),fill=1)
    trees=bits(tree)
    aq=[];mask=[]
    for y in range(48):
        row=[];mr=[]
        for x in range(64):
            dx=x-32
            opening=(y>=23 and abs(dx)<20) or (y>=9 and ((dx/20)**2+((y-23)/15)**2)<1)
            opaque=not opening or y>=44
            mortar=(y in (1,6,43,46)) or (y%7==0 and x%16<14) or ((x+(8 if (y//7)%2 else 0))%16==0)
            rim=opaque and 8<y<25 and abs((dx/23)**2+((y-23)/18)**2-1)<.19
            row.append(int(opaque and (not mortar or rim)));mr.append(int(not opaque))
        aq.append(row);mask.append(mr)
    # Fine horizontal ripples scroll left at twice the aqueduct rate.
    # Sixteen distinct rows repeat vertically; the period is 64 pixels.
    water=[]
    for y in range(16):
        row=[]
        for x in range(64):
            wave=math.sin(x*math.pi/16+y*2.19)+.48*math.sin(x*math.pi/4-y*1.7)
            row.append(int(wave>1.04 and ((x//3+y*5)%7)!=0))
        water.append(row)
    water=water*2
    waterattrs=[[13]*32 for _ in range(32)]
    # Side-profile 32-pixel hull faces right; 24 pixels behind it hold spray.
    # -1 is transparent. Four poses: parked plus three running spray frames.
    boats=[]
    for phase in range(4):
        sprite=Image.new('L',(56,14),255);bd=ImageDraw.Draw(sprite)
        bd.polygon([(24,6),(40,6),(49,5),(55,6),(50,10),(29,10),(25,8)],fill=1)
        bd.line((29,11,47,11),fill=1)
        bd.polygon([(33,5),(36,2),(42,2),(47,5)],fill=1)
        bd.polygon([(37,3),(41,3),(44,5),(35,5)],fill=0)
        bd.line((30,8,48,8),fill=0)
        bd.rectangle((25,5,28,6),fill=0)
        if phase:
            # Separate falling droplets and foam pulses: no solid triangular wake.
            for n in range(23):
                age=(n*7+(phase-1)*5)%23
                x=23-age;y=8-int(4*math.sin(age*math.pi/28))+(n%3)
                bd.line((x,y,x+(1 if n%3 else 2),y),fill=1)
            for n in range(8):
                x=(n*7+(phase-1)*3)%24
                bd.point((x,11+(n%3)),fill=1)
        boats.append([[(-1 if sprite.getpixel((x,y))==255 else sprite.getpixel((x,y))) for x in range(56)] for y in range(14)])
    hud=Image.new('1',(256,8));ImageDraw.Draw(hud).text((3,-2),'Q/A UP/DOWN  O/P SPEED   REV05',font=ImageFont.load_default(size=8),fill=1)
    return dict(background=background,mountain=mountain,mountmask=mountmask,boats=boats,clouds=clouds,trees=trees,aqueduct=aq,mask=mask,water=water,hud=bits(hud),attrs=attrs+waterattrs+[[69]*32 for _ in range(8)])
