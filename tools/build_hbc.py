#!/usr/bin/env python3
"""Build the static HOMELESS BY CHOICE pages from data/hbc/*.json.

Writes hbc/index.html, hbc/<category>/index.html, hbc/today/index.html and
hbc/about/index.html. Pages are plain HTML that work without JavaScript; a small
inline script adds search, filters and "open now" when JavaScript is available.

  python3 tools/build_hbc.py                       # public build: only verified / needs_recheck / unverified
  python3 tools/build_hbc.py --drafts --out /tmp/x # private preview that also shows drafts (never commit this)

Run tools/validate_hbc.py first; this script refuses to build if it fails.
"""
import argparse, datetime as dt, html, json, os, subprocess, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HBC = os.path.join(ROOT, 'data', 'hbc')
DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
COST_LABEL = {'free': 'Free', 'sliding': 'Sliding scale', 'insurance': 'Insurance / Apple Health', 'income-qualified': 'Income-qualified',
              'subsidy': 'Discount', 'loan': 'Loan', 'reimbursement': 'Reimbursement', 'cash-grant': 'Cash benefit',
              'restricted-benefit': 'Benefit (restricted use)', 'paid': 'Paid', 'unknown': 'Cost not stated — ask'}
STATUS_LABEL = {'verified': 'Verified', 'needs_recheck': 'Needs recheck — call first', 'unverified': 'Unverified — call first',
                'draft': 'DRAFT — not public'}
e = lambda s: html.escape(str(s or ''), quote=True)


def t12(hhmm):
    h, m = map(int, hhmm.split(':'))
    if h == 24 or (h == 0 and m == 0):
        return 'midnight'
    suf = 'am' if h < 12 else 'pm'
    h = h % 12 or 12
    return f'{h}{":%02d" % m if m else ""}{suf}'


def day_list(dows):
    dows = sorted(set(dows))
    if dows == list(range(7)):
        return 'Every day'
    if dows == [1, 2, 3, 4, 5]:
        return 'Mon–Fri'
    return ', '.join(DAYS[d][:3] for d in dows)


CSS = """
:root{--ink:#0a1a33;--paper:#f8f4ea;--card:#fff;--gold:#e8b818;--muted:#5a6475;--line:#d9d2c0;--warn:#8a5a00;--warnbg:#fff4d6;--ok:#1d6b3a;--okbg:#e3f3e8;--draft:#7a1f1f;--draftbg:#fbe3e3;--link:#0b4fa3}
@media (prefers-color-scheme:dark){:root{--ink:#eef0f4;--paper:#0d1422;--card:#16203a;--muted:#a8b0c0;--line:#2a3654;--warn:#ffd27a;--warnbg:#3a2e10;--ok:#8fe0a8;--okbg:#123222;--draft:#ffb3b3;--draftbg:#3b1616;--link:#8cc2ff}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.5 Georgia,"PT Serif",serif}
a{color:var(--link)}a:focus,button:focus,input:focus,select:focus{outline:3px solid var(--gold);outline-offset:2px}
.wrap{max-width:860px;margin:0 auto;padding:0 16px}
header.top{background:#0a1a33;color:#f8f4ea;padding:14px 0 12px;border-bottom:4px solid var(--gold)}
header.top a{color:#f8f4ea;text-decoration:none}
.kicker{font:600 12px/1.2 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;opacity:.85}
h1.mast{margin:4px 0 0;font:900 clamp(30px,8vw,48px)/1 Georgia,serif;letter-spacing:.02em}
.crisis{background:#7a1f1f;color:#fff;font:600 15px/1.4 system-ui,sans-serif;padding:8px 0}
.crisis a{color:#fff;font-weight:700}
nav.cats{font:15px/1.3 system-ui,sans-serif;padding:10px 0;border-bottom:1px solid var(--line);overflow-x:auto;white-space:nowrap}
nav.cats a{display:inline-block;margin:2px 10px 2px 0}nav.cats a[aria-current]{font-weight:700;color:var(--ink)}
h2{font:700 26px/1.2 Georgia,serif;margin:22px 0 6px}
.lede{color:var(--muted);margin:0 0 14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin:14px 0}
.tile{display:block;background:var(--card);border:1px solid var(--line);border-left:6px solid var(--gold);padding:12px 14px;text-decoration:none;color:var(--ink);border-radius:6px}
.tile b{display:block;font-size:18px}.tile span{font:14px system-ui,sans-serif;color:var(--muted)}
.today-cta{display:block;background:var(--ink);color:var(--paper);padding:14px 16px;border-radius:6px;text-decoration:none;font:700 19px/1.3 system-ui,sans-serif;margin:16px 0}
.today-cta small{display:block;font-weight:400;font-size:14px;opacity:.85}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0;font:15px system-ui,sans-serif}
.filters input,.filters select{font:16px system-ui,sans-serif;padding:8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);min-height:44px}
.filters input{flex:1 1 220px}.filters input[type=checkbox]{flex:0 0 auto;width:22px;height:22px;min-height:0}.filters label{display:flex;align-items:center;gap:6px;min-height:44px}
.count{font:14px system-ui,sans-serif;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:12px 0}
.card h3{margin:0 0 2px;font:700 20px/1.25 Georgia,serif}
.org{font:14px system-ui,sans-serif;color:var(--muted)}
.badges{margin:8px 0;display:flex;flex-wrap:wrap;gap:6px}
.b{font:600 13px/1 system-ui,sans-serif;padding:6px 8px;border-radius:999px;border:1px solid var(--line)}
.b.ok{background:var(--okbg);color:var(--ok);border-color:transparent}.b.warn{background:var(--warnbg);color:var(--warn);border-color:transparent}
.b.draft{background:var(--draftbg);color:var(--draft);border-color:transparent}.b.open{background:var(--ok);color:#fff;border-color:transparent}
.card p{margin:6px 0}.meta{font:15px/1.45 system-ui,sans-serif}.meta dt{font-weight:700;margin-top:6px}.meta dd{margin:0}
table.hrs{border-collapse:collapse;font:15px system-ui,sans-serif;margin:4px 0}table.hrs td{padding:2px 12px 2px 0;vertical-align:top}
.small{font:13px/1.4 system-ui,sans-serif;color:var(--muted)}
.empty{background:var(--card);border:1px dashed var(--line);padding:16px;border-radius:8px}
footer{margin:30px 0 40px;font:14px/1.5 system-ui,sans-serif;color:var(--muted);border-top:1px solid var(--line);padding-top:12px}
.preview{background:var(--draftbg);color:var(--draft);font:700 14px system-ui,sans-serif;padding:8px 0;text-align:center}
.day h2{font-size:22px}
@media print{header.top,.crisis,nav.cats,.filters,.today-cta,footer .noprint{display:none}body{background:#fff;color:#000;font-size:12pt}.card{break-inside:avoid;border:1px solid #999}}
"""

JS = """
(function(){
 var fmt=new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23',year:'numeric',month:'2-digit',day:'2-digit'});
 var p={};fmt.formatToParts(new Date()).forEach(function(x){p[x.type]=x.value});
 var dow=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(p.weekday),now=(+p.hour)*60+(+p.minute),date=p.year+'-'+p.month+'-'+p.day;
 function openState(c){var h;try{h=JSON.parse(c.getAttribute('data-hours')||'[]')}catch(_){h=[]}
  var today=h.filter(function(r){return r.date?r.date===date:(r.dow||[]).indexOf(dow)>=0});
  var o=today.some(function(r){return now>=r.o&&now<r.c});return {today:today.length>0,open:o}}
 var cards=[].slice.call(document.querySelectorAll('.card[data-hours]'));
 cards.forEach(function(c){var s=openState(c);c._today=s.today;c._open=s.open;var b=c.querySelector('.openbadge');
  if(b){if(s.open){b.textContent='Open now';b.className='b open openbadge';b.hidden=false}else if(s.today){b.textContent='Open later today or closed now';b.className='b openbadge';b.hidden=false}}});
 var q=document.getElementById('q'),hood=document.getElementById('hood'),cost=document.getElementById('cost'),ot=document.getElementById('opentoday'),cnt=document.getElementById('count');
 function apply(){var t=(q&&q.value||'').toLowerCase().trim(),n=0;cards.forEach(function(c){
  var ok=(!t||c.textContent.toLowerCase().indexOf(t)>=0)&&(!hood||!hood.value||c.getAttribute('data-hood')===hood.value)
   &&(!cost||!cost.value||c.getAttribute('data-cost')===cost.value)&&(!ot||!ot.checked||c._today);
  c.hidden=!ok;var d=c.closest('.day');if(ok&&!(d&&d.hidden))n++});if(cnt)cnt.textContent=n+' shown';}
 [q,hood,cost,ot].forEach(function(el){if(el)el.addEventListener('input',apply)});
 var f=document.querySelector('.filters');if(f)f.hidden=false;
 if(document.body.getAttribute('data-page')==='today'){document.querySelectorAll('.day').forEach(function(d){
  if(+d.getAttribute('data-dow')!==dow)d.hidden=true;else{var h=d.querySelector('h2');if(h)h.textContent='Today — '+h.textContent}});
  var note=document.getElementById('todaynote');if(note)note.hidden=false}
 apply();
})();
"""


def badge_html(it):
    out = []
    ct = it['cost']['type']
    out.append(f'<span class="b {"ok" if ct == "free" else ""}">{e(COST_LABEL.get(ct, ct))}</span>')
    st = it['status']
    cls = {'verified': 'ok', 'draft': 'draft'}.get(st, 'warn')
    label = STATUS_LABEL.get(st, st)
    if st == 'verified':
        label += ' ' + it['checked']
    out.append(f'<span class="b {cls}">{e(label)}</span>')
    el = it.get('elig') or {}
    if el.get('waitlist'):
        out.append('<span class="b warn">Waitlist</span>')
    if el.get('referral'):
        out.append('<span class="b warn">Referral required</span>')
    if el.get('appointment'):
        out.append('<span class="b">Appointment or sign-up</span>')
    if el.get('id_required'):
        out.append('<span class="b">Bring ID</span>')
    if it.get('religious') == 'required':
        out.append('<span class="b warn">Religious participation required</span>')
    out.append('<span class="b openbadge" hidden></span>')
    return '<div class="badges">' + ''.join(out) + '</div>'


def hours_html(it):
    rows = it.get('hours') or []
    if not rows:
        note = it.get('schedule_note')
        return f'<dt>Hours</dt><dd>{e(note) if note else "Not published — call or check the source before you go."}</dd>'
    trs = []
    for r in rows:
        when = day_list(r['dow']) if 'dow' in r else dt.date.fromisoformat(r['date']).strftime('%a %b %-d')
        span = 'Open 24 hours' if (r['open'], r['close']) == ('00:00', '24:00') else f'{t12(r["open"])}–{t12(r["close"])}'
        trs.append(f'<tr><td>{e(when)}</td><td>{e(span)}{(" · " + e(r["note"])) if r.get("note") and r.get("note") != "24/7" else ""}</td></tr>')
    extra = f'<div class="small">{e(it["schedule_note"])}</div>' if it.get('schedule_note') else ''
    return f'<dt>Hours</dt><dd><table class="hrs">{"".join(trs)}</table>{extra}</dd>'


def card_html(it, report_email):
    el = it.get('elig') or {}
    hrs = [{'dow': r.get('dow'), 'date': r.get('date'), 'o': int(r['open'][:2]) * 60 + int(r['open'][3:]),
            'c': int(r['close'][:2]) * 60 + int(r['close'][3:])} for r in it.get('hours') or []]
    parts = [f'<article class="card" id="{e(it["id"])}" data-hood="{e(it["hood"])}" data-cost="{e(it["cost"]["type"])}" data-hours="{e(json.dumps(hrs))}">',
             f'<h3>{e(it["name"])}</h3>']
    if it.get('org') and it['org'] != it['name']:
        parts.append(f'<div class="org">{e(it["org"])}</div>')
    parts.append(badge_html(it))
    parts.append(f'<p>{e(it["summary"])}</p><dl class="meta">')
    where = e(it['hood'])
    if it.get('address') and it['hood'] != 'Citywide':
        maps = 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(it['address'])
        where = f'{e(it["address"])} · {e(it["hood"])} · <a href="{e(maps)}" rel="noopener">Directions</a>'
    parts.append(f'<dt>Where</dt><dd>{where}</dd>')
    parts.append(hours_html(it))
    who = [x for x in (el.get('age'), el.get('income'), el.get('residency'), el.get('other')) if x]
    if who:
        parts.append('<dt>Who can use it</dt><dd>' + '<br>'.join(e(x) for x in who) + '</dd>')
    if it['cost'].get('amount') is not None or it['cost'].get('notes'):
        amt = it['cost'].get('amount')
        parts.append(f'<dt>Cost / amount</dt><dd>{e(("$%g · " % amt) if amt is not None else "")}{e(it["cost"].get("notes"))}</dd>')
    if it.get('religious') in ('optional',):
        parts.append('<dt>Faith</dt><dd>Religious activities are offered but optional.</dd>')
    if it.get('how_to_apply'):
        parts.append(f'<dt>How to get it</dt><dd>{e(it["how_to_apply"])}</dd>')
    c = it.get('contact') or {}
    contact = []
    if c.get('phone'):
        tel = ''.join(ch for ch in c['phone'] if ch.isdigit() or ch == '+')
        contact.append(f'<a href="tel:{e(tel)}">{e(c["phone"])}</a>')
    if c.get('url'):
        contact.append(f'<a href="{e(c["url"])}" rel="noopener">Official page</a>')
    if contact:
        parts.append('<dt>Contact</dt><dd>' + ' · '.join(contact) + '</dd>')
    parts.append('</dl>')
    srcs = ' · '.join(f'<a href="{e(u)}" rel="noopener">{e(t)}</a>' for t, u in it['src'])
    rep = ''
    if report_email:
        mail = 'mailto:' + report_email + '?subject=' + urllib.parse.quote(f'HBC correction: {it["id"]} {it["name"]}')
        rep = f' · <a href="{e(mail)}">Report a problem</a>'
    parts.append(f'<p class="small">Source: {srcs}<br>Last checked {e(it["checked"])}{rep}</p></article>')
    return ''.join(parts)


def page(title, body, conf, active=None, page_id='', preview=False, desc=''):
    cats = sorted(conf['categories'].items(), key=lambda kv: kv[1]['order'])
    nav = ['<a href="/hbc/"' + (' aria-current="page"' if active == 'home' else '') + '>Start</a>',
           '<a href="/hbc/today/"' + (' aria-current="page"' if active == 'today' else '') + '>Open today</a>']
    for k, cc in cats:
        short = cc['label'].split(',')[0].split(' & ')[0]
        nav.append(f'<a href="/hbc/{conf["slugs"].get(k, k)}/"' + (' aria-current="page"' if active == k else '') + f'>{e(short)}</a>')
    nav.append('<a href="/hbc/about/"' + (' aria-current="page"' if active == 'about' else '') + '>About</a>')
    robots = '<meta name="robots" content="noindex,nofollow">' if preview or conf.get('noindex', True) else ''
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · HOMELESS BY CHOICE · Seattle</title>
<meta name="description" content="{e(desc or 'Free and almost-free help in Seattle: rooms, food, benefits, health care, clothing, showers and more.')}">
{robots}<meta name="theme-color" content="#0a1a33"><link rel="icon" href="/app/favicon.png">
<style>{CSS}</style></head>
<body data-page="{e(page_id)}">
{'<div class="preview">PRIVATE PREVIEW — includes draft listings that are not public</div>' if preview else ''}
<header class="top"><div class="wrap"><a href="/"><span class="kicker">Seattle Sinner · The Guitar Doug Report</span></a>
<h1 class="mast"><a href="/hbc/">HOMELESS BY CHOICE</a></h1></div></header>
<div class="crisis"><div class="wrap">Emergency: <a href="tel:911">911</a> · Crisis or suicide: call or text <a href="tel:988">988</a> · Help finding services: <a href="tel:211">211</a></div></div>
<div class="wrap"><nav class="cats" aria-label="HOMELESS BY CHOICE sections">{''.join(nav)}</nav>
<main>{body}</main>
<footer><p>Seattle city limits only. Listings are checked against each provider's own page or an official government page; the date on every listing shows when. Hours and rules change — call before a long trip. Nothing here is legal, medical or financial advice. No ads, no sign-up, no paywall on this section.</p>
<p class="noprint"><a href="/hbc/about/">How we check listings</a> · Page built {e(conf['_built'])}</p></footer></div>
<script>{JS}</script></body></html>
"""


def filters(items):
    hoods = sorted({it['hood'] for it in items})
    costs = sorted({it['cost']['type'] for it in items}, key=lambda c: list(COST_LABEL).index(c) if c in COST_LABEL else 99)
    h = ''.join(f'<option value="{e(x)}">{e(x)}</option>' for x in hoods)
    c = ''.join(f'<option value="{e(x)}">{e(COST_LABEL.get(x, x))}</option>' for x in costs)
    return (f'<form class="filters" hidden role="search" onsubmit="return false"><input id="q" type="search" placeholder="Search this page" aria-label="Search this page">'
            f'<select id="hood" aria-label="Neighborhood"><option value="">All neighborhoods</option>{h}</select>'
            f'<select id="cost" aria-label="Cost"><option value="">Any cost</option>{c}</select>'
            f'<label><input id="opentoday" type="checkbox"> Open today</label><span id="count" class="count" aria-live="polite"></span></form>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--drafts', action='store_true', help='private preview: include draft listings')
    ap.add_argument('--out', default=os.path.join(ROOT, 'hbc'))
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if not a.drafts and out != os.path.join(ROOT, 'hbc'):
        pass
    if a.drafts and out == os.path.join(ROOT, 'hbc'):
        sys.exit('Refusing to write a draft preview into the repo. Use --out with a folder outside it.')
    if subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'tools', 'validate_hbc.py')], capture_output=True).returncode:
        sys.exit('validate_hbc.py reported errors; fix them first.')
    conf = json.load(open(os.path.join(HBC, 'config.json'), encoding='utf-8'))
    conf.setdefault('slugs', {'vehicle': 'vehicle-living'})
    conf['_built'] = dt.datetime.now(dt.timezone(dt.timedelta(hours=-8))).strftime('%Y-%m-%d %H:%M PT')
    show = set(conf['public_statuses']) | ({'draft'} if a.drafts else set())
    report_email = conf.get('report_email', '')
    cats = sorted(conf['categories'].items(), key=lambda kv: kv[1]['order'])
    data = {}
    for k, _ in cats:
        p = os.path.join(HBC, k + '.json')
        items = json.load(open(p, encoding='utf-8'))['items'] if os.path.exists(p) else []
        data[k] = sorted([it for it in items if it['status'] in show and it.get('in_city')], key=lambda it: (it['hood'] == 'Citywide', it['hood'], it['name']))

    def write(rel, text):
        path = os.path.join(out, rel, 'index.html')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

    # category pages
    for k, cc in cats:
        items = data[k]
        intro = f'<h2>{e(cc["label"])}</h2>'
        if k == 'vehicle':
            intro += '<p class="lede">Seattle parking rules are under review and this page will only list rules confirmed on the City\'s own pages. Nothing here means a spot is legal or safe to park overnight.</p>'
        elif k == 'rooms':
            intro += '<p class="lede">Rooms are listed only after we confirm the details. Contact goes through the original ad.</p>'
        if items:
            body = intro + filters(items) + ''.join(card_html(it, report_email) for it in items)
        else:
            body = intro + '<div class="empty">No checked listings here yet. We publish only what we can confirm from an official source. Meanwhile, call <a href="tel:211">211</a> for help finding services.</div>'
        write(conf['slugs'].get(k, k), page(cc['label'], body, conf, k, k, a.drafts))

    # today
    pub = [it for k, _ in cats for it in data[k] if it.get('hours')]
    days = []
    for d in range(7):
        rows = [it for it in pub if any(d in (r.get('dow') or []) for r in it['hours'])]
        if rows:
            days.append(f'<section class="day" data-dow="{d}"><h2>{DAYS[d]}</h2>' + ''.join(card_html(it, report_email) for it in rows) + '</section>')
    body = ('<h2>Free Help Available Today</h2><p class="lede">Built only from schedules on each provider\'s own page. '
            'Listings without published hours are left out, not guessed. Holiday hours may differ — call first.</p>'
            '<p id="todaynote" class="small" hidden>Showing today in Seattle time. Without JavaScript this page shows the whole week.</p>'
            + filters(pub) + (''.join(days) or '<div class="empty">No published schedules yet.</div>'))
    write('today', page('Free Help Available Today', body, conf, 'today', 'today', a.drafts))

    # landing
    tiles = ''.join(f'<a class="tile" href="/hbc/{conf["slugs"].get(k, k)}/"><b>{e(cc["label"])}</b><span>{len(data[k])} listing{"s" if len(data[k]) != 1 else ""}</span></a>' for k, cc in cats)
    body = ('<p class="lede" style="margin-top:16px">A practical guide to living in Seattle for free or almost nothing — whether by choice, by necessity, or because you have nowhere else to go. '
            'Every listing links to its source and shows the date we last checked it.</p>'
            '<a class="today-cta" href="/hbc/today/">Free Help Available Today<small>Meals, showers, clinics and more with published hours</small></a>'
            f'<div class="tiles">{tiles}</div>')
    write('', page('Seattle free help guide', body, conf, 'home', 'home', a.drafts))

    # about
    body = ('<h2>How this guide works</h2>'
            '<p>We cover Seattle city limits only. Federal and Washington State programs are included when Seattle residents can use them.</p>'
            '<p>Every fact comes from the provider\'s own page or an official government page. We write descriptions in our own words and link to the source. We never list a private person\'s phone number or email.</p>'
            '<p><b>Verified</b> means we confirmed the listing on the date shown. <b>Needs recheck</b> means that date is getting old or a source changed — call first. '
            '<b>Cost not stated</b> means the provider doesn\'t say it is free, so we don\'t either.</p>'
            '<p>"Free Help Available Today" uses only published schedules. If a place doesn\'t publish hours, it isn\'t on that page.</p>'
            '<p>For vehicle living we only describe rules confirmed on the City of Seattle\'s own pages, and we never promise a spot is legal or safe.</p>'
            + (f'<p>Found a mistake? Email <a href="mailto:{e(report_email)}">{e(report_email)}</a>. No account needed.</p>' if report_email else ''))
    write('about', page('About this guide', body, conf, 'about', 'about', a.drafts))
    n = sum(len(v) for v in data.values())
    print(f'Built {len(cats) + 3} pages with {n} listings into {out}{" (DRAFT PREVIEW)" if a.drafts else ""}')


if __name__ == '__main__':
    main()
