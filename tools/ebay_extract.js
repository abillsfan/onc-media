// Run in the built-in browser on https://www.ebay.com/sch/i.html?_ssn=cwright181&_ipg=240&_sop=1
// (javascript_tool). Returns JSON for onc-website/data/ebay-listings.json (minus "updated").
(async () => {
  const ids = [...new Set([...document.querySelectorAll('a[href*="/itm/"]')]
    .map(a => (a.href.match(/\/itm\/(\d{9,})/) || [])[1]).filter(Boolean))]
    .filter(id => id !== '123456');
  const out = [];
  for (const id of ids) {
    const r = await fetch('https://www.ebay.com/itm/' + id, { credentials: 'include' });
    const h = await r.text();
    const d = new DOMParser().parseFromString(h, 'text/html');
    const txt = d.body.innerText;
    const title = d.querySelector('h1')?.innerText?.trim();
    const og = d.querySelector('meta[property="og:image"]')?.content || '';
    const img = og.replace(/s-l\d+\.(jpg|webp|png)/, 's-l500.jpg');
    const priceRaw = d.querySelector('.x-price-primary')?.innerText?.trim() || '';
    const price = (priceRaw.match(/\$[\d,]+\.\d{2}/) || [''])[0];
    const isAuction = /Place bid/i.test(txt);
    const bidsM = txt.match(/(\d+)\s+bids?\b/i);
    const binM = txt.match(/(\$[\d,]+\.\d{2})\s*Buy It Now/);
    // end time: eBay embeds the end timestamp in page data
    const endM = h.match(/"endTime"\s*:\s*\{?[^}]*?"value"\s*:\s*"([^"]+)"/) || h.match(/"endDate"\s*:\s*"([^"]+)"/) || h.match(/"endTime"\s*:\s*"([^"]+)"/);
    const leftM = txt.match(/Ends in\s+((\d+)d\s*)?((\d+)h\s*)?((\d+)m)?/);
    let ends = endM ? new Date(endM[1]).toISOString() : null;
    if (!ends && leftM) {
      const ms = ((+leftM[2] || 0) * 1440 + (+leftM[4] || 0) * 60 + (+leftM[6] || 0)) * 60000;
      ends = new Date(Date.now() + ms).toISOString();
    }
    out.push({ id, title, url: 'https://www.ebay.com/itm/' + id, img, price,
      bids: bidsM ? parseInt(bidsM[1], 10) : 0, buy_it_now: isAuction && binM ? binM[1] : null,
      format: isAuction ? 'auction' : 'fixed', ends });
  }
  return JSON.stringify(out);
})()
