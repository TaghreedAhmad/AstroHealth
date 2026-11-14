<p align="center">
  <img src="apps/web/public/logo.png" alt="AstroHealth AI" width="96">
</p>

<h1 align="center">AstroHealth AI</h1>

<p align="center">
  A bone-loss digital twin for spaceflight crews — a research prototype built on NASA's open
  data for the NASA Space Apps Challenge 2026.
</p>

<p align="center">
  <a href="https://github.com/muhamedaldias/AstroHealth/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/muhamedaldias/AstroHealth/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.12+" src="https://img.shields.io/badge/Python-3.12%2B-306998?logo=python&logoColor=white">
  <img alt="React 19" src="https://img.shields.io/badge/React%2019%20%2B%20Vite-TypeScript%20strict-149eca">
  <img alt="Contract 0.1.4" src="https://img.shields.io/badge/OpenAPI%20contract-0.1.4-0d223a">
  &nbsp;&nbsp;<a href="https://astrohealth-ai.vercel.app"><strong>Live demo →</strong></a>
</p>

---

AstroHealth AI is a mission-control web platform for astronaut health. A contract-first FastAPI
backend runs a calibrated statistical bone-loss engine and serves six NASA OSDR gene-expression
studies, while a React 19 mission-control UI renders forecasts with uncertainty bands, crew
telemetry, a searchable gene table — in English and Arabic, with full RTL support.

> Research prototype, not a medical device. The crew and biomarkers are **simulated**, and every
> forecast ships with its warnings and a physician-review flag by design.

<p align="center">
  <img src="docs/submission/screenshots/40-dashboard.png" alt="AstroHealth AI mission-control dashboard" width="720">
  <br><em>Mission-control dashboard: radiation against the NASA 600 mSv limit, bone T-scores,
  DNA-damage index and cellular-repair efficiency.</em>
</p>

## What it does

- **Calibrated bone forecast** — pick a crew member, a mission scenario and countermeasures;
  get per-site BMD change at mission end with 95% uncertainty bands and a risk level per site.
- **Crew telemetry** — radiation dose against the NASA 600 mSv limit, T-scores, DNA-damage index
  and cellular-repair efficiency, per crew member.
- **NASA gene data** — six OSDR studies served offline, searchable, with a tested CSV export.
- **Bio-Rescue protocol** — countermeasure guidance tied to the OSDR studies that motivate it.
- **English and Arabic** — full UI translation with RTL layout, medical disclaimers included.
- **Degrades honestly** — when the API is down the UI falls back to a static crew seed and shows
  an offline chip instead of pretending everything is fine.

## How the forecast works

The engine is a closed-form statistical model — no black box. Four bone sites lose density at
per-site monthly rates anchored to published values:

| Bone site | Baseline loss |
|---|---|
| Lumbar spine | −1.15 %/month |
| Femoral neck | −1.25 %/month |
| Total hip | −1.35 %/month |
| Distal tibia | −0.95 %/month |

Countermeasures scale the loss: resistive exercise to 62% of baseline, flywheel to 82%,
vitamin D + calcium to 95%, bisphosphonate to 48%. A CTX-based resorption ratio personalizes
the rate per crew member, and uncertainty grows with √days. The multipliers and uncertainty
are literature-grounded but remain illustrative — the honest caveat ships with every forecast.

Sources: NASA-STD-3001, NASA's space-flight health fundamentals, ESA's "Preventing Bone Loss
in Space", and Axpe et al. 2020 (npj Microgravity). Full detail in
[docs/SCIENCE_NOTES.md](docs/SCIENCE_NOTES.md).

## Quickstart

Requirements: [uv](https://docs.astral.sh/uv/), Node 22+, GNU make (on Windows: Git Bash or WSL).

```bash
git clone https://github.com/muhamedaldias/AstroHealth.git
cd AstroHealth
make setup        # Python workspace (uv) + web deps (npm)
make dev-api      # API + docs at http://localhost:8000
make dev-web      # UI at http://localhost:5173
```

One container instead:

```bash
make docker-up    # UI + API together at http://localhost:8000
```

## Architecture

Contract-first monorepo: one OpenAPI file is the single source of truth, Python and TypeScript
types are generated from it, and CI fails on drift between any of them.

| Piece | What it is |
|---|---|
| `apps/web` | React 19 + Vite 8 + Tailwind v4 + TanStack Query 5 — types come from the contract; hand-written UI types are forbidden |
| `apps/api` | FastAPI — 12 routes under `/api/v1`, one `Error` shape for every non-2xx, unknown request fields rejected |
| `packages/twin_core` | Registry-selected engines (stub / calibrated) — deterministic, and every registered engine is contract-checked in tests |
| `contracts/` | OpenAPI 0.1.4 + golden fixtures + changelog discipline |

The full decisions log lives in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## API

| Method | Path | Returns |
|---|---|---|
| GET | `/api/v1/telemetry/crew` | simulated roster with engine-computed bone-loss risk |
| POST | `/api/v1/forecast` | per-site forecast with 95% bands, risk levels, warnings |
| GET | `/api/v1/osdr/studies` | six OSDR studies with a sync status |
| GET | `/api/v1/scenarios`, `/countermeasures`, `/crew` | catalogs for the forecast form |

## Data sources

NASA OSDR accessions served offline as JSON bundles:
`OSD-48`, `OSD-102`, `OSD-137`, `OSD-194`, `OSD-245`, `OSD-714` — [osdr.nasa.gov](https://osdr.nasa.gov/osdr/).

## Testing

```bash
make check        # spec-lint + gen-check + lint + typecheck + pytest + web tests + build
```

56 backend tests (contract parity, engine contract, validation edges) plus a frontend vitest suite.

## Deployment

- **Docker** — one container builds the web app, then serves UI + API on a single port.
- **Vercel** — static build + serverless `/api`, engine pinned to `calibrated`, in-memory SQLite.
  Running live at [astrohealth-ai.vercel.app](https://astrohealth-ai.vercel.app).

## Documentation

| File | What's inside |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | the decisions log — why each stack choice, and what was rejected |
| [docs/SCIENCE_NOTES.md](docs/SCIENCE_NOTES.md) | calibration constants, their sources and their limits |
| [docs/AI_USAGE.md](docs/AI_USAGE.md) | how AI tooling was used — and what was not AI-generated |
| [contracts/README.md](contracts/README.md) | how a contract change works |
| [CONTRIBUTING.md](CONTRIBUTING.md) | branch, generate, check, merge |

## Limitations

- Crew and biomarkers are simulated (`simulated_mission_telemetry`) — no real astronaut data.
- The engine is literature-grounded but illustrative, and every forecast requires physician
  review by design.
- On Vercel the SQLite database is in-memory — measurement writes don't survive cold starts.
- The offline fallback shows a static seed — don't assume on-screen data came from the API.

## Team

- [muhamed aldias](https://github.com/muhamedaldias)
- [mram alharbi](https://github.com/Maram1ll)
- manal
- [TaghreedAhmad](https://github.com/TaghreedAhmad)

## License

© 2026 the AstroHealth team. A source license hasn't been selected yet — reach out before reuse.
