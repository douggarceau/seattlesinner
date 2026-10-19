# Music & Sports Calendar — scheduled task prompt

Schedule: every 4 hours.

---

Every-4-hours CALENDAR DESK for The Guitar Doug Report, {{CITY}} Edition ({{DOMAIN}}, GitHub Pages repo {{REPO}}, branch main). The page merges data/cal.json and data/sports.json. Goal: AS MANY real upcoming {{CITY}} shows as possible.

1. Attach the repo with push access and clone it. Read data/cal.json. Shape: {"asof":"ISO time","events":[{"date":"YYYY-MM-DD","time":"8:00 PM" or "","artists":"Headliner w/ Opener","venue":"","hood":"neighborhood","genre":"live|hip-hop|r&b|jazz|electronic|latin|country|folk|metal|punk|indie|rock|experimental|world|pop|classical|goth|other","price":"","ages":"","url":"","src":""}]}.

2. Gather shows for the next 45 days inside {{CITY}} city limits. Rotate through aggregators (Songkick, Bandsintown, JamBase, DICE, Eventbrite, Ticketmaster, AXS, the local alt-weekly calendar, the local public radio station's calendar) and the major venue calendars, prioritizing sources not used last run (track in "sources_last_run").

3. Every event must come from a page you actually read; never invent dates, times, prices or URLs. Skip past, cancelled and private events.

4. Merge: dedupe by date + venue + first artist; drop past events; sort by date then time; cap at 1500. Keep one venue spelling and one neighborhood per venue. Set asof. Validate with json.load.
   SPORTS (data/sports.json, genre "sports"): home games only for {{TEAMS}}, next 60 days, once a day, from official schedules.

5. If changed, commit only those files with author "Guitar Doug Report" <douggarceau@users.noreply.github.com>, message "Calendar update <date time>", ending with "Co-Authored-By: Claude <noreply@anthropic.com>". git pull --rebase origin main, push to main.

6. Message the owner one short line: "Calendar: <n> new shows · <total> listed · <k> sources", or the error.
