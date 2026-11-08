"""Send a Telegram message, if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set.

Used by update_posts.sh for alerts. To test your settings, run this in the
container's terminal:   python /repo/scripts/notify.py "Test"
"""
import json
import os
import sys
import urllib.request

token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
chat = os.environ.get("TELEGRAM_CHAT_ID", "")
api = os.environ.get("TELEGRAM_API", "https://api.telegram.org")
text = " ".join(sys.argv[1:]) or "Test message from the newsfeed container"

if not token or not chat:
    print("Telegram isn't set up, so no message was sent.")
    sys.exit(0)

request = urllib.request.Request(
    f"{api}/bot{token}/sendMessage",
    data=json.dumps({"chat_id": chat, "text": text}).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    urllib.request.urlopen(request, timeout=20)
    print("Telegram message sent.")
except Exception as error:
    print(f"Could not send the Telegram message: {error}")
