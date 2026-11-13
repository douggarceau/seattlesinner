#!/usr/bin/env python3
"""Validate HOMELESS BY CHOICE data in data/hbc/.

Checks every data/hbc/<category>.json listed in config.json against the
rules below. Standard library only, so it runs in GitHub Actions without installs.

  python3 tools/validate_hbc.py            # errors fail (exit 1); warnings are printed
  python3 tools/validate_hbc.py --today 2026-11-20   # pretend it's another day (freshness checks)

Errors (block the build):
  * file shape, required fields, enum values, id format/prefix, duplicate ids
  * src links must be https; summary must not contain emails or phone numbers
  * hours must be HH:MM with open < close (24:00 allowed as close)
  * a public listing (verified / needs_recheck / unverified) must have in_city true,
    and if it has lat/lng the point must be inside the Seattle polygon
  * verified listings must be checked by the owner or a partner
  * rooms need a room block with rent

Warnings (shown in the review report):
  * past review_by (the daily sweep should move verified -> needs_recheck)
  * past expires
  * physical listing with no coordinates (city-limits test couldn't run)
  * likely duplicates (same name+address, or within 25 m with similar names)
"""
import argparse, datetime as dt, difflib, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HBC = os.path.join(ROOT, 'data', 'hbc')

STATUSES = {'draft', 'verified', 'needs_recheck', 'unverified', 'expired', 'removed'}
COST = {'free', 'sliding', 'insurance', 'income-qualified', 'subsidy', 'loan', 'reimbursement',
        'cash-grant', 'restricted-benefit', 'paid', 'unknown'}
RELIGIOUS = {'none', 'optional', 'required', 'unknown'}
CHECKED_BY = {'owner', 'partner', 'routine', 'claude'}
REQUIRED = ['id', 'name', 'summary', 'subcats', 'hood', 'in_city', 'cost', 'elig', 'religious',
            'hours', 'contact', 'src', 'status', 'checked', 'checked_by', 'review_by']
ALLOWED = set(REQUIRED) | {'org', 'level', 'address', 'lat', 'lng', 'how_to_apply', 'schedule_note', 'expires', 'notes', 'room'}
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
PHONE = re.compile(r'\(?\b\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b')
HHMM = re.compile(r'^(([01]\d|2[0-3]):[0-5]\d|24:00)$')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def load_polygon():
    g = json.load(open(os.path.join(HBC, 'seattle-area-polygon.geojson'), encoding='utf-8'))
    rings = []
    for f in g['features']:
        geom = f['geometry']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        for p in polys:
            rings.append(p)  # [outer, holes...]
    return rings


def in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def in_seattle(lat, lng, polys):
    for p in polys:
        if in_ring(lng, lat, p[0]) and not any(in_ring(lng, lat, h) for h in p[1:]):
            return True
    return False


def meters(a, b):
    r = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()


def mins(t):
    h, m = t.split(':')
    return int(h) * 60 + int(m)


def check_item(cat, conf, it, polys, today, err, warn):
    where = f"{cat}/{it.get('id', '?')}"
    for k in REQUIRED:
        if k not in it:
            err(where, f'missing field "{k}"')
    for k in it:
        if k not in ALLOWED:
            err(where, f'unknown field "{k}"')
    if not re.fullmatch(conf['prefix'] + r'-\d{4}', str(it.get('id', ''))):
        err(where, f'id must look like {conf["prefix"]}-0001')
    st = it.get('status')
    if st not in STATUSES:
        err(where, f'bad status {st!r}')
    if it.get('religious') not in RELIGIOUS:
        err(where, f'bad religious value {it.get("religious")!r}')
    if it.get('checked_by') not in CHECKED_BY:
        err(where, f'bad checked_by {it.get("checked_by")!r}')
    cost = it.get('cost') or {}
    if cost.get('type') not in COST:
        err(where, f'bad cost.type {cost.get("type")!r}')
    amt = cost.get('amount')
    if amt is not None and (isinstance(amt, bool) or not isinstance(amt, (int, float))):
        err(where, 'cost.amount must be a number or null; put text in cost.notes')
    summ = it.get('summary', '')
    if not 10 <= len(summ) <= 320:
        err(where, 'summary must be 10-320 characters')
    if EMAIL.search(summ) or PHONE.search(summ):
        err(where, 'summary contains an email or phone number; put organizational contacts in contact')
    if not it.get('subcats'):
        err(where, 'subcats is empty')
    src = it.get('src') or []
    if not src:
        err(where, 'needs at least one source link')
    for s in src:
        if not (isinstance(s, list) and len(s) == 2 and str(s[1]).startswith('https://')):
            err(where, f'source must be [title, https url]: {s!r}')
    url = (it.get('contact') or {}).get('url', '')
    if url and not url.startswith('https://'):
        err(where, 'contact.url must be https')
    for d in ('checked', 'review_by'):
        if not DATE.match(str(it.get(d, ''))):
            err(where, f'{d} must be YYYY-MM-DD')
    if it.get('expires') and not DATE.match(str(it['expires'])):
        err(where, 'expires must be YYYY-MM-DD or null')
    for h in it.get('hours', []):
        o, c = h.get('open', ''), h.get('close', '')
        if not (HHMM.match(o) and HHMM.match(c)):
            err(where, f'hours need HH:MM, got {o!r}-{c!r}')
            continue
        if mins(o) >= mins(c):
            err(where, f'hours open {o} must be before close {c} (split overnight hours into two rows)')
        if ('dow' in h) == ('date' in h):
            err(where, 'each hours row needs exactly one of dow or date')
        if 'dow' in h and (not h['dow'] or any(d not in range(7) for d in h['dow'])):
            err(where, f'dow must be 0-6 (0 = Sunday): {h["dow"]!r}')
    public = st in ('verified', 'needs_recheck', 'unverified')
    lat, lng = it.get('lat'), it.get('lng')
    if lat is not None and lng is not None:
        inside = in_seattle(lat, lng, polys)
        if inside != bool(it.get('in_city')):
            (err if public else warn)(where, f'in_city is {it.get("in_city")} but coordinates are {"inside" if inside else "outside"} Seattle')
    elif it.get('hood') != 'Citywide' and it.get('address'):
        warn(where, 'no coordinates, so the city-limits test could not run (run tools/hbc_geocode.py)')
    if public and not it.get('in_city'):
        err(where, 'public listings must be inside Seattle city limits')
    if st == 'verified' and it.get('checked_by') not in ('owner', 'partner'):
        err(where, 'only the owner or a named partner can mark a listing verified')
    if cat == 'rooms':
        room = it.get('room')
        if not isinstance(room, dict) or not isinstance(room.get('rent'), int):
            err(where, 'rooms need a room block with integer rent')
    elif 'room' in it:
        err(where, 'room block is only for the rooms category')
    if st in ('verified', 'needs_recheck', 'unverified', 'draft'):
        if DATE.match(str(it.get('review_by', ''))) and it['review_by'] < today:
            warn(where, f'review_by {it["review_by"]} has passed' + (' (sweep should mark needs_recheck)' if st == 'verified' else ''))
        if it.get('expires') and it['expires'] < today:
            warn(where, f'expired on {it["expires"]} (sweep should mark expired)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--today', default=dt.date.today().isoformat())
    a = ap.parse_args()
    conf = json.load(open(os.path.join(HBC, 'config.json'), encoding='utf-8'))
    polys = load_polygon()
    errors, warnings, ids, everything = [], [], {}, []

    def err(w, m): errors.append(f'ERROR   {w}: {m}')
    def warn(w, m): warnings.append(f'warning {w}: {m}')

    counts = {}
    for cat, cc in sorted(conf['categories'].items(), key=lambda kv: kv[1]['order']):
        path = os.path.join(HBC, cat + '.json')
        if not os.path.exists(path):
            continue
        try:
            doc = json.load(open(path, encoding='utf-8'))
        except json.JSONDecodeError as e:
            err(cat, f'invalid JSON: {e}')
            continue
        if set(doc) != {'asof', 'items'} or not isinstance(doc.get('items'), list):
            err(cat, 'file must be {"asof": ..., "items": [...]}')
            continue
        for it in doc['items']:
            check_item(cat, cc, it, polys, a.today, err, warn)
            i = it.get('id')
            if i in ids:
                err(f'{cat}/{i}', f'duplicate id (also in {ids[i]})')
            ids[i] = cat
            everything.append((cat, it))
            counts.setdefault(cat, {}).setdefault(it.get('status'), 0)
            counts[cat][it.get('status')] += 1

    live = [(c, it) for c, it in everything if it.get('status') not in ('removed', 'expired')]
    for n, (c1, x) in enumerate(live):
        for c2, y in live[n + 1:]:
            same_addr = x.get('address') and norm(x.get('address')) == norm(y.get('address'))
            sim = difflib.SequenceMatcher(None, norm(x['name']), norm(y['name'])).ratio()
            close = (None not in (x.get('lat'), y.get('lat')) and
                     meters((x['lat'], x['lng']), (y['lat'], y['lng'])) < 25)
            if (same_addr and sim > 0.8) or (close and sim > 0.6):
                warnings.append(f'warning {c1}/{x["id"]} ~ {c2}/{y["id"]}: possible duplicate ({x["name"]} / {y["name"]})')

    for line in errors + warnings:
        print(line)
    summary = ', '.join(f'{c}: ' + ' '.join(f'{k}={v}' for k, v in sorted(s.items())) for c, s in counts.items())
    print(f'\n{len(everything)} listings ({summary or "none"}); {len(errors)} errors, {len(warnings)} warnings')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
