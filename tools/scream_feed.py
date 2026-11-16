#!/usr/bin/env python3
"""Seattle Night Stalker: grisly-crime and sex-scandal headlines -> data/scream.json (owner, Nov. 16, 2026).

The page keeps the two newest grisly crimes in the top 5 of the Seattle headlines box,
and mixes the sex-scandal headlines in by date.

Staying within the law (how this works):
  - Links only. Every item is a headline already published by an established local newsroom,
    shown with that outlet's name and linking to its story. We add no words, claims or names
    of our own, so the site repeats nothing the outlet did not publish and the reader goes to
    the outlet for the facts (including "charged", "accused" and outcomes).
  - Sex-scandal items never involve minors: anything mentioning children, teens, students,
    schools, abuse, assault, rape or trafficking is skipped. Those are victims' stories, not scandals.
  - No sports (site rule).
Standard library only. No AI. Also dark and strange news at the top (underworld, cults and the occult, cryptids, the unexplained, true crime, Seattle scares, paranormal, UFOs, conspiracy theories, AI gone wrong, dangerous robots,
military drones, horror, bodies found, fights, drug raids, police scandals and lawsuits, protests, groups disrupting meetings and events, activists and human rights groups, peace, the environment, anti-establishment movements, antifa,
police corruption, passengers removed from planes):
newsroom reports about those subjects found through news search, again linked to the outlet.
Usage: python3 tools/scream_feed.py [repo_root]
"""
import json, os, re, sys, html, datetime as dt, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'data', 'scream.json')
PT = dt.timezone(dt.timedelta(hours=-8))
NOW = dt.datetime.now(PT)

FEEDS = [
    ('The Seattle Times', 'https://www.seattletimes.com/seattle-news/crime/feed/'),
    ('The Seattle Times', 'https://www.seattletimes.com/seattle-news/feed/'),
    ('KOMO News', 'https://komonews.com/news/local.rss'),
    ('KIRO 7', 'https://www.kiro7.com/arc/outboundfeeds/rss/category/news/local/?outputType=xml'),
    ('KING 5', 'https://www.king5.com/feeds/syndication/rss/news/local'),
    ('FOX 13 Seattle', 'https://www.fox13seattle.com/rss/category/news'),
]

GN = 'https://news.google.com/rss/search?q={}%20when:7d&hl=en-US&gl=US&ceid=US:en'
# Strange news (owner, Nov. 16, 2026): newsroom reports ABOUT these subjects, linked to the outlet.
STRANGE = [
 ('Underworld', ['Seattle gang OR cartel OR "organized crime" OR "drug ring"', 'mob OR mafia OR cartel OR "organized crime" boss', '"dark web" OR "black market" OR heist OR smuggling ring'],
  r"\b(gangs?|gangsters?|cartels?|mob|mobsters?|mafia|organized crime|crime (?:family|boss|ring)|drug ring|dark web|black market|heists?|smuggl\w*|underworld|hitm[ae]n|contract killing|racketeer\w*|money launder\w*)\b"),
 ('Cults & occult', ['cult leader OR "doomsday cult" OR "cult members"', 'occult OR ritual OR seance OR ouija OR "black magic"', 'vampire OR "blood ritual" OR satanic ritual'],
  r"\b(cults?|cultists?|occult\w*|(?:satanic|blood|occult|dark) rituals?|ritual(?:istic)? (?:killing|murder|sacrifice|abuse)|s[eé]ances?|ouija|black magic|voodoo|vampires?|sorcer\w*|necromanc\w*|human sacrifice)\b"),
 ('Cryptids', ['Bigfoot OR Sasquatch', 'cryptid OR "lake monster" OR mothman OR chupacabra'],
  r"\b(bigfoot|sasquatch|cryptids?|lake monster|sea serpent|mothman|chupacabra|yeti|skinwalker|dogman)\b"),
 ('Unexplained', ['Washington mysterious OR unexplained OR vanished', 'unexplained mystery OR "strange lights" OR "mysterious disappearance"'],
  r"\b(unexplained|myster(?:y|ies|ious)|vanish\w*|disappear(?:ed|ance)|strange (?:lights?|sounds?|noises?)|eerie|creepy|unsolved|enigma)\b"),
 ('True crime', ['"serial killer" OR "cold case" OR "unsolved murder"', 'Washington "cold case" OR "serial killer" OR "Green River"'],
  r"\b(serial killers?|cold cases?|unsolved (?:murders?|killings?|cases?)|true crime|green river|ted bundy|zodiac killer|manhunt|killing spree)\b"),
 ('Paranormal', ['Seattle ghost OR haunted', 'ghost sighting OR haunted house OR haunting OR poltergeist OR paranormal',
                 'demonic possession OR exorcism OR exorcist', 'demonic OR "evil spirit" OR "evil spirits" OR satanic',
                 'witchcraft OR "witch trial" OR coven OR "accused of witchcraft"'],
  r"\b(ghosts?|haunt(?:ed|ing|ings)|poltergeists?|demonic|demons?|exorcis\w*|possessed|possession|witchcraft|witch trials?|covens?|"
  r"evil spirits?|paranormal|satanic|satanists?|devil worship\w*|cursed?)\b"),
 ('UFOs', ['Washington UFO OR UAP', 'UFO OR UAP OR "unidentified anomalous"'],
  r"\b(ufos?|uaps?|aliens?|extraterrestrial\w*|flying saucers?|unidentified (?:flying|anomalous))\b"),
 ('Conspiracy', ['"conspiracy theory" OR "conspiracy theories" OR "conspiracy theorist"'], r"\bconspirac\w*\b"),
 ('AI gone wrong', ['AI chatbot lawsuit OR "AI error" OR "AI mistake" OR deepfake OR "AI hallucination" OR "rogue AI"'],
  r"\b(ai|a\.i\.|artificial intelligence|chatbots?|deepfakes?|chatgpt|gemini|grok)\b"),
 ('Robots', ['robot attack OR robot injured OR robot danger OR robotaxi crash OR "humanoid robot"', 'Waymo OR robotaxi OR "delivery robot"'],
  r"\b(robots?|robotic|robotaxis?|humanoids?|waymo)\b"),
 ('Military drones', ['military drone OR "drone strike" OR "drone swarm" OR "drone warfare" OR "killer drone"', 'drones over base OR drone incursion'],
  r"\b(drones?|uavs?|unmanned aerial)\b"),
 ('Body found', ['Seattle "body found" OR "remains found" OR "body discovered" OR "body recovered"', 'Washington "body found" OR "human remains"'],
  r"\b(bod(?:y|ies)|remains)\b.*\b(found|discovered|recovered|pulled)\b|\b(found|discovered)\b.*\b(bod(?:y|ies)|remains)\b"),
 ('Fights', ['Seattle fight breaks out OR brawl OR melee', 'Washington "fight breaks out" OR brawl'],
  r"\b(fights? breaks? out|brawls?|brawling|melee|fistfights?|street fight|fight erupts?|punch\w*|beat(?:en|ing) up)\b"),
 ('Drug raids', ['Seattle drug raid OR drug bust OR fentanyl seized', 'Washington "drug raid" OR "drug bust" OR "drug ring"'],
  r"\b(drug (?:raids?|busts?|rings?|sweeps?|trafficking)|raids?|busts?|seiz\w*|narcotics|fentanyl|meth\w*|cocaine|heroin)\b"),
 ('Police scandal', ['Seattle police lawsuit OR misconduct OR scandal', 'SPD officer lawsuit OR fired OR misconduct OR settlement', 'King County sheriff lawsuit OR misconduct'],
  r"\b(police|spd|officers?|cops?|sheriff\w*|deputies|deputy|troopers?)\b.*\b(lawsuits?|sue[ds]?|suing|settle(?:s|d|ment)|misconduct|scandal\w*|fired|excessive force|disciplined|cover-?up|wrongful)\b|\b(lawsuits?|sue[ds]?|settle(?:s|d|ment)|misconduct|scandal\w*|wrongful)\b.*\b(police|spd|officers?|sheriff\w*)\b"),
 ('Protests', ['Seattle protest OR rally OR demonstration', 'Seattle protesters OR walkout OR "sit-in"'],
  r"\b(protest\w*|rall(?:y|ies)|marchers|marched|protest march|march (?:on|against|through|to)|demonstrat(?:ors?|ions?)|walkouts?|sit-ins?|blockades?|picket\w*)\b"),
 ('Disruptions', ['Seattle city council meeting disrupted OR disruption OR "shouted down"', 'city council meeting disrupted OR "shouted down" OR "meeting halted"',
                  'protesters shut down event OR "shut down" speech OR event canceled after protest'],
  r"\b(disrupt\w*|shouted down|shut(?:s|ting)? down|halted|interrupt\w*|stormed|derail\w*|canceled after|cancelled after|cleared the room|recess(?:ed)? after)\b.*\b(meeting|council|hearing|event|speech|talk|show|rally|session|forum|commission)\b|\b(meeting|council|hearing|event|speech|talk|forum)\b.*\b(disrupt\w*|shouted down|shut down|halted|stormed|cleared)\b"),
 ('Antifa', ['antifa Seattle', 'antifa'], r"\bantifa\b"),
 ('Activists', ['Seattle activists OR activist group OR advocacy group', 'Washington ACLU OR "civil rights" lawsuit OR activists',
                'human rights group OR "Human Rights Watch" OR "Amnesty International" OR "human rights activists"'],
  r"\b(activists?|activism|human rights|civil rights|aclu|amnesty international|human rights watch|advocacy groups?|advocates|rights groups?|watchdog groups?)\b"),
 ('Peace', ['peace activists OR "anti-war" OR "peace march" OR "peace rally"', 'ceasefire OR "peace talks" OR "peace deal"'],
  r"\b(peace|anti-?war|ceasefire|cease-fire|truce|pacifis\w*|disarmament)\b"),
 ('Environment', ['Seattle environment OR climate OR pollution OR "Puget Sound"', 'environmental activists OR "climate activists" OR "climate protest"', 'environmental lawsuit OR pollution OR "toxic spill"'],
  r"\b(environment\w*|climate|pollut\w*|toxic|spill|emissions?|wildlife|orcas?|salmon|old-growth|deforest\w*|fossil fuels?|pipeline|greenpeace|sierra club|earthjustice|extinction rebellion)\b"),
 ('Anti-establishment', ['anti-establishment OR "against the establishment" OR "establishment revolt"', '"grassroots movement" OR "populist revolt" OR "outsider candidate" OR "anti-government"'],
  r"\b(anti-?establishment|establishment|grassroots|populis\w*|outsider|insurgen\w*|anti-?government|revolt|uprising|rebellion|rebel\w*)\b"),
 ('Police corruption', ['Washington police corruption OR bribery', 'police corruption OR "officer bribery" OR "police officer charged"'],
  r"\b(police|officers?|cops?|sheriff\w*|deputies|deputy|troopers?|detectives?)\b.*\b(corrupt\w*|brib\w*|kickbacks?|perjur\w*|falsif\w*|stole|theft|embezzl\w*|extort\w*|indicted|charged)\b|\b(corrupt\w*|brib\w*)\b.*\b(police|officers?|cops?|sheriff\w*)\b"),
 ('Plane drama', ['Sea-Tac passenger removed OR "kicked off" flight OR unruly passenger', 'passenger removed from plane OR "kicked off" flight OR "unruly passenger" OR "disruptive passenger"'],
  r"\b(removed|kicked off|escorted off|booted|dragged off|taken off|duct[- ]taped|restrained|unruly|disruptive|meltdown|diverted)\b.*\b(plane|flights?|airlines?|jet|sea-?tac|airport|aircraft)\b|\b(plane|flight|airline|sea-?tac)\b.*\b(removed|kicked off|escorted off|unruly|disruptive|meltdown|diverted)\b"),
 ('Horror', ['horror movie OR horror film OR "horror story" OR "real-life horror"', 'Seattle horror'],
  r"\b(horror\w*|horrific|terror\w* (?:film|movie)|slasher|scream \d)\b"),
]
STRANGE_RX = {c: rx for c, _, rx in STRANGE}
# owner's standing rule for this site: nothing LGBT-related
NO_LGBT = re.compile(r"\b(gay|lesbian|lgbt\w*|queer|trans|transgender|nonbinary|drag (?:queen|show|brunch)|pride (?:month|parade|march))\b", re.I)
LOCAL_CATS = {'Body found', 'Fights', 'Drug raids', 'Police scandal', 'Protests'}
SEA = re.compile(r"\b(seattle|tacoma|everett|bellevue|redmond|kent|renton|federal way|auburn|lynnwood|shoreline|burien|kirkland|bothell|"
                 r"issaquah|sammamish|puyallup|olympia|bremerton|edmonds|tukwila|seatac|mercer island|king county|snohomish|pierce county|"
                 r"kitsap|capitol hill|ballard|fremont|belltown|west seattle|wash\.|washington state|spd)\b", re.I)
NOT_FIGHT = re.compile(r"\b(postgame|game|acc|ncaa|nfl|nba|senate|congress|leadership|political|legal|court|budget|custody|election|campaign|party)\b", re.I)
# Seattle scares: local newsroom stories about people in the Seattle area frightened by something
SCARES = re.compile(r"\b(terrif\w*|frighten\w*|scar(?:ed|y|es)|spooked|panic\w*|fear(?:ful|s|ed)?|afraid|alarm(?:ed|ing)|startl\w*|"
                    r"creepy|eerie|mysterious|unsettl\w*|nightmare|shaken|horrif\w*|chilling)\b", re.I)
AI_BAD = re.compile(r"\b(lawsuit|sue[ds]?|suing|wrong|errors?|mistakes?|scams?|fake|danger\w*|warn\w*|threat\w*|blamed|harm\w*|rogue|lie[ds]?|"
                    r"hallucinat\w*|fail\w*|glitch\w*|crash\w*|attack\w*|injur\w*|kill\w*|death|dead|chaos|banned|deepfakes?|out of control|"
                    r"creepy|terrif\w*|fear\w*|alarm\w*|strike\w*|swarm\w*|war\w*|military|weapon\w*|incursion\w*|shot down|sighting\w*)\b", re.I)
NOT_NEWS = re.compile(r"\b(reviews?|reviewed|books?|free on youtube|streaming now|novel|manga|anime|comics?|trailer|season \d|episode|tickets?|museum|guide to|recipe|costumes?|ballet|musical|"
                      r"whisk(?:e)?y|beer|wine|cocktail|wardrobe|playstation|xbox|nintendo|video game|seahawks|mariners|kraken|sounders|nfl|nba|mlb|nhl|"
                      r"touchdown|quarterback|coach|playoffs?|defeats?|beats|win over|wins|victory|score[sd]?|points|marathon|tournament|no\. \d+|targets?|yards|roster|draft|sale|deals?|best .* to buy|box office|codes?|roblox|fortnite|gaming|game)\b", re.I)
NOT_FILM = re.compile(r"\b(movie|film|streaming|netflix|hulu|director|cast|sequel|remake)\b", re.I)

GRISLY = re.compile(r"\b(murder(?:ed|s|ing)?|homicides?|killed|killing|slain|stabb(?:ed|ing)s?|shot (?:and killed|dead|to death)|"
                    r"(?:deadly|fatal) (?:shooting|stabbing|attack|assault|beating)|body (?:was )?found|bodies found|human remains|"
                    r"dismember\w*|beaten to death|manslaughter|death investigation|found dead)\b", re.I)
NOT_CRIME = re.compile(r"\b(crash|collision|wreck|hit by (?:a )?(?:car|train)|fire|blaze|drown\w*|avalanche|climber|hiker|"
                       r"overdose|seahawks|mariners|kraken|sounders|storm|huskies|cougars|game|playoff|coach)\b", re.I)
SCANDAL = re.compile(r"\b(sex scandal|sexual misconduct|sexual harassment|harassment (?:claims?|allegations?|lawsuit)|"
                     r"(?:extramarital |secret )?affair with|prostitut\w*|sex work\w*|brothel|escort (?:service|agency)|"
                     r"massage parlou?r|lewd|indecent exposure|voyeur\w*|peeping tom|explicit (?:photos?|images?|videos?|messages?)|"
                     r"nude (?:photos?|images?|videos?)|sexting|onlyfans|strip club|sex sting|soliciting sex|solicitation of (?:a )?prostitut\w*|"
                     r"sex (?:club|shop|tape)|swingers?)\b", re.I)
NOT_SCANDAL = re.compile(r"\b(child|children|kids?|minors?|teens?|teenage\w*|underage|juveniles?|girls?|boys?|students?|schools?|"
                         r"infants?|toddlers?|babies|baby|rape[ds]?|raping|sexual(?:ly)? assault\w*|assault\w*|traffick\w*|abuse[ds]?|"
                         r"molest\w*|grooming|pornography)\b", re.I)

def clean_url(u):
    p = urlsplit(u.strip())
    q = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(('utm_', 'fbclid', 'gclid'))]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), ''))

def text(x):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x or ''))).strip()

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; seattle-scream-headlines/1.0)'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def items(outlet, url):
    out = []
    try:
        root = ET.fromstring(fetch(url))
    except Exception as e:
        print(f'{outlet}: skipped ({type(e).__name__})'); return out
    for it in root.iter('item'):
        title = text(it.findtext('title'))
        link = (it.findtext('link') or '').strip()
        if not title or not link.startswith('http'): continue
        try: when = parsedate_to_datetime(it.findtext('pubDate')).astimezone(PT)
        except Exception: when = NOW
        desc = text(it.findtext('description'))[:400]
        out.append({'h': title, 'url': clean_url(link), 'outlet': outlet, 'town': 'Seattle area',
                    'date': when.date().isoformat(), 't': when.isoformat(timespec='minutes'), 'sum': '', '_d': desc})
    print(f'{outlet}: {len(out)} items'); return out

def strange_items():
    res = []
    for cat, queries, rx in STRANGE:
        R = re.compile(rx, re.I)
        for q in queries:
            for x in items('news search', GN.format(urllib.request.quote(q))):
                h = x['h']; src = None
                if ' - ' in h:
                    h, src = [s.strip() for s in h.rsplit(' - ', 1)]
                if not R.search(h) or NOT_NEWS.search(h) or NO_LGBT.search(h): continue
                if cat != 'Horror' and NOT_FILM.search(h): continue
                if cat in ('AI gone wrong', 'Robots', 'Military drones') and not AI_BAD.search(h): continue
                if cat == 'Drug raids' and not re.search(r'drug|narcotic|fentanyl|meth|cocaine|heroin', h, re.I): continue
                if cat in LOCAL_CATS and not SEA.search(h): continue
                if cat == 'Fights' and NOT_FIGHT.search(h): continue
                x.update(h=h, outlet=src or 'News report', town=cat, cat=cat); res.append(x)
    return res

def main():
    prev = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {'crimes': [], 'scandals': []}
    got = [x for name, u in FEEDS for x in items(name, u)]
    crimes, scandals, scares = [], [], []
    for x in got:
        head = x['h']; both = head + ' ' + x['_d']
        if NO_LGBT.search(head): continue
        if (GRISLY.search(head) and not NOT_CRIME.search(head)) or re.search(STRANGE_RX['Body found'], head, re.I):
            crimes.append(x)
        elif re.search(STRANGE_RX['Police scandal'], head, re.I):
            scares.append(dict(x, cat='Police scandal'))
        elif re.search(STRANGE_RX['Protests'], head, re.I) and not NOT_NEWS.search(head):
            scares.append(dict(x, cat='Protests'))
        elif re.search(STRANGE_RX['Police corruption'], head, re.I):
            scares.append(dict(x, cat='Police corruption'))
        elif re.search(STRANGE_RX['Plane drama'], head, re.I):
            scares.append(dict(x, cat='Plane drama'))
        elif re.search(STRANGE_RX['Disruptions'], head, re.I) and not NOT_NEWS.search(head):
            scares.append(dict(x, cat='Disruptions'))
        elif re.search(STRANGE_RX['Activists'], head, re.I) and not NOT_NEWS.search(head):
            scares.append(dict(x, cat='Activists'))
        elif re.search(STRANGE_RX['Antifa'], head, re.I):
            scares.append(dict(x, cat='Antifa'))
        elif re.search(STRANGE_RX['Fights'], head, re.I) and not NOT_NEWS.search(head) and not NOT_FIGHT.search(head):
            scares.append(dict(x, cat='Fights'))
        elif re.search(STRANGE_RX['Drug raids'], head, re.I) and re.search(r'drug|narcotic|fentanyl|meth|cocaine|heroin', head, re.I):
            scares.append(dict(x, cat='Drug raids'))
        elif SCARES.search(head) and not NOT_NEWS.search(head):
            scares.append(dict(x, cat='Seattle scares'))
        elif SCANDAL.search(head) and not NOT_SCANDAL.search(both):
            scandals.append(x)
    STOP = set('after before their about where while there which being under over into from with that this have were said says will been police seattle'.split())
    def words(h): return {w for w in re.findall(r'[a-z]{4,}', h.lower()) if w not in STOP}
    def merge(new, old, keep_days, cap, kind):
        seen_u, kept, res = set(), [], []
        for x in sorted(new + old, key=lambda z: z.get('t') or z.get('date'), reverse=True):
            if x['url'] in seen_u: continue
            if (NOW.date() - dt.date.fromisoformat(x['date'])).days > keep_days: continue
            w = words(x['h'])
            # same story told by two outlets: share at least 3 key words, or more than 40% of them
            d = x['date']
            if any(len(w & k) >= 3 or (w and len(w & k) / len(w | k) > 0.4) or (kind == 'crime' and len(w & k) >= 2 and abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(kd)).days) <= 1)
                   for k, kd in kept): continue
            seen_u.add(x['url']); kept.append((w, d))
            x = {k2: v for k2, v in x.items() if not k2.startswith('_')}; x['kind'] = kind; res.append(x)
        return res[:cap]
    # crimes: keep older ones when the feeds are quiet, so two are always available for the top 5
    C = merge(crimes, prev.get('crimes', []), 45, 8, 'crime')
    S = merge(scandals, prev.get('scandals', []), 30, 8, 'scandal')
    # strange news: newest per category first, round-robin so the top of the list mixes subjects
    st = scares + strange_items(); bycat = {}
    def still_ok(x):
        # re-check items kept from earlier runs against today's rules
        c = x.get('cat'); h = x.get('h', '')
        if NO_LGBT.search(h): return False
        if NOT_NEWS.search(h) and c != 'Horror': return False
        rx = STRANGE_RX.get(c)
        return True if rx is None else bool(re.search(rx, h, re.I))
    for x in merge(st, [y for y in prev.get('strange', []) if still_ok(y)], 14, 60, 'strange'):
        bycat.setdefault(x['cat'], []).append(x)
    Z = []
    while any(bycat.values()):
        FIRST = ['Underworld', 'Paranormal', 'True crime', 'Cults & occult', 'Seattle scares', 'Cryptids', 'Unexplained', 'Body found', 'Police scandal', 'Police corruption', 'Fights', 'Plane drama', 'Protests', 'Activists', 'Peace', 'Environment', 'Anti-establishment', 'Disruptions', 'Drug raids', 'Antifa']
        for c in FIRST + [c for c, _, _ in STRANGE if c not in FIRST]:
            if bycat.get(c): x = bycat[c].pop(0); x['town'] = c; Z.append(x)
    Z = Z[:45]
    for i, x in enumerate(C): x['rank'] = (1, 3)[i] if i < 2 else 30 + i
    for x in S: x['rank'] = 8
    for x in C: x['town'] = 'Crime'
    for x in S: x['town'] = 'Scandal'
    data = {'asof': NOW.isoformat(timespec='minutes'), 'strange': Z, 'crimes': C, 'scandals': S,
            'note': 'Links to local newsrooms only; see tools/scream_feed.py for the rules.'}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('crimes', len(C), '| scandals', len(S), '| strange', len(Z))
    for x in Z[:10]: print('  strange', x['date'], x['cat'], '|', x['outlet'], '|', x['h'])
    for x in C[:4]: print('  crime  ', x['date'], x['outlet'], '|', x['h'])
    for x in S[:4]: print('  scandal', x['date'], x['outlet'], '|', x['h'])

if __name__ == '__main__':
    main()
