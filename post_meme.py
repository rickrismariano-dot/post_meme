"""
Posts a random meme to a Discord channel through a webhook.
No extra installs needed (standard library only).

Setup:
  1. In Discord: channel settings (gear icon) > Integrations > Webhooks > New Webhook.
     Pick #free-games-shits, then Copy Webhook URL.
  2. Keep that URL private. Anyone who has it can post in your channel.

Usage (Windows cmd):
  set WEBHOOK_URL=paste_webhook_url_here
  cls
  python post_meme.py              post one meme and exit
  python post_meme.py --every 60   keep running, post a meme every 60 minutes
  python post_meme.py --dry-run    fetch a meme and print it, post nothing

The window must stay open when using --every. To run it without a window open,
use Windows Task Scheduler and call "python post_meme.py" on a schedule.
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

# Subreddits to pull from. Edit freely.
SUBREDDITS = ["memes", "wholesomememes", "ProgrammerHumor", "dankmemes"]

MEME_API = "https://meme-api.com/gimme/{sub}"
UA = "friends-server-meme-poster/1.0"


def http_json(url, data=None):
    body = json.dumps(data).encode() if data is not None else None
    headers = {"User-Agent": UA}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def get_meme(tries=6):
    """Fetch a safe-for-work meme, retrying a few times."""
    for _ in range(tries):
        sub = random.choice(SUBREDDITS)
        try:
            m = http_json(MEME_API.format(sub=sub))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            print(f"  fetch failed from r/{sub}: {e}")
            continue
        if not m or m.get("nsfw") or m.get("spoiler") or not m.get("url"):
            continue
        if not m["url"].lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            continue
        return m
    return None


def post(webhook_url, meme):
    payload = {
        "username": "Meme Machine",
        "embeds": [
            {
                "title": meme.get("title", "meme")[:250],
                "url": meme.get("postLink"),
                "image": {"url": meme["url"]},
                "footer": {"text": f"r/{meme.get('subreddit', '?')}"},
            }
        ],
    }
    http_json(webhook_url, payload)


def once(webhook_url, dry):
    meme = get_meme()
    if not meme:
        print("No usable meme found this round, will try next time.")
        return
    print(f"Meme: {meme.get('title')}  ({meme['url']})")
    if dry:
        print("(dry run) not posted")
        return
    try:
        post(webhook_url, meme)
        print("Posted.")
    except urllib.error.HTTPError as e:
        print(f"Discord rejected the post: HTTP {e.code}. Check the webhook URL.")
    except urllib.error.URLError as e:
        print(f"Network error: {e}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--every", type=int, default=0, help="repeat every N minutes")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    url = os.environ.get("WEBHOOK_URL", "")
    if not args.dry_run and not url.startswith("https://discord.com/api/webhooks/"):
        sys.exit("Set WEBHOOK_URL to your full Discord webhook URL first.")

    once(url, args.dry_run)
    while args.every > 0:
        time.sleep(args.every * 60)
        once(url, args.dry_run)


if __name__ == "__main__":
    main()
