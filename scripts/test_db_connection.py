"""One-off diagnostic: test a Postgres connection string in isolation from
Vercel, so a bad credential and a bad deploy don't get confused with each
other. Run this yourself in your own Terminal (not through Claude) so the
password is masked on screen (via getpass) and never appears anywhere in
the chat/session. Delete this file once the DATABASE_URL issue is
resolved -- it's a throwaway diagnostic, not part of the app.

Usage:
    python3 scripts/test_db_connection.py
"""
import getpass
import sys

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed. Run: pip3 install psycopg2-binary")
    sys.exit(1)

print("Paste your full DATABASE_URL connection string (input is hidden):")
database_url = getpass.getpass("> ").strip()

if not (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
    print(
        "\nFAILED -- input doesn't start with 'postgresql://' or 'postgres://'. "
        "That usually means the paste picked up an extra character or the wrong "
        "clipboard contents. Copy just the connection string itself and try again."
    )
    sys.exit(1)

try:
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print("\nSUCCESS -- connected. Server reports:")
    print(version[0])
    conn.close()
except Exception as exc:
    print("\nFAILED -- connection did not work.")
    print(f"{type(exc).__name__}: {exc}")
