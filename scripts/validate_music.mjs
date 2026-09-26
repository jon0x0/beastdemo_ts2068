// Compare live cartridge AY writes against the unmodified Spectrum driver.
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),build=path.join(root,'build');
const {createMachine,setHomeRom,setExRom,insertDock,resetMachine,runFrame,enableSound,setSoundRate,takeAudio}=await import(pathToFileURL(path.resolve(root,'../TSRun/machine.js')));
const manifest=JSON.parse(fs.readFileSync(path.join(build,'manifest.json'))),reference=JSON.parse(fs.readFileSync(path.join(build,'music-reference.json')));
const sym=Object.fromEntries(fs.readFileSync(path.join(build,'symbols.txt'),'utf8').trim().split(/\r?\n/).map(l=>{const [n,,h]=l.trim().split(/\s+/);return[n,parseInt(h,16)]}));
const toggle=process.argv.includes('--toggle'),keys=new Uint8Array(8).fill(255);
const m=createMachine(keys,[255,255]);
setHomeRom(m,fs.readFileSync(path.resolve(root,'../TSRun/roms/ts2068-0.rom')));setExRom(m,fs.readFileSync(path.resolve(root,'../TSRun/roms/ts2068-1.rom')));
insertDock(m,fs.readFileSync(path.join(build,manifest.tag+'.dck')));resetMachine(m);setSoundRate(m,22050);enableSound(m,true);
let active=false,tick=-1,reg=0,writes=[],starts=[],end=0,irq=0,firstIrq=0,frames=0,initial=false;
const io=m.bus.ioWrite,read=m.bus.read,pcm=[];
let driverWrite=true;const refreshWrites=[];
const pressed=n=>[[120,240],[360,480],[600,720],[6700,6820]].some(([a,b])=>n>=a&&n<b);
const muted=n=>n>=120&&n<360||n>=600&&n<6700;
function compare(){let expected=tick<0?reference.initWrites:reference.frames[tick];if(toggle&&m.ram[sym.SOUND_OFF])expected=expected.map(([r,v])=>[r,r>=8&&r<=10?0:v]);assert.deepEqual(writes,expected,`AY write sequence at music tick ${tick}`);writes=[];}
m.bus.ioWrite=(p,v)=>{if(active&&(p&255)===0xf5){reg=v;assert.equal(p,0xfff5);}if(active&&(p&255)===0xf6){assert.equal(p,0xfff6);assert(reg<14);if(driverWrite)writes.push([reg,v]);else {assert(reg>=8&&reg<=10);assert.equal(v,m.ram[sym.SOUND_OFF]?0:m.ram[sym.AY_LEVELS+reg-8]);refreshWrites.push({irq,reg,value:v});}}io(p,v);};
m.bus.read=a=>{
 if(a===sym.music_init&&m.cpu.pc===a)active=true;
 if(active&&a===sym.READY&&!initial){compare();initial=true;firstIrq=irq;}
 if(initial&&a===0x5f5f&&m.cpu.pc===a)irq++;
 if(active&&a===sym.music_output&&m.cpu.pc===a)driverWrite=true;
 if(active&&a===sym.sound_refresh_write&&m.cpu.pc===a)driverWrite=false;
 if(initial&&a===sym.music_tick+3&&m.cpu.pc===a){
  assert.equal(m.ram[sym.SOUND_OFF],toggle&&muted(irq)?1:0,'Sound defaults on and changes once per press');
  if(toggle&&muted(irq))for(let r=8;r<=10;r++)assert.equal(m.ay.regs[r],0,'All channels silent while muted');
 }
 // Measure scheduled tick entry, before the extra init call on a song restart.
 if(initial&&a===sym.music_tick&&m.cpu.pc===a&&m.ram[0x7e30]>=1)starts.push(m.tstates);
 if(initial&&a===0xc003&&m.cpu.pc===a){tick++;assert.equal(m.portF4,0x13);}
 if(initial&&a===sym.music_tick_done&&m.cpu.pc===a){compare();end=m.tstates;}
 if(initial&&a===sym.FRAME_DONE&&m.cpu.pc===a)frames++;
 return read(a);
};
for(let f=0;f<16000&&tick<11999;f++){
 if(toggle&&initial)keys[1]=pressed(irq+1)?253:255;
 runFrame(m);const a=takeAudio(m);
 if(initial&&pcm.length<22050*30)for(let i=0;i<a.n;i++)pcm.push((a.a[i]+a.b[i]+a.c[i])/3);
}
assert.equal(tick,11999);assert.equal(Math.floor(irq*5/6),12000);assert(frames>4000);
const intervals=starts.slice(1).map((t,i)=>t-starts[i]);
assert(Math.min(...intervals)>58000&&Math.max(...intervals)<118000);
const wav=Buffer.alloc(44+pcm.length*2);wav.write('RIFF');wav.writeUInt32LE(wav.length-8,4);wav.write('WAVEfmt ',8);wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(1,22);wav.writeUInt32LE(22050,24);wav.writeUInt32LE(44100,28);wav.writeUInt16LE(2,32);wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(pcm.length*2,40);
let prev=0,filtered=0,energy=0;for(let i=0;i<pcm.length;i++){const x=pcm[i];filtered=.995*(filtered+x-prev);prev=x;const v=Math.max(-1,Math.min(1,filtered*2));energy+=v*v;wav.writeInt16LE(Math.round(v*32767),44+i*2);}
assert(energy/pcm.length>.0001,'Audible nonzero output');if(!toggle)fs.writeFileSync(path.join(build,manifest.tag+'_audio.wav'),wav);
if(toggle){assert.equal(refreshWrites.length,12,'Held S must not repeat');assert.deepEqual([...new Set(refreshWrites.map(w=>w.irq))],[120,360,600,6700]);}
const report={revision:manifest.revision,dck_sha256:manifest.sha256.dck,music_sha256:reference.sha256,ticksCompared:tick+1,displayInterrupts:irq,sceneryUpdates:frames,
 sourceLengthTicks:reference.length_ticks,secondsChecked:(end-starts[0])/3528000,minTickGap:Math.min(...intervals),maxTickGap:Math.max(...intervals),previewSeconds:pcm.length/22050,
 checks:'Every AY register write and envelope retrigger matches the original driver (amplitudes zeroed when muted); 5/6 interrupt cadence; scenery runs throughout; sound ports FFF5/FFF6 only.',...(toggle?{refreshWrites,toggleChanges:4,heldKeyDoesNotRepeat:true,mutedAcrossTuneRestart:true}:{})};
fs.writeFileSync(path.join(build,toggle?'music-toggle-validation.json':'music-validation.json'),JSON.stringify(report,null,2));console.log(report);
