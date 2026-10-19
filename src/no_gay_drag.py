# Content filter: keeps gay/LGBTQ news and drag shows out of the Wire, Scene, calendar and venue news.
# Run after any data update:  python3 src/no_gay_drag.py
import json,re,os
PAT=re.compile(r"queer|\bgay\b|lgbt|\bpride\b|\btrans(?:gender)?\b(?!-)|\bdrag\b(?!\s+the\s+river)|drag\s*(?:show|queen|king|cabaret|brunch|race)",re.I)
BAD_KINDS={'lgbtq','drag'}
def bad(x):return x.get('kind') in BAD_KINDS or bool(PAT.search(json.dumps(x,ensure_ascii=False)))
def clean(lst):return [x for x in lst if not bad(x)]
os.chdir(os.path.join(os.path.dirname(__file__),'..'))
n=0
s=open('index.html').read()
def sub_block(s,start_pat,end_pat):
    global n
    m=re.search(start_pat+r'(\[.*?\])'+end_pat,s,re.S)
    if not m:return s
    raw=m.group(1);lst=json.loads(raw.replace('<\\/','</'))
    c=clean(lst);n+=len(lst)-len(c)
    return s[:m.start(1)]+json.dumps(c,ensure_ascii=False).replace('</','<\\/')+s[m.end(1):]
s=sub_block(s,r'const BARS=/\*WIRE_START\*/',r'/\*WIRE_END\*/')
s=sub_block(s,r'const VNEWS=/\*VNEWS_START\*/',r'/\*VNEWS_END\*/')
s=sub_block(s,r'const SCENE=',r';\n')
s=sub_block(s,r'const CAL=',r';\n')
s=s.replace(",lgbtq:['#d9a400','Queer nightlife']","")
open('index.html','w').write(s)
for f,key in [('data/wire.json',None),('data/cal.json','events'),('src/data/scene.json',None),('src/data/briefs.json',None),('src/data/cal.json',None)]:
    if not os.path.exists(f):continue
    d=json.load(open(f))
    if key:lst=d[key]
    elif isinstance(d,list):lst=d
    else:continue
    c=clean(lst);n+=len(lst)-len(c)
    if key:d[key]=c
    else:d=c
    json.dump(d,open(f,'w'),ensure_ascii=False)
print('removed',n)
