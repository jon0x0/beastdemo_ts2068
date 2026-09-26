const frame=document.getElementById('emulator'),start=document.getElementById('start'),panel=document.getElementById('start-panel'),status=document.getElementById('status'),error=document.getElementById('error');
const api=()=>frame.contentWindow.beastDemo;
window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==frame.contentWindow)return;
  if(event.data?.type==='beast-ready'){start.disabled=false;start.textContent='Play demo';status.textContent='Cartridge ready · CRT scanlines on';error.textContent='';}
  if(event.data?.type==='beast-error'){error.textContent=event.data.message;status.textContent='Emulator unavailable';}
});
start.addEventListener('click',()=>{if(!api()?.start())return;panel.hidden=true;document.querySelectorAll('[data-key],#reset').forEach(b=>b.disabled=false);status.textContent='Playing revision 10 · O/P speed · S sound';});
document.querySelectorAll('[data-key]').forEach(button=>button.addEventListener('click',()=>api()?.press(button.dataset.key)));
document.getElementById('reset').addEventListener('click',()=>api()?.reset());
document.getElementById('crt').addEventListener('change',event=>api()?.crt(event.target.checked));
document.getElementById('fullscreen').addEventListener('click',()=>{frame.requestFullscreen?.().catch(()=>{status.textContent='Full screen unavailable in this browser';});});
setTimeout(()=>{if(start.disabled)error.textContent='The emulator is taking longer than expected. Reload or download the cartridge to use in another emulator.';},30000);
