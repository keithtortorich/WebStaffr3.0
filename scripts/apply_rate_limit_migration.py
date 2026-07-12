#!/usr/bin/env python3
import os, sys
from pathlib import Path

def _find_database_url():
    env = os.environ.get("DATABASE_URL")
    if env:
        return env
    sys.exit(
        "DATABASE_URL not set. Export it in your own shell before running this "
        "script -- never paste it into a committed file (see CREDENTIALS.md's "
        "Security note: never commit a credential value, including here)."
    )

def main():
    database_url = _find_database_url()
    sql_path = (
        Path(__file__).resolve().parent.parent
        / "webstaffr" / "migrations" / "postgres_manual" / "0005_rate_limit_counters.sql"
    )
    sql = sql_path.read_text()
    import psycopg2
    conn = psycopg2.connect(database_url)
    try:
        conn.cursor().execute(sql)
        conn.commit()
        print("OK: rate_limit_counters applied.")
    except Exception as exc:
        conn.rollback()
        sys.exit(f"ERROR: {exc}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
