"""Build report/index.html (The Guitar Doug Report) from the stories in the live index.html."""
import json,os,re
D=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(D)
live=open(R+'/classic.html',encoding='utf-8').read()
i=live.index('const STORIES=')+len('const STORIES=')
st,_=json.JSONDecoder().raw_decode(live,i)
tpl=open(D+'/report_tpl.html',encoding='utf-8').read()
out=tpl.replace('/*STORIES*/[]',json.dumps(st,ensure_ascii=False).replace('</','<\\/'))
os.makedirs(R+'/report',exist_ok=True)
open(R+'/report/index.html','w',encoding='utf-8').write(out)
print('report/index.html built with',len(st),'stories')
