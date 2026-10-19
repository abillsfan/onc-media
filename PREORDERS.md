# Adding Carl's pre-orders to on-cards.com ("Preordered for future breaks")

Carl's standing instruction: every time he says what he has pre-ordered for future breaks (often order screenshots),
do ALL of this. Don't wait to be asked for each piece.

## What goes on the site
Section `#preorders` in onc-website/index.html (between the On Deck section and `<!-- RELEASES`), plus the
"Preorders" link in the top nav.

- **No prices and no quantities.** Never show what Carl paid or how many boxes he ordered.
- One `.po-product` block per product (set), grouped by sport tag. Each has:
  - Topps' description of the product, rewritten in our own words (never copy Topps' text).
  - "Rookies/Prospects to chase" and "Notable chases" lists (headline inserts, autographs, case hits, 1/1s).
  - One `.break-card` per box format he ordered (Hobby, Jumbo, Mega, Value/Blaster, Hanger...) with the pack
    configuration, the format-exclusive parallels, any rare inserts printed on the box, and the Topps release date.
  - Any handling notes he gives (e.g. "Topps is sending Mega Boxes without the sealed plastic wrap").
- Product photos, **self-hosted** in `onc-website/images/preorders/` (never hotlink Topps' CDN).
- Small fine-print line: details come from Topps and checklists are subject to change.

## Where the facts come from (check every one)
1. The Topps.com product page for each format he ordered: config, "Look for ..." exclusives, release day,
   description tab. Topps.com shows a robot check to automated fetches, so use the built-in browser on Carl's PC
   (ask him to click the check if it appears). Ask Carl for the product link if you can't find it.
2. The box art itself (in the product photos): exclusive parallels and "rare inserts" printed on the box.
3. Checklists (Checklist Insider, Beckett, Cardsmiths) for top rookies/prospects and headline chases.
Never list a format exclusive you haven't confirmed. If Topps' page and the box disagree, use the box and Topps' page.

## Product photos
Topps product images are on cdn.shopify.com (find them with og:image on the product page). The workspace shell
can't download them, so in the built-in browser render each image full-window on a black and then a white
background, screenshot both at scale 1, and difference-matte them into a transparent WebP (≤560px, quality ~86) in
`images/preorders/<year>-<brand>-<product>-<format>.webp`. Opaque photos (no transparency) just crop the border.

## Release calendar + sold-out tracking
In `onc-media/site/releases.json`, for each product: "preorder" = the pre-order date, "date" = Topps' release day,
and "topps" = [{"format", "url", "soldout"}] for every Topps.com format. Then
`python3 -I tools/site_pages.py /home/claude/onc-website`. The daily "ONC Pre-order Sold-out Check" task
(PREORDER_STATUS.md) keeps "soldout" current.

## Finish
- Bump `V` in tools/site_pages.py (and the `?v=` on index.html / 404.html) whenever style.css or main.js changes.
- Commit/push both repos, then check the live page in the built-in browser (desktop and phone widths).
- When a product has been broken, remove its block (and its images) from the section; remove the section when empty.
