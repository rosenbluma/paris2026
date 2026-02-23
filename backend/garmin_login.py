#!/usr/bin/env python3
"""Manual Garmin login to save tokens."""
from garminconnect import Garmin
import getpass

print("Garmin Connect Login")
print("=" * 40)

email = input("Email: ")
password = getpass.getpass("Password: ")

try:
    print("\nConnecting to Garmin...")
    client = Garmin(email, password)
    client.login()

    # Save tokens
    client.garth.dump(".garmin_tokens")

    print(f"\nSuccess! Logged in as: {client.display_name}")
    print("Tokens saved. You can now use Sync in the app.")

except Exception as e:
    print(f"\nLogin failed: {e}")
    print("\nTips:")
    print("- Make sure your email/password are correct")
    print("- Log into https://connect.garmin.com in your browser first")
    print("- If you have 2FA, you may need to approve the login")
