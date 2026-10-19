// Run in the built-in browser on any www.topps.com page (javascript_tool), with this line prepended:
//   const HANDLES = ["2026-topps-pro-debut-baseball-hobby-box", ...];   // the part after /products/ in each url
// Returns {handle: true (sold out) | false (still for sale) | "error: ..."}.
// Topps pages are rendered client-side, so this reads the product data embedded in the page HTML:
// the product's "isSoldOut" flag. Anything else (blocked page, missing flag) is reported as an error.
const out = {};
for (const h of HANDLES) {
  try {
    const r = await fetch("/products/" + h, { cache: "no-store" });
    const t = await r.text();
    if (!r.ok) { out[h] = "error: HTTP " + r.status; continue; }
    const vals = [...t.matchAll(/\\?"isSoldOut\\?"\s*:\s*(true|false)/g)].map(m => m[1]);
    if (!vals.length) out[h] = "error: no isSoldOut flag (bot check or page change?)";
    else if (new Set(vals).size > 1) out[h] = "error: conflicting isSoldOut flags on page";
    else out[h] = vals[0] === "true";
  } catch (e) { out[h] = "error: " + e; }
}
out
