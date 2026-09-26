"""Build rev14: buffered parallax with the supplied native AY title driver."""
from pathlib import Path
import hashlib,json,subprocess,sys,struct
from beast_art import encode
from align_runner import align_runner
from music import extract
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True)
rom=bytearray([255])*65536
slots=[(0x100,0x2000),(0x2000,0x4000),(0xa000,0xc000),(0xc000,0xe000),(0xe000,0x10000),(0x4000,0x6000),(0x6000,0x8000)]
slot=0;cursor=slots[0][0];cache={}
def put(data):
    global slot,cursor
    data=bytes(data)
    if data in cache:return cache[data]
    if cursor+len(data)>slots[slot][1]:
        slot+=1
        if slot==len(slots):raise ValueError('Cartridge asset capacity exceeded')
        cursor=slots[slot][0]
    a=cursor;rom[a:a+len(data)]=data;cursor+=len(data);cache[data]=a;return a
def screen(y):return 0x4000+((y&192)<<5)+((y&7)<<8)+((y&56)<<2)
def packed(row):return bytes(sum(row[x+b]<<(7-b) for b in range(8)) for x in range(0,len(row),8))
def visible(a):return a+0x6000 if 0x4000<=a<0x6000 else a+0x8000 if 0x6000<=a<0x8000 else a
def bank(a):return 0x53 if 0x4000<=a<0x8000 else 0xf3
artpath=BUILD/'beast-art.json'
art=json.loads(artpath.read_text()) if '--reuse-art' in sys.argv else encode()
art=align_runner(art)
artpath.write_text(json.dumps(art,separators=(',',':')))
assert len(next(b for b in art['bands'] if b['name']=='hill')['phases'])==8
# Hill descriptors live in always-visible chunk 0; the remaining tables fit
# in the code chunk. Reserve before art allocation; never deduplicate this table.
hill_table=cursor;cursor+=60*8*3
assert cursor<=0x2000
music,music_meta=extract()
lines=[]
row_colors=[0]*192
for band in art['bands']:
    name=band['name'];height=band['height'];y0=band['y']
    fast=name=='hill'
    fixed=[]
    for r,attrs in enumerate(band['phases'][0]['attrs']):
        row_colors[y0+r]=attrs[0]
        fixed.append(len(set(attrs))==1 and all(ph['attrs'][r]==attrs for ph in band['phases']))
    lines += [name+'_phases:','dw '+','.join(name+'_phase_'+str(p) for p in range(len(band['phases'])))]
    for p,phase in enumerate(band['phases']):
        lines += [name+'_phase_'+str(p)+(f' equ {hill_table+p*60*3}' if name=='hill' else ':')]
        for r,(row,attrs) in enumerate(zip(phase['pixels'],phase['attrs'])):
            raw=packed(row)
            lookahead=fast and r<28
            a=put(raw+raw[:31] if lookahead else raw)
            descriptor=struct.pack('<HB',visible(a),bank(a))
            if name!='hill':
                at=put(attrs)
                descriptor+=struct.pack('<HB',visible(at),bank(at))
            if name=='hill':
                start=hill_table+(p*60+r)*3;rom[start:start+3]=descriptor
            else:lines += ['db '+','.join(map(str,descriptor))]
    if name!='hill':
        lines += ['draw_'+name+':']
        for y in range(y0,y0+height):
            if 120<=y<160:
                assert fixed[y-y0]
                lines += [f'ld hl,{0x5800+(y-120)*32+13}','ld (DEST),hl',f'ld de,{screen(y)}','call mixed_fixed_scanline']
            else:lines += [f'ld de,{screen(y)}','call '+('fixed_scanline' if fixed[y-y0] else 'color_scanline')]
        lines += ['ret']
    if name=='hill':
        lines += ['draw_hill_upper:']
        for y in range(92,120):lines += [f'ld de,{screen(y)}','call scanline']
        lines += ['ret','draw_hill_buffer:','ld de,84','add ix,de']
        for y in range(120,152):lines += [f'ld hl,{0x5800+(y-120)*32+13}','ld (DEST),hl',f'ld de,{screen(y)}','call mixed_scanline']
        lines += ['ret']
lines += ['sprite_frames:']
for frame in art['sprites']:
    data=[]
    for pixels,mask,attrs in zip(frame['pixels'],frame['mask'],frame['attrs']):
        for p,m,a in zip(packed(pixels),packed(mask),attrs):data += [m,p&(~m&255)]
    for y,(mask,attrs) in enumerate(zip(frame['mask'],frame['attrs'])):
        data += [a if m!=255 else row_colors[120+y] for m,a in zip(packed(mask),attrs)]
    a=put(data);lines += [f'dw {visible(a)}',f'db {bank(a)}']
music_address=put(music)
assert 0x6000<=music_address and music_address+len(music)<=0x8000
lines += [f'music_source equ {visible(music_address)}',f'music_size equ {len(music)}',f"music_length equ {music_meta['length_ticks']}"]
lines += ['publish:','ld a,(FRAME)','and 1','jp nz,publish_rocks']
for y in range(120,160):
    lines += [f'ld hl,{0x5800+(y-120)*32+13}',f'ld de,{screen(y)+13}','call copy4']
    lines += [f'ld hl,{0x7800+(y-120)*32+13}',f'ld de,{screen(y)+0x2000+13}','call copy4']
lines += ['ret']
lines += ['row_colors:','db '+','.join(map(str,row_colors))]
lines += ['publish_rocks:']
for y in range(120,152):
    lines += [f'ld hl,{0x5800+(y-120)*32+13}',f'ld de,{screen(y)+13}','call copy4']
lines += ['ret']
lines += ['mixed_patches:','dw '+','.join(str(0x5fd1 if c==0 else 0x5f80+(32-c)*2+(8 if 32-c>=13 else 0)+(8 if 32-c>=17 else 0)) for c in range(32))]
(ROOT/'src/generated.inc').write_text('\n'.join(lines)+'\n')
cells=[]
for i in range(4):
    cells += ['ld a,(hl)','inc hl','cp 255',f'jr z,runner_transparent_{i}','ld b,a','ld a,(de)','and b','or (hl)','inc hl','ld (de),a',
              f'jr runner_cell_done_{i}',f'runner_transparent_{i}:','inc hl',f'runner_cell_done_{i}:','inc de']
(ROOT/'src/runner_cells.inc').write_text('\n'.join(cells)+'\n')
subprocess.run(['wsl','bash','scripts/build.sh'],cwd=ROOT,check=True)
code=(BUILD/'code.bin').read_bytes();assert len(code)<=8192,len(code)
rom[0x8000:0x8000+len(code)]=code
symbols={n:int(v.rstrip('H'),16) for n,_,v in (line.split() for line in (BUILD/'symbols.txt').read_text().splitlines())}
assert symbols['mixed_end']-symbols['mixed_image']==81
assert symbols['isr_end']-symbols['isr_image']==3
rom[8:11]=b'\xc3'+struct.pack('<H',symbols['mixed_wrap'])
dck=bytes([0]+[2]*8)+rom;tag='beast_horizons_rev14'
for ext,data in [('dck',dck),('bin',rom)]:(BUILD/f'{tag}.{ext}').write_bytes(data)
manifest={'revision':14,'name':'Beast Horizons','tag':tag,'code_bytes':len(code),'asset_bytes':sum(map(len,cache)),
          'music':music_meta,
          'external_table_bytes':1440,'hill_phase_pixels':1,'hill_step_updates':1,
          'descriptors':[2]*8,'refreshes_per_update':2.5,'max_render_refreshes':3,'scroll_phase_pixels':2,'buffer_y':[120,160],'buffer_x':[104,136],'buffer_stride':32,
          'sha256':{ext:hashlib.sha256(data).hexdigest() for ext,data in [('dck',dck),('bin',rom)]}}
(BUILD/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
