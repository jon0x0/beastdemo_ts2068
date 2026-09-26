"""Freeze a validated revision without overwriting previous comparisons."""
from pathlib import Path
import hashlib,json,shutil
from zipfile import ZipFile,ZIP_DEFLATED

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'build/manifest.json').read_text())
rev=manifest['revision'];name=f'rev{rev:02d}';tag=manifest.get('tag',f'aqueduct_tides_{name}')
target=root/'revisions'/name
if target.exists():raise SystemExit(f'Refusing to overwrite preserved revision: {target}')
for ext in ['dck','bin']:
    data=(root/f'build/{tag}.{ext}').read_bytes()
    assert hashlib.sha256(data).hexdigest()==manifest['sha256'][ext]
assert json.loads((root/'build/runtime-validation.json').read_text())['framesChecked']>=1025
assert 'frame1024' in json.loads((root/'build/fuse-validation.json').read_text())
for report in ['runtime-validation.json','fuse-validation.json','fuse-timing.json']:
    assert json.loads((root/'build'/report).read_text())['dck_sha256']==manifest['sha256']['dck'],report
if rev>=6:
    cycle=json.loads((root/'build/fuse-cycle.json').read_text())
    assert cycle['dck_sha256']==manifest['sha256']['dck']
    assert cycle['maximum']<cycle['budget']
if rev>=9:
    for report_name in ['music-validation.json','fuse-music.json','fuse-cycle-long.json']:
        report=json.loads((root/'build'/report_name).read_text())
        assert report['dck_sha256']==manifest['sha256']['dck'],report_name
    assert json.loads((root/'build/music-validation.json').read_text())['ticksCompared']>=12000
if rev>=10:
    toggle=json.loads((root/'build/music-toggle-validation.json').read_text())
    assert toggle['dck_sha256']==manifest['sha256']['dck']
    assert toggle['toggleChanges']==4 and toggle['heldKeyDoesNotRepeat'] and toggle['mutedAcrossTuneRestart']
target.mkdir(parents=True)
for folder in ['src','scripts']:
    shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
if rev>=6:shutil.copytree(root/'references',target/'references')
for filename in ['README.md','MEMORY.md','REVISIONS.md','AGENTS.md','requirements.txt']:
    shutil.copy2(root/filename,target/filename)
if (root/'THIRD_PARTY.md').exists():shutil.copy2(root/'THIRD_PARTY.md',target/'THIRD_PARTY.md')
(target/'build').mkdir()
evidence=['manifest.json','code.bin','symbols.txt','runtime-validation.json',f'dck-inspection-{name}.json',
          f'comparison_rev{rev-1:02d}_{name}.png','art-reference.json','preview-states.json',
          'fuse-validation.json','fuse-timing.json']
evidence += [f'fuse-{checkpoint}.{ext}' for checkpoint in ['entry','initialized','interrupt','frame1024','timing-1','timing-2','timing-3','timing-8','timing-64'] for ext in ['txt','log']]
if rev>=6:
    evidence=['manifest.json','code.bin','symbols.txt','runtime-validation.json','beast-art.json',
              'fuse-validation.json','fuse-timing.json','fuse-cycle.json','fuse-cycle.txt','fuse-cycle.log',
              'emulator-animation.bin','preview-times.json','emulator_frame0.bin','emulator_frame64.bin','emulator_frame192.bin',
              f'dck-inspection-{name}.json',f'comparison_rev{rev-1:02d}_{name}.png']
    checkpoints=['entry','initialized','interrupt','frame1024']+['timing-'+k for k in json.loads((root/'build/fuse-timing.json').read_text())['updates']]
    evidence += [f'fuse-{checkpoint}.{ext}' for checkpoint in checkpoints for ext in ['txt','log']]
if rev>=9:
    evidence += ['music.json','music-original.bin','music-reference.json','music-validation.json',
                 'fuse-music.json','fuse-music.txt','fuse-music.log',
                 'fuse-cycle-long.json','fuse-cycle-long.txt','fuse-cycle-long.log']
if rev>=10:evidence += ['music-toggle-validation.json']
for p in sorted((root/'build').iterdir()):
    keep=(p.name.startswith((tag,) if rev>=6 else (tag,'emulator',f'reference_{name}')) or p.name in evidence)
    if keep and p.is_file():shutil.copy2(p,target/'build'/p.name)
hashes={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.rglob('*')) if p.is_file()}
(target/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
archive=root/'revisions'/f'{tag}_release.zip'
with ZipFile(archive,'x',ZIP_DEFLATED) as z:
    for p in sorted(target.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(target))
print(f'Preserved {len(hashes)} files in {target}\nRelease: {archive}')
