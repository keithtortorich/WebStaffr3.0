"""One-off diagnostic: test a GHL_API_KEY + GHL_LOCATION_ID pair against a
real GoHighLevel account, in isolation from the rest of the app. Run this
yourself in your own Terminal (not through Claude) so the key is masked on
screen (via getpass) and never appears anywhere in the chat/session. Delete
this file once GoHighLevelClient is confirmed working against your live GHL
account -- it's a throwaway diagnostic, not part of the app.

Verifies: the Private Integration Token authenticates and the location ID is
valid, using GET /calendars/ (list calendars in a location) -- a read-only
call with no side effects, so it's safe to run repeatedly. Does NOT create,
update, or cancel anything.

Usage:
    python3 scripts/test_ghl_connection.py
"""
import getpass
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"  # must match webstaffr/workers/angel/ghl.py

print("Paste your GHL_API_KEY / Private Integration Token (input is hidden):")
api_key = getpass.getpass("> ").strip()

if not api_key:
    print("No key entered. Aborting.")
    sys.exit(1)

location_id = input("Enter your GHL_LOCATION_ID (not hidden -- not a secret on its own): ").strip()

if not location_id:
    print("No location ID entered. Aborting.")
    sys.exit(1)

query = urllib.parse.urlencode({"locationId": location_id})
url = f"{BASE_URL}/calendars/?{query}"

req = urllib.request.Request(
    url,
    method="GET",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Version": API_VERSION,
    },
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        calendars = body.get("calendars", body)
        count = len(calendars) if isinstance(calendars, list) else "?"
        print("\nSUCCESS -- GHL accepted the token and location ID.")
        print(f"Calendars found in this location: {count}")
except urllib.error.HTTPError as exc:
    detail = exc.read().decode("utf-8", errors="replace")
    print(f"\nFAILED -- HTTP {exc.code} from GHL.")
    if exc.code == 401:
        print("Looks like an auth problem -- check the token is correct, active, and scoped to this location.")
    elif exc.code == 400:
        print("Possibly a bad/missing locationId -- double check GHL_LOCATION_ID.")
    print(f"Response body: {detail}")
except urllib.error.URLError as exc:
    print(f"\nFAILED -- could not reach GHL's API.")
    print(f"{type(exc).__name__}: {exc}")
except (KeyError, ValueError) as exc:
    print(f"\nFAILED -- got a response but couldn't parse it as expected.")
    print(f"{type(exc).__name__}: {exc}")
