# Site Schedule

A Gantt-style job planner for a carpentry business: jobs, site visits, deliveries and other notifications on one timeline.

- **Test site (this repo):** https://z-vz.github.io/site-schedule/. Jobs are saved in each browser only. Use **Load sample jobs** to try it out.
- **Live app:** runs separately on Cloudflare (Worker + D1 database). This repo never changes the live app or its data on its own.

## Files
| File | What it is |
|---|---|
| `site-schedule.html` | The app's source (the page, styles and logic) |
| `index.html` | The GitHub Pages test site, built from the source by `tools/build_pages.py` |
| `cloudflare/worker.js` | The Cloudflare version: one file you paste into the worker. Built by `cloudflare/build.py` |
| `version.json` | The current version number |
| `CHANGELOG.md` | What changed in each version |

## Building
```
python3 tools/build_pages.py     # test site -> index.html
python3 cloudflare/build.py      # live app  -> cloudflare/worker.js
```

## Updating the live app (only when you decide to)
Open the worker in Cloudflare → Edit code → paste `cloudflare/worker.js` over everything → Deploy. Your jobs are stored in the D1 database, separate from the code, so they aren't affected.
