(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.GhostStockWidgets=factory()})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 // Direct cross-origin frames reproduce the documented embed loader's generated URL.
 // No third-party script executes in the private dashboard. Attribution stays visible.
 const HOST='https://www.tradingview-widget.com';
 const names={chart:'advanced-chart',company:'financials',news:'timeline',technicals:'technical-analysis',discover:'screener',quote:'symbol-info'};
 function url(kind,symbol,pageOrigin){
  if(!names[kind]||!/^(NASDAQ|NYSE|AMEX|COINBASE):[A-Z][A-Z0-9.\-]{0,14}$/.test(symbol))throw Error('invalid_widget');
  const common={symbol,width:'100%',height:'100%',locale:'en',colorTheme:'dark',isTransparent:false};
  const settings={...common};
  if(kind==='chart')Object.assign(settings,{autosize:true,interval:'D',timezone:'America/New_York',theme:'dark',style:'1',allow_symbol_change:false,save_image:false,hide_side_toolbar:false,withdateranges:true,details:false,calendar:false});
  if(kind==='company')Object.assign(settings,{displayMode:'adaptive'});
  if(kind==='news')Object.assign(settings,{feedMode:'symbol',displayMode:'regular'});
  if(kind==='technicals')Object.assign(settings,{interval:'1D',showIntervalTabs:true,displayMode:'single'});
  if(kind==='discover'){delete settings.symbol;Object.assign(settings,{market:'america',defaultColumn:'performance',defaultScreen:'most_capitalized',showToolbar:true,enableScrolling:true})}
  // Only the public origin is sent. Private plan values, notes and query strings never leave.
  try{const origin=new URL(pageOrigin);if(['http:','https:'].includes(origin.protocol))settings['page-uri']=origin.host+'/'}catch{}
  const u=new URL(HOST+'/embed-widget/'+names[kind]+'/');u.searchParams.set('locale','en');if(['quote','news'].includes(kind))u.searchParams.set('symbol',symbol);u.hash=encodeURIComponent(JSON.stringify(settings));return u.href;
 }
 return {url,HOST};
});
