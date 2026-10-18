"""Builds the extra pages of on-cards.com into the onc-website repo.

Usage:
    python3 tools/site_pages.py /home/claude/onc-website

Writes:
  hits/index.html                      - every hit from site/hits.json, newest first (+ resized photos)
  card-breaks/index.html               - "What is a card break?" guide
  team-breaks/index.html               - how ONC team breaks work
  random-breaks/index.html             - how ONC random team breaks work
  2026-topps-allen-and-ginter/index.html
  and the "Latest hits" strip on the homepage (between the LATEST HITS markers in index.html)
  and sitemap.xml (all pages).

To add a week's hits: append an entry to site/hits.json (photos under hits/<date>/), run this, commit and push onc-website.
Rules: only facts Carl gave or that are on Whatnot/eBay/the published checklist. No shipping/packaging talk.
"""
import html, json, os, sys, datetime
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(HERE, "..")
SITE = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/onc-website"
BASE = "https://on-cards.com"
V = "20261018d"  # asset version tag; bump when style.css/main.js change
WHATNOT = "https://www.whatnot.com/user/outta_nowhere_cards"
FACEBOOK = "https://www.facebook.com/profile.php?id=61593196346193"
EBAY = "https://www.ebay.com/sch/i.html?_ssn=cwright181"
TODAY = datetime.date.today().isoformat()
e = html.escape


def page(path, title, desc, crumbs, body, og_image="/images/og-image.jpg"):
    url = BASE + path
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p} for i, (n, p) in enumerate(crumbs)]}
    crumb_html = " <span>›</span> ".join(
        (f'<a href="{p}">{e(n)}</a>' if i < len(crumbs) - 1 else f'<span aria-current="page">{e(n)}</span>')
        for i, (n, p) in enumerate(crumbs))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:site_name" content="On-Cards.com">
  <meta property="og:image" content="{BASE}{og_image}">
  <meta property="og:url" content="{url}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#05070d">
  <link rel="icon" type="image/png" sizes="32x32" href="/images/icon-32.png">
  <link rel="apple-touch-icon" href="/images/icon-180.png">
  <link rel="preload" href="/assets/fonts/anton.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/assets/style.css?v={V}">
  <script type="application/ld+json">{json.dumps(bc)}</script>
</head>
<body class="subpage">
  <header class="nav" id="top">
    <div class="wrap nav-inner">
      <a href="/" class="brand" aria-label="Outta Nowhere Cards home">
        <img src="/images/logo-112.png" alt="Outta Nowhere Cards logo" width="56" height="56">
        <span>Outta Nowhere <em>Cards</em></span>
      </a>
      <button class="nav-toggle" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>
      <nav class="nav-links" aria-label="Main">
        <a href="/#ondeck">On Deck</a>
        <a href="/#ebay">eBay</a>
        <a href="/hits/">Hits</a>
        <a href="/card-breaks/">Breaks</a>
        <a href="/#join">How to Join</a>
        <a href="/#faq">FAQ</a>
        <a class="btn btn-whatnot btn-sm js-whatnot" href="{WHATNOT}" target="_blank" rel="noopener">Watch Live</a>
      </nav>
    </div>
  </header>
  <main>
    <section class="page-hero">
      <div class="wrap narrow">
        <nav class="crumbs" aria-label="Breadcrumb">{crumb_html}</nav>
{body}
  </main>
  <footer class="footer">
    <div class="wrap footer-inner">
      <div>
        <strong>Outta Nowhere Cards</strong> · On-Cards.com<br>
        <span class="handle">@outta_nowhere_cards</span> on Whatnot &amp; Facebook<br>
        <a href="mailto:info@on-cards.com">info@on-cards.com</a>
      </div>
      <nav class="footer-links" aria-label="More pages">
        <a href="/">Home</a> · <a href="/hits/">Hits</a> · <a href="/card-breaks/">What is a card break?</a> ·
        <a href="/team-breaks/">Team breaks</a> · <a href="/random-breaks/">Random breaks</a> ·
        <a href="/2026-topps-allen-and-ginter/">2026 Allen &amp; Ginter</a>
      </nav>
      <div class="fine">
        &copy; <span id="year">2026</span> Outta Nowhere Cards. All rights reserved.<br>
        Whatnot and Facebook are trademarks of their respective owners. ONC is an independent seller.
      </div>
    </div>
  </footer>
  <script src="/assets/main.js?v={V}"></script>
</body>
</html>
"""


def cta(text="Catch the next break live on Whatnot"):
    return f"""        <div class="cta-box">
          <h2>{e(text)}</h2>
          <p>Follow <strong>outta_nowhere_cards</strong> and turn on alerts so you know the second we go live. Show announcements and hits land on Facebook first.</p>
          <div class="btn-row center">
            <a class="btn btn-whatnot btn-lg js-whatnot" href="{WHATNOT}" target="_blank" rel="noopener"><span class="live-dot"></span> Follow on Whatnot</a>
            <a class="btn btn-blue btn-lg js-facebook" href="{FACEBOOK}" target="_blank" rel="noopener"><span>Follow on Facebook</span></a>
          </div>
        </div>"""


# ---------------- hits ----------------
def build_hit_images(hits):
    for wk in hits:
        for h in wk["hits"]:
            src = os.path.join(MEDIA, h["photo"])
            d = os.path.join(SITE, "images", "hits", wk["date"]); os.makedirs(d, exist_ok=True)
            im = Image.open(src).convert("RGB")
            card = im.crop(tuple(h["card_rect"])).resize((600, 750), Image.LANCZOS)
            card.save(os.path.join(d, f'{h["slug"]}-card.webp'), "WEBP", quality=78, method=6)
            card.save(os.path.join(d, f'{h["slug"]}-card.jpg'), "JPEG", quality=80, optimize=True, progressive=True)
            full = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
            full.save(os.path.join(d, f'{h["slug"]}.jpg'), "JPEG", quality=80, optimize=True, progressive=True)
            h["_card"] = f'/images/hits/{wk["date"]}/{h["slug"]}-card'
            h["_full"] = f'/images/hits/{wk["date"]}/{h["slug"]}.jpg'


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%A, %B ") + str(d.day) + d.strftime(", %Y")


def hit_card(h, wk, heading="h3"):
    alt = f'{wk["product"]} {h["player"]} {h["card"]} pulled live by Outta Nowhere Cards'
    return f"""          <figure class="hit-card">
            <a href="{h['_full']}" target="_blank" rel="noopener" aria-label="Full photo: {e(h['player'])}">
              <picture>
                <source srcset="{h['_card']}.webp" type="image/webp">
                <img src="{h['_card']}.jpg" width="600" height="750" loading="lazy" alt="{e(alt)}">
              </picture>
            </a>
            <figcaption>
              <{heading}>{e(h['player'])}</{heading}>
              <p class="hit-card-desc">{e(h['card'])}</p>
              <p class="hit-card-meta">{e(wk['product'])} · {e(h['team'])} spot</p>
            </figcaption>
          </figure>"""


def hits_page(hits):
    weeks = sorted(hits, key=lambda w: w["date"], reverse=True)
    secs = []
    for wk in weeks:
        cards = "\n".join(hit_card(h, wk) for h in wk["hits"])
        secs.append(f"""        <section class="hit-week" id="hits-{wk['date']}">
          <h2>{e(nice_date(wk['date']))}</h2>
          <p class="hit-week-sub">{e(wk['break'])} · {e(wk['format'])} · <a href="{wk['product_url']}">{e(wk['product'])}</a></p>
          <div class="hits-grid">
{cards}
          </div>
        </section>""")
    names = ", ".join(h["player"] for h in weeks[0]["hits"])
    body = f"""        <h1 class="page-title"><span>Hits</span> pulled live</h1>
        <p class="page-lede">Every big pull from Outta Nowhere Cards breaks, ripped live on Whatnot. Autos, relics, numbered parallels and rookies. Tap a card for the full photo.</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap">
{chr(10).join(secs)}
{cta("Want the next hit to be yours?")}
      </div>
    </section>"""
    return page("/hits/", "Card Break Hits | Outta Nowhere Cards",
                f"Hits pulled live in Outta Nowhere Cards breaks on Whatnot, newest first. Latest: {names}.",
                [("Home", "/"), ("Hits", "/hits/")], body,
                og_image=weeks[0]["hits"][0]["_full"])


def latest_hits_strip(hits):
    wk = sorted(hits, key=lambda w: w["date"], reverse=True)[0]
    cards = "\n".join(hit_card(h, wk) for h in wk["hits"][:3])
    return f"""    <!-- LATEST HITS (generated by onc-media/tools/site_pages.py) -->
    <section class="latest-hits" id="hits">
      <div class="wrap">
        <h2 class="section-title"><span>Latest</span> hits</h2>
        <p class="section-sub">Pulled live {e(nice_date(wk['date']))} in {e(wk['product'])} {e(wk['format'].lower())}.</p>
        <div class="hits-grid">
{cards}
        </div>
        <div class="btn-row center"><a class="btn btn-blue btn-lg" href="/hits/"><span>See all hits</span></a></div>
      </div>
    </section>
    <!-- /LATEST HITS -->"""


# ---------------- guide pages ----------------
def faq(items):
    return "\n".join(f"""        <details>
          <summary>{e(q)}</summary>
          <p>{a}</p>
        </details>""" for q, a in items)


def card_breaks_page():
    body = f"""        <h1 class="page-title">What is a <span>card break?</span></h1>
        <p class="page-lede">A card break is when sealed boxes of trading cards are opened live on camera and the cards are split among the buyers. Here's how breaks work at Outta Nowhere Cards, and how to jump in on your first one.</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap narrow prose">
        <h2>How a break works</h2>
        <p>Instead of buying a whole box yourself, you buy a <strong>spot</strong> in the break. When the spots are filled, the boxes get opened live, start to finish, and every card goes to the spot it belongs to. You see every pull the moment it happens. No edits.</p>
        <p>Breaks let you chase big cards from high-end product for a fraction of the cost of a full box, and they're a lot more fun with a live chat full of collectors pulling for the same hits.</p>

        <h2>Break formats on ONC shows</h2>
        <div class="break-grid two">
          <article class="break-card">
            <h3><a href="/team-breaks/">Team breaks</a></h3>
            <p>Buy a specific team and get every card for that team pulled from the box. ONC sells teams one at a time, so you get your team, not a pairing, unless you ask for a combo.</p>
          </article>
          <article class="break-card">
            <h3><a href="/random-breaks/">Random team breaks</a></h3>
            <p>Grab a spot at a lower price and get a team assigned at random, live on stream. Could be a sleeper, could be the hit of the morning.</p>
          </article>
          <article class="break-card">
            <h3>Treasure Box Pull</h3>
            <p>A tiered pull. You pull your card live, and if you land the right tier, you level up to the next box for a shot at something bigger.</p>
          </article>
          <article class="break-card">
            <h3>Singles &amp; sudden death auctions</h3>
            <p>Want one specific card? Bid on singles throughout the show. Sudden death auctions move fast: the last bid standing when the timer hits zero takes it.</p>
          </article>
        </div>

        <h2>Card break terms</h2>
        <dl class="terms">
          <dt>Hit</dt><dd>The big cards in a box: autographs, relics (cards with a piece of game-used jersey or bat) and low-numbered parallels.</dd>
          <dt>Numbered card (/50, /150)</dt><dd>A card stamped with a serial number, like 16/50, meaning only 50 exist.</dd>
          <dt>Parallel</dt><dd>A version of a base card with a different color or finish, often numbered.</dd>
          <dt>Rookie card (RC)</dt><dd>A player's first year of cards, usually the most collected.</dd>
          <dt>Hobby box</dt><dd>The version of a product sold through hobby shops, usually with guaranteed hits.</dd>
          <dt>Spot</dt><dd>Your place in a break: a team, a random team, or a pull.</dd>
        </dl>

        <h2>How to join your first break</h2>
        <ol class="plain-steps">
          <li>Download the free Whatnot app, or watch at whatnot.com.</li>
          <li>Search <strong>outta_nowhere_cards</strong>, follow, and turn on alerts.</li>
          <li>When a show is live, buy a spot in the break or bid on a single.</li>
          <li>Watch your cards get ripped live. Everything is checked out and paid for in Whatnot, and your cards are sent to the address on your Whatnot account.</li>
        </ol>
        <p>See what's on deck on the <a href="/#ondeck">homepage</a>, and check out recent pulls on the <a href="/hits/">Hits page</a>.</p>

        <h2>Questions</h2>
{faq([
    ("Do I need to be watching to get my cards?", "To bid in an auction or grab a spot, you need to be in the live show. Once you own a spot, the cards are yours whether you stay to watch or not."),
    ("What sports do you break?", "Any card, any sport: baseball, football, basketball and more, plus non-sports and celebrity cards when a product has them. Product changes show to show."),
    ("How do I contact ONC?", 'Email <a href="mailto:info@on-cards.com">info@on-cards.com</a>, or message us on Facebook or Whatnot.'),
])}
{cta()}
      </div>
    </section>"""
    return page("/card-breaks/", "What Is a Card Break? How Live Breaks Work | Outta Nowhere Cards",
                "How live sports card breaks work: team breaks, random team breaks, Treasure Box Pulls and singles, plus card break terms and how to join your first break on Whatnot.",
                [("Home", "/"), ("What is a card break?", "/card-breaks/")], body)


def team_breaks_page():
    body = f"""        <h1 class="page-title"><span>Team breaks</span> on Whatnot</h1>
        <p class="page-lede">Pick your team, watch the boxes get ripped live, and get every card for your team. Here's how team breaks work at Outta Nowhere Cards.</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap narrow prose">
        <h2>How it works</h2>
        <ol class="plain-steps">
          <li><strong>Buy a team.</strong> Each team in the break is sold as its own spot during the live show on Whatnot.</li>
          <li><strong>We rip the product live.</strong> Every pack is opened on camera, start to finish.</li>
          <li><strong>You get every card for your team.</strong> Base, rookies, inserts, parallels and hits. If it's your team, it's yours.</li>
        </ol>

        <h2>One team per spot</h2>
        <p>ONC sells teams <strong>one at a time</strong>. You get your team, not a pairing with a weaker team, unless you specifically ask for a combo. It keeps it simple and fair: you know exactly what you're buying.</p>

        <h2>Why collectors like team breaks</h2>
        <ul class="checks">
          <li>Chase your favorite team or player collection (PC) in high-end product</li>
          <li>Pay for one team instead of a whole box</li>
          <li>Every card for your team, not just the hits</li>
          <li>Live on camera, so you see every pull</li>
        </ul>

        <h2>What we break</h2>
        <p>Any card, any sport. Recent team and random breaks include <a href="/2026-topps-allen-and-ginter/">2026 Topps Allen &amp; Ginter</a>. Product changes show to show. Check <a href="/#ondeck">On Deck</a> or follow ONC on Whatnot and Facebook to see what's next.</p>

        <h2>Questions</h2>
{faq([
    ("How much is a team?", "Team prices depend on the product and the team, and they're set during the show on Whatnot. Follow outta_nowhere_cards to see the lineup before it goes live."),
    ("What if my team doesn't hit?", "Every card for your team is yours, hit or not. That's part of breaking: some teams hit, some don't, and every pack is opened on camera so you see it all."),
    ("Can I buy two teams together?", "Yes, just ask in the chat. Teams are sold one at a time by default, and combos are available when you request one."),
])}
{cta("Grab your team at the next break")}
      </div>
    </section>"""
    return page("/team-breaks/", "Team Breaks: How Live Sports Card Team Breaks Work | Outta Nowhere Cards",
                "Buy a team, watch the boxes ripped live on Whatnot, and get every card for your team. How team breaks work at Outta Nowhere Cards, one team per spot.",
                [("Home", "/"), ("What is a card break?", "/card-breaks/"), ("Team breaks", "/team-breaks/")], body)


def random_breaks_page(hits):
    wk = sorted(hits, key=lambda w: w["date"], reverse=True)[0]
    recent = ", ".join(f'{h["player"]} ({h["card"].lower()}, {h["team"]} spot)' for h in wk["hits"])
    body = f"""        <h1 class="page-title"><span>Random team</span> breaks</h1>
        <p class="page-lede">Lower-priced spots, teams assigned live on stream. Here's how random team breaks work at Outta Nowhere Cards.</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap narrow prose">
        <h2>How it works</h2>
        <ol class="plain-steps">
          <li><strong>Grab a spot.</strong> Random spots cost less than picking a specific team.</li>
          <li><strong>Teams are assigned live.</strong> Once the spots are filled, each spot gets its team at random, on stream for everyone to see.</li>
          <li><strong>We rip the product.</strong> Every card for your assigned team is yours: base, rookies, parallels and hits.</li>
        </ol>

        <h2>Why go random?</h2>
        <ul class="checks">
          <li>Cheaper way into high-end product</li>
          <li>Every spot has a shot at the hit of the break</li>
          <li>Sleepers happen: smaller teams can land the big card</li>
        </ul>

        <h2>Special spots</h2>
        <p>Some products include cards that don't belong to a team. In <a href="/2026-topps-allen-and-ginter/">2026 Topps Allen &amp; Ginter</a>, which has celebrity and non-sports cards, the break includes a <strong>Non-Sports / Celebs</strong> spot, and we sometimes save one spot for the end of the break to keep the energy up all the way through.</p>

        <h2>Recent random break hits</h2>
        <p>From our {e(wk['product'])} random team breaks on {e(nice_date(wk['date']))}: {e(recent)}. See them all on the <a href="/hits/">Hits page</a>.</p>

        <h2>Questions</h2>
{faq([
    ("How are teams assigned?", "Teams are assigned at random, live on stream, after the spots are filled, so everyone sees the result at the same time."),
    ("Is a random spot cheaper than a team break?", "Usually, yes. Exact spot prices depend on the product and are set during the show on Whatnot."),
    ("What sports do you run random breaks for?", "Any sport, plus non-sports when a product has them. Follow outta_nowhere_cards on Whatnot to see the next lineup."),
])}
{cta("Grab a random spot at the next break")}
      </div>
    </section>"""
    return page("/random-breaks/", "Random Team Breaks: How They Work | Outta Nowhere Cards",
                "Grab a lower-priced spot and get a team assigned live on stream. How random team breaks work at Outta Nowhere Cards, with recent hits from our Whatnot breaks.",
                [("Home", "/"), ("What is a card break?", "/card-breaks/"), ("Random breaks", "/random-breaks/")], body)


def ag_page(hits):
    ag = [w for w in hits if "Allen & Ginter" in w["product"]]
    ag_cards = "\n".join(hit_card(h, w) for w in sorted(ag, key=lambda w: w["date"], reverse=True) for h in w["hits"])
    body = f"""        <h1 class="page-title">2026 Topps <span>Allen &amp; Ginter</span> breaks</h1>
        <p class="page-lede">Minis, celebrity autographs, rip cards and a deep rookie class. Here's what's in 2026 Topps Allen &amp; Ginter, and what we've pulled from it live on Whatnot.</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap narrow prose">
        <h2>What's in a hobby box</h2>
        <ul class="checks">
          <li>Released October 7, 2026</li>
          <li>24 packs per box, 8 cards per pack, 12 boxes per case</li>
          <li>2 hits per hobby box: autograph, relic, rip card or printing plate</li>
          <li>300-card base set, plus minis, inserts and parallels</li>
        </ul>

        <h2>What makes A&amp;G different</h2>
        <p>Allen &amp; Ginter mixes baseball with celebrities and non-sports subjects. The checklist includes framed mini autographs, full-size autographs, relics, and <strong>rip cards</strong>: hobby-exclusive cards you can keep sealed or tear open for an exclusive mini inside. Parallels include Foil Filigree (Blue /150, Green /99, Gold /50, Orange /25, Black /10, Red /5 and 1/1s), along with Chrome, mini metal, stained glass and wood minis.</p>
        <p>The rookie class includes Munetaka Murakami, Kyle Teel, Bryce Eldridge, Carson Benge, Justin Crawford, Owen Caissie and Trey Yesavage.</p>
        <p class="source-note">Product details from the published 2026 Topps Allen &amp; Ginter checklist (via <a href="https://www.checklistinsider.com/2026-topps-allen-ginter-baseball" target="_blank" rel="noopener">Checklist Insider</a>); the checklist is subject to change.</p>

        <h2>How we break A&amp;G</h2>
        <p>We run 2026 Allen &amp; Ginter in <a href="/random-breaks/">random team breaks</a> and <a href="/team-breaks/">team breaks</a> at Cheap Sunday Morning Breaks on Whatnot. Because A&amp;G has celebrity and non-sports cards, the break includes a <strong>Non-Sports / Celebs</strong> spot alongside the MLB teams.</p>

        <h2>A&amp;G hits pulled live at ONC</h2>
      </div>
      <div class="wrap">
        <div class="hits-grid">
{ag_cards}
        </div>
      </div>
      <div class="wrap narrow prose">
{cta("Catch the next A&G break live")}
      </div>
    </section>"""
    return page("/2026-topps-allen-and-ginter/", "2026 Topps Allen & Ginter Breaks | Outta Nowhere Cards",
                "2026 Topps Allen & Ginter hobby box breakdown (24 packs, 2 hits per box), checklist highlights, and the hits we've pulled live in ONC team and random breaks on Whatnot.",
                [("Home", "/"), ("What is a card break?", "/card-breaks/"), ("2026 Topps Allen & Ginter", "/2026-topps-allen-and-ginter/")], body,
                og_image=ag[0]["hits"][0]["_full"] if ag else "/images/og-image.jpg")


def write(rel, text):
    p = os.path.join(SITE, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(text); print("wrote", rel)


def main():
    hits = json.load(open(os.path.join(MEDIA, "site", "hits.json")))
    build_hit_images(hits)
    write("hits/index.html", hits_page(hits))
    write("card-breaks/index.html", card_breaks_page())
    write("team-breaks/index.html", team_breaks_page())
    write("random-breaks/index.html", random_breaks_page(hits))
    write("2026-topps-allen-and-ginter/index.html", ag_page(hits))
    # homepage latest-hits strip
    idx = os.path.join(SITE, "index.html"); s = open(idx).read()
    strip = latest_hits_strip(hits)
    a, b = "    <!-- LATEST HITS", "    <!-- /LATEST HITS -->"
    if a in s:
        s = s[:s.index(a)] + strip + s[s.index(b) + len(b):]
    else:
        anchor = "    <!-- ===================== PILLARS ===================== -->"
        s = s.replace(anchor, strip + "\n\n" + anchor, 1)
    open(idx, "w").write(s); print("updated index.html latest hits")
    # sitemap
    pages = ["/", "/hits/", "/card-breaks/", "/team-breaks/", "/random-breaks/", "/2026-topps-allen-and-ginter/"]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in pages:
        sm += f'  <url><loc>{BASE}{p}</loc><lastmod>{TODAY}</lastmod><priority>{"1.0" if p == "/" else "0.8"}</priority></url>\n'
    sm += "</urlset>\n"
    write("sitemap.xml", sm)


if __name__ == "__main__":
    main()
