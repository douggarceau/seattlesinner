'use strict';
const {boundedText}=require('../market-desk/market-data.cjs');
const {indicators}=require('../stock-desk/market-research.cjs');
const DAY=86400000,SYMBOLS=['BTC','ETH','SOL','XRP','ADA','AVAX','LINK','DOGE'];
function history(raw,now=Date.now()){
 const base=indicators(raw,now),end=Math.floor(now/DAY)*86400;
 const rows=JSON.parse(raw).filter(r=>Array.isArray(r)&&r.length>=6&&r.every(Number.isFinite)&&r[0]<end&&r[0]%86400===0&&r[1]>0&&r[2]>=r[1]&&r[3]>=r[1]&&r[3]<=r[2]&&r[4]>=r[1]&&r[4]<=r[2]&&r[5]>=0).sort((a,b)=>a[0]-b[0]).slice(-200);
 const last=rows.at(-1)[4],returns=rows.slice(-31).slice(1).map((r,i)=>Math.log(r[4]/rows.slice(-31)[i][4])),mean=returns.reduce((s,n)=>s+n,0)/returns.length;
 const volatility=Math.sqrt(returns.reduce((s,n)=>s+(n-mean)**2,0)/(returns.length-1))*Math.sqrt(365)*100;
 let peak=rows.at(-90)[4],drawdown=0;for(const r of rows.slice(-90)){peak=Math.max(peak,r[4]);drawdown=Math.min(drawdown,(r[4]/peak-1)*100)}
 let gain=0,loss=0;for(let i=rows.length-14;i<rows.length;i++){const change=rows[i][4]-rows[i-1][4];gain+=Math.max(0,change);loss+=Math.max(0,-change)}const rsi=loss===0?(gain===0?50:100):100-100/(1+gain/loss);
 return {...base,return7:(last/rows.at(-8)[4]-1)*100,return90:(last/rows.at(-91)[4]-1)*100,volatility30:volatility,maxDrawdown90:drawdown,rsi14Simple:rsi,path:rows.slice(-90).map(r=>({date:new Date(r[0]*1000).toISOString().slice(0,10),close:r[4]}))};
}
function createBoardCrypto({fetchImpl=fetch,clock=()=>Date.now(),pace=ms=>new Promise(r=>setTimeout(r,ms))}={}){
 let cache,pending;const histories=new Map();
 async function collect(){const now=clock(),end=Math.floor(now/DAY)*DAY,metrics=await Promise.all(SYMBOLS.map(async(symbol,index)=>{await pace(index*320);const base='https://api.exchange.coinbase.com/products/'+symbol+'-USD/',candleSourceUrl=base+'candles?granularity=86400&start='+new Date(end-220*DAY).toISOString()+'&end='+new Date(end).toISOString(),old=histories.get(symbol);
   const [stats,bars]=await Promise.allSettled([boundedText(fetchImpl,base+'stats'),old?.day===end?Promise.resolve(null):boundedText(fetchImpl,candleSourceUrl)]);
   let quote=null,technical=old?.day===end?old.technical:null;
   try{const s=JSON.parse(stats.value),num=v=>typeof v==='string'&&/^\d+(\.\d+)?$/.test(v)?Number(v):NaN,value=num(s.last),open=num(s.open),low=num(s.low),high=num(s.high),volume=num(s.volume),volume30=num(s.volume_30day);
    if(!(value>0&&open>0&&low>0&&high>=low&&value>=low&&value<=high))throw Error();
    quote={value,change:(value/open-1)*100,low,high,volume:Number.isFinite(volume)?volume:null,relativeVolume:volume30>0&&Number.isFinite(volume)?volume/(volume30/30):null,asOf:new Date(clock()).toISOString()};
   }catch{}
   if(!technical)try{technical=history(bars.value,now);histories.set(symbol,{day:end,technical})}catch{}
   return {symbol,status:quote?'available':'unavailable',...(quote||{}),technical,sourceUrl:base+'stats',candleSourceUrl};
  }));return {checkedAt:new Date(clock()).toISOString(),metrics,methodology:'Coinbase Exchange USD pairs only. Quotes cached 5 minutes; completed daily history cached until the next UTC day. 30-day volatility uses sample standard deviation of daily log returns × √365. Drawdown is the worst peak-to-trough close decline in 90 observations. RSI is a simple 14-change calculation, not Wilder smoothing. These measures describe past prices, not expected returns.'};
 }
 return {async snapshot(){if(cache&&clock()-Date.parse(cache.checkedAt)<300000)return cache;if(!pending)pending=collect().then(d=>(cache=d)).finally(()=>pending=null);return pending}};
}
module.exports={history,createBoardCrypto,SYMBOLS};
