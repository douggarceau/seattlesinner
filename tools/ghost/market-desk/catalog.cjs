'use strict';
const SOURCES=[
 ['fed','Federal Reserve','https://www.federalreserve.gov/feeds/press_all.xml','US','north-america',['economy','rates']],
 ['fedSpeeches','Federal Reserve speeches','https://www.federalreserve.gov/feeds/speeches.xml','US','north-america',['economy','rates']],
 ['cpi','BLS inflation','https://www.bls.gov/feed/cpi.rss','US','north-america',['economy','inflation']],
 ['jobs','BLS employment','https://www.bls.gov/feed/empsit.rss','US','north-america',['economy','jobs']],
 ['bea','BEA economy','https://apps.bea.gov/rss/rss.xml','US','north-america',['economy']],
 ['ecb','European Central Bank','https://www.ecb.europa.eu/rss/press.html','EA','europe',['economy','rates','eur']],
 ['boe','Bank of England','https://www.bankofengland.co.uk/rss/news','GB','europe',['economy','rates','gbp']],
 ['boc','Bank of Canada','https://www.bankofcanada.ca/content_type/press/feed/','CA','north-america',['economy','rates','cad']],
 ['boj','Bank of Japan','https://www.boj.or.jp/en/rss/whatsnew.xml','JP','asia',['economy','rates','jpy']],
 ['rbi','Reserve Bank of India','https://www.rbi.org.in/pressreleases_rss.xml','IN','asia',['economy','rates','inr']],
 ['rba','Reserve Bank of Australia','https://www.rba.gov.au/rss/rss-cb-media-releases.xml','AU','oceania',['economy','rates','aud']],
 ['bis','Bank for International Settlements','https://www.bis.org/doclist/all_pressrels.rss','GLOBAL','global',['economy','banking','bonds']],
 ['eiaPress','U.S. Energy Information Administration','https://www.eia.gov/rss/press_rss.xml','US','north-america',['energy']],
 ['eiaReports','EIA energy reports','https://www.eia.gov/about/new/WNtest3.php','US','north-america',['energy']],
 ['eiaToday','EIA Today in Energy','https://www.eia.gov/rss/todayinenergy.xml','US','north-america',['energy']],
 ['fao','Food and Agriculture Organization','https://www.fao.org/feeds/fao-newsroom-rss','GLOBAL','global',['agriculture']],
 ['adb','Asian Development Bank','https://www.adb.org/rss/news','GLOBAL','asia',['economy','development']],
 ['statsCanada','Statistics Canada','https://www150.statcan.gc.ca/n1/rss/dai-quo/0-eng.atom','CA','north-america',['economy']],
 ['usda','USDA crop reports','https://www.nass.usda.gov/rss/news.xml','US','north-america',['agriculture']]
].map(([id,name,url,country,region,topics])=>({id,name,url,country,region,topics,hosts:[new URL(url).hostname,...(id==='bea'?['www.bea.gov']:id==='statsCanada'?['www.statcan.gc.ca']:[])],...(id==='rbi'?{timezone:'+0530'}:{})}));
SOURCES.push({id:'wasde',name:'USDA World Agricultural Supply and Demand Estimates',url:'https://esmis.nal.usda.gov/publication/world-agricultural-supply-and-demand-estimates',country:'US',region:'north-america',topics:['agriculture','wheat','corn','soybeans','rice','cotton','livestock'],hosts:['esmis.nal.usda.gov'],format:'usda-publication'});
const REPORTING_SOURCES=[
 {id:'conversationBusiness',name:'The Conversation · Business',url:'https://theconversation.com/us/business/articles.atom',country:'GLOBAL',region:'global',topics:['economy'],hosts:['theconversation.com'],kind:'news_report'},
 {id:'conversationTechnology',name:'The Conversation · Technology',url:'https://theconversation.com/us/technology/articles.atom',country:'GLOBAL',region:'global',topics:['technology'],hosts:['theconversation.com'],kind:'news_report'},
 {id:'techdirt',name:'Techdirt · Technology & policy commentary',url:'https://www.techdirt.com/feed/',country:'US',region:'north-america',topics:['technology'],hosts:['www.techdirt.com','techdirt.com'],kind:'news_report'}
];
const COUNTRY_DIRECTORY=require('../country-desk/catalog.js');
const REGIONS=COUNTRY_DIRECTORY.regions.map(r=>({...r,countries:COUNTRY_DIRECTORY.countries.filter(c=>c.region===r.id).map(c=>[c.code,c.name])}));
const MARKETS=require('../country-desk/markets.js');
const RULES={inflation:/inflation|consumer prices|\bcpi\b/i,jobs:/employment|unemployment|payroll|labou?r market/i,gdp:/\bgdp\b|gross domestic|economic growth/i,trade:/trade|tariff|exports?|imports?/i,rates:/interest rate|monetary policy|policy rate/i,banking:/banking|financial stability|basel|bank supervision/i,equities:/stock market|equities|share prices|corporate earnings/i,technology:/semiconductor|artificial intelligence|\bAI\b|technology/i,financials:/banks?|insurance|financial sector/i,healthcare:/pharmaceutical|healthcare|biotech/i,earnings:/earnings|corporate profits/i,bonds:/bonds?|fixed income|debt market/i,treasuries:/treasur(?:y|ies)/i,gilts:/gilts?/i,sovereign:/sovereign|public debt|government debt/i,credit:/credit|corporate debt/i,usd:/dollars?|\bUSD\b/i,eur:/\beuro\b/i,gbp:/sterling|\bGBP\b/i,jpy:/\byen\b/i,cny:/\byuan\b|renminbi/i,oil:/crude|petroleum|\boil\b|opec|refiner/i,gas:/natural gas|\bLNG\b/i,fuel:/gasoline|diesel|propane|heating oil|fuel costs/i,power:/electricity|electric power|power grid/i,renewables:/renewable|solar|wind energy|biomass|biofuel/i,coal:/\bcoal\b/i,gold:/\bgold\b/i,silver:/\bsilver\b/i,copper:/\bcopper\b/i,aluminum:/alumin[ui]um/i,lithium:/lithium/i,wheat:/\bwheat\b/i,corn:/\bcorn\b|maize/i,soybeans:/soybean|\bsoy\b/i,rice:/\brice\b/i,coffee:/coffee/i,sugar:/\bsugar\b/i,cotton:/cotton/i,livestock:/cattle|livestock|dairy|milk|poultry|hogs|pork/i,bitcoin:/bitcoin|\bBTC\b/i,ethereum:/ethereum|\bETH\b/i,stablecoins:/stablecoins?/i,'crypto-policy':/digital assets?|cryptocurrenc|cryptoassets?/i};
const COUNTRY_WORDS={US:/united states|\bU\.S\.|american/i,CA:/canada|canadian/i,MX:/mexico|mexican/i,GB:/united kingdom|britain|british|\bUK\b/i,DE:/germany|german/i,FR:/france|french/i,IT:/italy|italian/i,ES:/spain|spanish/i,CH:/switzerland|swiss/i,UA:/ukraine|ukrainian/i,CN:/china|chinese/i,JP:/japan|japanese/i,IN:/\bindia\b|indian/i,HK:/hong kong/i,KR:/south korea|korean/i,SG:/singapore/i,ID:/indonesia/i,AU:/australia|australian/i,NZ:/new zealand/i,BR:/brazil|brazilian/i,AR:/argentina/i,CL:/\bchile\b/i,SA:/saudi/i,AE:/united arab emirates|\bUAE\b/i,IL:/israel/i,IR:/\biran\b|iranian/i,ZA:/south africa/i,NG:/nigeria/i,EG:/egypt/i,KE:/kenya/i};
const EXTRA_RULES={'industrials':/manufacturing|industrial output/i,'autos':/automotive|automakers?|electric vehicles?/i,'defense':/defen[cs]e|aerospace/i,'consumer':/retail|consumer spending/i,'utilities':/utilities|utility companies/i,'telecom':/telecom/i,'semiconductors':/semiconductors?|chipmakers?/i,'dividends':/dividends?|buybacks?/i,'ipos':/initial public offering|\bIPO\b/i,'municipal':/municipal debt/i,'high-yield':/high.yield|junk bonds?/i,'debt-stress':/default|debt restructuring/i,'em-fx':/emerging.market currenc/i,'fx-reserves':/foreign.exchange reserves/i,'capital-flows':/capital flows|capital flight/i,'lng':/\bLNG\b|liquefied natural gas/i,'uranium':/uranium|nuclear power/i,'hydrogen':/hydrogen/i,'nickel':/nickel/i,'rare-earths':/rare earth/i,'platinum':/platinum|palladium/i,'iron-ore':/iron ore|steel/i,'fertilizer':/fertili[sz]er/i,'cocoa':/cocoa/i,'palm-oil':/palm oil/i,'timber':/timber|lumber/i,'solana':/solana/i,'defi':/\bDeFi\b|decentralized finance/i,'tokenization':/tokeni[sz]/i,'crypto-mining':/bitcoin mining|crypto mining/i,'tariffs':/tariffs?|duties/i,'sanctions':/sanctions?|export controls/i,'trade-deals':/trade agreement|trade deal/i,'shipping':/shipping|seaports?|freight rates/i,'airlines':/airlines?|air freight/i,'rail':/railway|railroad|road freight/i,'supply-chain':/supply.chain/i,'housing':/housing|home prices/i,'commercial-property':/commercial property|office real estate/i,'reits':/\bREITs?\b/i,'mortgages':/mortgages?/i,'data-centers':/data.cent(?:er|re)s?/i,'construction':/construction/i,'water':/water infrastructure|desalination/i,'elections':/elections?/i,'fiscal-policy':/budget|fiscal|tax reform/i,'regulation':/regulat/i,'conflict':/war|conflict|military/i,'climate':/climate|hurricane|flood|drought/i,'sovereign-rating':/sovereign rating|credit rating/i};
Object.assign(RULES,EXTRA_RULES);
const fold=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const countryNames=COUNTRY_DIRECTORY.countries.filter(c=>!['GE','JE','CG'].includes(c.code)).map(c=>[c.code,c.aliases.map(fold)]);
function classify(title,source){
 const topics=new Set(source.topics);
 for(const [id,pattern] of Object.entries(RULES))if(pattern.test(title))topics.add(id);
 for(const market of MARKETS)for(const sector of market.sectors)if(topics.has(sector.id)||sector.topics.some(([id])=>topics.has(id))){topics.add(sector.id);topics.add(market.id)}
 const countries=new Set(source.country==='GLOBAL'?[]:[source.country]);
 for(const [id,pattern]of Object.entries(COUNTRY_WORDS))if(pattern.test(title))countries.add(id);
 const normalized=' '+fold(title).replace(/[^a-z0-9]+/g,' ')+' ';
 for(const [id,names]of countryNames)if(names.some(name=>normalized.includes(' '+name.replace(/[^a-z0-9]+/g,' ')+' ')))countries.add(id);
 const regions=new Set(source.region==='global'?[]:[source.region]);
 for(const r of REGIONS)if(r.countries.some(([id])=>countries.has(id)))regions.add(r.id);
 return {topics:[...topics],countries:[...countries],regions:[...regions]};
}
const RESOURCES=[
 ['oil','Oil & petroleum data','https://www.eia.gov/petroleum/','EIA'],['gas','Natural gas reports','https://www.eia.gov/naturalgas/','EIA'],['power','Electricity data','https://www.eia.gov/electricity/','EIA'],['renewables','Renewable energy','https://www.eia.gov/renewable/','EIA'],
 ['wheat','Wheat outlook & data','https://www.ers.usda.gov/topics/crops/wheat','USDA ERS'],['agriculture','World crop supply & demand','https://www.usda.gov/oce/commodity/wasde','USDA'],['agriculture','Global food prices','https://www.fao.org/worldfoodsituation/foodpricesindex/en/','FAO'],['corn','Feed grains & corn','https://www.ers.usda.gov/topics/crops/corn-and-other-feedgrains','USDA ERS'],['soybeans','Oil crops & soybeans','https://www.ers.usda.gov/topics/crops/soybeans-and-oil-crops','USDA ERS'],
 ['metals','Mineral commodity statistics','https://www.usgs.gov/centers/national-minerals-information-center/commodity-statistics-and-information','USGS'],['treasuries','Treasury interest rates','https://home.treasury.gov/resource-center-data-chart-center/interest-rates','U.S. Treasury'],['fx','Euro reference exchange rates','https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html','ECB'],['equities','U.S. stock market directory','https://www.nasdaq.com/market-activity/stocks','Nasdaq'],['economy','U.S. economic release calendar','https://www.bls.gov/schedule/','BLS']
].map(([topic,title,url,source])=>({topic,title,url,source}));
module.exports={SOURCES,REPORTING_SOURCES,REGIONS,MARKETS,RESOURCES,classify};
