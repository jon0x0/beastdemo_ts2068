"""Preview actual emulator display RAM, not an unconstrained RGB mockup."""
from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def render(raw):
    im=Image.new('RGB',(256,192));pixels=[]
    for y in range(192):
        base=((y&192)<<5)+((y&7)<<8)+((y&56)<<2)
        for x in range(256):
            i=base+x//8;a=raw[6144+i]
            c=(a&7) if raw[i]&(128>>(x&7)) else ((a>>3)&7)
            v=255 if a&64 else 205
            pixels.append((v if c&2 else 0,v if c&4 else 0,v if c&1 else 0))
    im.putdata(pixels);return im
if __name__=='__main__':
    manifest=json.loads((ROOT/'build/manifest.json').read_text());tag=manifest['tag']
    for n in [0,64,192]:
        render((ROOT/f'build/emulator_frame{n}.bin').read_bytes()).resize((768,576),Image.Resampling.NEAREST).save(ROOT/f'build/{tag}_frame{n}.png')
    data=(ROOT/'build/emulator-animation.bin').read_bytes()
    frames=[render(data[i:i+12288]).resize((512,384),Image.Resampling.NEAREST) for i in range(0,len(data),12288)]
    times=json.loads((ROOT/'build/preview-times.json').read_text())
    durations=[];elapsed=0;rounded=0
    for i in range(len(frames)):
        elapsed+=(times[i+1]-times[i] if i+1<len(times) else 58688*2.5)*1000/(58688*60)
        next_rounded=round(elapsed/10)*10
        durations.append(max(10,next_rounded-rounded));rounded=next_rounded
    frames[0].save(ROOT/f'build/{tag}.gif',save_all=True,append_images=frames[1:256],duration=durations[:256],loop=0)
    frames[256].save(ROOT/f'build/{tag}_controls.gif',save_all=True,append_images=frames[257:],duration=durations[256:],loop=0)
    print('Rendered',len(frames),'emulator frames')
