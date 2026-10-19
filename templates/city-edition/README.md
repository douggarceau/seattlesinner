# City Edition Template — The Guitar Doug Report

Everything needed to launch the Report in a new city: the newspaper-style front page, the daily story desks, and Doug's existing stories.

## What's in here

| File | What it is |
|---|---|
| `edition_tpl.html` | The newspaper front page (masthead, city-first layout, Crime Watch and Tonight rail, sections, story pages with a comment section, daily main-story slot). Point SB_URL/SB_KEY at the city's own Supabase project (same comments table as tools/supabase/sinner.sql). Change the city name and the `LOCALRX` place list. |
| `mk_edition.py` | Builds the page from the stories in the site's `index.html`. |
| `masthead.png` | The Guitar Doug Report masthead. |
| `stories_seattle.json` | Doug's stories as of Oct 19, 2026. National stories can run in every city; Seattle ones stay Seattle-only unless rewritten. |
| `task_main_story.md` | Daily main story desk (scandal, police misconduct, clubs/venues, celebrities, major crime, businesses/students, deadly crashes/fires, protests). |
| `task_overreach.md` | Daily government overreach / police-state story. |
| `task_crime_watch.md` | Crime Watch headlines every 4 hours. |
| `task_calendar.md` | Music and sports calendar every 4 hours. |

## Launching a new city

1. Make a new GitHub repo (or folder) for the city and copy this template into it.
2. Fill in the placeholders in every file:
   - `{{CITY}}` — e.g. Portland
   - `{{STATE}}` — e.g. Oregon
   - `{{COUNTY}}` — e.g. Multnomah County
   - `{{TZ}}` — e.g. America/Los_Angeles
   - `{{REPO}}` — e.g. douggarceau/portland-report
   - `{{DOMAIN}}` — the site's web address
   - `{{OUTLETS}}` — the city's TV stations, papers, alt-weeklies and neighborhood blogs
   - `{{POLICE}}` — police department, accountability office and blotter
   - `{{OFFICIALS}}` — council, mayor, county, school board
   - `{{TEAMS}}` — local pro and college teams
   - `{{CAMPUSES}}` — local colleges and school district
   - `{{NEIGHBORHOODS}}` — neighborhood list for Crime Watch
3. In `edition_tpl.html`, change "Seattle Edition", "Tonight in Seattle", the weather coordinates, and the `LOCALRX` list of local place names.
4. Create the four scheduled tasks from the `task_*.md` files.
5. Copy over any national stories from `stories_seattle.json` you want to run there.
