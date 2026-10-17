'use strict';
const {createBoardCrypto}=require('../investing/crypto.cjs');
const {createCountryDesk}=require('../country-desk/service.cjs');
const {createWorldNews}=require('./news-service.cjs');
const {createMarketData}=require('./market-data.cjs');
const {PLANS}=require('./plans.cjs');
const {SECURITY_HEADERS}=require('../http-security.cjs');
// Separate public Worker. No import of owner auth, account adapters, private portfolio records or licensed quote keys.
function createPublicApp({assets={},fetchImpl=fetch}={}){
 const news=createWorldNews({fetchImpl,includeReporting:true});
 const marketData=createMarketData({fetchImpl});
 const countryDesk=createCountryDesk({fetchImpl});
 const investmentBoard=createBoardCrypto({fetchImpl});
 return {async fetch(request){
  const headers=new Headers(SECURITY_HEADERS);
  const respond=(data,status=200,type='application/json')=>{headers.set('Content-Type',type);return new Response(request.method==='HEAD'?null:type==='application/json'?JSON.stringify(data):data,{status,headers})};
  try{
   if(!['GET','HEAD'].includes(request.method))return respond({error:'enrollment_not_open',message:'Paid enrollment is not open. No payment or membership change was made.'},405);
   const url=new URL(request.url),path=url.pathname;
   if(path==='/api/investment-board')return respond(await investmentBoard.snapshot());
   if(path==='/api/country-desk'){const result=await countryDesk.read(url.searchParams.get('country'),url.searchParams.get('topic')||'all');return respond(result.body,result.status)}
   if(path==='/api/health')return respond({status:'ok',mode:'public_news',enrollmentOpen:false});
   if(path==='/api/world-news')return respond(await news.news());
   if(path==='/api/market-overview')return respond(await marketData.snapshot());
   if(path==='/api/plans')return respond({plans:PLANS,enrollmentOpen:false});
   if(path==='/api/session')return respond({authenticated:false,mode:'public',membership:{tier:'public',scope:'public',billingRequired:false}});
   if(path.startsWith('/api/'))return respond({error:'not_available_on_public_site'},404);
   let name;try{name=path==='/'||path==='/markets'?'market-desk/index.html':decodeURIComponent(path.slice(1))}catch{return respond('Bad request',400,'text/plain')}
   if(!Object.hasOwn(assets,name))return respond('Not found',404,'text/plain');
   const type=name.endsWith('.css')?'text/css':name.endsWith('.js')?'text/javascript':'text/html';
   return respond(assets[name],200,type+'; charset=utf-8');
  }catch{return respond({error:'news_temporarily_unavailable'},503)}
 }};
}
module.exports={createPublicApp};
