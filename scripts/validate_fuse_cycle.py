"""Measure 256 consecutive maximum-speed updates in contended Fuse."""
from pathlib import Path
import subprocess,re,json,sys
ROOT=Path(__file__).resolve().parents[1];build=ROOT/'build'
manifest=json.loads((build/'manifest.json').read_text())
symbols={n:int(v.rstrip('H'),16) for n,_,v in (line.split() for line in (build/'symbols.txt').read_text().splitlines())}
count=6000 if '--long' in sys.argv else 256
stem='fuse-cycle-long' if count>256 else 'fuse-cycle'
distance=count*8
script='\n'.join([
    f"breakpoint 0x{symbols['render_frame']:04x}",
    f"breakpoint 0x{symbols['FRAME_DONE']:04x}",
    f"breakpoint 0x{symbols['READY']:04x} if [0x7e08] == {distance>>8} && [0x7e07] == {distance&255}",
    'commands 1','set 0x7e06 16','print spectrum:frames','print ula:tstates','continue','end',
    'commands 2','print spectrum:frames','print ula:tstates','continue','end',
    'commands 3','exit 0','end'])
(build/(stem+'.txt')).write_text(script+'\n')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW
p=subprocess.run([r'C:\Program Files (x86)\Fuse\fuse.exe','--machine','ts2068','--dock',str(build/(manifest['tag']+'.dck')),'--no-sound','--no-loading-sound','--speed','5000','--debugger-command',script],capture_output=True,text=True,timeout=55,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
(build/(stem+'.log')).write_text(p.stdout+p.stderr)
assert p.returncode==0,p.stderr
values=[int(s,16) for s in re.findall(r'^0x([0-9a-fA-F]+)\s*$',p.stdout,re.M)]
assert len(values)==count*4,len(values)
cost=[(values[i+2]-values[i])*59736+values[i+3]-values[i+1] for i in range(0,len(values),4)]
first_end=values[2]*59736+values[3]
last_end=values[-2]*59736+values[-1]
transit=(last_end-first_end)/(count-1)*256/(59736*60)
report={'revision':manifest['revision'],'dck_sha256':manifest['sha256']['dck'],'updates':len(cost),'minimum':min(cost),'maximum':max(cost),'worst_update':cost.index(max(cost))+1,'budget':manifest.get('max_render_refreshes',manifest['refreshes_per_update'])*59736,'transit_seconds_from_cadence':transit,'costs':cost}
(build/(stem+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print({k:v for k,v in report.items() if k!='costs'})
assert max(cost)<report['budget'],max(cost)
assert 10<=transit<=11,transit
