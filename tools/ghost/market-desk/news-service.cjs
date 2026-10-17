'use strict';
const {SOURCES,REPORTING_SOURCES,REGIONS,MARKETS,RESOURCES,classify}=require('./catalog.cjs');
const {parseFeed,parsePublication}=require('./feed-reader.cjs');
const {createNewsDiscovery}=require('./news-discovery.cjs');
const {priority,selectLeads}=require('./news-priority.cjs');
function createWorldNews({fetchImpl=fetch,clock=()=>Date.now(),sources=SOURCES,includeReporting=false}={}){
 sources=includeReporting?[...sources,...REPORTING_SOURCES]:sources;
 const discovery=includeReporting?createNewsDiscovery({fetchImpl,clock}):null;
 const cache=new Map();let pending;
 async function read(source){
  const prior=cache.get(source.id),now=clock();
  if(prior&&now<prior.retryAt)return prior;
  try{
   const response=await fetchImpl(source.url,{headers:{Accept:'application/rss+xml, application/atom+xml, application/xml, text/xml','User-Agent':'GhostMarketDesk/1.0 public RSS reader'},redirect:'manual',signal:AbortSignal.timeout(9000),cf:{cacheTtl:300,cacheEverything:true}});
   if(!response.ok)throw Error('source_unavailable');
   const reader=response.body?.getReader();let text='';
   if(reader){const parts=[];let size=0;for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>1500000){await reader.cancel();throw Error('payload_too_large')}parts.push(value)}const all=new Uint8Array(size);let at=0;for(const p of parts){all.set(p,at);at+=p.length}text=new TextDecoder().decode(all)}else{text=await response.text();if(text.length>1500000)throw Error('payload_too_large')}
   const parsed=(source.format==='usda-publication'?parsePublication:parseFeed)(text,source),result={...parsed,lastFetchedAt:new Date(now).toISOString(),retryAt:now+300000,status:'available'};cache.set(source.id,result);return result;
  }catch{
   const usable=prior?.lastFetchedAt&&now-Date.parse(prior.lastFetchedAt)<3600000;
   const result={stories:usable?prior.stories:[],rejectedDates:prior?.rejectedDates||0,lastFetchedAt:usable?prior.lastFetchedAt:null,retryAt:now+60000,status:usable?'cached':'unavailable'};cache.set(source.id,result);return result;
  }
 }
 async function collect(){
  const now=clock(),results=[];let next=0;const reporting=discovery?.news();
  await Promise.all(Array.from({length:Math.min(6,sources.length)},async()=>{for(;;){const i=next++;if(i>=sources.length)return;results[i]=await read(sources[i])}}));
  const seen=new Set(),articles=[],upcoming=[],health=[];
  sources.forEach((source,i)=>{
   const r=results[i],valid=r.stories.filter(s=>Date.parse(s.publishedAt)>=now-90*86400000&&Date.parse(s.publishedAt)<=now+300000);
   health.push({id:source.id,name:source.name,url:source.url,country:source.country,region:source.region,status:r.status==='available'&&!valid.length?'no_recent_releases':r.status,itemCount:valid.length,lastFetchedAt:r.lastFetchedAt,latestPublishedAt:valid.length?new Date(Math.max(...valid.map(s=>Date.parse(s.publishedAt)))).toISOString():null,rejectedDates:r.rejectedDates});
   for(const story of r.stories){
    const age=now-Date.parse(story.publishedAt),entry={...story,...classify(story.title,source),cached:r.status==='cached'};
    if(age< -300000){if(age>=-14*86400000)upcoming.push(entry);continue}
    if(age>90*86400000||seen.has(story.url))continue;seen.add(story.url);articles.push(entry);
   }
  });
  if(reporting){const r=await reporting;for(const a of r.articles){if(seen.has(a.url))continue;seen.add(a.url);articles.push({...a,...classify(a.title,{country:'GLOBAL',region:'global',topics:[]})})}health.push({id:'gdelt',name:'GDELT · public news discovery',url:'https://www.gdeltproject.org/',status:r.status,itemCount:r.articles.length,lastFetchedAt:r.lastFetchedAt,latestPublishedAt:null})}
  articles.sort((a,b)=>Date.parse(b.publishedAt||b.observedAt)-Date.parse(a.publishedAt||a.observedAt));upcoming.sort((a,b)=>Date.parse(a.publishedAt)-Date.parse(b.publishedAt));
  const enriched=articles.slice(0,600).map(a=>priority(a,now));
  return {articles:enriched,leadArticles:selectLeads(enriched),upcoming:upcoming.slice(0,30),sources:health,checkedAt:new Date(now).toISOString(),pollSeconds:300,historyDays:90,coverage:includeReporting?'Official releases, attributed publisher headlines and GDELT news discovery. GDELT dates identify first observation, not publication.':'Official releases and economic reports.',taxonomy:{regions:REGIONS,markets:MARKETS},resources:RESOURCES};
 }
 return {async news(){if(!pending)pending=collect().finally(()=>{pending=null});return pending}};
}
module.exports={createWorldNews};
