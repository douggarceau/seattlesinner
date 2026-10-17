# merge out_*.json into vstate.json, vnews.json, vup.json, desk.json (state/log) ; idempotent
import json,glob,hashlib,os,re,datetime as dt
D=os.path.dirname(os.path.abspath(__file__))
now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
reg=json.load(open(D+'/registry.json'));ids={v['venue_id'] for v in reg['venues']}
L=lambda f,dflt:json.load(open(D+'/'+f)) if os.path.exists(D+'/'+f) else dflt
vstate=L('vstate.json',{});news=L('vnews_all.json',[]);up=L('vup.json',[]);desk=L('desk.json',{'runs':[],'review_queue':[],'watch':[],'new_venue_candidates':[],'outlets':[],'access_failures':{}})
def norm(t):return re.sub(r'[^a-z0-9]+',' ',(t or '').lower()).strip()
def nkey(n):
    u=((n.get('sources') or [{}])[0].get('url') or '')
    return '|'.join(sorted(n.get('venue_ids') or []))+'|'+norm(n.get('headline'))[:60]
have={x['dedupe_key']:x for x in news}
added=revised=0;attempted=[];bad=[]
for f in sorted(glob.glob(D+'/out_*.json')):
    try:o=json.load(open(f))
    except Exception as e: bad.append(f+': '+str(e));continue
    for v in o.get('venues',[]):
        if v.get('venue_id') not in ids: bad.append('unknown id '+str(v.get('venue_id')));continue
        attempted.append(v['venue_id'])
        prev=vstate.get(v['venue_id'],{})
        vstate[v['venue_id']]={**prev,**{k:v.get(k) for k in ['official_url','calendar_url','other_sources','identity_verified','status','status_evidence_url','status_note','access_failures']},'last_checked':v.get('checked_at') or now}
    for r in o.get('review_queue',[]):
        if r not in desk['review_queue']: desk['review_queue'].append(r)
    for n in o.get('news',[]):
        n['venue_ids']=[i for i in (n.get('venue_ids') or []) if i in ids]
        if not n.get('sources') or not n['sources'][0].get('url'): continue
        k=nkey(n)
        # also dedupe by first source url + venue
        dup=next((x for x in news if x['sources'][0]['url']==n['sources'][0]['url'] and set(x['venue_ids'])==set(n['venue_ids'])),None) or have.get(k)
        if dup:
            urls={s['url'] for s in dup['sources']}
            for s in n['sources']:
                if s.get('url') not in urls: dup['sources'].append(s);revised+=1
            continue
        n['dedupe_key']=k;n['item_id']='vn-'+hashlib.sha1(k.encode()).hexdigest()[:12];n['discovered_at']=n.get('discovered_at') or now
        n['event_timezone']='America/Los_Angeles';n['last_verified_at']=now;n['publication_status']='published' if n.get('verification_status') in ('confirmed','reported') else 'draft'
        news.append(n);have[k]=n;added+=1
    for u in o.get('upcoming',[]):
        if u.get('venue_id') in ids and u.get('start_local') and u.get('url'):
            key=(u['venue_id'],norm(u.get('title')),u['start_local'])
            if not any((x['venue_id'],norm(x.get('title')),x['start_local'])==key for x in up): up.append(u)
    if 'watch' in o: desk['watch']=o['watch']
    if 'new_venue_candidates' in o: desk['new_venue_candidates']=o['new_venue_candidates']
    if 'outlets' in o: desk['outlets']=o['outlets']
news.sort(key=lambda x:(x.get('published_at') or x.get('discovered_at') or ''),reverse=True)
up=[u for u in up if u['start_local'][:10]>=dt.date.today().isoformat()];up.sort(key=lambda u:u['start_local'])
json.dump(vstate,open(D+'/vstate.json','w'),ensure_ascii=False)
json.dump([n for n in news],open(D+'/vnews_all.json','w'),ensure_ascii=False)
pub=[{k:n.get(k) for k in ['item_id','item_type','venue_ids','headline','factual_summary','why_it_matters','verification_status','published_at','discovered_at','event_start_local','sources']} for n in news if n['publication_status']=='published']
for p in pub: p['sources']=[{k:s.get(k) for k in ['url','publisher','title']} for s in p['sources']]
json.dump(pub,open(D+'/vnews.json','w'),ensure_ascii=False)
json.dump(up,open(D+'/vup.json','w'),ensure_ascii=False)
import collections
st=collections.Counter(v.get('status') for v in vstate.values())
desk['runs'].append({'run_id':'baseline-'+now,'finished_at':now,'venues_checked':len(set(attempted)),'items_added':added,'items_revised':revised,'errors':bad})
desk['coverage']={'checked':len(vstate),'of':len(ids),'status':dict(st),'unchecked_ids':sorted(ids-set(vstate))}
desk['review_queue']=[r for r in desk['review_queue'] if r.get('venue_id') in vstate]
json.dump(desk,open(D+'/desk.json','w'),ensure_ascii=False,indent=1)
print('checked',len(vstate),'/',len(ids),dict(st),'news',len(news),'published',len(pub),'added',added,'revised',revised,'upcoming',len(up),'errors',bad[:5])
