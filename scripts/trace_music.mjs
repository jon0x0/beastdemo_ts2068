// Independent execution of the unmodified Spectrum driver for reference AY writes.
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),build=path.join(root,'build');
const {createZ80,runZ80}=await import(pathToFileURL(path.resolve(root,'../TSRun/z80.js')));
const memory=new Uint8Array(fs.readFileSync(path.join(build,'music-original.bin')));
const meta=JSON.parse(fs.readFileSync(path.join(build,'music.json'))),cpu=createZ80(),clock={tstates:0,stepAdded:0};
let reg=0,writes=[],ports=new Set(),addresses=new Set();
const bus={read:a=>memory[a],write:(a,v)=>{addresses.add(a);memory[a]=v},ioRead:p=>255,
 ioWrite:(p,v)=>{ports.add(p);if(p===0xfffd)reg=v;else if(p===0xbffd){assert(reg<14);writes.push([reg,v]);}else throw Error('Unexpected port '+p.toString(16));}};
function call(address){cpu.sp=0xbff0;memory[0xbff0]=0;memory[0xbff1]=1;cpu.pc=address;const t=clock.tstates;
 while(cpu.pc!==0x100){runZ80(cpu,bus,1,clock);assert(clock.tstates-t<1000000,'Driver did not return');}
 return clock.tstates-t;
}
cpu.a=0;const initCost=call(meta.init),initWrites=writes;const frames=[],costs=[];
for(let i=0;i<12000;i++){writes=[];let cost=0;if(i&&i%meta.length_ticks===0){cpu.a=0;cost+=call(meta.init);}costs.push(cost+call(meta.play));frames.push(writes);}
const report={...meta,initCost,maxTickCost:Math.max(...costs),averageTickCost:costs.reduce((a,b)=>a+b)/costs.length,
 minWrite:Math.min(...addresses),maxWrite:Math.max(...addresses),ports:[...ports],initWrites,frames};
fs.writeFileSync(path.join(build,'music-reference.json'),JSON.stringify(report));
console.log(JSON.stringify({...report,frames:frames.length},null,2));
