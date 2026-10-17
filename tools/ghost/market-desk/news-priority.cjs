'use strict';
function priority(story,now){
 const title=story.title||'',topics=story.topics||[];
 const routine=/auction results?|liquidity adjustment facility|variable rate (?:repo|reverse)|registration|cancellation of (?:licen[cs]e|certificate)|imposes? (?:a )?monetary penalty|enforcement action|releases? (?:the )?minutes of|daily deal|funniest|insightful comments|podcast episode|weekly statistical supplement|departmental results|appointments?|board meeting/i.test(title);
 const material=/inflation|consumer prices|payroll|employment|unemployment|gross domestic|\bGDP\b|monetary policy|interest rate|rate decision|tariffs?|trade (?:deficit|balance|war)|crude|petroleum|oil prices|energy outlook|natural gas|wheat|crop|agricultural supply|food price|earnings|semiconductor|artificial intelligence|data cent(?:er|re)|stablecoin|bitcoin|financial stability|credit conditions|bank lending|capital spending/i.test(title);
 const age=Math.max(0,(now-Date.parse(story.publishedAt||story.observedAt))/86400000);
 const importance=routine?'routine':material?'material':'context';
 let context='Open the original report for its findings, methodology and publication context.';
 if(topics.includes('oil')||topics.includes('energy'))context='Energy transmission: compare supply, inventories and product demand before inferring an effect on producer or transport margins.';
 else if(topics.includes('agriculture'))context='Crop balance: production, exports and ending stocks determine supply pressure; separate a forecast revision from an observed shortage.';
 else if(topics.includes('inflation'))context='Policy channel: separate broad price pressure from a few volatile components, then compare it with the path of interest rates.';
 else if(topics.includes('jobs'))context='Demand channel: payroll growth, unemployment and wages together give a fuller reading than a single headline number.';
 else if(topics.includes('technology'))context='Technology exposure: trace the development to revenue, costs, capital spending or regulation before drawing an earnings conclusion.';
 else if(topics.includes('trade'))context='Trade channel: identify which goods, countries and effective dates are affected, then assess substitution and margin exposure.';
 else if(topics.includes('rates'))context='Financing channel: distinguish a policy announcement from market borrowing rates and the credit spread paid by an actual borrower.';
 return {...story,importance,priorityScore:(routine?-100:material?45:12)+Math.max(0,30-age*2)-Math.max(0,age-7)*3,context,editorialLabel:story.sourceId==='techdirt'?'Technology / policy commentary':story.kind==='news_report'?'Publisher reporting':'Original source'};
}
function selectLeads(articles,count=8){
 const used=new Map();return [...articles].filter(a=>a.importance!=='routine').sort((a,b)=>b.priorityScore-a.priorityScore||Date.parse(b.publishedAt||b.observedAt)-Date.parse(a.publishedAt||a.observedAt)).filter(a=>{const id=a.sourceId||a.source,n=used.get(id)||0;if(n>=2)return false;used.set(id,n+1);return true}).slice(0,count);
}
module.exports={priority,selectLeads};
