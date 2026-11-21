/* 2027 theme, shared by all three city sites. Site settings come from window.T27 = {a:accent, k:'kicker', n:'NAME', tz:'America/New_York'} */
window.WO_CATS=[['Live Music',/^(live|rock|indie|jazz|pop|electronic|folk|r&b|latin|metal|hip-hop|punk|experimental|world|goth|country|blues|soul|reggae|funk)$/i],['Comedy',/^comedy$/i],['Shows',/^(theater|dance|classical|opera|stage)$/i],['Film',/^film$/i],['Art',/^(arts|art)$/i],['Nightlife',/^(clubs|club|nightlife)$/i],['Food & Drink',/^(food|drink|dining)$/i],['Outdoors',/^recreation$/i],['Talks & Books',/^talks$/i]];
window.WO_OTHER='More Events';window.WO_SKIP=/^(sports|support|worship|drag)$/i;
(function(){
const C=window.T27||{};const R=document.documentElement;
R.setAttribute('data-t27','');if(C.keepArt)R.setAttribute('data-keepart','');R.style.setProperty('--a',C.a||'#E10600');
const f=document.createElement('link');f.rel='stylesheet';f.href='https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800&display=swap';document.head.appendChild(f);
/* calendar filter hook used by vCal: music only, or the weekend */
const MUS=/^(live|rock|indie|jazz|pop|electronic|folk|r&b|latin|metal|hip-hop|punk|experimental|world|goth|country|music|blues|soul|reggae|funk|classical|clubs)$/i;
let MODE=null,WK=null,SF=null;window.T27S=s=>SF?SF(s):true;
window.T27F=e=>{if(MODE==='music')return MUS.test(e.genre||'');if(MODE==='wk'&&WK)return e.date>=WK[0]&&e.date<=WK[1];return true};
const TZ=C.tz||'America/New_York';const ymd=d=>d.toLocaleDateString('en-CA',{timeZone:TZ});
function weekend(){const n=new Date(),td=ymd(n),dow=new Date(td+'T12:00:00').getDay();const a=(k)=>ymd(new Date(n.getTime()+k*864e5));
 const fri=dow===0?a(-2):dow===6?a(-1):a(5-dow);const sun=dow===0?td:dow===6?a(1):a(7-dow);return [fri<td?td:fri,sun]}
const ITEMS=[
 ['Now',()=>nav('front')],
 ['News',()=>nav('stories')],
 ['Music',()=>nav('cal','music',30)],
 ['Tech',()=>{SF=s=>/^tech-/.test(s.slug)||/\b(AI|robot|tech)\b/i.test(s.title||'');nav('stories')}],
 ['Calendar',()=>nav('cal',null,14)],
 ['Explore',()=>nav('visit')]];
function nav(v,mode,days){MODE=mode||null;try{STATE.genre='all';STATE.cq='';if(days)STATE.cdays=days;else STATE.cdays=14}catch(_){}
 try{go(v)}catch(e){const b=document.querySelector('#nav [data-go="'+v+'"]');if(b)b.click()}}
if(C.items)ITEMS.splice(0,ITEMS.length,...C.items.map(([t,v])=>[t,()=>nav(v)]));
let cur='Now';
function mark(){document.querySelectorAll('#nav .nb27').forEach(b=>b.toggleAttribute('aria-current',b.textContent===cur))}
function build(){
 const m=document.querySelector('header.mast');
 if(m&&!m.querySelector('.wm27')){const w=document.createElement('a');w.className='wm27';w.href='/';w.setAttribute('aria-label',(C.k||'')+' '+(C.n||''));
  w.innerHTML='<span class="k"><i></i>'+(C.k||'')+'</span><span class="n"'+(C.sz?' style="font-size:'+C.sz+'"':'')+'>'+(C.n||'')+'</span><span class="r"></span>';
  w.onclick=e=>{e.preventDefault();cur='Now';mark();nav('front')};(m.querySelector('div')||m).appendChild(w)}
 const n=document.getElementById('nav');
 if(n&&!n.querySelector('.nb27')){ITEMS.forEach(([t,fn],i)=>{const b=document.createElement('button');b.type='button';b.className='nb27';b.textContent=t;b.style.order=i;
  b.onclick=()=>{cur=t;mark();if(t!=='Tech')SF=null;fn()};n.appendChild(b)});mark()}
 const ft=document.querySelector('footer.site-footer');
 if(ft&&!ft.querySelector('.ft27')){const d=document.createElement('div');d.className='ft27';
  d.innerHTML=(C.foot||[]).map(f=>'<button type="button" '+(f[1][0]==='#'?'data-c="'+f[1].slice(1)+'"':'data-g="'+f[1]+'"')+'>'+f[0]+'</button>').join('')+'<button type="button" data-dir="1">Business Directory</button><button type="button" data-g="advertise">Advertising</button><button type="button" data-g="privacy">Privacy &amp; Contact</button>';
  d.querySelectorAll('button').forEach(b=>b.onclick=()=>{if(b.dataset.dir){R.classList.toggle('dir27');return}if(b.dataset.c){const x=document.getElementById(b.dataset.c);if(x)x.click();return}cur='';mark();try{go(b.dataset.g)}catch(_){}});ft.insertBefore(d,ft.firstChild)}
 hero();dedupe();cal1();upd();labels();rails();dress();fonts()}
/* any old serif or display face left over from earlier styling switches to the new faces */
const OLD=/Georgia|Playfair|PT Serif|Libre Caslon|Bodoni|Abril|DM Serif|Old Standard|Cinzel|Marcellus|Satisfy|Special Elite|Cormorant|Alfa Slab|Oswald|Anton|Bebas|Times|serif$/i;
function fonts(){document.addEventListener('keydown',e=>{if(e.key==='Escape')R.classList.remove('dir27')});
const RED=/^rgba?\((193, 18, 31|225, 6, 0|200, 16, 46)(, 1)?\)$/,swap=!/^#(E10600|C1121F)$/i.test(C.a||'');
document.body.querySelectorAll(':is(b,strong,span,a,h1,h2,h3,h4,p,button,div,small,i,em,li,summary,label,section,article,aside):not([data-f27])').forEach(e=>{e.dataset.f27='';const cs=getComputedStyle(e);
 if(swap){for(const [k,c] of [['border-left-color',cs.borderLeftColor],['border-top-color',cs.borderTopColor],['border-bottom-color',cs.borderBottomColor],['background-color',cs.backgroundColor],['color',cs.color]])if(RED.test(c))e.style.setProperty(k,'var(--a)','important')}
 const bi=cs.backgroundImage;if(!C.keepArt&&bi&&/url\(/.test(bi)&&!/bg27|data:/.test(bi)&&e.getBoundingClientRect().width>150)e.style.setProperty('background-image','linear-gradient(180deg,rgba(6,7,9,.2),rgba(6,7,9,.7)),url(/img/bg27/'+BG[bi_++%BG.length]+'.jpg)','important');if(OLD.test(cs.fontFamily)){e.style.setProperty('font-family',parseFloat(cs.fontSize)>=17?'"Geist",system-ui,sans-serif':'"Geist",system-ui,sans-serif','important');e.style.setProperty('font-style','normal','important')}})}

/* lead story at the top of the front page, and one place per story */
function leadStory(){let L=[];try{L=STORIES}catch(_){return null}const td=ymd(new Date());
 const ok=s=>s&&s.title&&!/^today-(and-tonight|on-the-island)-/.test(s.slug)&&(!s.until||s.until>=td)&&s.topic!=='crime';
 return L.find(s=>s.lead&&ok(s))||L.filter(ok).sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))||(/^tech-/.test(b.slug)?1:0)-(/^tech-/.test(a.slug)?1:0))[0]||null}
function hero(){let v='';try{v=STATE.view}catch(_){}const old=document.getElementById('hero27');
 if(v!=='front'){if(old)old.remove();return}
 const s=leadStory();if(!s)return;if(old&&old.dataset.story===s.slug)return;if(old)old.remove();
 const anchor=document.getElementById('whatsOn')||document.getElementById('coverSlot');if(!anchor)return;
 const H=x=>String(x==null?'':x).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
 const k=/^tech-/.test(s.slug)?'Tech':s.topic==='music'?'Music':s.topic==='stage'?'On stage':'Top story';
 const b=document.createElement('button');b.type='button';b.id='hero27';b.dataset.story=s.slug;
 b.style.setProperty('--hb',C.heroImgs?'url('+C.heroImgs[hash(s.slug)%C.heroImgs.length]+')':'url(/img/bg27/'+HBG[hash(s.slug)%HBG.length]+'.jpg)');
 b.innerHTML='<span class="hk">'+H(k)+'</span><span class="ht">'+H(s.title)+'</span>'+(s.dek?'<span class="hd">'+H(s.dek)+'</span>':'')+'<span class="hg">Read the story →</span>';
 anchor.parentNode.insertBefore(b,anchor)}
function cal1(){const w=document.getElementById('whatsOn');if(!w||w.dataset.t27a)return;const d=w.querySelector('details.wo-d');if(!d)return;w.dataset.t27a='1';if(!w.querySelector('details[open]')){d.open=true;d.classList.add('t27auto');setTimeout(()=>d.addEventListener('toggle',()=>d.classList.remove('t27auto'),{once:true}),400)}}
function labels(){const set=(el,t)=>{if(el&&el.firstChild&&el.textContent.trim()!==t){const n=[...el.childNodes].find(x=>x.nodeType===3&&x.textContent.trim());if(n)n.textContent=t;else el.textContent=t}};
 const h=document.querySelector('.cvside .sea-h');if(h){set(h.querySelector('b'),'News');const a=h.querySelector('button,a');if(a)set(a,'All stories →')}
 const hb=document.querySelector('#hlBox .bh b');if(hb)set(hb,'Headlines')}
function rails(){if(!window.jtEvPool)return;let P=[];try{P=jtEvPool()}catch(_){return}if(!P.length)return;
 const H=x=>String(x==null?'':x).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
 const used=new Set([...document.querySelectorAll('.lspot a[data-promo-key]')].map(a=>a.dataset.promoKey));document.querySelectorAll('.lspot :is(.ep-t,.bp-t,.ls-big)').forEach(t=>used.add('title:'+t.textContent.replace(/\s+/g,' ').trim().toLowerCase()));
 document.querySelectorAll('.lsrow .lspot.t-st').forEach(sp=>{const a=sp.querySelector('a[id]');if(!a)return;
  let e=P.find(x=>!used.has('title:'+String(x.bigText||'').replace(/\s+/g,' ').trim().toLowerCase()));if(!e)return;
  const key='title:'+String(e.bigText||'').replace(/\s+/g,' ').trim().toLowerCase();used.add(key);
  const ev=e.ev||{};const d=ev.date?new Date(ev.date+'T12:00:00'):null;
  const mo=d?d.toLocaleDateString('en-US',{month:'short'}).toUpperCase():'',dy=d?d.getDate():'';
  sp.classList.remove('t-st');sp.classList.add('t-mu');
  a.dataset.promoKey=key;a.href=e.href||'#';if(e.ext){a.target='_blank';a.rel='noopener'}a.removeAttribute('data-story');a.setAttribute('aria-label',e.bigText||'');
  const bg=C.keepArt&&C.heroImgs?' style="background:linear-gradient(180deg,rgba(246,241,230,.92) 0,rgba(246,241,230,.75) 45%,rgba(246,241,230,0) 75%),url('+C.heroImgs[hash(key)%C.heroImgs.length]+') center/cover;color:#0A1F3D"':'';
  a.innerHTML='<span class="ep ep-gig t27ev"'+bg+'><span class="ep-k">'+H(ev.genre&&/classical|opera|ballet|stage|theater/i.test(ev.genre)?'The Big Room':'Live')+'</span><span class="ep-t s2">'+H(e.bigText)+'</span><span class="ep-d">'+mo+'<b>'+dy+'</b>'+H(ev.time||e.when||'')+'</span><span class="ep-foot"><span class="ep-v">'+H([e.name,ev.hood].filter(Boolean).join(' · '))+'</span><span class="ep-cta">Get in →</span></span></span>';
  a.querySelectorAll('.ep').forEach(x=>{x.dataset.b27='';if(!C.keepArt)x.style.setProperty('--b27','url(/img/bg27/'+BG[hash(key)%BG.length]+'.jpg)')})})}
setInterval(()=>{try{rails()}catch(_){}},1500);
let updT=null;function upd(){const t=document.querySelector('.clsbar.top');if(!t||t.querySelector('.upd27'))return;const s=document.createElement('span');s.className='upd27';t.insertBefore(s,t.querySelector('.rec'));
 const show=d=>{if(!d)return;const x=new Date(d);if(isNaN(x))return;s.textContent='Updated '+x.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit',timeZone:TZ})};
 fetch('data/headlines.json?'+Date.now(),{cache:'no-cache'}).then(r=>r.ok?r.json():null).then(d=>show(d&&d.asof)).catch(()=>{})}
const HBG=['bg42-wireframe-terrain','bg44-particle-field','bg46-lidar-scan','bg50-orbit-lines','bg41-data-mesh','bg45-glass-panels'];
const hash=s=>{let h=7;for(const c of String(s))h=(h*31+c.charCodeAt(0))>>>0;return h};
function dedupe(){const hb=document.getElementById('hlBox');if(hb){const vis=[...hb.querySelectorAll('a.hlr')].some(a=>!/^\?story=/.test(a.getAttribute('href')||''));hb.style.setProperty('display',vis?'':'none',vis?'':'important')}
const h=document.getElementById('hero27');const lead=h&&h.dataset.story;
 document.querySelectorAll('.cvside .sea-g [data-story]').forEach(b=>{if(lead&&b.dataset.story===lead)b.style.setProperty('display','none','important');
  if(!C.keepArt&&!b.dataset.b27){b.dataset.b27='1';b.style.setProperty('background-image','linear-gradient(90deg,rgba(12,14,18,.96) 35%,rgba(12,14,18,.6)),url(/img/bg27/'+BG[hash(b.dataset.story)%BG.length]+'.jpg)','important');b.style.setProperty('background-size','cover','important');b.style.setProperty('background-position','center','important')}})}
/* backgrounds for the flipping boxes */
const BG=['bg41-data-mesh','bg42-wireframe-terrain','bg43-graphite-gradient','bg44-particle-field','bg45-glass-panels','bg46-lidar-scan','bg47-liquid-chrome','bg48-aurora-edge','bg49-led-dot-matrix','bg50-orbit-lines'];
let bi=Math.floor(Math.random()*BG.length),bi_=bi+3;
function dress(){if(C.keepArt)return;document.querySelectorAll('.bp:not([data-b27]),.ep.os:not([data-b27]),.lspot .ep:not([data-b27])').forEach(el=>{el.dataset.b27='1';el.style.setProperty('--b27','url(/img/bg27/'+BG[bi++%BG.length]+'.jpg)')})}
const go_=()=>{build();new MutationObserver(()=>{clearTimeout(go_.t);go_.t=setTimeout(build,60)}).observe(document.body,{childList:true,subtree:true})};
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',go_):go_();
})();
