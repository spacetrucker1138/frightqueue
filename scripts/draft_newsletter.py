#!/usr/bin/env python3
"""Build 'The Weekly Fright' from data/games.json and save it as a DRAFT in Buttondown.

Never sends: always posts status="draft". Needs env BUTTONDOWN_API_KEY.
Usage: python3 scripts/draft_newsletter.py [--dry-run]   (dry run prints the markdown only)
"""
import json, os, sys, urllib.request, urllib.error
from datetime import date, datetime, timedelta
from pathlib import Path

R = Path(__file__).resolve().parent.parent
SITE = "https://frightqueue.thejurn.com"
API = "https://api.buttondown.com/v1/emails"

def iso(d):
    try: return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception: return None

def line(g, extra=""):
    plats = ", ".join(g["platforms"])
    return (f'- **[{g["title"]}]({SITE}/games/{g["id"]}.html)** by {g["developer"]} ({plats}){extra}  \n'
            f'  {g["blurb"]} [{"Play the demo" if g["status"]=="demo" else "View"} on {g["store"]}]({g["link"]})')

def build(today=None):
    today = today or date.today()
    games = json.loads((R/"data/games.json").read_text())["games"]
    arcade = json.loads((R/"data/arcade.json").read_text())
    demos = sorted([g for g in games if g["status"] == "demo"],
                   key=lambda g: iso(g["release_date"]) or date.max, reverse=True)[:5]
    new = sorted([g for g in games if g["status"] == "released" and iso(g["release_date"])
                  and today - timedelta(days=14) <= iso(g["release_date"]) <= today],
                 key=lambda g: g["release_date"], reverse=True)[:5]
    soon = sorted([g for g in games if g["status"] == "upcoming" and iso(g["release_date"])
                   and today <= iso(g["release_date"]) <= today + timedelta(days=21)],
                  key=lambda g: g["release_date"])[:5]
    pick = arcade[today.isocalendar()[1] % len(arcade)]
    a_url = pick.get("url") or "https://thejurn.com/" + pick["path"]
    subject = f"The Weekly Fright: {len(demos)} free demos to play this weekend ({today:%b %-d})"
    parts = [
        "Fresh horror crawled out of the indie graveyard this week. Here's what to play, what just dropped, and what's lurking on the horizon.",
        "## 🎃 5 demos to play this weekend", "\n".join(line(g) for g in demos) or "_Quiet week for demos._",
        "## 🩸 New releases", "\n".join(line(g, f' · out {g["release_date"]}') for g in new) or "_Nothing new clawed out this week._",
        "## 🕯️ Coming soon", "\n".join(line(g, f' · {g["release_date"]}') for g in soon) or "_The release calendar is suspiciously quiet._",
        "## 💀 JURN Arcade pick",
        f'**[{pick["title"]}]({a_url})** ({pick["genre"]}). Free in your browser, straight from the Graveyard Dimension. '
        f'[Play the whole JURN Arcade](https://thejurn.com/games.html) or catch the [24/7 stream](https://www.youtube.com/@Spacetrucker138).',
        "## 📼 Sponsor",
        "<!-- SPONSOR SLOT: replace with this week's sponsor (name, one line, link) or delete this section before sending. -->\n"
        "_[SPONSOR SLOT: your indie horror game here. Reply to this email to get featured.]_",
        "---",
        f"Browse the full queue at [{SITE.replace('https://','')}]({SITE}) · Making a horror game? [Submit it]({SITE}/submit.html).  \n"
        "Store links may become affiliate links later; we'll always say so.",
    ]
    return subject, "\n\n".join(parts)

def main():
    subject, body = build()
    if "--dry-run" in sys.argv:
        print(subject); print(body); return
    key = os.environ.get("BUTTONDOWN_API_KEY")
    if not key: sys.exit("BUTTONDOWN_API_KEY not set")
    payload = json.dumps({"subject": subject, "body": body, "status": "draft"}).encode()
    req = urllib.request.Request(API, data=payload, method="POST",
                                 headers={"Authorization": f"Token {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Buttondown error {e.code}: {e.read().decode()[:500]}")
    assert d.get("status") == "draft", f"unexpected status {d.get('status')}"
    print(f'Draft created: {d.get("id")} | {d.get("subject")} | status={d.get("status")}')
    print(f'Edit: https://buttondown.com/emails/{d.get("id")}')

if __name__ == "__main__":
    main()
