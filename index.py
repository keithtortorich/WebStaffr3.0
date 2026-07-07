"""Vercel entrypoint -- re-exports the real FastAPI app instance.

Vercel's Python builder auto-detects a supported root-level file
(index.py/app.py/main.py/server.py) exposing an `app` FastAPI instance.
The actual app is constructed in webstaffr/workers/angel/router.py; this
file just points Vercel at it rather than duplicating app construction
here, or requiring a pyproject.toml [project] table that would duplicate
requirements.txt as a second dependency source (see CLAUDE.md session
addendum, 2026-07-07 -- pyproject.toml with only [tool.vercel].entrypoint
was tried first and failed the build: uv requires a full [project] table
once pyproject.toml exists at all).
"""

from webstaffr.workers.angel.router import app  # noqa: F401
