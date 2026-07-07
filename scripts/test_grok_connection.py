"""One-off diagnostic: test a GROK_API_KEY against xAI's real chat-completions
endpoint, in isolation from the rest of the app. Run this yourself in your own
Terminal (not through Claude) so the key is masked on screen (via getpass) and
never appears anywhere in the chat/session. Delete this file once
GrokVoiceBackend is confirmed working against your live xAI account -- it's a
throwaway diagnostic, not part of the app.

Verifies: the key authenticates, and the model name webstaffr/workers/angel/
voice.py actually requests ("grok-4.3") is accepted by your account. Makes
exactly one real API call and prints only success/failure -- never the key.

Usage:
    python3 scripts/test_grok_connection.py
"""
import getpass
import json
import sys
import urllib.error
import urllib.request

API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-4.3"  # must match webstaffr/workers/angel/voice.py

print("Paste your GROK_API_KEY (input is hidden):")
api_key = getpass.getpass("> ").strip()

if not api_key:
    print("No key entered. Aborting.")
    sys.exit(1)

payload = json.dumps(
    {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a connectivity test. Reply with one short sentence."},
            {"role": "user", "content": "Say hello in exactly five words."},
        ],
        "temperature": 0.7,
        "max_tokens": 30,
    }
).encode("utf-8")

req = urllib.request.Request(
    API_URL,
    data=payload,
    method="POST",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        reply = body["choices"][0]["message"]["content"].strip()
        model_used = body.get("model", "?")
        print("\nSUCCESS -- xAI accepted the key and the model name.")
        print(f"Model reported by API: {model_used}")
        print(f"Sample reply: {reply}")
except urllib.error.HTTPError as exc:
    detail = exc.read().decode("utf-8", errors="replace")
    print(f"\nFAILED -- HTTP {exc.code} from xAI.")
    if exc.code == 401:
        print("Looks like an auth problem -- check the key is correct and active.")
    elif exc.code == 404:
        print(f"Model '{MODEL}' may not be available on this account/tier.")
    print(f"Response body: {detail}")
except urllib.error.URLError as exc:
    print(f"\nFAILED -- could not reach xAI's API.")
    print(f"{type(exc).__name__}: {exc}")
except (KeyError, IndexError, ValueError) as exc:
    print(f"\nFAILED -- got a response but couldn't parse it as expected.")
    print(f"{type(exc).__name__}: {exc}")
