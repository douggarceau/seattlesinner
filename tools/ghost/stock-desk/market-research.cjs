'use strict';
const {boundedText}=require('../market-desk/market-data.cjs');
const DAY=86400000;
function indicators(raw,now=Date.now()){
 const start=Math.floor(now/DAY)*DAY/1000,parsed=JSON.parse(raw);if(!Array.isArray(parsed))throw Error('invalid_candles');
 const rows=parsed.filter(r=>Array.isArray(r)&&r.length>=6&&r.every(Number.isFinite)&&r[0]<start&&r[0]%86400===0&&r[1]>0&&r[2]>=r[1]&&r[3]>=r[1]&&r[3]<=r[2]&&r[4]>=r[1]&&r[4]<=r[2]&&r[5]>=0).sort((a,b)=>a[0]-b[0]).slice(-200);
 if(rows.length!==200||rows[199][0]!==start-86400||rows.some((r,i)=>i&&r[0]-rows[i-1][0]!==86400))throw Error('incomplete_candles');
 const avg=n=>rows.slice(-n).reduce((s,r)=>s+r[4],0)/n,last=rows.at(-1)[4];
 return {asOf:new Date(rows.at(-1)[0]*1000).toISOString().slice(0,10),sma20:avg(20),sma50:avg(50),sma200:avg(200),return30:(last/rows.at(-31)[4]-1)*100,low20:Math.min(...rows.slice(-20).map(r=>r[1])),high20:Math.max(...rows.slice(-20).map(r=>r[2])),lastClose:last,sampleDays:200};
}
function createInvestmentMarkets({fetchImpl=fetch,clock=()=>Date.now()}={}){let cached,pending;
 async function collect(){const now=clock(),end=Math.floor(now/DAY)*DAY,assets=await Promise.all(['BTC','ETH','SOL'].map(async symbol=>{const base='https://api.exchange.coinbase.com/products/'+symbol+'-USD/',url=base+'candles?granularity=86400&start='+new Date(end-220*DAY).toISOString()+'&end='+new Date(end).toISOString();
 const [stats,bars]=await Promise.allSettled([boundedText(fetchImpl,base+'stats'),boundedText(fetchImpl,url)]);let price=null,technical=null;
 try{const s=JSON.parse(stats.value),n=v=>typeof v==='string'&&/^\d+(?:\.\d+)?$/.test(v)?Number(v):NaN;const value=n(s.last),open=n(s.open),low=n(s.low),high=n(s.high);if(!(value>0&&open>0&&low>0&&high>=low&&value>=low&&value<=high))throw Error();price={value,change:(value/open-1)*100,low,high,asOf:new Date(now).toISOString()}}catch{}
 try{technical=indicators(bars.value,now)}catch{}
 return {symbol,id:symbol.toLowerCase(),group:'crypto',status:price?'available':'unavailable',...(price||{}),technical,technicalStatus:technical?'available':'unavailable',sourceUrl:base+'stats',candleSourceUrl:url};}));return {checkedAt:new Date(now).toISOString(),metrics:assets,methodology:'Coinbase Exchange only. Daily averages use 200 contiguous completed UTC candles; unfinished days and incomplete series are excluded. Rule-based trend checks are not valuation or buy signals.'}}
 return {async snapshot(){if(cached&&clock()-Date.parse(cached.checkedAt)<300000)return cached;if(!pending)pending=collect().then(v=>(cached=v)).finally(()=>pending=null);return pending}};
}
module.exports={indicators,createInvestmentMarkets};
