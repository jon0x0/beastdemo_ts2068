"""Verify preserved checksums, current cartridge payload and preview duration."""
from pathlib import Path
import hashlib,json
from zipfile import ZipFile
from PIL import Image
r=Path(__file__).resolve().parents[1]
for archive in sorted((r/'revisions').glob('rev[0-9][0-9]')):
    if not (archive/'SHA256SUMS.json').exists():
        print(archive.name,'has no checksum manifest; skipped')
        continue
    hashes=json.loads((archive/'SHA256SUMS.json').read_text())
    for name,digest in hashes.items():
        assert hashlib.sha256((archive/name).read_bytes()).hexdigest()==digest,(archive,name)
    print(archive.name,len(hashes),'checksums verified')
m=json.loads((r/'build/manifest.json').read_text());tag=m['tag']
assert (r/f'build/{tag}_expanded.bin').read_bytes()==(r/f'build/{tag}.bin').read_bytes()
old=json.loads((r/'revisions/rev07/build/beast-art.json').read_text())
new=json.loads((r/'build/beast-art.json').read_text())
if m['revision']>=9:
    baseline=json.loads((r/'revisions/rev08/build/beast-art.json').read_text())
    assert new['bands']==baseline['bands']
    if m['revision']<14:assert new['sprites']==baseline['sprites']
    for name in ['music-validation.json','fuse-music.json','fuse-cycle-long.json']:
        assert json.loads((r/'build'/name).read_text())['dck_sha256']==m['sha256']['dck']
if m['revision']>=10:
    toggle=json.loads((r/'build/music-toggle-validation.json').read_text())
    assert toggle['dck_sha256']==m['sha256']['dck'] and toggle['toggleChanges']==4
if m['revision']>=14:
    from align_runner import align_runner
    baseline=json.loads((r/'revisions/rev10/build/beast-art.json').read_text())
    assert new==align_runner(baseline),'Only lossless runner alignment may differ'
    alignment=json.loads((r/'build/alignment-validation.json').read_text())
    assert alignment['dck_sha256']==m['sha256']['dck']
else:assert old['sprites']==new['sprites']
for a,b in zip(old['bands'],new['bands']):
    if a['name'].startswith('cloud') or a['name']=='sky_gap':assert a==b,a['name']
im=Image.open(r/f'build/{tag}.gif');duration=0
for n in range(im.n_frames):
    im.seek(n);duration+=im.info['duration']
assert 10000<=duration<=11000,duration
print('Preview duration',duration,'ms; clouds/sprites unchanged; DCK payload matches')
z=r/f'revisions/{tag}_release.zip'
if z.exists():
    with ZipFile(z) as f:assert f.testzip() is None
    print('Release ZIP CRC verified')
