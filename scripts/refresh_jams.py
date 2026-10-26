#!/usr/bin/env python3
"""Refresh data/jams.json: current + upcoming horror game jams from itch.io (live listing pages + each jam's page)."""
import json, re, time, html, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
R = Path(__file__).resolve().parent.parent
OUT = R/"data/jams.json"
UA = {"User-Agent": "Mozilla/5.0 FrightQueue/1.0 (+https://frightqueue.thejurn.com)"}
# Horror filter: jam name must match one of these, or the jam page's own text must mention horror.
KW = re.compile(r"horror|spook|scary|scare|fright|creep|haunt|hallow|dread|terror|nightmare|ghost|ghoul|macabre|eldritch|"
                r"lovecraft|cosmic horror|occult|zombie|undead|grave|crypt|gore|fear|liminal|analog horror|cursed|demon|witch|vampire|"
                r"monster|slasher|survival horror|psx horror|creepypasta|backrooms|uncanny", re.I)
def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as ex:
            if ex.code != 429 or i == tries - 1: raise
            time.sleep(20 * (i + 1))
def strip(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
def listing(kind, max_pages=12):
    out = []
    for p in range(1, max_pages + 1):
        s = get(f"https://itch.io/jams/{kind}?page={p}")
        cells = s.split('<div class="jam lazy_images">')[1:]
        if not cells: break
        for c in cells:
            m = re.search(r'<h3 dir="auto"><a href="(/jam/[^"]+)">(.*?)</a>', c)
            if not m: continue
            j = re.search(r'<span class="number">([\d,]+)</span> joined', c)
            img = re.search(r'data-background_image="([^"]+)"', c)
            host = re.search(r'Hosted by (.*?)</div>', c)
            out.append({"path": m.group(1), "name": strip(m.group(2)), "joined": int(j.group(1).replace(",", "")) if j else 0,
                        "image": img.group(1) if img else "", "host": strip(host.group(1)) if host else "", "status": kind})
        if 'class="next_page' not in s: break
        time.sleep(1)
    return out
def prize_of(title, text):
    # Only report a prize when the jam states a concrete one (money amount or "prize" in the jam's own title).
    t = re.search(r"\(?[^()]*\$\s?\d[\d,]*\+?[^()]*prizes?[^()]*\)?|prizes?[^.]{0,40}\$\s?\d[\d,]*", title, re.I)
    if t: return t.group(0).strip(" ()")[:120]
    for sent in re.split(r"(?<=[.!?])\s+|\s{2,}", text):
        if "?" in sent or re.search(r"\bno\b[^.]{0,20}prize|only prize|not (a )?ranked", sent, re.I): continue
        m = re.search(r"((?:1st|first)[^$€£]{0,30})?(?:AU|US|CA)?[$€£]\s?\d[\d,.]*[^.]{0,60}", sent)
        if m and re.search(r"prize|win|place|award|cash|gift", sent, re.I): return m.group(0).strip()[:140]
    return ""
def main():
    now = datetime.now(timezone.utc)
    cands = listing("in-progress") + listing("upcoming")
    out, seen = [], set()
    t0 = time.time()
    for c in cands:
        if c["path"] in seen: continue
        # Stay inside the CI timeout: after 13 minutes only check jams whose names already look like horror.
        if time.time() - t0 > 780 and not KW.search(c["name"]): continue
        seen.add(c["path"])
        name_hit = bool(KW.search(c["name"]))
        try:
            s = get("https://itch.io" + c["path"])
        except Exception as ex:
            print("skip", c["path"], ex); continue
        time.sleep(0.8)
        desc_m = re.search(r'class="jam_content user_formatted">(.*?)</div><div class="jam_', s, re.S)
        desc = strip(desc_m.group(1)) if desc_m else ""
        title_m = re.search(r"<title>(.*?) - itch\.io</title>", s)
        title = html.unescape(title_m.group(1)) if title_m else c["name"]
        # Not horror in the name? Require "horror" near the top of the jam's own description (theme statement).
        if not name_hit and not re.search(r"\bhorror\b", desc[:500], re.I):
            continue
        sd = re.search(r'"start_date":"([^"]+)"', s); ed = re.search(r'"end_date":"([^"]+)"', s)
        vd = re.search(r'"voting_end_date":"([^"]+)"', s)
        iso = lambda m: m.group(1).replace(" ", "T") + "Z" if m else ""
        end = iso(ed)
        if end and datetime.fromisoformat(end.replace("Z", "+00:00")) < now and c["status"] == "upcoming": continue
        out.append({"name": c["name"], "link": "https://itch.io" + c["path"], "host": c["host"], "image": c["image"],
                    "status": "in progress" if c["status"] == "in-progress" else "upcoming",
                    "start": iso(sd), "end": end, "voting_end": iso(vd), "joined": c["joined"],
                    "prize": prize_of(title, desc)})
    out.sort(key=lambda j: (j["status"] != "in progress", j["start"]))
    if len(out) < 2 and OUT.exists():
        print("too few results, keeping existing file"); return
    OUT.write_text(json.dumps({"updated": now.isoformat(), "source": "https://itch.io/jams", "jams": out}, indent=1, ensure_ascii=False))
    print(f"wrote {len(out)} horror jams from {len(seen)} listed jams")
if __name__ == "__main__": main()
