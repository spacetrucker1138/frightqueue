# Fright Queue
New/upcoming indie horror games and free demos. Static site for GitHub Pages at frightqueue.thejurn.com (see `CNAME`).

- `data/games.json`: game data (title, developer, status, release_date, platforms, store, link, blurb, tags, image, free, price). Set `"pinned": true` to keep a hand-added entry through refreshes.
- `data/arcade.json`: JURN Arcade games (links to thejurn.com).
- `scripts/refresh_games.py`: pulls Steam (horror tag search + appdetails) and itch.io horror RSS feeds. Edit `EXCLUDE` to curate. Stdlib only.
- `scripts/build.py`: generates index.html, games/*.html, submit.html, 404.html, sitemap.xml, robots.txt.
- Run locally: `python3 scripts/refresh_games.py && python3 scripts/build.py && python3 -m http.server 8000`
- Placeholders: newsletter form (`<!-- NEWSLETTER PLACEHOLDER -->` in build.py), affiliate params (`AFFILIATE` dict in build.py), submit uses mailto:contact@thejurn.com (GitHub issue URL noted in a comment).
- Nightly automation: `.github/workflows/refresh.yml` (daily 09:17 UTC + manual), commits only when the game list changes.
- DNS (owner to do at Porkbun): CNAME `frightqueue` -> `spacetrucker1138.github.io`.
