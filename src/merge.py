import json,os
D=os.path.dirname(os.path.abspath(__file__))
L=lambda f: json.load(open(D+'/'+f)) if os.path.exists(D+'/'+f) else []
h=L('f_hard.json'); one=lambda f:[x] if isinstance((x:=L(f)),dict) else x
order=h[:1]+one('f_tate.json')+one('f_clav.json')+one('f_kirk.json')+one('f_mack.json')+one('f_film.json')+one('f_homeless.json')+h[1:]+one('f_hf.json')+one('f_psy.json')+one('f_satan.json')+L('local.json')+L('f_ink.json')
json.dump(order,open(D+'/stories.json','w'),ensure_ascii=False)
print(len(order),[s['slug'] for s in order])
