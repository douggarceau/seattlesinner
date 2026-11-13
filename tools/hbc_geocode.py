#!/usr/bin/env python3
"""Fill in lat/lng for HOMELESS BY CHOICE listings that have an address but no coordinates.

Uses the U.S. Census Bureau geocoder (free, no key, public-domain results).
Only fills empty coordinates; never changes an existing lat/lng. Listings the
geocoder can't match are reported so they can be placed by hand.

  python3 tools/hbc_geocode.py              # all category files
  python3 tools/hbc_geocode.py food health  # just these
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HBC = os.path.join(ROOT, 'data', 'hbc')
API = 'https://geocoding.geo.census.gov/geocoder/locations/onelineaddress'


def geocode(address):
    q = urllib.parse.urlencode({'address': address, 'benchmark': 'Public_AR_Current', 'format': 'json'})
    req = urllib.request.Request(API + '?' + q, headers={'User-Agent': 'seattlesinner-hbc/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        m = json.load(r)['result']['addressMatches']
    if not m:
        return None
    c = m[0]['coordinates']
    return round(c['y'], 6), round(c['x'], 6), m[0]['matchedAddress']


def main():
    conf = json.load(open(os.path.join(HBC, 'config.json'), encoding='utf-8'))
    cats = sys.argv[1:] or list(conf['categories'])
    for cat in cats:
        path = os.path.join(HBC, cat + '.json')
        if not os.path.exists(path):
            continue
        doc = json.load(open(path, encoding='utf-8'))
        changed = False
        for it in doc['items']:
            # Citywide programs and phone lines have no single location to map.
            if it.get('hood') == 'Citywide' or it.get('lat') is not None:
                continue
            addr = re.sub(r'\s*\([^)]*\)', '', it.get('address') or '')  # drop "(basement level)" etc.
            addr = re.sub(r'^[^\d,]+,\s*(?=\d)', '', addr)               # drop a leading place name
            if not addr:
                continue
            try:
                hit = geocode(addr)
            except Exception as e:  # network or API trouble: leave it empty, report it
                print(f'{cat}/{it["id"]}: geocoder error {e}')
                continue
            if hit:
                it['lat'], it['lng'] = hit[0], hit[1]
                changed = True
                print(f'{cat}/{it["id"]}: {hit[2]} -> {hit[0]}, {hit[1]}')
            else:
                print(f'{cat}/{it["id"]}: NO MATCH for {addr!r} (place by hand)')
            time.sleep(0.3)
        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(doc, f, ensure_ascii=False, indent=1)
                f.write('\n')


if __name__ == '__main__':
    main()
