# The Guitar Doug Report

The site behind seattlesinner.com. Published with GitHub Pages; content refreshes daily.

## Layout (Oct 2026)
- `index.html` is the main site (classic dark design) and the source of truth for stories (`const STORIES=`) and the Wire/venue/band data blocks.
- `/rs/` is the Rolling Stone-style edition. It reads `data/stories.json`, `data/wire.json`, `data/cal.json`, `data/crime.json` and `data/photos.json`; after editing index.html run `python3 src/export_data.py`.
- `/newsprint/` opens the main site in black-and-white; `/report/` is the NYT-style edition.
