/* Newspaper Mode: the site's own articles laid out as a daily broadsheet. Seattle Night Stalker edition (ported from Rhode Island Hurricane, Nov 16 2026). */
(()=>{
const H=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const TD=()=>new Date().toLocaleDateString('en-CA',{timeZone:'America/Los_Angeles'});
const LONG=d=>new Date(d+'T12:00:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'});
const SHORT=d=>new Date(d+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric'});
const SITE=()=>'Seattle Night Stalker';
const PLACE=()=>'Seattle';
const SEC0={music:'Arts & Entertainment',stage:'Arts & Entertainment',culture:'Arts & Entertainment',family:'Local',people:'Local',news:'Local',transit:'Local',food:'Food'};
const SEC=new Proxy(SEC0,{get:(o,k)=>k==='news'?'Local & State News':o[k]});
const css=`
#paper{position:fixed;inset:0;z-index:9999;background:#000000;overflow:auto;-webkit-overflow-scrolling:touch}
#paper .pp-bar{position:sticky;top:0;z-index:3;display:flex;gap:8px;align-items:center;justify-content:center;padding:8px;background:#050505;border-bottom:1px solid #1A1B1F;font:700 14px/1 Georgia,serif;color:#FFFFFF}
#paper .pp-bar button{all:unset;cursor:pointer;white-space:nowrap;padding:9px 14px;border:1px solid #8E9196;border-radius:4px;color:#fff;background:#000000;font:700 14px/1 Georgia,serif}
#paper .pp-bar button:hover{background:#1A1B1F}#paper .pp-bar .pp-x{margin-left:auto}#paper .pp-bar .pp-pg{min-width:150px;text-align:center}
#paper .pp-wrap{display:grid;grid-template-columns:210px minmax(0,1180px);gap:18px;justify-content:center;align-items:start;padding:18px 12px 40px}
#paper .pp-side{position:sticky;top:64px;background:#EEE9E5;color:#050505;padding:14px 14px 16px;box-shadow:0 10px 30px #05050599;font-family:Georgia,serif}
#paper .pp-side h4{margin:0 0 8px;padding-bottom:6px;border-bottom:3px double #050505;font:900 20px/1.1 "Playfair Display",Georgia,serif}
#paper .pp-side button{all:unset;box-sizing:border-box;cursor:pointer;display:flex;justify-content:space-between;gap:8px;width:100%;padding:9px 4px;border-bottom:1px solid #DDE1E6;font:700 16px/1.25 Georgia,serif;color:#D34A12;text-decoration:underline;text-underline-offset:2px}
#paper .pp-side button span{color:#050505;text-decoration:none;font:700 13px/1.25 "Libre Franklin",Arial,sans-serif;white-space:nowrap}
#paper .pp-side button.on{background:#050505;color:#fff;text-decoration:none;padding-left:8px;padding-right:8px}#paper .pp-side button.on span{color:#fff}
#paper .pp-side small{display:block;margin-top:10px;font:400 12.5px/1.4 Georgia,serif;color:#1A1B1F}
#paper .pp-bar i{font-style:normal}#paper .pp-bar .sm{display:none}@media(max-width:700px){#paper .pp-bar{gap:6px;padding:6px}#paper .pp-bar button{padding:10px 10px;font-size:14px}#paper .pp-bar .lg{display:none}#paper .pp-bar .sm{display:inline}#paper .pp-bar .pp-pg{display:none}#paper .pp-bar .pp-x{margin-left:0}}
#paper .pp-bar .pp-home{background:#D34A12;border-color:#D34A12;font-size:16px;padding:11px 18px}#paper .pp-bar .pp-home:hover{background:#D34A12}
#paper .sheet *{box-sizing:border-box}#paper .sheet{max-width:1180px;margin:0;background:#EEE9E5;color:#050505;padding:22px 30px 34px;box-shadow:0 10px 40px #050505AA;font-family:Georgia,"Times New Roman",serif}
#paper .ear{display:flex;justify-content:space-between;align-items:flex-end;gap:16px}
#paper .ear .ppbox{flex:0 0 190px;border:1px solid #050505;padding:7px 9px;font:400 12.5px/1.35 Georgia,serif}
#paper .ear .ppbox b{display:block;font:800 10.5px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;margin-bottom:3px}
#paper .flag{flex:1;text-align:center}
#paper .flag img{width:min(640px,100%);height:auto;filter:brightness(0)}
#paper .flag .nm{font:900 clamp(34px,6vw,72px)/1 "Playfair Display",Georgia,serif;letter-spacing:-.01em}
#paper .dl{display:flex;justify-content:space-between;gap:10px;margin-top:8px;padding:5px 0;border-top:3px double #050505;border-bottom:1px solid #050505;font:700 12px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase}
#paper .sh{display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px double #050505;padding:4px 0 6px;margin-bottom:12px}
#paper .sh b{font:900 30px/1 "Playfair Display",Georgia,serif}#paper .sh span{font:700 12px/1 "Libre Franklin",Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase}
#paper .fp{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:0 22px;margin-top:14px}
#paper .pplead{grid-column:1/5;border-right:1px solid #8E9196;padding-right:22px}
#paper .rail{grid-column:5/7}
#paper .kk{font:800 11px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#000000;margin-bottom:4px}
#paper h2.hd{font:800 clamp(30px,4vw,50px)/1.03 "Playfair Display",Georgia,serif;margin:0 0 8px;letter-spacing:-.01em}
#paper h3.hd{font:800 23px/1.12 "Playfair Display",Georgia,serif;margin:0 0 6px}
#paper h4.hd{font:700 17px/1.18 "Playfair Display",Georgia,serif;margin:0 0 4px}
#paper .dk{font:italic 400 19px/1.35 Georgia,serif;color:#000000;margin:0 0 8px}
#paper .by{font:700 11px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;margin:6px 0 10px;padding-bottom:6px;border-bottom:1px solid #DDE1E6}
#paper .txt{column-gap:20px;column-rule:1px solid #DDE1E6;font:400 15.5px/1.5 Georgia,serif;text-align:justify;hyphens:auto}
#paper .txt p{margin:0 0 8px;text-indent:1.2em}#paper .txt p:first-child{text-indent:0}
#paper .txt p.dc:first-letter{float:left;font:900 54px/.8 "Playfair Display",Georgia,serif;margin:6px 6px 0 0}
#paper .txt h5{font:800 13px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;margin:10px 0 4px;break-after:avoid}
#paper .txt table{width:100%;border-collapse:collapse;font:400 12.5px/1.3 Georgia,serif;margin:4px 0 10px;break-inside:avoid;text-align:left}
#paper .txt td,#paper .txt th{border-bottom:1px solid #DDE1E6;padding:3px 4px;vertical-align:top}#paper .txt th{font:800 10.5px/1.2 "Libre Franklin",Arial,sans-serif;text-transform:uppercase;letter-spacing:.06em}
#paper .txt caption{font:800 11px/1.2 "Libre Franklin",Arial,sans-serif;text-transform:uppercase;letter-spacing:.08em;text-align:left;padding:4px 0}
#paper .c2{column-count:2}#paper .c3{column-count:3}
#paper figure{margin:0 0 10px}#paper figure img{width:100%;height:auto;filter:grayscale(1) contrast(1.05);display:block}
#paper figcaption{font:italic 12.5px/1.3 Georgia,serif;color:#000000;padding-top:4px;border-bottom:1px solid #DDE1E6;padding-bottom:5px}
#paper .jump{font:700 12px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase;margin-top:6px}
#paper a.jl,#paper button.jl{all:unset;cursor:pointer;color:#D34A12;text-decoration:underline;text-underline-offset:2px}#paper a.jl:hover,#paper button.jl:hover{color:#D34A12}
#paper .brief{padding:0 0 10px;margin:0 0 10px;border-bottom:1px solid #8E9196}#paper .brief p{margin:0;font:400 14.5px/1.42 Georgia,serif}
#paper .brief .src{font:700 10.5px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#1A1B1F;margin-top:3px}
#paper .idx{border:2px solid #050505;padding:8px 10px;margin-bottom:14px}#paper .idx b{display:block;font:900 18px/1 "Playfair Display",Georgia,serif;border-bottom:1px solid #050505;padding-bottom:5px;margin-bottom:5px}
#paper .idx div{display:flex;justify-content:space-between;font:400 14px/1.6 Georgia,serif;cursor:pointer;color:#D34A12;text-decoration:underline;text-underline-offset:2px}#paper .idx div:hover{text-decoration:underline}
#paper .fold{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 22px;margin-top:16px;padding-top:14px;border-top:4px solid #050505}
#paper .fold>div{border-right:1px solid #8E9196;padding-right:22px}#paper .fold>div:last-child{border-right:0;padding-right:0}
#paper .agate{column-count:4;column-gap:16px;column-rule:1px solid #DDE1E6;font:400 13px/1.38 Georgia,serif}
#paper .agate .day{font:900 15px/1.2 "Playfair Display",Georgia,serif;border-bottom:2px solid #050505;margin:8px 0 4px;break-after:avoid}
#paper .agate .cat{font:800 10.5px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;margin:7px 0 2px;break-after:avoid}
#paper .agate p{margin:0 0 4px;break-inside:avoid}#paper .agate p b{font-weight:700}
#paper .ft{margin-top:20px;padding-top:6px;border-top:1px solid #050505;display:flex;justify-content:space-between;font:700 11px/1.2 "Libre Franklin",Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase}
#paper .grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 22px}#paper .grid2>div:first-child{border-right:1px solid #8E9196;padding-right:22px}
@media(max-width:980px){#paper .pp-wrap{grid-template-columns:minmax(0,1fr);padding:0}#paper .pp-side{position:static;box-shadow:none;border-bottom:3px double #050505}#paper .pp-side .pp-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:14px}}
@media(max-width:820px){#paper .sheet{padding:14px 14px 24px;margin:0}#paper .ear .ppbox{display:none}#paper .fp,#paper .fold,#paper .grid2{grid-template-columns:minmax(0,1fr)}#paper .pplead,#paper .rail,#paper .fold>div,#paper .grid2>div:first-child{grid-column:auto;border-right:0;padding-right:0}#paper .c2,#paper .c3{column-count:1}#paper .agate{column-count:2}#paper .rail{margin-top:16px;padding-top:12px;border-top:3px double #050505}#paper .fold>div{margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #8E9196}#paper .pp-bar .pp-pg{min-width:0}}
@media(max-width:460px){#paper .agate{column-count:1}}
#paper .pp-printall{display:none}
@media print{@page{size:letter;margin:0}html,body{background:#fff!important;overflow:visible!important}body>*:not(#paper){display:none!important}#paper{position:static!important;background:#fff!important;overflow:visible!important}#paper .pp-printall,#paper .pp-printall .sheet{background:#fff!important}#paper .pp-bar,#paper .pp-wrap{display:none!important}#paper .pp-printall{display:block}#paper .pp-printall .sheet{box-shadow:none;margin:0;max-width:none;padding:0.4in!important;box-sizing:border-box;break-after:auto;page-break-after:auto}#paper .pp-printall .sheet.brk{break-before:page;page-break-before:always}#paper .pp-printall .sheet+.sheet:not(.brk){border-top:4px solid #050505;padding-top:0.25in!important}#paper .pp-printall .ft{display:none}#paper .pp-printall p{orphans:3;widows:3}#paper .pp-printall .jump{display:none}#paper a.jl,#paper button.jl{color:#050505}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}
html::before,html::after,body::before,body::after{display:none!important;content:none!important}
#paper .pp-printall .sheet{font-size:12px}#paper .pp-printall .fp{grid-template-columns:repeat(6,minmax(0,1fr))!important}#paper .pp-printall .pplead{grid-column:1/5!important;border-right:1px solid #8E9196!important;padding-right:16px!important}#paper .pp-printall .rail{grid-column:5/7!important;margin-top:0!important;padding-top:0!important;border-top:0!important}
#paper .pp-printall .fold{grid-template-columns:repeat(3,minmax(0,1fr))!important}#paper .pp-printall .fold>div{border-right:1px solid #8E9196!important;padding-right:16px!important;margin-bottom:0!important;border-bottom:0!important}#paper .pp-printall .fold>div:last-child{border-right:0!important}#paper .pp-printall .fold.one{grid-template-columns:minmax(0,1fr)!important}#paper .pp-printall .fold.one>div{border-right:0!important;padding-right:0!important}
#paper .pp-printall .c3{column-count:3!important}#paper .pp-printall .c2{column-count:2!important}#paper .pp-printall .agate{column-count:4!important;font-size:10.5px}#paper .pp-printall .ear .ppbox{display:block!important}
#paper .pp-printall .txt{font-size:11.5px;line-height:1.42}#paper .pp-printall h2.hd{font-size:30px}#paper .pp-printall .dk{font-size:14px}#paper .pp-printall .brief p{font-size:11.5px}
#paper .pp-printall figure,#paper .pp-printall table,#paper .pp-printall .brief,#paper .pp-printall h2,#paper .pp-printall h3{break-inside:avoid}}`;
let pages=[],cur=0,EV=null,depth=0;
const stories=()=>{const k=TD();return (typeof STORIES!=='undefined'?STORIES:[]).filter(s=>s&&s.slug&&s.title&&s.body&&!(s.until&&s.until<k)&&!(s.date&&s.date>k)).slice().sort((a,b)=>(b.date||'').localeCompare(a.date||''))};
const para=(b,dc)=>{const o=[];let first=true;for(const p of b){if(typeof p!=='string'||p.startsWith('@go ')||p.startsWith('= '))continue;
 if(p.startsWith('## ')){o.push('<h5>'+H(p.slice(3))+'</h5>');continue}
 if(p.startsWith('#T ')){try{const t=JSON.parse(p.slice(3));o.push('<table>'+(t.title?'<caption>'+H(t.title)+'</caption>':'')+(t.head?'<tr>'+t.head.map(h=>'<th>'+H(h)+'</th>').join('')+'</tr>':'')+(t.rows||[]).map(r=>'<tr>'+r.map(c=>'<td>'+H(c)+'</td>').join('')+'</tr>').join('')+'</table>')}catch(_){}continue}
 if(p.startsWith('> ')){o.push('<p><i>'+H(p.slice(2))+'</i></p>');continue}
 o.push('<p'+(first&&dc?' class="dc"':'')+'>'+H(p)+'</p>');first=false}return o.join('')};
const words=b=>b.filter(p=>typeof p==='string'&&!/^(## |#T |@go |= )/.test(p));
const teaser=(s,n)=>{const w=words(s.body);let out=[],c=0;for(const p of w){out.push(p);c+=p.length;if(c>n)break}return out};
const by=s=>'<div class="by">By '+H(SITE())+(s.date?' · '+H(SHORT(s.date)):'')+'</div>';
const top=d=>{const n=EV?EV.filter(e=>e.date===d).length:0;return `<div class="ear"><div class="ppbox"><b>Today in ${H(PLACE())}</b>${n?n.toLocaleString()+' events on the calendar. Listings, Page C1.':'Event listings, Page C1.'}</div><div class="flag">${(()=>{const im=document.querySelector('header.mast img');return im?'<img src="'+H(im.getAttribute('src'))+'" alt="'+H(SITE())+'">':'<div class="nm">'+H(SITE())+'</div>'})()}</div><div class="ppbox"><b>Inside</b>The Dark Wire, D1<br>Seattle Underground, E1</div></div><div class="dl"><span>${H(LONG(d))}</span><span>${H(PLACE())} Edition</span><span>${H(location.hostname.replace(/^www\./,''))}</span></div>`};
const ph=(s)=>s.img?`<figure><img src="${H(s.img)}" alt="${H(s.imgAlt||'')}"><figcaption>${H(s.imgAlt||s.title)}</figcaption></figure>`:'';
const sh=(name,pg)=>`<div class="sh"><b>${H(name)}</b><span>${H(SITE())} · ${H(LONG(TD()))} · Page ${H(pg)}</span></div>`;
const foot=pg=>`<div class="ft"><span>${H(SITE())}</span><span>Page ${H(pg)}</span></div>`;
function build(){
 const S=stories(),d=TD();pages=[];const jumps={};
 const NW=S.filter(s=>s.news).slice(0,4);const feat=S.filter(s=>!s.news);
 const lead=NW[0]||feat[0];const second=NW[1]||null;const rest=feat.filter(s=>s!==lead);
 const fold=NW.slice(2,4).concat(rest).slice(0,3),briefs=rest.filter(s=>!fold.includes(s)).slice(0,6);
 let pgA=2;[lead,second,...fold].forEach(s=>{if(s)jumps[s.slug]='A'+(pgA++)});
 const jl=s=>`<div class="jump"><button class="jl" data-pp="${H(jumps[s.slug])}">Continued on Page ${H(jumps[s.slug])} ›</button></div>`;
 const hl=(window.H&&window.H.items)||[];
 let A1=top(d)+'<div class="fp"><div class="pplead">';
 if(lead)A1+=`<div class="kk">${H(SEC[lead.topic]||'Local')}</div><h2 class="hd">${H(lead.title)}</h2>${lead.dek?'<p class="dk">'+H(lead.dek)+'</p>':''}${by(lead)}${ph(lead)}<div class="txt c3">${teaser(lead,1400).map((p,i)=>'<p'+(i?'':' class="dc"')+'>'+H(p)+'</p>').join('')}</div>${jl(lead)}`;
 A1+='</div><div class="rail"><div class="idx"><b>Inside today</b>'+[['Front page news','A2'],['Arts & Entertainment','B1'],['Event listings','C1'],['The Dark Wire','D1'],['Seattle Underground','E1']].map(([a,b])=>`<div data-pp="${b}"><span>${H(a)}</span><span>${b}</span></div>`).join('')+'</div><div class="kk">In brief</div>'+briefs.map(s=>`<div class="brief"><h4 class="hd">${H(s.title)}</h4><p>${H(s.dek||'')} <button class="jl" data-story="${H(s.slug)}">Read more ›</button></p></div>`).join('')+'</div></div>';
 if(second)A1+=`<div class="fold one" style="grid-template-columns:minmax(0,1fr)"><div><div class="kk">${H(SEC[second.topic]||'Local')}</div><h2 class="hd" style="font-size:36px">${H(second.title)}</h2>${second.dek?'<p class="dk">'+H(second.dek)+'</p>':''}${by(second)}<div class="txt c3">${teaser(second,900).map((p,i)=>'<p'+(i?'':' class="dc"')+'>'+H(p)+'</p>').join('')}</div>${jl(second)}</div></div>`;
 if(fold.length)A1+='<div class="fold">'+fold.map(s=>`<div><div class="kk">${H(SEC[s.topic]||'Local')}</div><h3 class="hd">${H(s.title)}</h3>${by(s)}<div class="txt">${teaser(s,420).map(p=>'<p>'+H(p)+'</p>').join('')}</div>${jl(s)}</div>`).join('')+'</div>';
 pages.push({id:'A1',name:'Front Page',html:A1+foot('A1')});
 [lead,second,...fold].forEach(s=>{if(!s)return;const pg=jumps[s.slug];pages.push({id:pg,name:'Front Page News',html:sh('News',pg)+`<div class="kk">${H(SEC[s.topic]||'Local')} · Continued from Page A1</div><h2 class="hd">${H(s.title)}</h2>${s.dek?'<p class="dk">'+H(s.dek)+'</p>':''}${by(s)}<div class="txt c3">${para(s.body,true)}</div>${(s.sources&&s.sources.length)?'<div class="by" style="border:0;margin-top:10px">Sources: '+s.sources.map(x=>'<a class="jl" href="'+H(x.url)+'" target="_blank" rel="noopener">'+H(x.outlet)+'</a>').join(' · ')+'</div>':''}<div class="jump"><button class="jl" data-pp="A1">‹ Back to the front page</button> · <button class="jl" data-story="${H(s.slug)}">Open this article on the website ›</button></div>`+foot(pg)})});
 // B section: arts
 const arts=S.filter(s=>/music|stage|culture/.test(s.topic)&&!fold.includes(s)&&s!==lead).slice(0,7);let bp=1;
 for(let i=0;i<arts.length;i+=3){const ch=arts.slice(i,i+3),pg='B'+(bp++);const [a,...o]=ch;
  pages.push({id:pg,name:'Arts & Entertainment',html:sh('Arts & Entertainment',pg)+`<div class="kk">${H(a.topic==='music'?'Music':a.topic==='stage'?'On Stage':'Culture')}</div><h2 class="hd">${H(a.title)}</h2>${a.dek?'<p class="dk">'+H(a.dek)+'</p>':''}${by(a)}${ph(a)}<div class="txt c3">${para(a.body,true)}</div>`+(o.length?'<div class="fold" style="grid-template-columns:repeat('+o.length+',minmax(0,1fr))">'+o.map(s=>`<div><h3 class="hd">${H(s.title)}</h3>${by(s)}<div class="txt c2">${para(s.body)}</div></div>`).join('')+'</div>':'')+foot(pg)})}
 // C: listings
 if(EV){const days=[0,1,2].map(n=>{const t=new Date(d+'T12:00:00');t.setDate(t.getDate()+n);return t.toLocaleDateString('en-CA')});
  const CAT={live:'Live music',rock:'Rock, punk & metal',punk:'Rock, punk & metal',metal:'Rock, punk & metal',goth:'Rock, punk & metal',indie:'Live music',jazz:'Live music',country:'Live music',folk:'Live music','hip-hop':'Live music','r&b':'Live music',pop:'Live music',world:'Live music',latin:'Live music',experimental:'Live music',other:'Live music',electronic:'Club nights',classical:'Classical',theater:'Theater & comedy',film:'Film',arts:'Art & museums',community:'Community',talks:'Talks'};
  let h='';for(const dd of days){const L=EV.filter(e=>e.date===dd&&CAT[e.genre]);if(!L.length)continue;h+='<div class="day">'+H(LONG(dd))+'</div>';const g={};L.forEach(e=>{(g[CAT[e.genre]]=g[CAT[e.genre]]||[]).push(e)});
   for(const c of Object.keys(g)){h+='<div class="cat">'+H(c)+'</div>';const seen=new Set();g[c].forEach(e=>{const k=(e.artists||'')+e.venue;if(seen.has(k))return;seen.add(k);h+='<p><b>'+H(e.artists)+'</b>'+(e.time?', '+H(e.time):'')+'. '+H(e.venue||'')+(e.hood&&e.hood!==e.venue?', '+H(e.hood):'')+(e.price?'. '+H(e.price):'')+'.</p>'})}}
  pages.push({id:'C1',name:'Event Listings',html:sh('Event Listings',"C1")+'<div class="agate">'+h+'</div>'+foot('C1')})}
 // D: the dark wire (scream.json) and E: Seattle Underground (directory)
 if(window.__ppScream){const S=window.__ppScream;const L=[].concat(S.crimes||[],S.strange||[],S.scandals||[]).filter(x=>x&&x.h&&x.url);const g={};L.forEach(x=>{const c=x.town||'Dark';(g[c]=g[c]||[]).push(x)});let h='';
  Object.keys(g).forEach(c=>{h+='<div class="day">'+H(c)+'</div>';g[c].forEach(x=>{h+='<p><b>'+H(x.h)+'</b>. '+H(x.outlet||'')+(x.date?', '+H(SHORT(x.date)):'')+'. <a class="jl" href="'+H(x.url)+'" target="_blank" rel="noopener">Read it ›</a></p>'})});
  if(h)pages.push({id:'D1',name:'The Dark Wire',html:sh('The Dark Wire','D1')+'<div class="agate">'+h+'</div>'+foot('D1')})}
 if(window.__ppDir&&window.__ppDir.items){const D=window.__ppDir,C=new Set(D.badass_cats||[]);const g={};D.items.filter(x=>x&&!x.cl&&C.has(x.c)).forEach(x=>{(g[x.c]=g[x.c]||[]).push(x)});let h='';
  Object.keys(g).sort().forEach(c=>{h+='<div class="day">'+H(c)+'</div>';g[c].forEach(x=>{const age=((x.nt||[]).join(' ').match(/Age:\s*([^,;]+)/)||[])[1]||'';h+='<p><b>'+H(x.n)+'</b>'+(age?' ('+H(age)+')':'')+'. '+H(x.a||'')+(x.p?'. '+H(x.p):'')+'.</p>'})});
  if(h)pages.push({id:'E1',name:'Seattle Underground',html:sh('Seattle Underground','E1')+'<div class="agate">'+h+'</div>'+foot('E1')})}
}
function side(){const P=document.getElementById('paper');const L=[];const seen={};pages.forEach((p,i)=>{const k=p.id==='A1'?'Front Page':p.name;if(seen[k]){seen[k].last=p.id;return}seen[k]={i,first:p.id,last:p.id,k};L.push(seen[k])});
 P.querySelector('.pp-list').innerHTML=L.map(x=>{const on=pages[cur].id===x.first||(x.k===(pages[cur].id==='A1'?'Front Page':pages[cur].name));return '<button data-ppgo="'+x.i+'" class="'+(on?'on':'')+'">'+H(x.k)+'<span>'+H(x.first===x.last?x.first:x.first+'–'+x.last)+'</span></button>'}).join('')}
function go_(i,push){cur=(i+pages.length)%pages.length;show();if(push!==false){try{depth++;history.pushState({pp:cur,d:depth},'')}catch(_){}}}
function show(){const P=document.getElementById('paper');const p=pages[cur];side();P.querySelector('.sheet').innerHTML=p.html;P.querySelector('.pp-pg').textContent='Page '+p.id+' · '+(cur+1)+' of '+pages.length;P.scrollTop=0}
async function open(){
 if(!document.getElementById('ppCss')){const st=document.createElement('style');st.id='ppCss';st.textContent=css;document.head.appendChild(st)}
 try{if(!EV){const j=await fetch('data/cal.json',{cache:'no-cache'}).then(r=>r.json());EV=j.events||[]}}catch(_){EV=[]}
 try{if(!window.__ppScream){window.__ppScream=await fetch('data/scream.json',{cache:'no-cache'}).then(r=>r.ok?r.json():null)}}catch(_){} try{if(!window.__ppDir){window.__ppDir=await fetch('data/directory.json',{cache:'no-cache'}).then(r=>r.ok?r.json():null)}}catch(_){}
 build();cur=0;
 let P=document.getElementById('paper');if(!P){P=document.createElement('div');P.id='paper';P.setAttribute('role','dialog');P.setAttribute('aria-label','Newspaper mode');
  P.innerHTML='<div class="pp-bar"><button class="pp-home">⌂ <i class="lg">Back to </i>Page One</button><button class="pp-p">‹ <i class="lg">Previous page</i><i class="sm">Back</i></button><span class="pp-pg"></span><button class="pp-n"><i class="lg">Next page</i><i class="sm">Next</i> ›</button><button class="pp-print-btn">🖨 <i class="lg">Print or save as PDF</i><i class="sm">Print</i></button><button class="pp-x"><i class="lg">Close newspaper</i><i class="sm">Close</i> ✕</button></div><div class="pp-wrap"><nav class="pp-side" aria-label="Sections of the newspaper"><h4>Sections</h4><div class="pp-list"></div><small>Tap a section to go there. The browser back button goes to the page you were on before.</small></nav><div class="sheet"></div></div>';document.body.appendChild(P);
  P.addEventListener('click',e=>{const t=e.target.closest('button,[data-pp]');if(!t||!P.contains(t))return;e.stopPropagation();if(!t)return;
   if(t.classList.contains('pp-x'))return close();if(t.classList.contains('pp-print-btn'))return printAll();if(t.classList.contains('pp-home'))return go_(0);if(t.classList.contains('pp-p'))return go_(cur-1);if(t.classList.contains('pp-n'))return go_(cur+1);if(t.dataset.ppgo!=null)return go_(+t.dataset.ppgo);
   if(t.dataset.pp){const k=pages.findIndex(p=>p.id===t.dataset.pp);if(k>=0)go_(k);return}
   if(t.dataset.story){e.preventDefault();e.stopPropagation();close();try{STATE.story=t.dataset.story;STATE.prev='front';STATE.view='read';render();scrollTo(0,0)}catch(_){location.href='?story='+t.dataset.story}}});
  addEventListener('keydown',e=>{if(!document.getElementById('paper')||document.getElementById('paper').hidden)return;if(e.key==='Escape')close();if(e.key==='ArrowRight')go_(cur+1);if(e.key==='ArrowLeft')go_(cur-1)})}
 P.hidden=false;document.documentElement.style.overflow='hidden';show();depth=1;try{history.pushState({pp:0,d:1},'')}catch(_){}}
addEventListener('popstate',e=>{const P=document.getElementById('paper');if(!P)return;const st=e.state;if(st&&typeof st.pp==='number'){if(P.hidden){P.hidden=false;document.documentElement.style.overflow='hidden'}depth=st.d||1;cur=Math.min(st.pp,pages.length-1);show()}else{depth=0;if(!P.hidden){P.hidden=true;document.documentElement.style.overflow=''}}});
function printAll(){const P=document.getElementById('paper');let A=P.querySelector('.pp-printall');if(!A){A=document.createElement('div');A.className='pp-printall';P.appendChild(A)}
 A.innerHTML=pages.map((p,i)=>'<div class="sheet'+(i&&/1$/.test(p.id)?' brk':'')+'">'+p.html+'</div>').join('');
 const imgs=[...A.querySelectorAll('img')];Promise.all(imgs.map(i=>i.complete?0:new Promise(r=>{i.onload=i.onerror=r}))).then(()=>{try{window.print()}catch(_){}});}
function close(){const P=document.getElementById('paper');if(P)P.hidden=true;document.documentElement.style.overflow='';const n=depth;depth=0;if(n>0){try{history.go(-n)}catch(_){}}}
window.openNewspaper=open;
const btn=()=>{const h=document.querySelector('header.mast');if(!h||document.getElementById('paperBtn'))return;const b=document.createElement('button');b.id='paperBtn';b.type='button';b.textContent='Newspaper Mode';b.addEventListener('click',open);h.appendChild(b)};
btn();addEventListener('DOMContentLoaded',btn);
})();
