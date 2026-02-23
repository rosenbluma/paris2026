#!/usr/bin/env python3
"""
Export Garmin tokens to base64 for Railway environment variable.
Run locally after authenticating with Garmin.

Usage:
    python scripts/export_garmin_tokens.py

Output:
    Prints base64-encoded token data to paste into GARMIN_TOKEN_DATA env var
"""
import os
import sys
import json
import base64

# Token directory path
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", ".garmin_tokens")


def main():
    """Export Garmin tokens to base64."""
    print("=== Export Garmin Tokens ===\n")

    if not os.path.exists(TOKEN_PATH):
        print(f"ERROR: Token directory not found: {TOKEN_PATH}")
        print("Run 'python backend/garmin_login.py' first to authenticate with Garmin.")
        sys.exit(1)

    # Read all token files
    tokens = {}
    for filename in os.listdir(TOKEN_PATH):
        filepath = os.path.join(TOKEN_PATH, filename)
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                try:
                    tokens[filename] = json.load(f)
                except json.JSONDecodeError:
                    # Read as raw text
                    f.seek(0)
                    tokens[filename] = f.read()

    if not tokens:
        print("ERROR: No token files found")
        sys.exit(1)

    print(f"Found {len(tokens)} token file(s): {list(tokens.keys())}")

    # Encode to base64
    token_json = json.dumps(tokens)
    token_b64 = base64.b64encode(token_json.encode("utf-8")).decode("utf-8")

    print(f"\n{'=' * 60}")
    print("GARMIN_TOKEN_DATA value (copy this entire string):")
    print("=" * 60)
    print(token_b64)
    print("=" * 60)
    print(f"\nLength: {len(token_b64)} characters")
    print("\nPaste this value into Railway's GARMIN_TOKEN_DATA environment variable.")


if __name__ == "__main__":
    main()
