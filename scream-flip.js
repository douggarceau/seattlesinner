/* Seattle Scream: the side boxes flip one by one, each revealing a word, until a phrase is spelled out.
   It holds, flips back, and a new phrase comes later. (owner, Nov 16 2026) */
(function(){
const PHRASES=[
'SOMETHING FOLLOWED YOU HOME','THE DEAD KNOW YOUR NAME','DO NOT LOOK BEHIND YOU','THEY ARE ALREADY INSIDE','THE MOON IS HUNGRY TONIGHT',
'SAY HIS NAME THREE TIMES','WE NEVER LEFT SEATTLE','THE MIRROR IS LYING','YOUR SHADOW MOVED FIRST','THE WITCHES ARE AWAKE',
'ALL DOORS LEAD DOWN','SOMETHING LEARNED YOUR VOICE','THE CANDLES KNOW','HE IS COUNTING THE DAYS','SHE NEVER STOPPED WATCHING',
'THE BASEMENT IS BREATHING','DONT ANSWER THE KNOCKING','THE FOG HAS TEETH','SOMEONE IS STILL SINGING','THE CARDS SAID TONIGHT',
'BLOOD REMEMBERS','THE SOUND IS NOT EMPTY','THE OLD ONES ARE STIRRING','YOU LEFT THE DOOR OPEN','EVERY CLOCK STOPPED AT THREE',
'NOTHING HERE IS ALIVE','THE RAIN WHISPERS NAMES','IT WEARS YOUR FACE','THE SPELL IS ALREADY CAST','DONT TRUST THE QUIET',
'THE HOLLOW ONES ARE HUNGRY','WE SEE YOU READING THIS','THE TIDE BRINGS THEM BACK','A DEAL WAS MADE HERE','THE NIGHT IS LISTENING',
'LOCK THE WINDOWS TONIGHT','THE STARS ARE WRONG','SOMETHING WAITS IN THE WOODS','THE CIRCLE IS BROKEN','HE KNOWS WHERE YOU SLEEP',
'THE LIGHTS ARE NOT OURS','YOUR DREAMS ARE NOT YOURS','THE BELL TOLLS FOR SEATTLE','DARKNESS HAS A PULSE','THE VEIL IS THIN TONIGHT',
'THEY CRAWL UP FROM BELOW','THE HOUSE WANTS YOU BACK','NO ONE LEAVES THE PARTY','THE RAVEN SAID YOUR NAME','THE DEVIL KEEPS RECEIPTS',
'THE BONES ARE TALKING','SALT THE DOORWAY NOW','THE HAUNTING NEVER ENDED','IT IS ALREADY MIDNIGHT','MAGIC IS FUN WHEN YOU’RE DEAD','DO WHAT THOU WILT','LOVE IS THE LAW','VADE RETRO SATANA','CRUX SACRA SIT MIHI LUX','NUNQUAM SUADE MIHI VANA','IPSE VENENA BIBAS','EXORCIZO TE IMMUNDISSIME SPIRITUS','DA LOCUM CHRISTO','BEGONE UNCLEAN SPIRIT','I CAST YOU OUT','CHRIST COMMANDS YOU','THE CROSS COMMANDS YOU','GIVE PLACE TO CHRIST','DEPART YOU DECEIVER'
];
const reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
let bag=[],busy=false;
function nextPhrase(max){if(!bag.length)bag=PHRASES.slice().sort(()=>Math.random()-.5);
 const i=bag.findIndex(p=>p.split(' ').length<=max);if(i<0)return null;return bag.splice(i,1)[0].split(' ')}
function visibleBoxes(){const top=70,bot=innerHeight-30;
 return [...document.querySelectorAll('.lsrow .lspot')].filter(b=>!b.hidden&&b.offsetParent&&getComputedStyle(b).display!=='none').map(b=>({b,r:b.getBoundingClientRect()}))
  .filter(o=>o.r.width>60&&o.r.top>=top&&o.r.bottom<=bot).sort((a,c)=>Math.abs(a.r.top-c.r.top)>20?a.r.top-c.r.top:a.r.left-c.r.left).map(o=>o.b)}
function cycle(){if(busy||document.hidden)return;const B=visibleBoxes();if(B.length<2)return;
 if(B.some(b=>b.matches(':hover')))return;const W=nextPhrase(B.length);if(!W)return;busy=true;
 const used=B.slice(0,W.length),gap=reduce?250:850;
 used.forEach((b,i)=>setTimeout(()=>{const o=document.createElement('div');o.className='scrw';o.setAttribute('aria-hidden','true');o.textContent=W[i];b.appendChild(o)},i*gap));
 const hold=W.length*gap+4800;
 setTimeout(()=>{used.forEach((b,i)=>setTimeout(()=>{const o=b.querySelector('.scrw');if(!o)return;o.classList.add('out');setTimeout(()=>o.remove(),600)},i*300));
  setTimeout(()=>{busy=false},used.length*300+700)},hold)}
const css=document.createElement('style');css.id='scrwCss';css.textContent=`
.lsrow .lspot{position:relative}
.lsrow .lspot .scrw{position:absolute;inset:0;z-index:20;display:flex;align-items:center;justify-content:center;text-align:center;padding:8px;
 background:radial-gradient(90% 80% at 50% 50%,#1A0C00,#000 70%);border:1px solid #FF6600;box-shadow:inset 0 0 30px #FF660055;
 font:900 clamp(22px,2.3vw,40px)/1 Oswald,"Arial Narrow",Impact,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#fff;
 text-shadow:0 0 8px #FF8A1F,0 0 22px #FF6600,0 0 44px #FF6600;backface-visibility:hidden;transform-origin:50% 50%;
 animation:scrIn .7s cubic-bezier(.2,.8,.2,1) both,scrFlick 3.2s steps(1) .7s infinite;pointer-events:none}
.lsrow .lspot .scrw.out{animation:scrOut .55s ease-in both}
@keyframes scrIn{from{transform:perspective(700px) rotateY(-95deg);opacity:0}to{transform:perspective(700px) rotateY(0);opacity:1}}
@keyframes scrOut{to{transform:perspective(700px) rotateY(95deg);opacity:0}}
@keyframes scrFlick{0%,100%{opacity:1}47%{opacity:1}48%{opacity:.55}49%{opacity:1}83%{opacity:.8}84%{opacity:1}}
@media (prefers-reduced-motion:reduce){.lsrow .lspot .scrw{animation:none}.lsrow .lspot .scrw.out{animation:none;opacity:0}}`;
document.head.appendChild(css);
setTimeout(cycle,6000);setInterval(cycle,24000);
document.addEventListener('scroll',()=>{clearTimeout(window.__scrT);window.__scrT=setTimeout(()=>{if(!busy&&Math.random()<.35)cycle()},2500)},{passive:true});
})();
