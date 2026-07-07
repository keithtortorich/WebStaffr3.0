"""One-off helper: takes the RAW database password (as shown by Supabase's
"Reset database password" reveal, not the connection-string modal) and
builds a correctly URL-encoded DATABASE_URL. Manually pasting a raw
password into a connection string breaks silently if it contains
characters like @ / + % # -- this removes that whole class of error.

Run this yourself, right after resetting the password on Supabase, so the
password is as fresh as possible:

    python3 scripts/build_database_url.py

It prints the finished connection string. Test it immediately with
test_db_connection.py before touching Vercel. Delete both scripts once
this is resolved -- they're throwaway diagnostics.
"""
import getpass
from urllib.parse import quote

PROJECT_REF = "ntbnenymyqiautaqhyhe"
HOST = "aws-1-ap-south-1.pooler.supabase.com"
PORT = "6543"

print("Paste the RAW password from Supabase's password-reset reveal (hidden input):")
raw_password = getpass.getpass("> ")

encoded_password = quote(raw_password, safe="")
url = f"postgresql://postgres.{PROJECT_REF}:{encoded_password}@{HOST}:{PORT}/postgres"

print("\nBuilt connection string (safe to copy -- password is percent-encoded):")
print(url)
