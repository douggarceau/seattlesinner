# merge briefs.json items into the WIRE blob of seattle-sinner.html (union by url, newest first, cap 90)
import json,re
s=open('seattle-sinner.html').read();m=re.search(r'/\*WIRE_START\*/(.*?)/\*WIRE_END\*/',s,re.S)
w=json.loads(m.group(1).replace('<\\/','</'));have={x.get('url') for x in w}
for x in json.load(open('briefs.json')):
    if x.get('url') not in have:w.append(x);have.add(x.get('url'))
w.sort(key=lambda x:x.get('date',''),reverse=True);w=w[:90]
s=s[:m.start(1)]+json.dumps(w,ensure_ascii=False).replace('</','<\\/')+s[m.end(1):]
open('seattle-sinner.html','w').write(s);open('t.js','w').write(re.findall(r'<script>(.*?)</script>',s,re.S)[0])
print('wire',len(w),sum(1 for x in w if x.get('kind')=='news'))
