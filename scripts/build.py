#!/usr/bin/env python3
"""Build static pages from data/*.json: index.html, games/<id>.html, submit.html, sitemap.xml, robots.txt."""
import json, html
from datetime import date
from pathlib import Path
R = Path(__file__).resolve().parent.parent
SITE = "https://frightqueue.thejurn.com"
JURN = "https://thejurn.com/"
data = json.loads((R/"data/games.json").read_text())
games = data["games"]
arcade = json.loads((R/"data/arcade.json").read_text())
e = lambda s: html.escape(str(s or ""), quote=True)
# AFFILIATE HOOK: set per-store affiliate params here once programs are approved (none signed up yet).
AFFILIATE = {"Steam": "", "itch.io": ""}  # e.g. "itch.io": "?ac=XXXX"

GA = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-RG06HTMTSE"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-RG06HTMTSE');
</script>
"""

def head(title, desc, path, img=None, extra=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
{GA}<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}"><meta property="og:type" content="website">
{f'<meta property="og:image" content="{e(img)}">' if img else ''}<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎃</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Creepster&family=Inter:wght@300;400;600;700&display=swap">
<link rel="stylesheet" href="/assets/style.css">{extra}</head><body>
<header class="top"><div class="wrap"><a class="logo" href="/">Fright Queue</a>
<nav><a href="/#this-week">This Week</a><a href="/#queue">The Queue</a><a href="/#arcade">JURN Arcade</a><a href="/submit.html">Submit</a><a href="{JURN}ghoulbox/">Ghoul Box</a><a href="{JURN}">The JURN ↗</a></nav></div></header>"""

def foot():
    return f"""<footer><div class="wrap jurn"><a href="{JURN}" aria-label="The JURN"><img src="/assets/jurn-logo.png" alt="The JURN logo" loading="lazy" width="96" height="48"></a>
<div>Fright Queue is dug up nightly by <a href="{JURN}">The JURN</a>, horror punk from the grave in Amityville, NY.
Watch the <a href="https://www.youtube.com/@Spacetrucker138">24/7 stream</a> · play the <a href="{JURN}games.html">JURN Arcade</a> · <a href="https://discord.gg/4aWt5h52t">Discord</a>.<br>
Game names, art and trademarks belong to their owners. Data comes from public Steam and itch.io pages. As an Amazon Associate, Fright Queue earns from qualifying purchases.</div></div></footer>"""

def news():
    # Buttondown HTML embed (official format: standard <form> POST, no fetch). Newsletter: buttondown.com/frightqueue
    return """<section class="news" id="newsletter">
<div class="eyebrow">The Weekly Fright</div><h2 class="sec" style="margin-top:.3rem">Get the Queue in your inbox</h2>
<p>Free demos to play this weekend, new releases, what's coming, and one cursed JURN transmission. Weekly. No spam, unsubscribe anytime.</p>
<form action="https://buttondown.com/api/emails/embed-subscribe/frightqueue" method="post" target="popupwindow" onsubmit="window.open('https://buttondown.com/frightqueue', 'popupwindow')" class="embeddable-buttondown-form">
<label for="bd-email" class="sr-only">Email address</label><input type="email" name="email" id="bd-email" placeholder="you@crypt.com" required>
<input type="hidden" value="1" name="embed"><input type="hidden" name="tag" value="frightqueue-site">
<button class="btn" type="submit">Summon me</button></form>
<p class="meta" style="margin-top:.6rem">Powered by <a href="https://buttondown.com/refer/frightqueue" target="_blank" rel="noopener">Buttondown</a>. You'll get a confirmation email.</p></section>"""

# Amazon Associates: generic search links only (no specific products).
AMAZON_TAG = "frightqueue-20"
GEAR = [("🎧 Gaming headsets", "gaming headset"), ("🎮 Horror games for PS5", "horror game PS5"),
        ("🕹 Horror games for Nintendo Switch", "horror game Nintendo Switch"), ("💡 LED gaming room lights", "LED gaming room lights"),
        ("🎮 PC game controllers", "PC game controller"), ("🖼 Horror movie posters", "horror movie posters")]
def gear():
    from urllib.parse import quote_plus
    items = "".join(f'<a class="btn" href="https://www.amazon.com/s?k={quote_plus(q)}&amp;tag={AMAZON_TAG}" target="_blank" rel="sponsored noopener">{e(label)}</a> ' for label, q in GEAR)
    return f"""<section id="gear" class="gear"><h2 class="sec">Horror Gaming Gear</h2>
<p class="sub">Kit out your crypt. These are Amazon searches; we earn a small commission on qualifying purchases.</p>
<p class="gear-links" style="display:flex;flex-wrap:wrap;gap:.5rem">{items}</p></section>"""

def link(g): return g["link"] + AFFILIATE.get(g["store"], "")

# ---------- game pages ----------
(R/"games").mkdir(exist_ok=True)
_keep = {f"{g['id']}.html" for g in games}
for _f in (R/"games").glob("*.html"):  # drop pages for games no longer in the data
    if _f.name not in _keep: _f.unlink()
for g in games:
    desc = f'{g["title"]} by {g["developer"]}: {g["blurb"]}'[:300]
    ld = {"@context":"https://schema.org","@type":"VideoGame","name":g["title"],"author":{"@type":"Organization","name":g["developer"]},
          "gamePlatform":g["platforms"],"image":g["image"],"url":g["link"],"description":g["blurb"],"genre":g["tags"]}
    if g["release_date"][:2] in ("19","20"): ld["datePublished"]=g["release_date"]
    p = head(f'{g["title"]} | Fright Queue', desc, f'/games/{g["id"]}.html', g["image"],
             f'<script type="application/ld+json">{json.dumps(ld)}</script>')
    demo = f' <a class="btn" href="{e(g["demo_link"])}" rel="noopener">Get the demo</a>' if g.get("demo_link") else ""
    p += f"""<main class="wrap"><div class="detail"><img src="{e(g["image"])}" alt="{e(g["title"])} key art" width="460" height="215">
<div><span class="pill {g["status"]}">{ {"demo":"Free demo","released":"Out now","upcoming":"Upcoming"}[g["status"]] }</span>{'<span class="pill free">Free</span>' if g["free"] else ''}
<h1>{e(g["title"])}</h1><p class="meta">by {e(g["developer"])} · {e(g["release_date"])} · {e(", ".join(g["platforms"]))}{' · '+e(g["price"]) if g.get("price") else ''}</p>
<p style="margin:1rem 0">{e(g["blurb"])}</p><p>{"".join(f'<span class="pill">{e(t)}</span>' for t in g["tags"])}</p>
<p style="margin-top:1rem"><a class="btn" href="{e(link(g))}" rel="noopener sponsored">View on {e(g["store"])}</a>{demo}</p>
<p style="margin-top:1rem"><a href="/#queue">← Back to the Queue</a></p></div></div>{news()}</main>{foot()}</body></html>"""
    (R/f"games/{g['id']}.html").write_text(p)

# ---------- index ----------
arc = "".join(f"""<article class="card"><a href="{e(a.get("url") or JURN+a["path"])}"><img src="/{e(a["img"])}" alt="{e(a["title"])}" loading="lazy" width="320" height="180"></a>
<div class="b"><span class="meta">{e(a["genre"])} · free in your browser</span><h3><a href="{e(a.get("url") or JURN+a["path"])}">{e(a["title"])}</a></h3></div></article>""" for a in arcade)
noscript = "".join(f'<li><a href="/games/{g["id"]}.html">{e(g["title"])}</a> ({e(g["developer"])})</li>' for g in games)
idx = head("Fright Queue: New & Upcoming Indie Horror Games and Free Demos",
           "A living tracker of new, upcoming and free-demo indie horror games on Steam and itch.io, from The JURN.", "/")
idx += f"""<main class="wrap">
<section class="hero"><div class="eyebrow">Indie horror radar · updated {e(data["updated"][:10])}</div><h1>Fright Queue</h1>
<p>New and upcoming indie horror, plus free demos you can play tonight. Dug up from Steam and itch.io so you don't have to.</p>
<p style="margin-top:1.2rem"><a class="btn" href="#queue">Browse the Queue</a> <a class="btn" href="/submit.html">Submit your game</a></p></section>
<section id="this-week"><h2 class="sec">This Week</h2><p class="sub">Releasing within 7 days of today, or newly out in the last 7 days.</p><div class="grid" id="week-grid"></div></section>
<section id="queue"><h2 class="sec">The Queue</h2>
<div class="filters" role="group" aria-label="Filters">
<button data-f="all" class="on">All</button><button data-f="demo">Demos</button><button data-f="released">Out now</button><button data-f="upcoming">Upcoming</button><button data-f="free">Free</button>
<select id="plat" aria-label="Platform"><option value="">All platforms</option><option>Windows</option><option>Mac</option><option>Linux</option><option>Browser</option><option>Android</option></select>
<select id="store" aria-label="Store"><option value="">All stores</option><option>Steam</option><option>itch.io</option></select>
<input type="search" id="q" placeholder="Search titles, devs, tags…" aria-label="Search"></div>
<p class="sub" id="count"></p><div class="grid" id="grid"></div>
<noscript><ul>{noscript}</ul></noscript></section>
{news()}
{gear()}
<section id="arcade" class="arcade"><h2 class="sec">JURN Arcade</h2><p class="sub">Free browser games from the Graveyard Dimension by <a href="{JURN}">The JURN</a>. No downloads, just play.</p><div class="grid">{arc}</div>
<p style="margin-top:1rem"><a class="btn" href="{JURN}games.html">Enter the full Arcade</a></p></section>
</main>{foot()}<script src="/assets/app.js" defer></script></body></html>"""
(R/"index.html").write_text(idx)

# ---------- submit ----------
sub = head("Submit Your Indie Horror Game | Fright Queue", "Making an indie horror game or demo? Submit it to Fright Queue.", "/submit.html")
sub += """<main class="wrap prose"><h2 class="sec">Submit your game</h2>
<p>Got a horror game, demo or jam entry? Send it in. Indie and solo devs come first. Steam, itch.io, Game Jolt and browser games are all welcome.</p>
<!-- SUBMISSION METHOD: mailto (opens the visitor's mail app). To switch to GitHub Issues later, point the form at
     https://github.com/OWNER/REPO/issues/new?template=submit-game.yml (placeholder: no repo exists yet). -->
<form class="submit" id="submit-form">
<label>Game title<input name="title" required></label><label>Developer / studio<input name="developer" required></label>
<label>Store link (Steam / itch.io)<input name="link" type="url" required></label>
<label>Status<select name="status"><option>Demo</option><option>Out now</option><option>Upcoming</option></select></label>
<label>Release date<input name="date" placeholder="2026-10-31 or TBA"></label><label>Platforms<input name="platforms" placeholder="Windows, Mac, Browser…"></label>
<label>Short pitch (1–2 sentences)<textarea name="blurb" rows="3"></textarea></label>
<button class="btn" type="submit">Send submission</button></form>
<p class="meta">This opens your email app with everything filled in, addressed to contact@thejurn.com. We don't store anything on this site.</p></main>"""
sub += foot() + """<script>document.getElementById('submit-form').addEventListener('submit',ev=>{ev.preventDefault();const f=new FormData(ev.target);
let b='';for(const[k,v]of f)b+=k+': '+v+'\\n';location.href='mailto:contact@thejurn.com?subject='+encodeURIComponent('Fright Queue submission: '+f.get('title'))+'&body='+encodeURIComponent(b);});</script></body></html>"""
(R/"submit.html").write_text(sub)

# ---------- 404, sitemap, robots ----------
(R/"404.html").write_text(head("Lost in the crypt | Fright Queue","Page not found","/404.html")+'<main class="wrap hero"><h1>404</h1><p>This page has been buried. <a href="/">Back to the Queue</a></p></main>'+foot()+"</body></html>")
today = date.today().isoformat()
urls = ["/", "/submit.html"] + [f"/games/{g['id']}.html" for g in games]
(R/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
(R/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
print(f"built {len(games)} game pages")
