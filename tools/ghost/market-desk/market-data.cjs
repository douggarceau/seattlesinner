'use strict';
const {buildAssessments}=require('./market-insights.cjs');
const DAY=86400000;
const SOURCES={
 treasury:{id:'treasury',name:'U.S. Treasury',url:'https://home.treasury.gov/treasury-daily-interest-rate-xml-feed',cadence:'Daily closing par yields',maxAge:7*DAY},
 fx:{id:'fx',name:'European Central Bank',url:'https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html',cadence:'Daily reference rates',maxAge:7*DAY},
 sofr:{id:'sofr',name:'Federal Reserve Bank of New York',url:'https://www.newyorkfed.org/markets/reference-rates/sofr',cadence:'Prior business-day overnight rate',maxAge:7*DAY},
 oil:{id:'oil',name:'U.S. Energy Information Administration',url:'https://www.eia.gov/petroleum/supply/weekly/',cadence:'Weekly inventories',maxAge:16*DAY},
 crypto:{id:'crypto',name:'Coinbase Exchange',url:'https://www.coinbase.com/advanced-trade/spot/BTC-USD',cadence:'Rolling 24-hour statistics',maxAge:15*60000}
};
const num=value=>typeof value==='number'?Number.isFinite(value)?value:null:typeof value==='string'&&/^-?\d+(?:,\d{3})*(?:\.\d+)?$/.test(value.trim())?Number(value.replaceAll(',','')):null;
const day=value=>{const d=String(value||'').slice(0,10);return /^\d{4}-\d{2}-\d{2}$/.test(d)&&new Date(d+'T00:00:00Z').toISOString().slice(0,10)===d?d:null};
const change=(a,b,scale=1)=>a!==null&&b!==null?(a-b)*scale:null;
function metric(id,label,value,previous,asOf,priorAsOf,unit,group,extra={}){return {id,label,value,previous,asOf,priorAsOf,unit,group,sourceId:group,change:change(value,previous,unit==='percent'?100:1),changeUnit:unit==='percent'?'bps':unit,comparison:'previous observation',...extra}}
const TERMS=[['3m','3 MONTH','BC_3MONTH'],['2y','2 YEAR','BC_2YEAR'],['5y','5 YEAR','BC_5YEAR'],['10y','10 YEAR','BC_10YEAR'],['30y','30 YEAR','BC_30YEAR']];
function treasuryRows(xml){
 if(/<!DOCTYPE|<!ENTITY/i.test(xml))throw Error('invalid_xml');
 return [...xml.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(([,entry])=>{
  const get=key=>entry.match(new RegExp('<(?:\\w+:)?'+key+'(?:\\s[^>]*)?>([^<]*)<\\/(?:\\w+:)?'+key+'>','i'))?.[1];
  return {date:day(get('NEW_DATE')),values:TERMS.map(([, ,key])=>num(get(key)))};
 }).filter(r=>r.date&&r.values.some(v=>v!==null)).sort((a,b)=>b.date.localeCompare(a.date));
}
function parseTreasury(xml){
 const rows=treasuryRows(xml),[a,b]=rows;if(!a)throw Error('missing_yields');
 const metrics=TERMS.map(([id,label],i)=>metric('ust-'+id,'Treasury '+label.toLowerCase(),a.values[i],b?.values[i]??null,a.date,b?.date??null,'percent','treasury'));
 const spread=r=>r&&r.values[3]!==null&&r.values[1]!==null?(r.values[3]-r.values[1])*100:null;
 metrics.push(metric('curve','10-year − 2-year',spread(a),spread(b),a.date,b?.date??null,'bps','treasury'));
 return {metrics:metrics.filter(m=>m.value!==null),curve:{date:a.date,priorDate:b?.date??null,points:TERMS.map(([id,label],i)=>({id,label,value:a.values[i],previous:b?.values[i]??null}))}};
}
function parseFx(xml){
 if(/<!DOCTYPE|<!ENTITY/i.test(xml))throw Error('invalid_xml');
 const rows=[...xml.matchAll(/<Cube\s+time=['"]([^'"]+)['"]>([\s\S]*?)<\/Cube>/g)].map(([,d,body])=>({date:day(d),rates:Object.fromEntries([...body.matchAll(/<Cube\s+currency=['"]([A-Z]{3})['"]\s+rate=['"]([^'"]+)['"]/g)].map(([,c,r])=>[c,num(r)]))})).filter(r=>r.date).sort((a,b)=>b.date.localeCompare(a.date));
 const [a,b]=rows;if(!a)throw Error('missing_fx');
 const rates=[['eur-usd','EUR / USD',r=>r.USD,'USD per euro'],['usd-jpy','USD / JPY',r=>r.USD>0&&r.JPY>0?r.JPY/r.USD:null,'yen per dollar'],['gbp-usd','GBP / USD',r=>r.USD>0&&r.GBP>0?r.USD/r.GBP:null,'USD per pound']];
 const metrics=rates.map(([id,label,calc,note])=>{const value=calc(a.rates)??null,previous=b?calc(b.rates)??null:null;return metric(id,label,value,previous,a.date,b?.date??null,'rate','fx',{note,change:value!==null&&previous>0?(value/previous-1)*100:null,changeUnit:'pct',derived:id!=='eur-usd'})}).filter(m=>m.value>0);
 if(!metrics.length)throw Error('missing_fx');return {metrics};
}
function parseSofr(raw){const rows=JSON.parse(raw).refRates?.filter(r=>r.type==='SOFR'&&day(r.effectiveDate)&&num(r.percentRate)!==null).sort((a,b)=>b.effectiveDate.localeCompare(a.effectiveDate)),[a,b]=rows||[];if(!a)throw Error('missing_sofr');return {metrics:[metric('sofr','Overnight funding · SOFR',num(a.percentRate),num(b?.percentRate),a.effectiveDate,b?.effectiveDate??null,'percent','sofr')]}}
function csv(text){return text.trim().split(/\r?\n/).map(line=>[...line.matchAll(/"((?:[^"]|"")*)"(?:,|$)/g)].map(m=>m[1].replaceAll('""','"')))}
function parseOil(raw){
 const rows=csv(raw),header=rows[0],date=s=>{const p=s?.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/);return p?day((p[3].length===2?'20':'')+p[3]+'-'+p[1].padStart(2,'0')+'-'+p[2].padStart(2,'0')):null};
 const asOf=date(header?.[1]),priorAsOf=date(header?.[2]);if(!asOf)throw Error('missing_oil_date');
 const fields=[['crude','Commercial crude stocks','Commercial (Excluding SPR)'],['gasoline','Gasoline stocks','Total Motor Gasoline'],['distillate','Diesel & heating oil stocks','Distillate Fuel Oil']];
 const metrics=fields.map(([id,label,key])=>{const r=rows.find(r=>r[0]===key)||[];return metric(id,label,num(r[1]),num(r[2]),asOf,priorAsOf,'million barrels','oil',{comparison:'previous week',yearAgo:num(r[5]),yearChange:num(r[7]),note:'Week ending · excludes SPR where applicable'})}).filter(m=>m.value!==null);
 if(!metrics.length)throw Error('missing_oil');return {metrics};
}
function parseCrypto(raw,symbol,now){const r=JSON.parse(raw),value=num(r.last),open=num(r.open);if(!(value>0&&open>0))throw Error('missing_crypto');return {metrics:[metric(symbol.toLowerCase(),symbol+' / USD',value,open,new Date(now).toISOString(),null,'usd','crypto',{change:(value/open-1)*100,changeUnit:'pct',comparison:'rolling 24 hours',timestampKind:'retrieved',low:num(r.low),high:num(r.high),sourceUrl:'https://www.coinbase.com/advanced-trade/spot/'+symbol+'-USD'})]}}
async function boundedText(fetchImpl,input){
 let url=new URL(input);
 for(let hop=0;hop<3;hop++){
  const response=await fetchImpl(url.href,{redirect:'manual',headers:{Accept:'application/json, application/xml, text/csv, text/plain','User-Agent':'GhostMarketDesk/1.0 public data reader'},signal:AbortSignal.timeout(12000),cf:{cacheTtl:300,cacheEverything:true}});
  if([301,302,303,307,308].includes(response.status)){
   const location=response.headers.get('location');if(!location)throw Error('redirect_rejected');const next=new URL(location,url);
   if(url.hostname!=='ir.eia.gov'||next.hostname!=='ir.eia.gov'||next.protocol!=='https:'||next.port||next.username||next.password||!next.pathname.startsWith('/secure/wpsr/'))throw Error('redirect_rejected');
   await response.body?.cancel();url=next;continue;
  }
  if(!response.ok)throw Error('source_unavailable');
  const reader=response.body?.getReader();if(!reader){const text=await response.text();if(text.length>1500000)throw Error('oversize');return text}
  let size=0,text='';const decoder=new TextDecoder();for(;;){const part=await reader.read();if(part.done)break;size+=part.value.byteLength;if(size>1500000){await reader.cancel();throw Error('oversize')}text+=decoder.decode(part.value,{stream:true})}return text+decoder.decode();
 }
 throw Error('redirect_limit');
}
function createMarketData({fetchImpl=fetch,clock=()=>Date.now()}={}){
 const cache=new Map();let pending;
 async function read(id,source,url,parse){const now=clock(),prior=cache.get(id);if(prior&&prior.retryAt>now)return prior;
  try{let raw=await boundedText(fetchImpl,url);if(id==='treasury'&&treasuryRows(raw).length<2){const previous=new Date(now);previous.setUTCDate(1);previous.setUTCMonth(previous.getUTCMonth()-1);raw+=await boundedText(fetchImpl,url.replace(/\d{6}$/,(previous.getUTCFullYear()*100+previous.getUTCMonth()+1).toString()))}
   const result=parse(raw);if(result.metrics.some(m=>Date.parse(m.asOf)>now+300000))throw Error('future_observation');const out={...result,id,sourceId:source,status:'available',fetchedAt:new Date(now).toISOString(),retryAt:now+(source==='crypto'?60000:900000)};cache.set(id,out);return out;
  }catch{const usable=prior?.fetchedAt&&now-Date.parse(prior.fetchedAt)<(source==='crypto'?15*60000:DAY);const out={...(usable?prior:{metrics:[]}),id,sourceId:source,status:usable?'cached':'unavailable',retryAt:now+60000};cache.set(id,out);return out}
 }
 async function collect(){const now=clock(),date=new Date(now),month=date.getUTCFullYear()*100+date.getUTCMonth()+1;
  const results=await Promise.all([
   read('treasury','treasury','https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month='+month,parseTreasury),
   read('fx','fx','https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml',parseFx),
   read('sofr','sofr','https://markets.newyorkfed.org/api/rates/secured/sofr/last/5.json',parseSofr),
   read('oil','oil','https://ir.eia.gov/wpsr/table1.csv',parseOil),
   ...['BTC','ETH','SOL'].map(s=>read(s,'crypto','https://api.exchange.coinbase.com/products/'+s+'-USD/stats',r=>parseCrypto(r,s,now)))
  ]);
  const metrics=results.flatMap(r=>r.metrics.map(m=>({...m,source:SOURCES[m.sourceId].name,sourceUrl:m.sourceUrl||SOURCES[m.sourceId].url,fetchedAt:r.fetchedAt,status:r.status,stale:now-Date.parse(m.asOf)>SOURCES[m.sourceId].maxAge})));
  return {checkedAt:new Date(now).toISOString(),metrics,curve:results.find(r=>r.id==='treasury')?.curve||null,assessments:buildAssessments(metrics),sources:results.map(r=>({id:r.id,...SOURCES[r.sourceId],feedId:r.id,status:r.status,fetchedAt:r.fetchedAt||null})),methodology:'Changes, cross rates and interpretations are calculated by Ghost from the named public sources. Daily and weekly observations are not live tradable prices. Interpretations explain mechanisms; they are not forecasts or personalized recommendations.'};
 }
 return {async snapshot(){if(!pending)pending=collect().finally(()=>pending=null);return pending}};
}
module.exports={createMarketData,parseTreasury,parseFx,parseSofr,parseOil,parseCrypto,boundedText};
