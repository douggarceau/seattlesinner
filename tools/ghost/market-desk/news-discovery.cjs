'use strict';
// GDELT supplies public news-link metadata. First-seen time is never presented as publication time.
const {cleanText}=require('../official-feeds.cjs');
const ENDPOINT='https://api.gdeltproject.org/api/v2/doc/doc';
const QUERY='(economy OR inflation OR tariffs OR "artificial intelligence" OR "stock market" OR bitcoin OR "crude oil") sourcelang:english';
const PUBLISHERS=['reuters.com','apnews.com','bbc.com','bbc.co.uk','cnbc.com','npr.org','ft.com','wsj.com','bloomberg.com','aljazeera.com','techcrunch.com','coindesk.com','fortune.com','cnn.com','abcnews.go.com','cbsnews.com','sciencedaily.com'];
function publisherUrl(raw){try{const u=new URL(raw);if(u.protocol!=='https:'||u.username||u.password||u.port||!PUBLISHERS.some(h=>u.hostname===h||u.hostname.endsWith('.'+h)))return null;u.hash='';for(const k of [...u.searchParams.keys()])if(/^utm_|^(fbclid|gclid)$/i.test(k))u.searchParams.delete(k);return u.href}catch{return null}}
function normalize(body,now=Date.now()){
 if(!body||!Array.isArray(body.articles))throw Error('invalid_news_index');
 const seen=new Set();return body.articles.slice(0,250).flatMap(a=>{
  const url=publisherUrl(a.url),title=cleanText(a.title),raw=String(a.seendate||'');
  const stamp=/^\d{8}T\d{6}Z$/.test(raw)?raw.replace(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/,'$1-$2-$3T$4:$5:$6Z'):raw;
  const time=Date.parse(stamp);if(!url||seen.has(url)||title.length<12||title.length>300||!Number.isFinite(time)||time>now+300000||now-time>7*86400000)return [];seen.add(url);
  return [{title,url,source:new URL(url).hostname.replace(/^www\./,''),sourceId:'gdelt',kind:'news_report',publishedAt:null,observedAt:new Date(time).toISOString(),datePrecision:'observed',verified:false}];
 });
}
function createNewsDiscovery({fetchImpl=fetch,clock=()=>Date.now(),query=QUERY}={}){
 let result=null,retryAt=0,pending;
 async function collect(){
  const now=clock();if(result&&now<retryAt)return result;
  try{
   const u=new URL(ENDPOINT);for(const [k,v]of Object.entries({query,mode:'artlist',format:'json',maxrecords:'150',timespan:'3d',sort:'datedesc'}))u.searchParams.set(k,v);
   const r=await fetchImpl(u.href,{headers:{Accept:'application/json'},redirect:'manual',signal:AbortSignal.timeout(12000),cf:{cacheTtl:900,cacheEverything:true}});if(!r.ok)throw Error('news_index_unavailable');
   const reader=r.body?.getReader();let raw='';if(reader){let bytes=0;const decoder=new TextDecoder();for(;;){const p=await reader.read();if(p.done)break;bytes+=p.value.byteLength;if(bytes>750000){await reader.cancel();throw Error('payload_too_large')}raw+=decoder.decode(p.value,{stream:true})}raw+=decoder.decode()}else{raw=await r.text();if(raw.length>750000)throw Error('payload_too_large')}
   const articles=normalize(JSON.parse(raw),now);result={articles,status:articles.length?'available':'no_recent_releases',lastFetchedAt:new Date(now).toISOString()};retryAt=now+900000;
  }catch{const usable=result?.lastFetchedAt&&now-Date.parse(result.lastFetchedAt)<3600000;result={articles:usable?result.articles.map(a=>({...a,cached:true})):[],status:usable?'cached':'unavailable',lastFetchedAt:usable?result.lastFetchedAt:null};retryAt=now+900000}
  return result;
 }
 return {async news(){if(!pending)pending=collect().finally(()=>{pending=null});return pending}};
}
module.exports={createNewsDiscovery,normalize,publisherUrl,PUBLISHERS};
