# ResumeIQ

Resume screening dashboard: PDF resumes → skills → job-fit scores.

## Live dashboard (GitHub Pages)
`index.html` redirects to `frontend/`. With no backend configured it shows the
snapshot in `frontend/data/dashboard.json`. Regenerate it with
`python export_static.py` after changing resumes or jobs, then commit.

## Backend on Render (optional, live MySQL data)
Render has no managed MySQL, so use an external MySQL host (Aiven, TiDB Cloud, Railway…).
1. Load `Database/schema.sql` into that database; run `parser.py` and `job_matcher.py` against it.
2. Create a Render Web Service from this repo (`render.yaml` is picked up).
   Set `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.
3. Put the Render URL in `frontend/config.js` (`window.RESUMEIQ_API_BASE`) and commit.
   The dashboard then shows live data and falls back to the snapshot if the API is down.

## Local
`pip install -r requirements.txt`, set `MYSQL_PASSWORD`, `python backend/app.py`, open `frontend/index.html`.
