(function(r,f){if(typeof module==='object'&&module.exports)module.exports=f();else r.GhostInvestingMath=f()})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const finite=n=>typeof n==='number'&&Number.isFinite(n),ratio=(a,b)=>finite(a)&&finite(b)&&b>0?a/b:null;
const percent=(a,b)=>{const r=ratio(a,b);return r===null?null:r*100};
function company(a,price=a.price){const f=a.annual,cash=f.bank?null:finite(f.ocf)&&finite(f.capex)?f.ocf-f.capex:null;return {growth:percent(f.revenue-f.priorRevenue,f.priorRevenue),netMargin:percent(f.netIncome,f.revenue),cashSurplus:cash,cashMargin:cash===null?null:percent(cash,f.revenue),capexShare:f.bank?null:percent(f.capex,f.ocf),pe:price>0&&f.eps>0?price/f.eps:null,earningsYield:price>0&&f.eps>0?f.eps/price*100:null}}
function valuation({price,eps,multiple,discount}){if(![price,eps,multiple,discount].every(finite)||price<=0||eps<=0||multiple<=0||multiple>200||discount<0||discount>=100)return null;const value=eps*multiple;return {value,entry:value*(1-discount/100),returnPct:(value/price-1)*100,breakEvenEPS:price/multiple}}
function position({price,stop,target,capital,risk,fees=0,fractional=false}){if(![price,stop,target,capital,risk,fees].every(finite)||!(price>0&&price<=1e8&&stop>0&&stop<price&&target>price&&target<=1e9&&capital>fees&&capital<=1e12&&risk>fees&&risk<=1e10&&fees>=0))return null;const max=Math.min((capital-fees)/price,(risk-fees)/(price-stop)),scale=fractional?1e8:1,quantity=Math.floor((max+Number.EPSILON)*scale)/scale,cost=quantity*price+fees,loss=quantity*(price-stop)+fees,gain=quantity*(target-price)-fees;return {quantity,cost,loss,gain,rr:loss>0?gain/loss:null,breakEven:gain>0&&loss>0?loss/(gain+loss)*100:null,gapLoss:quantity*(price-stop*.95)+fees}}
function fundCost(amount,expense){return finite(amount)&&amount>=0&&finite(expense)&&expense>=0?amount*expense/100:null}
function csv(rows){return rows.map(row=>row.map(value=>{let s=String(value??'');if(/^[=+@\t\r]/.test(s)||/^-(?!\d)/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"'}).join(',')).join('\r\n')}
return {company,valuation,position,fundCost,csv};
});
