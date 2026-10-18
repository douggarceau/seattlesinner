import json,base64,os,re
D=os.path.dirname(os.path.abspath(__file__))
s=open(D+'/tpl.html').read()
jl=lambda f:json.load(open(D+'/'+f)) if os.path.exists(D+'/'+f) else []
U='/root/.claude/uploads/5e0b75ef-62b7-5f82-80c9-432f023378dc/'
covers=[('732dc1b1-image.jpg','Issue 7.79 · Aug 2009','Seattle Sinner cover, August 2009: burlesque artist Waxy Moon, Valis Unmasked'),
        ('5cadfd18-image.jpg','Issue 85 · Apr 2010','Seattle Sinner cover, April 2010: zombie on a Seattle street at night, Slats Unmasked'),
        ('e5ccdb04-image.jpg','Issue 86 · Jul 2010','Seattle Sinner cover, July 2010: Skin Deep with Stu, Badlands Unmasked')]
C=[{'src':'data:image/jpeg;base64,'+base64.b64encode(open(U+f,'rb').read()).decode(),'label':l,'alt':a} for f,l,a in covers]
cal=sorted(jl('cal.json'),key=lambda e:(e['date'],e.get('time') or ''))
scene=sorted(jl('scene.json'),key=lambda e:e['date'])
st=jl('stories.json')
d=lambda x:json.dumps(x,ensure_ascii=False).replace('</','<\\/')
s=s.replace('/*STORIES*/[]',d(st)).replace('/*CAL*/[]',d(cal)).replace('/*SCENE*/[]',d(scene)).replace('/*COVERS*/[]','[]').replace('/*UPDATED*/""',d('Oct 17, 2026'))
s=s.replace('/*LOGO*/','data:image/webp;base64,'+base64.b64encode(open(D+'/sinner-logo.webp','rb').read()).decode())
cv=D+'/cover.jpg'
s=s.replace('/*COVER*/""',d('data:image/jpeg;base64,'+base64.b64encode(open(cv,'rb').read()).decode()) if os.path.exists(cv) else '""')
s=s.replace('/*ISSUE1*/""',d('data:image/jpeg;base64,'+base64.b64encode(open(D+'/issue1.jpg','rb').read()).decode()))
s=s.replace('/*TECHDATA*/{}',d(jl('tech.json')) if os.path.exists(D+'/tech.json') else '{}')
SN=[]  # sounds are synthesized in tpl.html now
s=s.replace('/*SND*/{}',json.dumps({k:base64.b64encode(open(D+'/snd/'+k+'.mp3','rb').read()).decode() for k in SN}))
VD=D+'/vdesk/'
reg=json.load(open(VD+'registry.json'))['venues']
vst=json.load(open(VD+'vstate.json')) if os.path.exists(VD+'vstate.json') else {}
VEN=[{'id':v['venue_id'],'name':v['name'],'cat':v['primary_category'],'city':v['city'],'region':v['region'],'addr':v['address'],'hood':v['neighborhood'],'desc':v['entertainment_description'],'url':v['listed_website_url']} for v in reg]
s=s.replace('/*VENUES*/[]',d(VEN))
VSTM={k:{kk:vv for kk,vv in {'status':x.get('status'),'url':x.get('official_url'),'cal':x.get('calendar_url')}.items() if vv} for k,x in vst.items()}
s=s.replace('/*VSTDATA*/{}',d(VSTM))
s=s.replace('/*VNEWSDATA*/[]',d(jl('vdesk/vnews.json')))
s=s.replace('/*VUPDATA*/[]',d(jl('vdesk/vup.json')))
BD=D+'/bdesk/'
s=s.replace('/*BANDS*/[]',d(json.load(open(BD+'bands_slim.json'))))
bst=json.load(open(BD+'bstate.json')) if os.path.exists(BD+'bstate.json') else {}
s=s.replace('/*BSTDATA*/{}',d({k:{kk:vv for kk,vv in {'status':x.get('status'),'url':x.get('official_url'),'tour':x.get('tour_url')}.items() if vv} for k,x in bst.items()}))
s=s.replace('/*BNEWSDATA*/[]',d(jl('bdesk/bnews.json')))
s=s.replace('/*BEVDATA*/[]',d(jl('bdesk/bev.json')))
s=s.replace('/*BARS*/[]','/*WIRE_START*/'+d(jl('briefs.json'))+'/*WIRE_END*/')
open(D+'/seattle-sinner.html','w').write(s)
open(D+'/t.js','w').write(re.findall(r'<script>(.*?)</script>',s,re.S)[0])
print('stories',len(st),'cal',len(cal),'scene',len(scene))
