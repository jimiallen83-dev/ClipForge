ClipForge — Local dev & run instructions

This repository contains the ClipForge API and worker scaffolding. Below are step-by-step instructions to run the project locally (Python venv) or with Docker, plus CI details.

Prerequisites
- Git (to clone/push)
- Either:
  - Python 3.11+ (Windows) or
  - Docker Desktop (recommended)

Quick paths
- Start with Docker (recommended): `docker compose up --build`
- Local Python: use the included `requirements.txt` and `smoke_test.py`

Run with Docker (recommended)

1. Install Docker Desktop and enable WSL2 if on Windows.
2. From project root run:

```powershell
docker compose up --build
```

The `web` service runs the FastAPI app on port 8000 and will attempt to run migrations on start.

Run locally with Python

1. Install Python 3.11+ from python.org.
2. Create a venv and activate it (PowerShell):

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

3. Run migrations then start the app (or use the smoke test):

```powershell
python scripts/run_migrations.py upgrade head

# run the API
uvicorn app:app --host 0.0.0.0 --port 8000

# or run the smoke test (migrations + health check)
python smoke_test.py
```

CI

A GitHub Actions workflow is included at `.github/workflows/ci.yml` which installs deps, runs migrations against an ephemeral sqlite DB, and runs the `smoke_test.py`.

Helpful Git commands

```powershell
git checkout -b feat/setup
git add .
git commit -m "Add README and CI smoke test"
git push --set-upstream origin feat/setup
```

If you want, I can open a branch and prepare a PR for you, or help run these steps interactively on your machine.
# ClipForge (minimal runner)

This workspace contains small modules for scoring clips, building a timeline, transcription, and FFmpeg rendering.

Quick demo:

```bash
python main.py
```

Windows setup (PowerShell):

1. Install Python if you don't have it: https://www.python.org/downloads/windows/
2. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1    # in PowerShell
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Helper script:

Run the included PowerShell helper which creates the venv and installs requirements (it will exit with a helpful message if `python` is not found):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_env.ps1
```

Notes:
- `ffmpeg` and Whisper model weights are not included. Install ffmpeg and ensure it's on `PATH` to use `ffmpeg_renderer.py`.
- If you plan to run Whisper transcription, install the package from `requirements.txt` and ensure model download completes before running large jobs.

YouTube OAuth setup:

1. Create an OAuth 2.0 Client ID in Google Cloud Console (type: Web application).
2. Add an authorized redirect URI matching `http://localhost:8000/youtube/oauth2callback` (adjust host if running elsewhere).
3. Download the JSON credentials and save as `client_secrets.json` in the project root.

Endpoints provided by the API app (`app.py`):

- `GET /youtube/authorize` — start OAuth flow (redirects to Google consent).
- `GET /youtube/oauth2callback` — OAuth redirect handler; exchanges code and fetches videos.
- `POST /youtube/scan` — scans authorized channels, stores videos, and creates a job per video.

SaaS notes
-------

- To enable payments with Stripe, set environment variable `STRIPE_API_KEY` and configure a webhook in your Stripe dashboard to point at `/payments/webhook`.
- The payment endpoints in `payments.py` are placeholders; implement real checkout/session creation and webhook signature validation for production.
- Authentication in this demo is a simple header-based approach (`X-User-Id`); replace with real auth (OAuth/JWT/session) for a SaaS product.
- Events are recorded in the `events` table; use `get_user_analytics` in `db.py` to fetch basic aggregates. I can add more analytics dashboards if needed.
- For quotas and usage limits, I can add middleware that checks events and enforces per-tier limits (free/creator/pro/agency).

Performance & fine-tuning workflow
- Export historical clips for model training:
	- Run `python scripts/export_history.py` to create `dataset/manifest.jsonl` and copy media into `dataset/media/`.
- Training scaffolding available in `training/`; adapt `training/train.py` to your model and data needs. A `training/Dockerfile` is included for reproducible environments.
- For faster exports and rendering, the app includes `ffmpeg_worker.py` and `ffmpeg_renderer.render_clips_parallel()` which will process clips in parallel and avoid re-rendering when outputs are already current.
- To scale further, run worker instances on separate machines and use a central job queue (Redis/RQ or Celery). I can add that integration next.

Docker quick start (recommended for demo/run anywhere)

1. Install Docker and Docker Compose on your machine.
2. Build and run the container:

```bash
docker compose build --pull
docker compose up
```

3. The API will be available at `http://localhost:8000`.

Notes:
- The container installs `ffmpeg` and the Python dependencies listed in `requirements.txt`.
- Before using OAuth or OpenAI/Stripe features, set `OPENAI_API_KEY` and `STRIPE_API_KEY` in your environment and rebuild or supply them to `docker compose`.
- The DB is SQLite stored inside the container workspace (project root) at `clipforge.db`. If you need a production DB, I can add Postgres + migrations.


