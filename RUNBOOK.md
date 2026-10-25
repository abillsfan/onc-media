# ONC Reel Autopost — Runbook

Each run posts ONE vertical reel to the **Outta Nowhere Cards** Facebook Page:
a **show reel** if a Whatnot show is coming up soon, otherwise a rotating **brand reel**.

**Style (Carl's choice, Oct 23 2026): 8-bit retro video-game reels only**, built with `tools/retro_reel.py`
(original pixel art + original chiptune; football and baseball; several camera angles). The old `make_reel.py`
logo-slam reels are retired: they lost viewers in the first second. Never use Tecmo/Nintendo names, logos, screens or music.

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
2. **Check for a show.** Open the Whatnot Shows tab in the built-in browser and read the page text (`get_page_text`).
   - If a show starts within the next 48 hours → **show reel** (step 3a).
   - If no show in that window, or the browser/PC can't be reached → **brand reel** (step 3b). Never guess show times.
3a. **Show reel.** Open that show's page and read its title and description. **Match the sport:** if the show is baseball
   (title/description/product says baseball, e.g. Topps Chrome Baseball, Allen & Ginter, Bowman baseball) use the next
   `bb_` theme in the rotation; if it is football use the next `fb_` theme; otherwise take the NEXT theme in
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
3b. **Brand reel.** Read `reels/log.json`; find the last entry whose `theme_or_show` starts with `retro:` and pick the theme
   in `brand/retro_themes.json` that comes after it (wrap around; start at the first if none). Use its `spec` and `caption`.
   Log it as `theme_or_show: "retro:<theme id>"` (show reels: `"retro:<theme id> | <show title>"`).
4. **Render:** `python3 -I tools/retro_reel.py spec.json reels/<YYYY-MM-DD>-<slug>.mp4` (takes ~1 min). Variants:
   `bb_homer` (behind the catcher, then the outfield wall), `fb_kick` (behind the kicker, then behind the goalposts),
   `fb_run` (overhead, behind the runner).
5. **Publish the file:** append `{date, type: "show"|"brand", theme_or_show, file, posted_at}` to `reels/log.json`, commit as
   `Claude <noreply@anthropic.com>`, push to `main`. Confirm the raw URL returns HTTP 200.
6. **Post** with `page_video` using that raw URL, a short title, and the caption.
7. **Report** to Carl in 1–3 lines: which reel went out and why (show vs brand), and the post id. If anything failed, say what.

## Voice / rules
Friendly, hype but honest, short lines, light emoji, Southern-casual. Tagline: "Any card. Any sport. Anytime."
Never invent hits, buyer names, prices, products or show times. Keep giveaway language general and never describe chance mechanics in ways that could break Whatnot rules.
No licensed music, team logos or player photos in reels (text only for team names).
Do not mention shipping, packaging, mailers or "measured and weighed" in reels, captions or the website (Carl removed it).

## Hits (when Carl sends hit photos after a break)
1. Save photos to `hits/<YYYY-MM-DD>/<slug>.jpg`; write one spec per hit in `hits/<date>/specs/` (see the 2026-10-18 ones) and render
   `python3 -I tools/hit_reel.py <spec> reels/<date>-hit-<slug>.mp4` (set `"audio": "ballgame"`: no music, crowd in the background and a bat crack when the card appears; Carl, Oct 25 2026).
   Hit reels get spread over the week, so never say "today": set `"opener": ["SUNDAY'S", "LIVE SHOW", "HITS"]` and
   `"pulled": ["PULLED LIVE", "SUNDAY ON WHATNOT"]` (use the show's weekday), and captions say "from Sunday's live show". Carl approves before posting.
2. Add the week to `site/hits.json` (player, card, team spot, product, photo, card_rect — only what Carl said or what's printed on the card).
3. Run `python3 -I tools/site_pages.py /home/claude/onc-website`, then commit and push onc-website. This updates /hits/, the homepage
   "Latest hits" strip, the product page and the sitemap; the IndexNow GitHub action pings Bing after Hostinger deploys.
