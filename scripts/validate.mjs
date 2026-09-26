// Cold boot, keyboard controls, independent pixel compositor and buffered-write checks.
import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..'),build=path.join(root,'build');
const manifest=JSON.parse(fs.readFileSync(path.join(build,'manifest.json')));
const art=JSON.parse(fs.readFileSync(path.join(build,'beast-art.json')));
const tsrun=process.env.TSRUN_DIR||path.resolve(root,'../TSRun');
const {createMachine,setHomeRom,setExRom,insertDock,resetMachine,runFrame}=await import(pathToFileURL(path.join(tsrun,'machine.js')));
const symbols=Object.fromEntries(fs.readFileSync(path.join(build,'symbols.txt'),'utf8').trim().split(/\r?\n/).map(l=>{const [n,,h]=l.trim().split(/\s+/);return[n,parseInt(h,16)]}));
const dck=fs.readFileSync(path.join(build,manifest.tag+'.dck')),flat=fs.readFileSync(path.join(build,manifest.tag+'.bin'));
const hash=crypto.createHash('sha256').update(dck).digest('hex');assert.equal(hash,manifest.sha256.dck);
assert.equal(dck.length,65545);assert.deepEqual(dck.subarray(1,9),Buffer.alloc(8,2));assert.deepEqual(dck.subarray(9),flat);
const keys=new Uint8Array(8).fill(255),m=createMachine(keys,[255,255]);
for(const [f,setter] of [['ts2068-0.rom',setHomeRom],['ts2068-1.rom',setExRom]])assert.equal(setter(m,fs.readFileSync(path.join(tsrun,'roms',f))),null);
assert.equal(insertDock(m,dck),null);resetMachine(m);
const read=m.bus.read,write=m.bus.write;
const offset=y=>((y&192)<<5)+((y&7)<<8)+((y&56)<<2);
const model={frame:0,speed:8,distance:0,groundDistance:0,fraction:0,pose:0,hill:0,clouds:[0,0,0,0,0]};
function input(f){return{p:f>=65&&f<=128||f>=513&&f<=640,o:f>=257&&f<=384}}
function setKeys(f){const k=input(f);keys.fill(255);if(k.o)keys[5]&=253;if(k.p)keys[5]&=254}
function advance(f){const k=input(f);model.frame=f&255;
 if(!(f&7)){if(k.p)model.speed=Math.min(16,model.speed+1);if(k.o)model.speed=Math.max(0,model.speed-1)}
 const travel=model.speed+model.fraction;model.distance=(model.distance+(travel>>1))&65535;model.fraction=travel&1;
 if(!(f&1))model.groundDistance=model.distance;
 if(model.speed){model.hill=(model.hill+1)&255;if(!(f&1))model.pose=(model.pose+1)%6}
 if((f&3)===1)model.clouds[0]=(model.clouds[0]+2)&255;
 else if((f&7)===3)model.clouds[1]=(model.clouds[1]+2)&255;
 else if((f&15)===7)model.clouds[2]=(model.clouds[2]+2)&255;
 else if((f&31)===15)model.clouds[3]=(model.clouds[3]+2)&255;
 else if((f&63)===31)model.clouds[4]=(model.clouds[4]+2)&255;
}
function reference(){
 const rows=[],attrs=[];const base=model.groundDistance>>2;
 for(let i=0;i<art.bands.length;i++){
  const b=art.bands[i],pos=(b.name==='sky_gap'?0:i<5?model.clouds[i]:i===5?model.hill:base*(i-5))&(i===5?255:254);
  const phase=b.phases[Math.floor((pos&7)/b.phase_step)],coarse=pos>>3;
  for(let y=0;y<b.height;y++){
   rows[b.y+y]=Array.from({length:256},(_,x)=>phase.pixels[y][(x+coarse*8)&255]);
   attrs[b.y+y]=Array.from({length:32},(_,x)=>phase.attrs[y][(x+coarse)&31]);
  }
 }
 const sprite=art.sprites[model.pose];
 for(let y=0;y<40;y++)for(let x=0;x<32;x++)if(!sprite.mask[y][x]){rows[120+y][112+x]=sprite.pixels[y][x];attrs[120+y][14+(x>>3)]=sprite.attrs[y][x>>3]}
 const out=Buffer.alloc(12288),buffer=Buffer.alloc(3072);
 for(let y=0;y<192;y++)for(let b=0;b<32;b++){
  let v=0;for(let bit=0;bit<8;bit++)v|=rows[y][b*8+bit]<<(7-bit);
  out[offset(y)+b]=v;out[6144+offset(y)+b]=attrs[y][b];
  if(y>=120&&y<168){buffer[(y-120)*32+b]=v;buffer[1536+(y-120)*32+b]=attrs[y][b]}
 }return{out,buffer};
}
let entry=false,initialized=false,done=0,started=0,publishing=false,expected,previous;
const timings=[],animation=[],snapshots=[],gaps=[],hillSteps=[],previewTimes=[];let lastDone=0,bufferChecks=0,displayWrites=0,lastHill=0,transitStart=0,transitEnd=0;
const stripAddresses=new Set();for(let y=120;y<160;y++)for(let b=14;b<18;b++)for(const p of [0x4000,0x6000])stripAddresses.add(p+offset(y)+b);
const dump=()=>Buffer.concat([Buffer.from(m.ram.slice(0x4000,0x5800)),Buffer.from(m.ram.slice(0x6000,0x7800))]);
const dumpBuffer=()=>Buffer.concat([Buffer.from(m.ram.slice(0x5800,0x5e00)),Buffer.from(m.ram.slice(0x7800,0x7e00))]);
function check(){
 const raw=dump(),mismatch=raw.findIndex((v,i)=>v!==expected.out[i]);
 assert.equal(mismatch,-1,`Update ${done}: mismatch ${mismatch}, got ${raw[mismatch]}, expected ${expected.out[mismatch]}`);
 assert.deepEqual(Buffer.from(m.ram.slice(0xa000,0xc000)),flat.subarray(0x4000,0x6000));
 assert.deepEqual(Buffer.from(m.ram.slice(0xe000,0x10000)),flat.subarray(0x6000,0x8000));
 for(const [a,v]of [[0x7e06,model.speed],[0x7e07,model.distance&255],[0x7e08,model.distance>>8],[0x7e09,model.pose],[0x7e0a,model.hill]])assert.equal(m.ram[a],v);
 assert([0xf3,0x53].includes(m.portF4));assert.equal(m.portFF,2);assert.equal(m.cpu.sp,0x8000);return raw;
}
m.bus.read=a=>{
 if(a===symbols.START&&m.cpu.pc===a)entry=true;
 if(entry&&a===symbols.READY&&!initialized){expected=reference();previous=check();initialized=true;fs.writeFileSync(path.join(build,'emulator_frame0.bin'),previous);animation.push(previous);previewTimes.push(m.tstates);setKeys(1)}
 if(initialized&&a===symbols.render_frame){started=m.tstates;advance(done+1);expected=reference();publishing=false;displayWrites=0}
 if(initialized&&a===symbols.BUFFER_READY){const actualBuffer=dumpBuffer();for(let y=0;y<40;y++)for(let x=14;x<18;x++)for(const plane of [0,1536]){const j=plane+y*32+x;assert.equal(actualBuffer[j],expected.buffer[j],'Complete character buffer before publish');}for(const addr of stripAddresses)assert.equal(m.ram[addr],previous[(addr>=0x6000?6144:0)+addr-(addr>=0x6000?0x6000:0x4000)],'Old strip stays intact while composing');bufferChecks++;publishing=true}
 if(initialized&&a===symbols.FRAME_DONE){done++;const raw=check();const delta=(m.ram[0x7e0a]-lastHill)&255;assert(delta===0||delta===1,'Rocks never skip a pixel');if(delta)hillSteps.push({update:done,position:m.ram[0x7e0a]});lastHill=m.ram[0x7e0a];assert.equal(displayWrites,done&1?128:320,'Final bitmap and sprite attribute bytes published once');publishing=false;previous=raw;timings.push(m.tstates-started);if(lastDone)gaps.push(m.tstates-lastDone);lastDone=m.tstates;
  if(done===1)transitStart=m.tstates;if(done===257)transitEnd=m.tstates;
  if(done<768){animation.push(raw);previewTimes.push(m.tstates)}
  if([1,64,128,192,256,320,384,512,640,1024].includes(done))snapshots.push({done,...model,clouds:[...model.clouds]});
  if([64,192].includes(done))fs.writeFileSync(path.join(build,`emulator_frame${done}.bin`),raw);
  setKeys(done+1);
 }return read(a);
};
m.bus.write=(a,v)=>{if(initialized){assert((a>=0x4000&&a<0x8000)||(a>=0xc000&&a<0xe000&&m.portF4===0x13),`Unexpected write ${a.toString(16)}`);if(stripAddresses.has(a)){assert(publishing,'No visible strip writes during background/sprite composition');const i=(a>=0x6000?6144:0)+a-(a>=0x6000?0x6000:0x4000);assert.equal(v,expected.out[i],'Only final composed bytes reach display');displayWrites++}}write(a,v)};
for(let f=0;f<13000&&done<2305;f++)runFrame(m);
assert(done>=2305);assert(Math.max(...timings)<manifest.max_render_refreshes*58688);
assert.equal(snapshots.find(s=>s.done===128).speed,16);assert.equal(snapshots.find(s=>s.done===384).speed,0);
for(const key of ['distance','pose','hill'])assert.equal(snapshots.find(s=>s.done===384)[key],snapshots.find(s=>s.done===512)[key]);
assert.equal(snapshots.find(s=>s.done===640).speed,16);
assert(hillSteps.length>256);assert(new Set(hillSteps.map(s=>s.position)).size===256);
const transitSeconds=(transitEnd-transitStart)/(58688*60);
assert(transitSeconds>=10&&transitSeconds<=11,`Rock screen transit ${transitSeconds}s`);
for(const band of art.bands.filter(b=>b.name==='hill'))for(let p=0;p<band.phases.length;p++)for(let y=0;y<band.height;y++){
 const offset=p*band.phase_step,row=band.phases[0].pixels[y];
 assert.deepEqual(band.phases[p].pixels[y],row.slice(offset).concat(row.slice(0,offset)),'Dither texture moves rigidly');
 assert.equal(new Set(band.phases[p].attrs[y]).size,1,'No horizontal attribute blocks');
}
const report={revision:manifest.revision,dck_sha256:hash,entry,framesChecked:done,bufferChecks,snapshots,hillSteps,transitSeconds,minRendererTstates:Math.min(...timings),maxRendererTstates:Math.max(...timings),averageCompletionInterval:gaps.reduce((a,b)=>a+b,0)/gaps.length,checks:'Full display/buffer comparisons, protected writes, bank/cache integrity, controls, one-pixel steps, rigid dithering, row-uniform palettes, and measured 256-pixel transit'};
fs.writeFileSync(path.join(build,'runtime-validation.json'),JSON.stringify(report,null,2));fs.writeFileSync(path.join(build,'emulator-animation.bin'),Buffer.concat(animation));fs.writeFileSync(path.join(build,'preview-times.json'),JSON.stringify(previewTimes));console.log(JSON.stringify({...report,hillSteps:hillSteps.length},null,2));


