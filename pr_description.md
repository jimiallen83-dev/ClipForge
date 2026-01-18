PR title: chore(ci): add CI + smoke tests and Docker entrypoint improvements

Summary
- Adds a GitHub Actions CI workflow that installs dependencies, runs Alembic migrations, and executes a smoke test (`smoke_test.py`).
- Adds `requirements.txt`, `smoke_test.py`, `README.md`, and PowerShell helper scripts in `scripts/`.
- Improves `docker-entrypoint.sh` to run migrations on container start and to support worker mode.
- Adds an Alembic initial migration at `alembic/versions/0001_initial.py` to create the DB schema.

Files of interest
- `docker-compose.yml`
- `docker-entrypoint.sh`
- `alembic/versions/0001_initial.py`
- `requirements.txt`
- `smoke_test.py`
- `README.md`
- `.github/workflows/ci.yml`

What to test
- Confirm CI passes on GitHub Actions (workflow `CI`).
- Verify `docker compose up --build` runs and exposes `/health` on port 8000.
- Run the smoke test locally inside a Python venv:
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`
  - `pip install -r requirements.txt`
  - `python smoke_test.py`
- Confirm `clipforge.db` is created after migrations run (default sqlite).

Checklist (for reviewers)
- [ ] CI passes on GitHub Actions
- [ ] Migrations run successfully (sqlite in CI)
- [ ] `docker compose up --build` starts services and `/health` returns status ok
- [ ] README instructions are clear and accurate
- [ ] No secrets committed; `.env` usage documented

Notes / TODOs remaining after this PR
- Harden Stripe webhook verification and signature checking.
- Replace heuristic emotion classifier with a trained model + inference API.
- Implement batch export worker and progress endpoints.
- Add further unit/integration tests for core routers and workers.

How to push (run locally)
```
git checkout -b feat/ci-setup
git add pr_description.md
git commit -m "chore(ci): add PR description"
git push --set-upstream origin feat/ci-setup
```

If you'd like, I can also generate the PR body file elsewhere or open a draft PR command for you to run locally.
