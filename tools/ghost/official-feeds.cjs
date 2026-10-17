'use strict';
// Fixed publisher URLs only. Visitors cannot turn this reader into an outbound proxy.
const OFFICIAL_FEEDS=Object.freeze([
 {id:'federalReserve',name:'Federal Reserve',url:'https://www.federalreserve.gov/feeds/press_all.xml',hosts:['www.federalreserve.gov']},
 {id:'fedSpeeches',name:'Fed speeches',url:'https://www.federalreserve.gov/feeds/speeches.xml',hosts:['www.federalreserve.gov']},
 {id:'inflation',name:'BLS inflation',url:'https://www.bls.gov/feed/cpi.rss',hosts:['www.bls.gov']},
 {id:'employment',name:'BLS jobs',url:'https://www.bls.gov/feed/empsit.rss',hosts:['www.bls.gov']},
 {id:'economicAnalysis',name:'BEA economy',url:'https://apps.bea.gov/rss/rss.xml',hosts:['www.bea.gov','apps.bea.gov']}
]);
function cleanText(value){
 return String(value||'').replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,'$1').replace(/<[^>]*>/g,'')
  .replace(/&(amp|lt|gt|quot|apos);/g,(_,e)=>({amp:'&',lt:'<',gt:'>',quot:'"',apos:"'"}[e]))
  .replace(/&#(x[0-9a-f]+|\d{1,7});/gi,(m,n)=>{const cp=n[0].toLowerCase()==='x'?parseInt(n.slice(1),16):Number(n);return cp>0&&cp<=0x10ffff&&!(cp>=0xd800&&cp<=0xdfff)?String.fromCodePoint(cp):''})
  .replace(/\s+/g,' ').trim();
}
function parseOfficialFeed(xml,feed){
 if(typeof xml!=='string'||/<!DOCTYPE|<!ENTITY/i.test(xml)||!/<(?:rss|feed)\b/i.test(xml))throw Error('invalid_feed');
 const entries=[...xml.matchAll(/<(item|entry)(?:\s[^>]*)?>([\s\S]*?)<\/\1>/gi)].slice(0,50);
 const stories=entries.map(([,kind,item])=>{
  const tag=name=>cleanText(item.match(new RegExp('<'+name+'(?:\\s[^>]*)?>([\\s\\S]*?)<\\/'+name+'>','i'))?.[1]);
  let link=tag('link');
  if(kind.toLowerCase()==='entry'){
   for(const [,attributes] of item.matchAll(/<link\b([^>]*)\/?\s*>/gi)){
    const attrs=Object.fromEntries([...attributes.matchAll(/([\w:-]+)\s*=\s*(["'])(.*?)\2/g)].map(([,name,,value])=>[name.toLowerCase(),value]));
    if(attrs.href&&(!attrs.rel||attrs.rel==='alternate')){link=cleanText(attrs.href);break}
   }
  }
  const title=tag('title'),publishedAt=tag('pubDate')||tag('published')||tag('updated');
  if(title.length<12||title.length>240||!Number.isFinite(Date.parse(publishedAt)))return null;
  let u;try{u=new URL(link);if(u.protocol!=='https:'||!feed.hosts.includes(u.hostname)||u.port||u.username||u.password)return null}catch{return null}
  return {title,url:u.href,source:feed.name,publishedAt:new Date(publishedAt).toISOString(),tickers:[],impact:'general',direction:'uncertain',verified:true};
 }).filter(Boolean);
 // HTML error pages and incompatible/nonempty feeds must not report a healthy connection.
 if(!stories.length)throw Error('empty_feed');
 return stories;
}
module.exports={OFFICIAL_FEEDS,cleanText,parseOfficialFeed};
