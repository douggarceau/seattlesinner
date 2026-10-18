// Rebuilds data/pm-teaser.json (front-page Power Map teaser box) from tech/index.html.
// Run after the Power Map refresh: node src/pm_teaser.js  (needs playwright; paths are absolute to the clone at /home/claude/ss, adjust if needed)
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file:///home/claude/ss/tech/index.html',{waitUntil:'domcontentloaded'});await p.waitForTimeout(2500);
const d=await p.evaluate(()=>{
 const nm=id=>byId[id].n, col=id=>{try{let c=colOf(id);const m=/^var\((--[^)]+)\)$/.exec(c);if(m)c=getComputedStyle(document.documentElement).getPropertyValue(m[1]).trim()||"#8fb3d9";return c}catch(e){return "#8fb3d9"}};
 const cnt=(arr,f)=>{const m={};arr.forEach(x=>{const k=f(x);if(k&&byId[k])m[k]=(m[k]||0)+1});return Object.entries(m).sort((a,b)=>b[1]-a[1]).slice(0,4)};
 const deg={};E.forEach(e=>{deg[e[0]]=(deg[e[0]]||0)+1;deg[e[1]]=(deg[e[1]]||0)+1});
 const R=(t,rows)=>({t,rows:rows.map(([id,v])=>({n:nm(id),v,c:col(id)}))});
 const cats=[
  R("Most valuable in tech",N.slice().sort((a,b)=>(b.b||0)-(a.b||0)).slice(0,4).map(n=>[n.id,(n.v||"").replace(/ \(.*\)/,"")])),
  R("Most connected players",Object.entries(deg).filter(([k])=>byId[k]).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([k,v])=>[k,v+" links"])),
  R("Most government contracts",cnt(CON,c=>c.co).map(([k,v])=>[k,v+""])),
  R("Most military & spy agency ties",cnt(MIL,m=>m.co).map(([k,v])=>[k,v+""])),
  R("Biggest China players",N.filter(n=>n.c==="china").sort((a,b)=>(b.b||0)-(a.b||0)).slice(0,4).map(n=>[n.id,(n.v||"").replace(/ \(.*\)/,"")])),
  R("Top AI labs by value",N.filter(n=>n.c==="labs").sort((a,b)=>(b.b||0)-(a.b||0)).slice(0,4).map(n=>[n.id,(n.v||"").replace(/ \(.*\)/,"")]))
 ].filter(c=>c.rows.length===4);
 let stocks=[];try{stocks=INV.filter(x=>x.ticker&&x.price).slice(0,30).map(x=>({tk:x.ticker,n:byId[x.id]?byId[x.id].n:x.id,p:x.price,cap:x.mktcap,ytd:x.ytd,c:col(x.id)}))}catch(e){}
 return {nodes:N.length,links:E.length,cats,stocks}});
require('fs').writeFileSync('/home/claude/ss/data/pm-teaser.json',JSON.stringify(d));console.log(d.nodes,d.links,d.cats.length,d.stocks.length,JSON.stringify(d.stocks[0]),JSON.stringify(d.cats[0]));await b.close()})()
