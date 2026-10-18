# ONC eBay → website sync

Keeps the "Live on eBay" section of on-cards.com in step with Carl's eBay listings (seller cwright181).

1. add_repo owner "abillsfan", repo "onc-website", access "push"; clone to /home/claude/onc-website; git user Claude <noreply@anthropic.com>.
   Also clone abillsfan/onc-media (for tools/ebay_extract.js).
2. Load the built-in browser tools (ToolSearch "mcp__remote-devices__Claude_Browser__", max_results 64).
   preview_start https://www.ebay.com/sch/i.html?_ssn=cwright181&_ipg=240&_sop=1, then run the contents of
   onc-media/tools/ebay_extract.js with javascript_tool (action javascript_exec). It returns a JSON array of listings.
   If the computer or browser can't be reached, stop and change nothing (the site already hides ended auctions on its own).
3. Sanity-check the result: every item needs id, title, url, img and price. Keep only items whose `ends` is in the future
   (fixed-price items with no end time are allowed: set "ends" to 30 days from now so they stay visible).
   Never invent or edit titles or prices.
4. Write onc-website/data/ebay-listings.json as
   {"updated": "<now, ISO with Central offset>", "seller_url": "https://www.ebay.com/sch/i.html?_ssn=cwright181", "items": [...]}
   keeping the field names shown in the current file. If the items (ids, prices, bids, end times) are unchanged from the
   current file, change nothing and stop.
5. Commit ("Sync eBay listings") and push to main. Hostinger deploys it automatically.
6. Report in one line: how many listings are live and what changed (new, ended, new bids). Do not post anywhere.
