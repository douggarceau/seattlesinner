/* Guitar Doug Report pop-up for pages outside the main front page: rotates a Newspace promo and an "advertise here" card. */
(function(){if(window.__gdrPop)return;window.__gdrPop=1;
var KEY='gdrPopOff';try{if(sessionStorage.getItem(KEY))return}catch(e){}
var NS='https://newspace.douggarceau.workers.dev/signup',AD='https://seattlesinner.com/?go=advertise';
var css='.gdrpop{position:fixed;left:16px;bottom:64px;z-index:2147483000;width:270px;max-width:calc(100vw - 32px);box-sizing:border-box;border-radius:8px;overflow:hidden;font-family:Verdana,Tahoma,Arial,sans-serif;color:#fff;opacity:0;transform:translateY(16px);transition:opacity .4s,transform .4s}'+
'.gdrpop.on{opacity:1;transform:none}.gdrpop a{display:block;padding:14px 16px 14px;color:#fff;text-decoration:none}'+
'.gdrpop .x{position:absolute;left:6px;top:4px;z-index:4;border:0;background:none;color:#fff9;font:700 16px/1 Arial,sans-serif;cursor:pointer;padding:4px}.gdrpop .x:hover{color:#fff}'+
'.gdrpop.ns{background:linear-gradient(180deg,#00133d,#060a14 60%,#050608);border:1px solid #4d8cff88;border-top:3px solid #3366cc;animation:gdrNs 2.2s ease-in-out infinite}'+
'@keyframes gdrNs{0%,100%{box-shadow:0 12px 30px #000c,0 0 24px #3a7bff88}50%{box-shadow:0 12px 30px #000c,0 0 50px #4d8cffdd}}'+
'.gdrpop.ns::after{content:"NEW \\00B7  FREE";position:absolute;top:20px;right:-44px;width:176px;padding:6px 0;transform:rotate(35deg);background:#d10f1f;color:#fff;font:900 11px/1 monospace;letter-spacing:.18em;text-align:center;box-shadow:0 0 0 1px #ff6b75,0 0 16px #ff1e2ecc;pointer-events:none}'+
'.gdrpop small{display:block;margin:4px 0 0 14px;font:700 10px/1.2 monospace;letter-spacing:.16em;text-transform:uppercase;color:#9cc0ff;padding-right:60px}'+
'.gdrpop big{display:block;margin:8px 0 4px;font:700 34px/1 Verdana,Tahoma,Arial,sans-serif;letter-spacing:-.04em;text-shadow:0 0 22px #3366cc88}'+
'.gdrpop p{margin:0 0 10px;font:400 13px/1.4 Verdana,Tahoma,Arial,sans-serif;color:#d6dde8}'+
'.gdrpop i{display:inline-block;font:800 11px/1 monospace;font-style:normal;letter-spacing:.14em;text-transform:uppercase;padding:8px 12px;border-radius:4px;background:#003399;border:1px solid #6699cc}'+
'.gdrpop.ad{background:linear-gradient(160deg,#16181d,#0a0b0e);border:1px solid #1e90ff88;animation:gdrAd 1.6s ease-in-out infinite}.gdrpop.ad small{color:#d6d6d6;letter-spacing:.04em;text-transform:none;font:500 12px/1.2 Georgia,serif}'+
'.gdrpop.ad big{font:800 26px/1.05 Georgia,serif;letter-spacing:0;text-shadow:none}.gdrpop.ad i{background:#c8102e;border-color:#ff4d5e}'+
'@keyframes gdrAd{0%,100%{box-shadow:0 12px 30px #000c,0 0 8px rgba(30,144,255,.55)}50%{box-shadow:0 12px 30px #000c,0 0 24px rgba(30,144,255,1)}}'+
'@media (prefers-reduced-motion:reduce){.gdrpop{transition:none;animation:none!important}}@media print{.gdrpop{display:none}}';
var C=[{k:'ns',h:NS,ext:1,html:'<small>Social messaging app</small><big>newspace</big><p>Brand new and free to join. Message friends, post on your wall, pick your Top 8 and add a profile song.</p><i>Join free →</i>'},
{k:'ad',h:AD,html:'<small>Your next customer is reading this.</small><big>Advertise in this spot.</big><p>Front-page boxes, Venue Guide spots and margin ads. 30-day runs.</p><i>Click here →</i>'}];
function start(){var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
var el=document.createElement('div');el.className='gdrpop';el.setAttribute('role','complementary');el.setAttribute('aria-label','The Guitar Doug Report');document.body.appendChild(el);
var n=0,show=function(){var c=C[n++%C.length];el.className='gdrpop '+c.k;el.innerHTML='<button class="x" type="button" aria-label="Close">×</button><a href="'+c.h+'"'+(c.ext?' target="_blank" rel="noopener"':'')+'>'+c.html+'</a>';
 el.querySelector('.x').onclick=function(){el.remove();clearInterval(t);try{sessionStorage.setItem(KEY,'1')}catch(e){}};requestAnimationFrame(function(){el.classList.add('on')})};
var t;setTimeout(function(){show();t=setInterval(function(){if(document.hidden)return;el.classList.remove('on');setTimeout(show,420)},14000)},5000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start()})();
