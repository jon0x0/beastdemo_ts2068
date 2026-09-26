// Adapter derived from the speech2ay web demo; follows the live TSRun APIs.
const upstream='https://josef-jelinek.github.io/TSRun/';
function notify(type,message){parent.postMessage({type,message},location.origin);}
async function resource(url,binary=false){const r=await fetch(url);if(!r.ok)throw Error(`${url}: HTTP ${r.status}`);return binary?new Uint8Array(await r.arrayBuffer()):r.text();}
async function boot(){
  const [cpu,video,sound,keys,pads]=await Promise.all(['machine.js','screen.js','sound.js','keyboard.js','joystick.js'].map(p=>import(upstream+p)));
  const fps=cpu.cpuHz/cpu.tStatesPerFrame,frameMs=1000/fps;
  const canvas=document.getElementById('screen'),matrix=new Uint8Array(8),joystick=new Uint8Array(2);
  const kbd=keys.initKeyboard(document.getElementById('keyboard'),matrix);pads.initJoysticks(joystick);
  const machine=cpu.createMachine(matrix,joystick);
  const [rom0,rom1,cart,vert,frag]=await Promise.all([resource(upstream+'roms/ts2068-0.rom',true),resource(upstream+'roms/ts2068-1.rom',true),resource('../assets/beast_horizons_rev14.dck',true),resource(upstream+'screen.vert.glsl'),resource(upstream+'screen.frag.glsl')]);
  if(rom0.length!==cpu.homeRomSize||rom1.length!==cpu.exRomSize)throw Error('Unexpected system ROM sizes');
  for(const e of [cpu.setHomeRom(machine,rom0),cpu.setExRom(machine,rom1),cpu.insertDock(machine,cart)])if(e)throw Error(e);
  cpu.resetMachine(machine);
  let gfx,crtOn=true;
  const slot=document.getElementById('screen-slot');
  function resize(){
    if(!gfx)return;
    video.resizeScreen(gfx);
    // TSRun uses integer zoom without CRT. Fullscreen should still use all
    // available space, preserving the display's 4:3 aspect ratio.
    if(document.fullscreenElement===slot&&!crtOn){
      const width=Math.min(slot.clientWidth,slot.clientHeight*4/3);
      canvas.style.width=width+'px';canvas.style.height=(width*3/4)+'px';
    }
  }
  await new Promise((resolve,reject)=>video.initScreen(canvas,{vert,frag},(err,value)=>{if(err||!value){reject(Error(err||'WebGL2 unavailable'));notify('beast-error',err);return;}gfx=value;video.setCrt(gfx,crtOn);resolve();}));
  const sfx=await new Promise((resolve,reject)=>sound.initSound(fps,(err,value)=>err||!value?reject(Error(err||'Web Audio unavailable')):resolve(value)));
  cpu.setSoundRate(machine,sfx.context.sampleRate);sound.setSoundStereo(sfx,false);
  let started=false,last=0,carry=0,frames=0;
  const timers=new Map();
  function step(){cpu.enableSound(machine,sound.soundIsRunning(sfx));cpu.runFrame(machine);frames++;const chunk=cpu.takeAudio(machine);if(chunk.n>0&&sound.soundIsRunning(sfx))sound.pushSound(sfx,chunk);}
  function fill(){if(!started||!sound.soundIsRunning(sfx))return;for(let n=0;n<4&&sound.soundWantsFrame(sfx);n++){step();carry=Math.max(carry-frameMs,-4*frameMs);}}
  sound.setSoundNeedCallback(sfx,fill);
  sound.setSoundStateCallback(sfx,running=>{cpu.enableSound(machine,running);if(running)fill();});
  function frame(now){requestAnimationFrame(frame);if(!started){last=now;return;}pads.pollJoysticks(joystick);if(!last)last=now;carry+=Math.min(80,now-last);last=now;let n=0;while(carry>=frameMs&&n<4){step();carry-=frameMs;n++;}if(n<4)fill();video.drawScreen(gfx,machine.pixels);}
  function release(){for(const timer of timers.values())clearTimeout(timer);timers.clear();keys.handleBlur(kbd);}
  window.beastDemo={
    start(){started=true;sound.resumeSound(sfx);window.focus();canvas.focus();return true;},
    press(code){this.start();if(timers.has(code))clearTimeout(timers.get(code));const e={code,repeat:false,preventDefault(){}};keys.handleKeyDown(kbd,e);timers.set(code,setTimeout(()=>{keys.handleKeyUp(kbd,e);timers.delete(code);},code==='KeyS'?120:400));},
    reset(){release();sound.resetSound(sfx);cpu.resetMachine(machine);carry=0;last=0;this.start();},
    crt(on){crtOn=Boolean(on);video.setCrt(gfx,crtOn);resize();},
    async fullscreen(){
      this.start();
      if(document.fullscreenElement)await document.exitFullscreen();
      else await slot.requestFullscreen();
      resize();
    },
    // Read-only diagnostics for release verification.
    inspect(){return {frames,started,crt:crtOn,audio:sfx.context.state,audioStats:{...sound.soundStats(sfx)},speed:machine.ram[0x7e06],soundOff:machine.ram[0x7e3b],heldKeys:Array.from(matrix)};},
  };
  window.addEventListener('keydown',e=>{window.beastDemo.start();keys.handleKeyDown(kbd,e);});window.addEventListener('keyup',e=>keys.handleKeyUp(kbd,e));window.addEventListener('blur',release);window.addEventListener('pointerdown',()=>window.beastDemo.start());window.addEventListener('resize',resize);
  document.addEventListener('fullscreenchange',()=>requestAnimationFrame(resize));
  new ResizeObserver(resize).observe(slot);
  requestAnimationFrame(frame);notify('beast-ready');
}
boot().catch(e=>{console.error(e);const message='TSRun could not start. '+e.message;document.getElementById('error').hidden=false;document.getElementById('error').textContent=message;notify('beast-error',message);});
