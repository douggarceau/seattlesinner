'use strict';
const {cleanText}=require('../official-feeds.cjs');
function parseFeed(xml,source){
 if(typeof xml!=='string'||/<!DOCTYPE|<!ENTITY/i.test(xml)||!/<(?:rss|feed|rdf:RDF)\b/i.test(xml))throw Error('invalid_feed');
 const items=[...xml.matchAll(/<(item|entry)(?:\s[^>]*)?>([\s\S]*?)<\/\1>/gi)].slice(0,120);
 const stories=[];let rejectedDates=0;
 for(const [,kind,item]of items){
  const tag=name=>cleanText(item.match(new RegExp('<'+name+'(?:\\s[^>]*)?>([\\s\\S]*?)<\\/'+name+'>','i'))?.[1]);
  const title=tag('title');let link=tag('link');
  if(kind.toLowerCase()==='entry')for(const [,attrs] of item.matchAll(/<link\b([^>]*)\/?\s*>/gi)){
   const a=Object.fromEntries([...attrs.matchAll(/([\w:-]+)\s*=\s*(["'])(.*?)\2/g)].map(([,k,,v])=>[k.toLowerCase(),v]));
   if(a.href&&(!a.rel||a.rel==='alternate')){link=cleanText(a.href);break}
  }
  let raw=tag('pubDate')||tag('published')||tag('dc:date')||tag('updated');
  if(!/\b(?:19|20)\d{2}\b/.test(raw)){rejectedDates++;continue}
  const dateOnly=/^\d{4}-\d{2}-\d{2}$/.test(raw);
  if(!dateOnly&&!/(?:Z|[+-]\d\d:?\d\d|\b(?:GMT|UTC|EST|EDT|CST|CDT|PST|PDT))$/i.test(raw)){
   if(!source.timezone){rejectedDates++;continue}raw+=' '+source.timezone;
  }
  const time=Date.parse(raw);if(!Number.isFinite(time)){rejectedDates++;continue}
  if(title.length<10||title.length>300||!link)continue;
  let url;try{
   url=new URL(link,source.url);
   if(!source.hosts.includes(url.hostname)||url.port||url.username||url.password||!['http:','https:'].includes(url.protocol))continue;
   url.protocol='https:';url.hash='';
  }catch{continue}
  const author=source.kind==='news_report'?([...item.matchAll(/<author\b[^>]*>[\s\S]*?<name\b[^>]*>([\s\S]*?)<\/name>[\s\S]*?<\/author>/gi)].map(m=>cleanText(m[1])).join('; ')||tag('dc:creator')).slice(0,1000):'';
  stories.push({title,url:url.href,source:source.name,sourceId:source.id,publishedAt:new Date(time).toISOString(),datePrecision:dateOnly?'day':'time',kind:source.kind||'official_release',...(author?{author}:{})});
 }
 if(!stories.length)throw Error(rejectedDates?'invalid_dates':'empty_feed');
 return {stories,rejectedDates};
}
function parsePublication(html,source){
 // One fixed USDA report archive, using its published release date and report link.
 if(source.id!=='wasde'||typeof html!=='string')throw Error('invalid_publication');
 const stories=[];
 for(const [row] of html.matchAll(/<tr\b[^>]*>[\s\S]*?<\/tr>/gi)){
  const date=row.match(/<time\b[^>]*datetime=["'](\d{4}-\d{2}-\d{2}T[\d:]+Z)["']/i)?.[1];
  const link=row.match(/href=["'](\/publication\/world-agricultural-supply-and-demand-estimates\/\d{4}-\d{2}-\d{2})["']/i)?.[1];
  if(!date||!link||!Number.isFinite(Date.parse(date)))continue;
  stories.push({title:'World Agricultural Supply and Demand Estimates — '+date.slice(0,10),url:new URL(link,source.url).href,source:source.name,sourceId:source.id,publishedAt:new Date(date).toISOString(),datePrecision:'time',kind:'official_report'});
 }
 if(!stories.length)throw Error('empty_publication');
 return {stories:stories.slice(0,120),rejectedDates:0};
}
module.exports={parseFeed,parsePublication};
