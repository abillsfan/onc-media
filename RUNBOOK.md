# ONC Reel Autopost — Runbook

Each run posts ONE vertical reel to the **Outta Nowhere Cards** Facebook Page:
a **show reel** if a Whatnot show is coming up soon, otherwise a rotating **brand reel**.

**Style:** retro video-game reels built with `tools/era_reel.py` (original art + original music; football and baseball;
several camera angles). It renders the same games as `tools/retro_reel.py` in different console-era looks set by the spec's
`"era"`: `8bit` (NES-style) and `16bit` (shaded sprites, gradient skies, striped turf, FM-synth music). The old `make_reel.py`
logo-slam reels are retired: they lost viewers in the first second. Never use Tecmo/Nintendo/Sega names, logos, screens or music.
**Style rotation (Carl, Oct 31 2026): random, never the same style twice in a row.** Each reel (brand or show) picks its `era`
at random from `brand/eras.json` "approved", excluding the `era` of the most recent entry in `reels/log.json` (a log entry with
no `era` counts as `8bit`). Only "approved" eras are used (if just one is approved, use it every time); a new style joins only after Carl approves a sample. Log the era.

**Schedule:** Tue, Thu, Fri, Sat at about 6 PM Central. Video/Reels reach is strongest roughly 5–7 PM on weekdays;
Fri and Sat evening runs land just before the early-morning weekend Whatnot shows.

## Fixed values
- Facebook Page: Outta Nowhere Cards, page id `1252006641328350`
- Zapier connection (Facebook Pages): `02c900c9-2568-889e-b183-ab662b0c3de1`
- Zapier app `FacebookV2CLIAPI`
  - read recent posts: action `post_by_you`, tool_name `facebook_pages_new_post_by_you`, params `{page}`
  - post video: action `page_video`, tool_name `facebook_pages_create_page_video`, params `{page, title, source, description}`
    (`source` = public raw.githubusercontent.com URL of the mp4)
- Whatnot shows tab: https://www.whatnot.com/user/outta_nowhere_cards/shows (read through the built-in browser on Carl's PC; whatnot.com is already approved there)
- Public video base URL: `https://raw.githubusercontent.com/abillsfan/onc-media/main/reels/`
- Website https://on-cards.com · Whatnot https://www.whatnot.com/user/outta_nowhere_cards · eBay https://www.ebay.com/usr/cwright181

## Steps
1. **Duplicate guard.** Read the Page's recent posts. If a *video* was posted in the last 20 hours, stop and post nothing.
   (The hit reel drip is scheduled around this so it never blocks a brand/show reel.)
2. **Check for a show.** Open the Whatnot Shows tab in the built-in browser and read the page text (`get_page_text`).
   - If a show starts within the next 48 hours → **show reel** (step 3a).
   - If no show in that window, or the browser/PC can't be reached → **brand reel** (step 3b). Never guess show times.
3a. **Show reel.** Open that show's page and read its title and description. **Match the sport:** if the show is baseball
   (title/description/product says baseball, e.g. Topps Chrome Baseball, Allen & Ginter, Bowman baseball) use the first
   never-posted `bb_` theme (list order); if it is football, the first never-posted `fb_` theme; otherwise take the NEXT theme in
   `brand/retro_themes.json` (same rotation as 3b). Add to its spec:
   `"end": {"banner": ["NEXT BREAK", "<DAY> <M/D> <TIME> CT"], "lines": ["LIVE ON", "WHATNOT"]}`
   (e.g. `["NEXT BREAK", "SUN 10/26 6 AM CT"]`), and, only if the show names a product, `"pack_label"` = two short words
   from it (e.g. `["ALLEN &", "GINTER"]`, each <= 8 characters). Use only facts shown on Whatnot.
   Caption: the theme's first line + "Next break: <day> <time> CT" + the show link + 3–5 hashtags.
3c. **Website On Deck (show reels only).** If the show's Whatnot title or description names a specific product, format or lineup
   (more than the generic "Raw Cards, $1 Starts, New Release"), update the website's On Deck card:
   - add_repo owner "abillsfan", repo "onc-website", access "push"; clone to /home/claude/onc-website; git user Claude <noreply@anthropic.com>.
   - In index.html, fill the `<article class="... ondeck-lineup">` card: `.tag` = day + time CT (e.g. "Sunday 6 AM CT"),
     `h3` = the product/format, `p` = one or two sentences using only what Whatnot says, plus a link to the show page.
     Remove `hidden` from that card, add `hidden` to the `ondeck-tbd` (stay-tuned) card.
   - Set `data-until` on the lineup card to show start + 4 hours as ISO time with the correct Central offset
     (-05:00 during daylight time, -06:00 after the first Sunday in November).
   - Set sitemap.xml lastmod to today. If you change assets/style.css or assets/main.js, bump their ?v= tag in index.html. Change nothing else. Commit and push to main (Hostinger deploys it automatically).
   - After the show, assets/main.js flips the site back to "Stay tuned for next week's break lineup" by itself; no run needed.
   If the show details are generic, leave the site alone.
3b. **Brand reel.** Read `reels/log.json` and pick the FIRST theme in `brand/retro_themes.json` (list order) whose id has never
   been posted (no log entry `retro:<id>`), so themes skipped by a show reel's sport match still get their turn. Only when every
   theme has been posted, go back to taking the theme after the last `retro:` entry (wrap around). Use its `spec` and `caption`
   **only if that theme id has never been posted**. If it has (the rotation wrapped), make a fresh version (see "Every post is unique").
   **Pre-rendered themes:** a theme with a `file` is a finished reel Carl approved (Oct 29 2026). If it has never been posted,
   skip rendering: for a brand reel post that file exactly as it is; for a show reel, render the theme's same `spec` plus the
   show's `end` banner (and `pack_label`) so the video still matches what Carl approved. Run the uniqueness check either way.
   Log it as `theme_or_show: "retro:<theme id>"` (show reels: `"retro:<theme id> | <show title>"`).
4. **Render:** add the chosen `"era"` to the spec, then `python3 -I tools/era_reel.py spec.json reels/<YYYY-MM-DD>-<slug>.mp4` (takes ~1 min).
   A pre-rendered theme `file` is 8-bit: use it only when the chosen era is `8bit`; otherwise render its `spec` with the chosen era. Variants:
   `bb_homer` (behind the catcher, then the outfield wall), `bb_gap` (center-field broadcast cam over the pitcher, then the
   overhead full field as the ball splits the gap, then a close-up cut-in of the slide at the plate and the ump's SAFE call),
   `fb_kick` (behind the kicker, then behind the goalposts), `fb_return` (side-scrolling sideline camera on a kickoff return,
   a close-up stiff-arm cut-in, then back to the sideline cam for the touchdown), `fb_pass` (overhead behind the QB scramble +
   Hail Mary, then the back of the end zone for the jump-ball catch).
   **Big-moment plays (Carl, Oct 31 2026): reels show any exciting moment of a game, not only scores** (`tools/plays_big.py`):
   `fb_sack` (overhead behind the defense as the ONC blitzer loops in free, close-up blindside hit, ground camera: QB down,
   ball loose, "SACKED!"), `fb_block` (behind the CPU kicker as ONC's #99 leaps, close-up of the ball off his hands,
   "BLOCKED!", reverse angle from behind the posts with the ref waving it off). New plays join the theme list once Carl
   approves a sample.
   **Angles (Carl, Oct 29 2026):** every reel, in every era, must cut between different camera angles to tell different parts of the play,
   the way real 8-bit sports games do (broadcast cam, overhead, sideline scroll, close-up cut-ins). Do not use `fb_run`
   (one angle only). Every reel opens with the ONC "PRESS START" title screen: always set `"start": true`.
5. **Uniqueness check:** save the caption to a temp file and run
   `python3 -I tools/unique_check.py reels/<file>.mp4 <caption.txt> <spec.json>`. If it says NOT UNIQUE, change what it names,
   re-render and re-check. Never post until it prints OK.
   **Publish the file:** append `{date, type: "show"|"brand", theme_or_show, era, file, spec, caption, posted_at}` to `reels/log.json`, commit as
   `Claude <noreply@anthropic.com>`, push to `main`. Confirm the raw URL returns HTTP 200.
6. **Post** with `page_video` using that raw URL, a short title, and the caption.
7. **Report** to Carl in 1–3 lines: which reel went out and why (show vs brand), and the post id. If anything failed, say what.

## Every post is unique (Carl, Oct 29 2026)
Carl does not want the same reel posting over and over. Every reel that goes to Facebook must be new: never repost a video file,
never re-render an earlier spec unchanged, never reuse a caption.
- A theme that has already been posted gets a fresh version: write a new original 2-line `hook`, pick an `away_color` not yet
  used with that `variant`, change the scoreboard `away` name and/or `pack_label`, and set `seed` to the number of times the theme
  has been used + 1. Log it as `retro:<theme id>#<n>`.
- Write a brand-new caption each post (same voice and links, different words and hashtags order/mix).
- Hit reels post once each from `reels/hit_queue.json`; never add a file that is already in the queue or the log.
- `tools/unique_check.py` enforces this before every post (step 5).

## Voice / rules
Friendly, hype but honest, short lines, light emoji, Southern-casual. Tagline: "Any card. Any sport. Anytime."
Never invent hits, buyer names, prices, products or show times. Keep giveaway language general and never describe chance mechanics in ways that could break Whatnot rules.
No licensed music, team logos or player photos in reels (text only for team names).
Do not mention shipping, packaging, mailers or "measured and weighed" in reels, captions or the website (Carl removed it).

## Hits (when Carl sends hit photos after a break)
1. Save photos to `hits/<YYYY-MM-DD>/<slug>.jpg`; write one spec per hit in `hits/<date>/specs/` (see the 2026-10-18 ones) and render
   `python3 -I tools/hit_reel.py <spec> reels/<date>-hit-<slug>.mp4` (set `"audio": "none"`: Carl wants hit reels with NO sound at all — no music, no sound effects; Oct 25 2026).
   Hit reels get spread over the week, so never say "today": set `"opener": ["SUNDAY'S", "LIVE SHOW", "HITS"]` and
   `"pulled": ["PULLED LIVE", "SUNDAY ON WHATNOT"]` (use the show's weekday), and captions say "from Sunday's live show". Carl approves before posting.
2. Add the week to `site/hits.json` (player, card, team spot, product, photo, card_rect — only what Carl said or what's printed on the card).
3. Run `python3 -I tools/site_pages.py /home/claude/onc-website`, then commit and push onc-website. This updates /hits/, the homepage
   "Latest hits" strip, the product page and the sitemap; the IndexNow GitHub action pings Bing after Hostinger deploys.

## Hit reel drip ("ONC Hit Reel Drip" scheduled task, 12:27 PM and 7:27 PM CT daily)
After Carl approves a show's hit reels, add them to `reels/hit_queue.json` (file, title, caption, posted_at null).
Each run: `git pull`; skip (and mark `"skipped": "duplicate"`) any item whose file or caption was already posted; the 12:27 PM run posts only on Mon and Wed (the 8-bit reel task's 20-hour guard would otherwise
skip Tue/Thu/Fri/Sat brand reels); the 7:27 PM run posts every day. Take the FIRST item with
posted_at null; if none, stop quietly. Check the mp4 URL (raw.githubusercontent.com/abillsfan/onc-media/main/<file>) returns 200,
post it with `page_video` (title + caption as description), then set posted_at and fb_video_id, commit "Hit reel posted: <file>", push.
Captions name the show day ("from Sunday's live show"), never "today". Hit reels have no sound.
