#!/usr/bin/env python3
"""Refresh data/games.json from public Steam + itch.io sources (stdlib only).

Sources:
  * Steam store search JSON (Horror tag 1667): upcoming, new releases, demos
  * Steam appdetails API for each app (developer, date, platforms, blurb, image)
  * itch.io public RSS feeds: tag-horror featured / has-demo / free
Usage: python3 scripts/refresh_games.py [--per-source N]
Manual entries in data/games.json with "pinned": true are kept.
"""
import json, re, sys, time, html, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "games.json"
UA = {"User-Agent": "FrightQueueBot/1.0 (+https://frightqueue.thejurn.com)"}
N = int(sys.argv[sys.argv.index("--per-source") + 1]) if "--per-source" in sys.argv else 12
# Steam tag ids: Horror=1667, Psychological Horror=1721, Survival Horror=3978; Indie=492
STEAM_QUERIES = [
    ("upcoming", "tags=1667,492&category1=998&filter=comingsoon"),
    ("released", "tags=1667,492&category1=998&filter=popularnew"),
    ("demo", "tags=1667,492&category1=10"),  # category1=10 -> demos
]
ITCH_FEEDS = [
    ("demo", "https://itch.io/games/has-demo/tag-horror.xml"),
    ("released", "https://itch.io/games/featured/tag-horror.xml"),
    ("released", "https://itch.io/games/free/tag-horror.xml"),
]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]

def clean(s, n=180):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"

def parse_date(s):
    for fmt in ("%b %d, %Y", "%d %b, %Y", "%B %d, %Y", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(s.strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return s.strip() or "TBA"

def steam_app(appid, status):
    d = json.loads(get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=english"))
    d = d.get(str(appid), {})
    if not d.get("success"):
        return None
    a = d["data"]
    if a.get("type") == "demo":  # resolve demo to its full game
        full = a.get("fullgame", {}).get("appid")
        if full:
            g = steam_app(full, "demo")
            if g: g["demo_link"] = f"https://store.steampowered.com/app/{appid}/"
            return g
        return None
    if a.get("type") != "game":
        return None
    plats = [p.replace("windows", "Windows").replace("mac", "Mac").replace("linux", "Linux")
             for p, ok in a.get("platforms", {}).items() if ok]
    rd = a.get("release_date", {})
    if status != "demo":
        status = "upcoming" if rd.get("coming_soon") else "released"
    tags = [g["description"] for g in a.get("genres", [])][:4]
    price = a.get("price_overview", {}).get("final_formatted") or ("Free" if a.get("is_free") else None)
    return {
        "id": slug(a["name"]), "title": a["name"],
        "developer": ", ".join(a.get("developers", [])) or "Unknown",
        "status": status, "release_date": parse_date(rd.get("date", "")),
        "platforms": plats, "store": "Steam",
        "link": f"https://store.steampowered.com/app/{appid}/",
        "blurb": clean(a.get("short_description")), "tags": ["Horror"] + [t for t in tags if t != "Horror"],
        "image": a.get("header_image", ""), "free": bool(a.get("is_free")), "price": price,
        "source": "steam", "steam_appid": int(appid),
    }

def steam_games():
    out = []
    for status, q in STEAM_QUERIES:
        data = json.loads(get(f"https://store.steampowered.com/search/results/?{q}&json=1&count={N*2}&cc=us&l=english"))
        n = 0
        for it in data.get("items", []):
            m = re.search(r"/apps/(\d+)/", it.get("logo", ""))
            if not m: continue
            try:
                g = steam_app(m.group(1), status)
            except Exception as e:
                print("steam err", m.group(1), e, file=sys.stderr); g = None
            time.sleep(1.2)  # be polite with appdetails rate limits
            if g:
                out.append(g); n += 1
            if n >= N: break
    return out

def itch_games():
    out = []
    for status, url in ITCH_FEEDS:
        root = ET.fromstring(get(url))
        for i, it in enumerate(root.iter("item")):
            if i >= N: break
            t = lambda k: (it.findtext(k) or "")
            link = t("link")
            plats = [p.tag.replace("html", "Browser").title().replace("Osx", "Mac")
                     for p in (it.find("platforms") if it.find("platforms") is not None else []) if p.text == "yes"]
            title = html.unescape(t("plainTitle"))
            dev = re.match(r"https://([^.]+)\.itch\.io", link)
            price = t("price")
            out.append({
                "id": slug(title), "title": title, "developer": dev.group(1) if dev else "Unknown",
                "status": status, "release_date": parse_date(t("createDate")),
                "platforms": plats or ["Windows"], "store": "itch.io", "link": link,
                "blurb": clean(t("description")) or "Indie horror on itch.io.",
                "tags": ["Horror"], "image": t("imageurl"), "free": price in ("$0.00", ""),
                "price": "Free" if price in ("$0.00", "") else price, "source": "itch",
            })
    return out

# Curation: titles that slip through tag search but aren't indie horror / are off-brand.
EXCLUDE = {"warhammer-40-000-boltgun-2","the-isle","outer-wilds","stray","the-binding-of-isaac-rebirth",
           "i-can-smell-you-from-here","the-freak-circus","repurpose","say-that-you-love-me","plaguebound"}

def main():
    old = json.loads(OUT.read_text()) if OUT.exists() else {"games": []}
    pinned = [g for g in old.get("games", []) if g.get("pinned")]
    fresh = []
    for fn in (steam_games, itch_games):
        try: fresh += fn()
        except Exception as e: print(fn.__name__, "failed:", e, file=sys.stderr)
    seen, games = set(), []
    for g in pinned + fresh:
        if g["id"] in seen or g["id"] in EXCLUDE: continue
        seen.add(g["id"]); games.append(g)
    OUT.write_text(json.dumps({"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                               "games": games}, indent=2, ensure_ascii=False))
    print(f"wrote {len(games)} games -> {OUT}")

if __name__ == "__main__":
    main()
