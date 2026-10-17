'use strict';
const {countries}=require('./catalog.js'),markets=require('./markets.js');
const {boundedText}=require('../market-desk/market-data.cjs');
const {createNewsDiscovery}=require('../market-desk/news-discovery.cjs');
const METRICS=[
 ['NY.GDP.MKTP.CD','GDP','USD'],['NY.GDP.MKTP.KD.ZG','Real GDP growth','%'],['FP.CPI.TOTL.ZG','Consumer inflation','%'],['SL.UEM.TOTL.ZS','Unemployment','%'],['NE.EXP.GNFS.ZS','Exports / GDP','%'],['BX.KLT.DINV.WD.GD.ZS','Net FDI inflows / GDP','%']
].map(([id,label,unit])=>({id,label,unit}));
const topics=new Map([['all','economy OR markets OR trade OR inflation']]);
for(const m of markets){topics.set(m.id,m.name);for(const s of m.sectors){topics.set(s.id,s.name);for(const [id,name]of s.topics)topics.set(id,name)}}
function parseIndicators(raw,country,now=Date.now()){
 const d=JSON.parse(raw);if(!Array.isArray(d)||!Array.isArray(d[1]))throw Error('invalid_indicators');
 if(Number(d[0]?.pages)>1)throw Error('incomplete_indicator_page');
 const year=new Date(now).getUTCFullYear();
 const rows=d[1].filter(r=>(r.country?.id===country.worldbank||r.countryiso3code===country.worldbank)&&/^\d{4}$/.test(r.date)&&+r.date<=year&&+r.date>=year-10&&typeof r.value==='number'&&Number.isFinite(r.value));
 return METRICS.map(m=>{const matches=rows.filter(r=>r.indicator?.id===m.id).sort((a,b)=>+b.date-+a.date);const r=matches[0],prior=matches.find(v=>r&&v.date!==r.date);return {...m,value:r?.value??null,year:r?.date??null,priorValue:prior?.value??null,priorYear:prior?.date??null,sourceUrl:'https://data.worldbank.org/indicator/'+m.id+'?locations='+country.worldbank}});
}
function createCountryDesk({fetchImpl=fetch,clock=()=>Date.now()}={}){
 const macroCache=new Map(),pending=new Map(),newsCache=new Map();
 const cap=map=>{while(map.size>48)map.delete(map.keys().next().value)};
 async function macro(c){const now=clock(),old=macroCache.get(c.code);if(old&&now<old.retryAt)return old;
  if(pending.has(c.code))return pending.get(c.code);
  const task=(async()=>{if(!c.worldbank)return {status:'not_covered',metrics:[],checkedAt:new Date(now).toISOString(),sourceUpdatedAt:null};
   const url='https://api.worldbank.org/v2/country/'+c.worldbank+'/indicator/'+METRICS.map(m=>m.id).join(';')+'?source=2&date='+(new Date(now).getUTCFullYear()-10)+':'+new Date(now).getUTCFullYear()+'&format=json&per_page=100';
   let result;try{const raw=await boundedText(fetchImpl,url),parsed=JSON.parse(raw),metrics=parseIndicators(raw,c,now);result={status:metrics.some(m=>m.value!==null)?'available':'no_observations',metrics,checkedAt:new Date(now).toISOString(),sourceUpdatedAt:parsed[0]?.lastupdated||null,retryAt:now+3600000,sourceUrl:url};}catch{const usable=old?.metrics?.some(m=>m.value!==null)&&now-Date.parse(old.checkedAt)<86400000;result={status:usable?'cached':'unavailable',metrics:usable?old.metrics:[],checkedAt:usable?old.checkedAt:new Date(now).toISOString(),sourceUpdatedAt:usable?old.sourceUpdatedAt:null,retryAt:now+60000,sourceUrl:url}}
   macroCache.set(c.code,result);cap(macroCache);return result;
  })().finally(()=>pending.delete(c.code));pending.set(c.code,task);return task;
 }
 return {async read(code,topic='all'){
  const c=countries.find(c=>c.code===code);if(!c||!topics.has(topic))return {status:400,body:{error:'invalid_country_or_topic'}};
  const key=c.code+':'+topic;let news=newsCache.get(key);if(!news){const name=c.code==='GE'?'Georgia Tbilisi':c.code==='CG'?'Congo Brazzaville':c.code==='CD'?'Democratic Republic of the Congo':c.name.replace(/\s*\/.*$/,'');const terms=topic==='all'?'(economy OR markets OR trade OR inflation)':'('+topics.get(topic).replaceAll('/','&').split('&').map(s=>'"'+s.trim().replace(/["()]/g,'')+'"').join(' OR ')+')';news=createNewsDiscovery({fetchImpl,clock,query:'"'+name.replace(/["()]/g,'')+'" '+terms+' sourcelang:english'});newsCache.set(key,news);cap(newsCache)}
  const [economy,reporting]=await Promise.all([macro(c),news.news()]);return {status:200,body:{country:c.code,topic,economy,news:reporting,checkedAt:new Date(clock()).toISOString(),coverage:'Annual World Bank observations and English-language country/topic news discovery. Keyword matches require geographic verification; country menus do not imply complete data coverage.'}};
 }};
}
module.exports={createCountryDesk,parseIndicators,METRICS};
