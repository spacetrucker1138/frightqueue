#!/usr/bin/env python3
"""Refresh data/nextfest.json: horror-tagged demos on Steam for upcoming games (live Steam search + appdetails)."""
import json, re, time, html, urllib.request
from datetime import datetime, timezone
from pathlib import Path
R = Path(__file__).resolve().parent.parent
OUT = R/"data/nextfest.json"
UA = {"User-Agent": "Mozilla/5.0 FrightQueue/1.0 (+https://frightqueue.thejurn.com)"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: return json.load(r)
def main(limit=36):
    # tag 1667 = Horror, category1=10 = Demo, upcoming titles
    items = get("https://store.steampowered.com/search/results/?tags=1667&category1=10&filter=comingsoon&json=1&count=80&cc=us&l=english")["items"]
    out, seen = [], set()
    for it in items:
        if len(out) >= limit: break
        m = re.search(r"/apps/(\d+)/", it.get("logo", ""))
        if not m: continue
        try:
            d = get(f"https://store.steampowered.com/api/appdetails?appids={m.group(1)}&cc=us&l=english")[m.group(1)]
            if not d.get("success"): continue
            demo = d["data"]; full = (demo.get("fullgame") or {}).get("appid")
            if not full or full in seen: continue
            g = get(f"https://store.steampowered.com/api/appdetails?appids={full}&cc=us&l=english")[str(full)]
            if not g.get("success"): continue
            g = g["data"]; seen.add(full)
            if not g.get("release_date", {}).get("coming_soon"): continue
            out.append({"appid": int(full), "demo_appid": int(m.group(1)), "title": g["name"],
                "developer": ", ".join(g.get("developers") or ["Unknown"]),
                "blurb": html.unescape(re.sub("<[^>]+>", "", g.get("short_description", "")))[:240],
                "image": g.get("header_image", ""), "release_date": g["release_date"].get("date", "TBA"),
                "link": f"https://store.steampowered.com/app/{full}/", "demo_link": f"https://store.steampowered.com/app/{m.group(1)}/",
                "demo_available": True})
        except Exception as ex:
            print("skip", m.group(1), ex)
        time.sleep(1.2)
    if len(out) < 5:  # keep previous data if Steam hiccups
        print("too few results, keeping existing file"); return
    OUT.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(), "demos": out}, indent=1, ensure_ascii=False))
    print(f"wrote {len(out)} demos")
if __name__ == "__main__": main()
