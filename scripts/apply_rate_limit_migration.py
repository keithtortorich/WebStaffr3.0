#!/usr/bin/env python3
import os, sys
from pathlib import Path

def _find_database_url():
    env = os.environ.get("DATABASE_URL")
    if env:
        return env
    creds = Path(__file__).resolve().parent.parent / "CREDENTIALS.md"
    if creds.exists():
        for line in creds.read_text().splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1]
    sys.exit("DATABASE_URL not found")

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
