"""Check actual TS2068-port output against the independent original AY driver."""
from pathlib import Path
import json,re,subprocess
r=Path(__file__).resolve().parents[1];b=r/'build'
m=json.loads((b/'manifest.json').read_text());ref=json.loads((b/'music-reference.json').read_text())
s={n:int(v.rstrip('H'),16) for n,_,v in (l.split() for l in (b/'symbols.txt').read_text().splitlines())}
script='\n'.join([f"breakpoint 0x{s['music_output']:x}",f"breakpoint 0x{s['music_tick_done']:x}",'ignore 2 999',
    'commands 1','print z80:de','print z80:af','continue','end','commands 2','exit 0','end'])
(b/'fuse-music.txt').write_text(script+'\n')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW
p=subprocess.run([r'C:\Program Files (x86)\Fuse\fuse.exe','--machine','ts2068','--dock',str(b/(m['tag']+'.dck')),
    '--no-sound','--speed','5000','--debugger-command',script],capture_output=True,text=True,timeout=55,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
(b/'fuse-music.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
v=[int(x,16) for x in re.findall(r'^0x([0-9a-fA-F]+)\s*$',p.stdout,re.M)]
actual=[[v[i]&255,v[i+1]>>8] for i in range(0,len(v),2)]
expected=ref['initWrites']+sum(ref['frames'][:1000],[])
assert actual==expected,'Fuse driver output differs from original AY'
report=dict(revision=m['revision'],dck_sha256=m['sha256']['dck'],ticksCompared=1000,writesCompared=len(actual),passed=True)
(b/'fuse-music.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
