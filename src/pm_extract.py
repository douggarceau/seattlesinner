# usage: python3 pm_extract.py <power-map.html>  -> tech.json
import json,sys,os
s=open(sys.argv[1]).read();dec=json.JSONDecoder()
def get(n):
    i=s.find('const '+n+'=')+len('const '+n+'=')
    if s.startswith('/*',i): i=s.find('*/',i)+2
    return dec.raw_decode(s,i)[0]
B=get('BELL');D=get('DARK');I=get('INTEL')
nm={d['id']:d.get('name',d['id']) for d in I}
news=[{'t':a['title'],'src':a.get('source',''),'d':a.get('date',''),'u':a['url'],'co':d.get('name',d['id'])} for d in I for a in d.get('news',[]) if a.get('url')]
seen=set();N=[]
for a in sorted(news,key=lambda a:a['d'],reverse=True):
    k=a['t'][:50].lower()
    if k in seen or 'webcast' in k: continue
    seen.add(k);N.append(a)
dk=lambda L:sorted(L,key=lambda x:x.get('date',''),reverse=True)
T={'asof':B.get('day',''),'bell':{'day':B.get('day'),'asof':B.get('asof'),'setup':B.get('setup'),'snap':B.get('snap',[]),
   'movers':[dict(m,name=nm.get(m.get('id'),m.get('id','').upper())) for m in B.get('movers',[])],'watch':B.get('watch',[])},
   'news':N[:36],'rogue':dk(D.get('rogue',[]))[:12],'machines':dk(D.get('machines',[]))[:8]}
json.dump(T,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'tech.json'),'w'),ensure_ascii=False)
print(len(T['news']),len(T['rogue']),len(T['machines']),len(T['bell']['movers']))
