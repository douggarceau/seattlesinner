# merge bout_*.json into bstate.json, bnews_all.json, bnews.json, bev.json, bdesk.json; idempotent
import json,glob,hashlib,os,re,datetime as dt
D=os.path.dirname(os.path.abspath(__file__))
now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
reg=json.load(open(D+'/bands_slim.json'));ids={b['id'] for b in reg}
vreg=json.load(open(D+'/vnames.json')) if os.path.exists(D+'/vnames.json') else []
norm=lambda s:re.sub(r'[^a-z0-9]+',' ',(s or '').lower().replace('’','').replace("'",'')).replace(' the ',' ').strip()
vidx={norm(v['name']):v['venue_id'] for v in vreg}
L=lambda f,dflt:json.load(open(D+'/'+f)) if os.path.exists(D+'/'+f) else dflt
st=L('bstate.json',{});news=L('bnews_all.json',[]);ev=L('bev.json',[]);desk=L('bdesk.json',{'runs':[],'review_queue':[]})
added=revised=eadd=0;att=[];bad=[]
for f in sorted(glob.glob(D+'/bout_*.json')):
    try:o=json.load(open(f))
    except Exception as e:bad.append(f+': '+str(e));continue
    for b in o.get('bands',[]):
        if b.get('band_id') not in ids: bad.append('unknown '+str(b.get('band_id')));continue
        att.append(b['band_id']);st[b['band_id']]={**st.get(b['band_id'],{}),**{k:b.get(k) for k in ['status','status_evidence_url','status_note','official_url','tour_url','access_failures']},'last_checked':b.get('checked_at') or now}
    for r in o.get('review_queue',[]):
        if r not in desk['review_queue']:desk['review_queue'].append(r)
    for n in o.get('news',[]):
        n['band_ids']=[i for i in n.get('band_ids') or [] if i in ids]
        if not n['band_ids'] or not n.get('sources') or not n['sources'][0].get('url'):continue
        k='|'.join(sorted(n['band_ids']))+'|'+norm(n.get('headline'))[:60]
        dup=next((x for x in news if x['dedupe_key']==k or (x['sources'][0]['url']==n['sources'][0]['url'] and set(x['band_ids'])==set(n['band_ids']))),None)
        if dup:
            u={s['url'] for s in dup['sources']}
            for s in n['sources']:
                if s.get('url') not in u:dup['sources'].append(s);revised+=1
            continue
        n['dedupe_key']=k;n['item_id']='bn-'+hashlib.sha1(k.encode()).hexdigest()[:12];n['discovered_at']=n.get('discovered_at') or now
        n['publication_status']='published' if n.get('verification_status') in ('primary_confirmed','independently_corroborated','secondary_reported') else 'draft'
        news.append(n);added+=1
    for e in o.get('events',[]):
        e['band_ids']=[i for i in e.get('band_ids') or [] if i in ids]
        if not e['band_ids'] or not e.get('date') or not e.get('url'):continue
        if not e.get('venue_ids') and e.get('venue_name'):
            vi=vidx.get(norm(e['venue_name']));e['venue_ids']=[vi] if vi else []
        key=(e.get('venue_name') or '|'.join(e.get('venue_ids') or []), e['date'][:10], norm(e.get('headline'))[:40])
        ex=next((x for x in ev if (x.get('venue_name') or '|'.join(x.get('venue_ids') or []),x['date'][:10],norm(x.get('headline'))[:40])==key or (x.get('url')==e['url'] and x['date'][:10]==e['date'][:10])),None)
        if ex:
            ex['band_ids']=sorted(set(ex['band_ids'])|set(e['band_ids']));
            if e.get('status'):ex['status']=e['status']
            continue
        e['id']='ev-'+hashlib.sha1(('|'.join(map(str,key))).encode()).hexdigest()[:12];ev.append(e);eadd+=1
news.sort(key=lambda x:(x.get('published_at') or x.get('discovered_at') or ''),reverse=True)
json.dump(st,open(D+'/bstate.json','w'),ensure_ascii=False)
json.dump(news,open(D+'/bnews_all.json','w'),ensure_ascii=False)
pub=[{k:n.get(k) for k in ['item_id','item_type','band_ids','venue_ids','headline','factual_summary','verification_status','published_at','discovered_at','event_or_release_date']}|{'sources':[{k:s.get(k) for k in ['url','publisher','title']} for s in n['sources']]} for n in news if n['publication_status']=='published']
json.dump(pub,open(D+'/bnews.json','w'),ensure_ascii=False)
json.dump(ev,open(D+'/bev.json','w'),ensure_ascii=False)
import collections
desk['review_queue']=[r for r in desk['review_queue'] if r.get('band_id') in st]
desk['runs'].append({'run_id':'bands-'+now,'finished_at':now,'bands_checked':len(set(att)),'items_added':added,'items_revised':revised,'events_added':eadd,'errors':bad})
desk['coverage']={'checked':len(st),'of':len(ids),'status':dict(collections.Counter(v.get('status') for v in st.values()))}
json.dump(desk,open(D+'/bdesk.json','w'),ensure_ascii=False,indent=1)
print('bands checked',len(st),'/',len(ids),'news',len(news),'published',len(pub),'added',added,'events',len(ev),'+',eadd,'errors',bad[:5])
