# usage: python3 sync_live.py <live.html>  -> copies marker blobs from live into seattle-sinner.html (and saves wire/tech/venue data locally)
import re,sys,json,os
D=os.path.dirname(os.path.abspath(__file__))
live=open(sys.argv[1]).read();out=open(D+'/seattle-sinner.html').read()
for m in ['WIRE','TECH','VST','VNEWS','VUP','BST','BNEWS','BEV','FEAT']:
    pat=re.compile(r'/\*'+m+r'_START\*/(.*?)/\*'+m+r'_END\*/',re.S)
    a=pat.search(live);b=pat.search(out)
    if not a or not b: print('skip',m,bool(a),bool(b));continue
    out=out[:b.start(1)]+a.group(1)+out[b.end(1):]
    print(m,len(a.group(1)))
open(D+'/seattle-sinner.html','w').write(out)
open(D+'/t.js','w').write(re.findall(r'<script>(.*?)</script>',out,re.S)[0])
