# Daily pre-order sold-out check (run by the "ONC Pre-order Sold-out Check" scheduled task)

Carl approved this: once a day, mark pre-orders on the on-cards.com release calendar as sold out when Topps.com
sells out. Change nothing else on the site.

1. add_repo owner "abillsfan": "onc-media" (push) and "onc-website" (push). Clone both to /home/claude/<repo>
   (git clone --depth 1, generous timeout). git user "Claude" <noreply@anthropic.com> in both.
2. In `site/releases.json`, collect every item that has a "topps" list and whose "date" (release date) is today or later.
   Each entry is {"format", "url", "soldout"}. If there are none, stop and change nothing.
3. Load the built-in browser tools (ToolSearch query "mcp__remote-devices__Claude_Browser__", max_results 64).
   Open https://www.topps.com/ with preview_start. If Topps shows a "not a robot" check, or the browser/Carl's PC
   can't be reached, stop and change nothing (say so in the final line).
4. Run `tools/topps_status.js` with javascript_tool on that tab, prepending
   `const HANDLES = [...];` with the part of each url after `/products/` (keep it URL-encoded, e.g. `%C2%AE`).
   It returns true (sold out), false (for sale) or an "error: ..." string per product.
5. For each product with a true/false result, set "soldout" to that value. Leave entries with errors unchanged.
   Never guess. Set "status_checked" on the item to today's date (Central time).
6. Only if any "soldout" value changed: run `python3 -I tools/site_pages.py /home/claude/onc-website`, then commit/push
   onc-media ("Pre-order status refresh") and onc-website ("Pre-order sold-out status"). End every commit message with:
   Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
7. Finish with one line: which pre-orders are sold out / still available, and what changed (or "no change").

How it shows on the site: the calendar row says "Pre-orders sold out on Topps.com" when every listed Topps.com format
is sold out, or "Sold out on Topps.com: <formats>" when only some are.
