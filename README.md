# The Guitar Doug Report

The site behind seattlesinner.com. Published with GitHub Pages; content refreshes daily.

## Layout (Oct 2026)
- `index.html` is the front page (Rolling Stone-style edition). It reads `data/stories.json`, `data/wire.json`, `data/cal.json`, `data/crime.json` and `data/photos.json`.
- `classic.html` is the original full site and the source of truth for stories (`const STORIES=`) and the Wire/venue/band data blocks. After editing it, run `python3 src/export_data.py` and commit the updated `data/stories.json` and `data/wire.json`.
- `/newsprint/` opens the classic site in black-and-white; `/report/` is the NYT-style edition.
