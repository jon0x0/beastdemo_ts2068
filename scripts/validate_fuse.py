"""Boot the released DCK in Fuse's TS2068 model and record checkpoints."""
from pathlib import Path
import subprocess, re, json

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'build/manifest.json').read_text())
media=ROOT/"build"/(manifest["tag"]+".dck")
symbols={}
for line in (ROOT/'build/symbols.txt').read_text().splitlines():
    name,_,value=line.split();symbols[name]=int(value.rstrip('H'),16)
fuse=Path(r'C:\Program Files (x86)\Fuse\fuse.exe')
results={'revision':manifest['revision'],'dck_sha256':manifest['sha256']['dck']}
for name,address,ignore in [('entry',symbols['START'],0),('initialized',symbols['READY'],0),('interrupt',0x5f5f,0),('frame1024',symbols['FRAME_DONE'],1023)]:
    expressions=['z80:pc','z80:sp','z80:im','z80:i','z80:iff1','spectrum:frames','ula:tstates']
    if name!='entry': expressions += [f'[0x{a:04x}]' for a in [0x7e00,0x7e01,0x7e04,0x7e05,0x7e06,0x7e07,0x7e08,0x7e09,0x7e0a,0x7e0b,0x7e0c,0x7e0d,0x7e0e,0x5e00,0x5f00,0x5f5f,0x4000,0x4800,0x5000,0x6000,0x6800,0x7000]]
    commands=[f'breakpoint 0x{address:04x}']
    if ignore:commands += [f'ignore 1 {ignore}']
    commands += ['commands 1']+[f'print {e}' for e in expressions]+['exit 0','end']
    script='\n'.join(commands)
    (ROOT/f'build/fuse-{name}.txt').write_text(script+'\n')
    si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW
    p=subprocess.run([str(fuse),'--machine','ts2068','--dock',str(media),'--no-sound','--no-loading-sound','--speed','5000','--debugger-command',script],capture_output=True,text=True,timeout=55,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
    (ROOT/f'build/fuse-{name}.log').write_text(p.stdout+p.stderr)
    assert p.returncode==0,(name,p.stderr)
    values=[int(s,16) for s in re.findall(r'^0x([0-9a-fA-F]+)\s*$',p.stdout,re.M)]
    assert len(values)==len(expressions),(name,p.stdout)
    results[name]=dict(zip(expressions,values))
    assert values[0]==address
    if name!='entry':
        assert results[name]['[0x7e04]'] in (0xf3,0x53)
        assert results[name]['[0x7e05]']==2
        assert results[name]['z80:im']==2
        assert results[name]['z80:i']==0x5e
    if name=='frame1024':
        assert results[name]['z80:sp']==0x8000
        assert results[name]['[0x7e01]']==0
        assert results[name]['[0x7e06]']==8
        assert results[name]['[0x7e07]']==0
        assert results[name]['[0x7e08]']==16
        assert results[name]['[0x7e09]']==2
    print(name,results[name],flush=True)
(ROOT/'build/fuse-validation.json').write_text(json.dumps(results,indent=2)+'\n')
timings={}
for phase in [1,2,3,7,11,15,31,64]:
    commands=[f"breakpoint 0x{symbols['render_frame']:04x} if [0x7e01] == {phase}",f"breakpoint 0x{symbols['FRAME_DONE']:04x} if [0x7e01] == {phase}",'commands 1','set 0x7e06 16','print spectrum:frames','print ula:tstates','continue','end','commands 2','print spectrum:frames','print ula:tstates','exit 0','end']
    script='\n'.join(commands)
    (ROOT/f'build/fuse-timing-{phase}.txt').write_text(script+'\n')
    p=subprocess.run([str(fuse),'--machine','ts2068','--dock',str(media),'--no-sound','--no-loading-sound','--speed','5000','--debugger-command',script],capture_output=True,text=True,timeout=55,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
    (ROOT/f'build/fuse-timing-{phase}.log').write_text(p.stdout+p.stderr)
    assert p.returncode==0
    values=[int(s,16) for s in re.findall(r'^0x([0-9a-fA-F]+)\s*$',p.stdout,re.M)]
    assert len(values)==4,p.stdout
    elapsed=(values[2]-values[0])*59736+values[3]-values[1]
    assert elapsed<manifest.get('max_render_refreshes',manifest['refreshes_per_update'])*59736,elapsed
    timings[str(phase)]={'tstates':elapsed,'checkpoints':values}
(ROOT/'build/fuse-timing.json').write_text(json.dumps({'revision':manifest['revision'],'dck_sha256':manifest['sha256']['dck'],'throttle':16,'updates':timings,'max_tstates':max(t['tstates'] for t in timings.values()),'budget_tstates':manifest.get('max_render_refreshes',manifest['refreshes_per_update'])*59736},indent=2)+'\n')
print('Fuse renderer timings:',timings)
