#!/usr/bin/env python3
"""Helper script to obtain a Dropbox OAuth Refresh Token."""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("DROPBOX_APP_KEY", "khmtgqjbprv89c8").strip()
APP_SECRET = os.getenv("DROPBOX_APP_SECRET", "jvlv8obtlub6pza").strip()

if not APP_KEY or not APP_SECRET:
    print("Error: DROPBOX_APP_KEY and DROPBOX_APP_SECRET must be set.")
    sys.exit(1)

auth_url = f"https://www.dropbox.com/oauth2/authorize?client_id={APP_KEY}&token_access_type=offline&response_type=code"

print("\n" + "=" * 70)
print("DROPBOX REFRESH TOKEN GENERATOR")
print("=" * 70)
print("\n1. Open this URL in your browser:\n")
print(f"   {auth_url}\n")
print("2. Click 'Continue' and 'Allow'.")
print("3. Copy the authorization code shown on screen.\n")

if len(sys.argv) > 1:
    code = sys.argv[1].strip()
else:
    code = input("Paste the authorization code here: ").strip()

if not code:
    print("No code provided. Exiting.")
    sys.exit(1)

token_url = "https://api.dropbox.com/oauth2/token"
data = {
    "code": code,
    "grant_type": "authorization_code",
}

try:
    response = requests.post(token_url, data=data, auth=(APP_KEY, APP_SECRET))
    res_data = response.json()

    if "refresh_token" in res_data:
        refresh_token = res_data["refresh_token"]
        print("\n" + "=" * 70)
        print("SUCCESS! Your permanent refresh token is:\n")
        print(f"DROPBOX_REFRESH_TOKEN={refresh_token}\n")
        print("=" * 70)

        # Update .env
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            new_lines = []
            found = False
            for line in lines:
                if line.startswith("DROPBOX_REFRESH_TOKEN="):
                    new_lines.append(f"DROPBOX_REFRESH_TOKEN={refresh_token}")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"DROPBOX_REFRESH_TOKEN={refresh_token}")

            with open(env_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
            print("-> Successfully saved DROPBOX_REFRESH_TOKEN to .env!")
    else:
        print("\nError from Dropbox API:")
        print(res_data)
except Exception as e:
    print(f"Request failed: {e}")
