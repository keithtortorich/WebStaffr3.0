# WebStaffr 3.0

Production repository for the WebStaffr AI workforce platform. Backend
(Angel, tenant isolation, GHL/voice integration, executor engine) lives
here; customer site generation is delegated to Lovable.

## Local development

```
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
./.venv/bin/python -m pytest tests/
./.venv/bin/python scripts/health_check.py
```

`requirements-dev.txt` is test-only (currently just `pytest`) -- not needed to run the service itself.

Run the Angel service locally:

```
./.venv/bin/uvicorn webstaffr.workers.angel.router:app --reload
```

Optional environment variables (unset by default -- the service runs safely with no external calls when they're absent): `GROK_API_KEY`, `GHL_API_KEY`, `GHL_LOCATION_ID`, `RETELL_WEBHOOK_SECRET`, `WEBSTAFFR_DB_PATH`. See `CREDENTIALS.md` for what each does, how to get one, and current implementation status.

See `CLAUDE.md` for how this repository is governed and `PROJECT.md` for product vision and MVP scope.
