# usage: python3 src/sync_markers.py <artifact page> <repo index.html>
# Copies ONLY the data blocks (between /*X_START*/ and /*X_END*/) from the artifact into the site page.
# Layout, nav, scripts and everything else on the site stay as they are.
import re,sys
live=open(sys.argv[1]).read();out=open(sys.argv[2]).read()
n=0
for m in ['WIRE','TECH','VST','VNEWS','VUP','BST','BNEWS','BEV','FEAT']:
    pat=re.compile(r'/\*'+m+r'_START\*/(.*?)/\*'+m+r'_END\*/',re.S)
    a=pat.search(live);b=pat.search(out)
    if not a or not b: print('skip',m);continue
    if a.group(1)!=b.group(1): n+=1
    out=out[:b.start(1)]+a.group(1)+out[b.end(1):]
    print(m,len(a.group(1)))
open(sys.argv[2],'w').write(out)
print('changed blocks:',n)
