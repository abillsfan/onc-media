# ONC Reel Autopost — Runbook

Each run posts ONE vertical reel to the **Outta Nowhere Cards** Facebook Page:
a **show reel** if a Whatnot show is coming up soon, otherwise a rotating **brand reel**.

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
3a. **Show reel.** Open that show's page and read its title and description. Build a spec like `examples/show_example.json`:
   intro `["LIVE BREAK", "TOMORROW"|"TONIGHT"|"<DAY>"]`, scenes from the format/product/teams Carl wrote in the title or description
   (e.g. RANDOM TEAM BREAKS / 2026 TOPPS ALLEN & GINTER / SAVING THE DODGERS FOR LAST), outro `["<DAY> <TIME> CT", "LIVE ON WHATNOT", "@outta_nowhere_cards"]`.
   Use only facts shown on Whatnot. Caption: short hype + day/time CT + the show link + 3–5 hashtags.
3b. **Brand reel.** Read `reels/log.json`; pick the theme in `brand/themes.json` that comes after the last brand theme used (wrap around).
   Use its `spec` (bump `seed` by +1 per use so each render differs slightly) and its `caption`.
4. **Render:** `python3 -I tools/make_reel.py spec.json reels/<YYYY-MM-DD>-<slug>.mp4` (takes ~1.5 min).
5. **Publish the file:** append `{date, type: "show"|"brand", theme_or_show, file, posted_at}` to `reels/log.json`, commit as
   `Claude <noreply@anthropic.com>`, push to `main`. Confirm the raw URL returns HTTP 200.
6. **Post** with `page_video` using that raw URL, a short title, and the caption.
7. **Report** to Carl in 1–3 lines: which reel went out and why (show vs brand), and the post id. If anything failed, say what.

## Voice / rules
Friendly, hype but honest, short lines, light emoji, Southern-casual. Tagline: "Any card. Any sport. Anytime."
Never invent hits, buyer names, prices, products or show times. Keep giveaway language general and never describe chance mechanics in ways that could break Whatnot rules.
No licensed music, team logos or player photos in reels (text only for team names).
Do not mention shipping, packaging, mailers or "measured and weighed" in reels or captions (Carl removed it).
