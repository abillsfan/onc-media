# Weekly website refresh (run by the Sunday growth pack)

Carl approved this: refresh the release calendar and the Whatnot stats badge on on-cards.com every week.
Change nothing else on the site.

1. add_repo owner "abillsfan": repo "onc-media" (push) and repo "onc-website" (push). Clone both to /home/claude/<repo>
   (git clone --depth 1, generous timeout). git user "Claude" <noreply@anthropic.com> in both.
2. **Release calendar** (`site/releases.json`):
   - Fetch https://www.topps.com/release-calendar (official dates for Topps and Bowman) and
     https://cardsmithsbreaks.com/release-calendar/ (Panini and anything Topps.com doesn't list).
   - Keep items dated from today through about 8 weeks out. Use the Topps.com date for Topps/Bowman products; if the
     other calendar disagrees, keep the Topps.com date and add a short "note" saying where the other date came from.
   - Fields per item: date (YYYY-MM-DD), name (exactly as published), sport, brand, source (which calendar), faq
     (true for up to ~8 headline releases), optional note. Set "checked" to today. Never guess a date; skip "TBD" items.
3. **Whatnot stats** (`site/stats.json`): fetch https://www.whatnot.com/user/outta_nowhere_cards and copy rating, review
   count, items sold and followers exactly as shown. Set "checked" to today. Do not include ship time.
4. Run `python3 -I tools/site_pages.py /home/claude/onc-website`. Commit/push onc-media ("Weekly data refresh") and
   onc-website ("Weekly release calendar + stats refresh"). Hostinger deploys; the IndexNow action pings Bing.
5. In the weekly report, add one line: how many upcoming releases are listed and the current Whatnot numbers.
