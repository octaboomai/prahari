# Prahari — breach compliance automation

This is the piece of the SME cyber-defense product that's actually worth building
from scratch: the layer that turns one detected incident into two correctly-timed,
correctly-formatted regulatory filings — CERT-In (6-hour clock) and the DPDP Board
(72-hour clock for the detailed report, "without delay" for the initial notice).

Everything else in the wider product plan — dark-web/credential monitoring,
external attack-surface scanning — is deliberately **not** built here. Those are
license-not-build: wrap an existing vendor API (e.g. Flare's partner program for
credential/dark-web monitoring, Shodan/Censys for exposure scanning) rather than
re-implementing years of threat-intel infrastructure. This repo is the one
component nobody else is selling to the Indian SME segment: the dual-regulator
compliance workflow itself.

## What's actually built

- **Incident intake** modeled on CERT-In's own published Incident Reporting Form
  (`app/reference_data.py` mirrors the real Annexure I category list), plus the
  extra fields DPDP's breach-notification content requires (data categories,
  estimated individuals affected, likely consequences, mitigation measures).
- **The dual-clock engine** (`app/compliance.py`) — computes the CERT-In 6-hour
  deadline and the DPDP 72-hour detailed-report deadline from a single
  detection timestamp, plus urgency banding (ok / warning / critical / breached)
  scaled to each clock's own window so a 6-hour and a 72-hour clock feel equally
  urgent at equivalent points in their countdown.
- **Live dashboard** with the twin countdown clocks ticking client-side
  (`static/clock.js`) — no polling, updates every second, color-shifts as the
  deadline approaches.
- **Report generation** (`app/reports.py`) — renders both a CERT-In report and a
  DPDP Board report (initial + detailed tiers) from the same incident record,
  each viewable as HTML or downloadable as plain text. Unknown fields render as
  "Under investigation" rather than blank, matching CERT-In's own guidance to
  submit with known fields filled and gaps explicitly marked.
- **Mark-as-reported audit trail** — each clock has its own "mark reported"
  action that timestamps the actual filing, so `on_time` vs `late` is provable
  later, not just assumed.
- **Retention tracking** (`/log-sources`) — tracks how long each log source has
  been continuously monitored against a unified 365-day window (CERT-In wants
  180 days, DPDP wants 365 — building for 365 satisfies both).

## What's stubbed / explicitly out of scope here

- **Dark-web / credential-leak monitoring** — not built. Integrate via an
  existing vendor's API (Flare's TEM platform has a white-label reseller tier
  aimed at exactly this price point) rather than building crawler
  infrastructure.
- **External attack-surface scanning** — not built. Wrap Shodan or Censys'
  API for the client's known domains/IPs rather than writing a scanner.
- **Multi-tenancy** — the schema is single-org (`org_profile` is a single-row
  table). Adding real customers means adding an `org_id` column to every table
  and a real login per org; the schema is deliberately flat now so that
  migration is additive, not a rewrite.
- **Real user accounts** — there's HTTP Basic Auth (see below) gating the
  whole app behind one shared username/password, which is enough to keep a
  random link-clicker out. It is not a real multi-user permission system.

## Auth

Every route is gated behind HTTP Basic Auth. Set these as environment
variables before running anywhere other than your own machine:

```
PRAHARI_USER=yourname
PRAHARI_PASSWORD=something-real-not-changeme
```

If left unset, it falls back to `admin` / `changeme` locally and prints a
warning to the console on startup so you don't forget to set real ones before
deploying.

## Running it locally

```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
export PRAHARI_USER=yourname            # Windows (PowerShell): $env:PRAHARI_USER="yourname"
export PRAHARI_PASSWORD=yourpassword    # Windows (PowerShell): $env:PRAHARI_PASSWORD="yourpassword"
uvicorn app.main:app --reload --port 8000
```

Then open `http://localhost:8000` and log in with the credentials you set.
A default org profile is seeded automatically on first run — fill in real
details at `/settings` before using this for a real incident.

## Deploying it so you can share a live link

Recommended: **Railway** (railway.com). It's the least fiddly option that
actually keeps your SQLite data between requests and doesn't cold-start
mid-demo — both real problems on most free tiers in 2026.

1. Push this folder to a new GitHub repo.
2. In Railway: New Project → Deploy from GitHub repo → pick the repo.
   Railway reads `Procfile` and `requirements.txt` automatically; no
   Dockerfile needed.
3. In the service's **Variables** tab, add:
   - `PRAHARI_USER` = your username
   - `PRAHARI_PASSWORD` = a real password
   - `PRAHARI_DB_PATH` = `/data/prahari.db`
4. In the service's **Volumes** tab, attach a volume mounted at `/data` —
   this is what makes incident data survive restarts and redeploys instead
   of vanishing.
5. Railway gives you a live `*.up.railway.app` URL immediately. A custom
   domain can be attached later under Settings → Domains for free (you'd
   just need to own the domain itself, e.g. from GoDaddy or Namecheap).

Expect roughly $5/month on Railway's Hobby plan once your one-time trial
credit runs out — worth it for a link that actually works when you click it
on a customer call, rather than a cold-start blank screen or a demo where
last week's test incidents have silently disappeared.



## Project layout

```
Procfile               start command for Railway/Render/Heroku-style hosts
app/
  main.py            FastAPI routes
  auth.py             HTTP Basic Auth gate
  db.py               SQLite access (schema.sql defines the tables)
  compliance.py        the dual-clock engine -- this is the core IP
  reports.py            builds CERT-In / DPDP report content from an incident
  reference_data.py    CERT-In's official incident category list
templates/            Jinja2 templates (server-rendered, no JS framework)
static/                style.css + clock.js (the live countdown ticking)
schema.sql             SQLite schema, Postgres-portable if this needs to scale
```

## Suggested next steps for whoever picks this up

1. Add real per-org login (the `org_id` migration) once there's more than one
   customer — the shared Basic Auth password is fine for a single org demo,
   not for multiple paying customers.
2. Wire in Flare's API for the dark-web layer and Shodan/Censys for exposure
   scanning as separate modules that write into a shared `alerts` table, which
   can itself become "incidents" here with one click.
3. Get the actual CERT-In and DPDP Board submission channels (email/portal)
   wired in as a real "submit" action instead of "generate for manual filing" —
   that's the natural v2 once the report content itself has been validated
   against a few real filings.
