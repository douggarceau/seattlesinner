/* Seattle Scream: The Stars Over Seattle (owner, Nov 16 2026). Replaces the tide chart.
   Live sky math (sun sign, moon phase, moon sign, rising sign for Seattle right now) plus a daily
   reading for each sign. Readings are for entertainment; they come from a phrase bank keyed to the date. */
(function(){
const SIGNS=[['Aries','♈︎','Mar 21 – Apr 19','Fire','Mars'],['Taurus','♉︎','Apr 20 – May 20','Earth','Venus'],['Gemini','♊︎','May 21 – Jun 20','Air','Mercury'],
 ['Cancer','♋︎','Jun 21 – Jul 22','Water','Moon'],['Leo','♌︎','Jul 23 – Aug 22','Fire','Sun'],['Virgo','♍︎','Aug 23 – Sep 22','Earth','Mercury'],
 ['Libra','♎︎','Sep 23 – Oct 22','Air','Venus'],['Scorpio','♏︎','Oct 23 – Nov 21','Water','Pluto'],['Sagittarius','♐︎','Nov 22 – Dec 21','Fire','Jupiter'],
 ['Capricorn','♑︎','Dec 22 – Jan 19','Earth','Saturn'],['Aquarius','♒︎','Jan 20 – Feb 18','Air','Uranus'],['Pisces','♓︎','Feb 19 – Mar 20','Water','Neptune']];
const LAT=47.6062,LON=-122.3321,R=Math.PI/180,norm=x=>((x%360)+360)%360;
function jd(d){return d.getTime()/864e5+2440587.5}
function sky(d){const n=jd(d)-2451545.0;
 const L=norm(280.460+0.9856474*n),g=norm(357.528+0.9856003*n)*R;const sun=norm(L+1.915*Math.sin(g)+0.020*Math.sin(2*g));
 const Lm=norm(218.316+13.176396*n),Mm=norm(134.963+13.064993*n)*R,F=norm(93.272+13.229350*n)*R;const moon=norm(Lm+6.289*Math.sin(Mm));
 const age=((jd(d)-2451550.1)%29.530588853+29.530588853)%29.530588853;const illum=Math.round((1-Math.cos(2*Math.PI*age/29.530588853))/2*100);
 const gmst=norm(280.46061837+360.98564736629*n),lst=norm(gmst+LON)*R,eps=23.4393*R,lat=LAT*R;
 const asc=norm(Math.atan2(Math.cos(lst),-(Math.sin(lst)*Math.cos(eps)+Math.tan(lat)*Math.sin(eps)))/R);
 return {sun,moon,age,illum,asc}}
const signOf=l=>Math.floor(norm(l)/30);
function phaseName(a){return a<1.85?'New Moon':a<5.54?'Waxing Crescent':a<9.23?'First Quarter':a<12.92?'Waxing Gibbous':a<16.61?'Full Moon':a<20.30?'Waning Gibbous':a<23.99?'Last Quarter':a<27.68?'Waning Crescent':'New Moon'}
/* daily reading: seeded by date + sign, so it changes every day and stays the same all day */
function rng(seed){let s=seed>>>0;return()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296}}
const OPEN=['The sky turns its full attention on you today.','A charged current runs under everything you touch today.','Today rewards nerve over caution.','Something you set in motion weeks ago comes back around today.','The planets are loud today; trust your gut over the noise.','A sharp, electric day for you.','Today has an edge to it, and that suits you.','The cosmos hands you the wheel today.'];
const LOVE=['Someone is watching you closer than you think; let them.','Say the bold thing. The timing is better than it looks.','An old flame flickers. Decide if it is worth the burn.','Chemistry is high after dark; follow it.','A slow-burning connection finally catches.','Keep your cool in love today; mystery works in your favor.'];
const MONEY=['Money moves in your direction if you ask for it.','Hold your cash today; a better deal is coming.','A side hustle shows real promise.','Watch the fine print before you sign anything.','Spend on experience, not stuff.','A risk with your money pays off only if you did your homework.'];
const WORK=['At work, your instincts are sharper than the plan.','Push back on the thing everyone is too polite to question.','A rival shows their hand. Stay a step ahead.','Finish what you started before you chase the next shiny thing.','Your reputation opens a door today.','Lead loud. People are ready to follow.'];
const NIGHT=['Tonight: loud music, low light, good company.','Tonight favors a dive bar over a dinner party.','Tonight, go where the bass is heaviest.','Tonight, a late-night conversation changes your mind about something.','Tonight, ride out and clear your head.','Tonight, stay in and plot your next move.'];
const COLORS=['Blood red','Gunmetal','Midnight black','Chrome','Oxblood','Smoke gray','Bone white','Crimson'];
function reading(i,day){const r=rng(([...day].reduce((a,c)=>a*31+c.charCodeAt(0),7)^((i+1)*2654435761))>>>0);const p=a=>a[Math.floor(r()*a.length)];
 return {text:[p(OPEN),p(LOVE),p(MONEY),p(WORK),p(NIGHT)].join(' '),love:40+Math.floor(r()*61),money:30+Math.floor(r()*71),energy:45+Math.floor(r()*56),lucky:1+Math.floor(r()*99),color:p(COLORS),match:SIGNS[(i+4+Math.floor(r()*5))%12][0]}}
const H=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let sel=null;try{const v=localStorage.getItem('astroSign');if(v!==null)sel=+v}catch(_){}
function wheel(sunI,moonI,selI){let s='<svg class="as-wheel" viewBox="-110 -110 220 220" aria-hidden="true"><defs><radialGradient id="asG"><stop offset="0" stop-color="#FF6600" stop-opacity=".35"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient></defs>'+
 '<circle r="106" fill="url(#asG)"/><circle r="100" class="as-ring"/><circle r="72" class="as-ring dim"/><circle r="44" class="as-ring"/><g class="as-spin">';
 for(let i=0;i<12;i++){const a=(i*30-90+15)*R,a0=(i*30-90)*R;s+='<line x1="'+(44*Math.cos(a0)).toFixed(1)+'" y1="'+(44*Math.sin(a0)).toFixed(1)+'" x2="'+(100*Math.cos(a0)).toFixed(1)+'" y2="'+(100*Math.sin(a0)).toFixed(1)+'" class="as-tick"/>'+
  '<text x="'+(86*Math.cos(a)).toFixed(1)+'" y="'+(86*Math.sin(a)).toFixed(1)+'" class="as-gl'+(i===selI?' on':'')+(i===sunI?' sun':'')+'">'+SIGNS[i][1]+'</text>'}
 for(let i=0;i<72;i++){const a=(i*5)*R;s+='<line x1="'+(100*Math.cos(a)).toFixed(1)+'" y1="'+(100*Math.sin(a)).toFixed(1)+'" x2="'+(104*Math.cos(a)).toFixed(1)+'" y2="'+(104*Math.sin(a)).toFixed(1)+'" class="as-deg"/>'}
 const ma=(moonI*30-90+15)*R;s+='</g><circle cx="'+(58*Math.cos(ma)).toFixed(1)+'" cy="'+(58*Math.sin(ma)).toFixed(1)+'" r="4" class="as-moon"/>';
 return s+'<text y="9" class="as-core">'+SIGNS[selI][1]+'</text></svg>'}
function bar(k,v){return '<div class="as-bar"><span>'+k+'</span><i><b style="width:'+v+'%"></b></i><em>'+v+'%</em></div>'}
function paint(){const box=document.getElementById('astro');if(!box)return;const now=new Date(),S=sky(now);
 const sunI=signOf(S.sun),moonI=signOf(S.moon),ascI=signOf(S.asc);if(sel===null||isNaN(sel))sel=sunI;
 const day=now.toLocaleDateString('en-CA',{timeZone:'America/Los_Angeles'}),Rd=reading(sel,day),Z=SIGNS[sel];
 box.innerHTML='<div class="as-h"><span class="as-k">What the stars aren’t telling Seattle</span><span class="as-live"><i></i>LIVE SKY · '+H(now.toLocaleTimeString('en-US',{timeZone:'America/Los_Angeles',hour:'numeric',minute:'2-digit'}))+'</span></div>'+
 '<div class="as-grid"><div class="as-left">'+wheel(sunI,moonI,sel)+'<div class="as-sky">'+
  '<div><small>Sun in</small><b>'+SIGNS[sunI][1]+' '+SIGNS[sunI][0]+'</b></div>'+
  '<div><small>Moon in</small><b>'+SIGNS[moonI][1]+' '+SIGNS[moonI][0]+'</b></div>'+
  '<div><small>Rising now</small><b>'+SIGNS[ascI][1]+' '+SIGNS[ascI][0]+'</b></div>'+
  '<div><small>Moon</small><b>'+phaseName(S.age)+' · '+S.illum+'%</b></div></div></div>'+
 '<div class="as-right"><div class="as-signs" role="tablist" aria-label="Choose your sign">'+SIGNS.map((z,i)=>'<button type="button" role="tab" aria-selected="'+(i===sel)+'" data-as="'+i+'" title="'+z[0]+'">'+z[1]+'<span>'+z[0]+'</span></button>').join('')+'</div>'+
  '<div class="as-read"><div class="as-t"><b>'+Z[1]+' '+Z[0]+'</b><span>'+Z[2]+' · '+Z[3]+' · ruled by '+Z[4]+'</span></div><p>'+H(Rd.text)+'</p>'+
  bar('Love',Rd.love)+bar('Money',Rd.money)+bar('Energy',Rd.energy)+
  '<div class="as-meta"><span>Lucky number <b>'+Rd.lucky+'</b></span><span>Power color <b>'+H(Rd.color)+'</b></span><span>Best match <b>'+H(Rd.match)+'</b></span></div>'+
  '<small class="as-note">“Do what thou wilt shall be the whole of the Law.” — Aleister Crowley, 1904 · For entertainment. Sky positions computed for Seattle.</small></div></div></div>'}
document.addEventListener('click',e=>{const b=e.target.closest('#astro [data-as]');if(!b)return;sel=+b.dataset.as;try{localStorage.setItem('astroSign',String(sel))}catch(_){};paint()});
function mount(){if(document.getElementById('astro')){paint();return}const anchor=document.getElementById('jtSea')||document.getElementById('coverSlot');if(!anchor)return;
 const s=document.createElement('section');s.id='astro';s.setAttribute('aria-label','Astrology and horoscope');anchor.parentNode.insertBefore(s,anchor.nextSibling);paint()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
setInterval(paint,60000);
})();
