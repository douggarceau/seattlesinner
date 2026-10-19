"""Export the stories and Wire from classic.html to small JSON files the front page reads.
usage: python3 src/export_data.py   (run from the repo root after any edit to classic.html)"""
import json,os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
h=open(os.path.join(R,'classic.html'),encoding='utf-8').read()
d=json.JSONDecoder()
def grab(marker):
    i=h.find(marker)
    if i<0: raise SystemExit('missing '+marker)
    return d.raw_decode(h,i+len(marker))[0]
S=grab('const STORIES=');W=grab('/*WIRE_START*/')
for name,obj in (('stories.json',S),('wire.json',W)):
    p=os.path.join(R,'data',name);s=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
    old=open(p,encoding='utf-8').read() if os.path.exists(p) else ''
    if s!=old: open(p,'w',encoding='utf-8').write(s)
print('exported',len(S),'stories,',len(W),'wire items')
