"""Builds the extra pages of on-cards.com into the onc-website repo.

Usage:
    python3 tools/site_pages.py /home/claude/onc-website

Writes:
  hits/index.html                      - every hit from site/hits.json, newest first (+ resized photos)
  card-breaks/index.html               - "What is a card break?" guide
  team-breaks/index.html               - how ONC team breaks work
  random-breaks/index.html             - how ONC random team breaks work
  what-we-break/index.html             - product library hub (site/products.json)
  <product-slug>/index.html            - one page per product broken (site/products.json + hits)
  release-calendar/index.html          - upcoming releases (site/releases.json, refreshed weekly)
  and the "Latest hits" strip + Whatnot stats badge on the homepage (between the LATEST HITS markers in index.html)
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
V = "20261019so"  # asset version tag; bump when style.css/main.js change
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
  <link rel="preload" href="/assets/fonts/barlow-400.woff2" as="font" type="font/woff2" crossorigin>
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
        <a href="/release-calendar/">Releases</a>
        <a href="/card-breaks/">Breaks</a>
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
        <a href="/">Home</a> · <a href="/hits/">Hits</a> · <a href="/card-breaks/">What is a card break?</a> · <a href="/break-rules/">Break rules &amp; FAQ</a> ·
        <a href="/team-breaks/">Team breaks</a> · <a href="/random-breaks/">Random breaks</a> ·
        <a href="/what-we-break/">What we break</a> · <a href="/release-calendar/">Release calendar</a>
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
            <p>Grab a spot at a lower price and get a team from Whatnot's random wheel, live on stream. Could be a sleeper, could be the hit of the morning.</p>
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
        <p>See the full <a href="/break-rules/">break rules &amp; FAQ</a>, what's on deck on the <a href="/#ondeck">homepage</a>, and recent pulls on the <a href="/hits/">Hits page</a>.</p>

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
          <li><strong>You get every card for your team.</strong> Base, rookies, inserts, parallels and hits. All cards ship, base included.</li>
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
        <p>Any card, any sport, and the product changes show to show. See every product we've broken in <a href="/what-we-break/">What we break</a>, what's coming out in the <a href="/release-calendar/">release calendar</a>, and what's next on <a href="/#ondeck">On Deck</a>.</p>

        <h2>Questions</h2>
{faq([
    ("How much is a team?", "Team prices depend on the product and the team, and they're set during the show on Whatnot. Follow outta_nowhere_cards to see the lineup before it goes live."),
    ("When does my break run?", "During a scheduled show on Whatnot. Follow outta_nowhere_cards and turn on alerts to catch it. Full details in the <a href=\"/break-rules/\">break rules</a>."),
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
          <li><strong>Teams are assigned live.</strong> Once the spots are filled, each spot gets its team from Whatnot's random wheel, on stream for everyone to see.</li>
          <li><strong>We rip the product.</strong> Every card for your assigned team is yours: base, rookies, parallels and hits.</li>
        </ol>

        <h2>Why go random?</h2>
        <ul class="checks">
          <li>Cheaper way into high-end product</li>
          <li>Every spot has a shot at the hit of the break</li>
          <li>Sleepers happen: smaller teams can land the big card</li>
        </ul>

        <h2>Special spots</h2>
        <p>Some products include cards that don't belong to a team. When a product has celebrity or non-sports cards, like <a href="/2026-topps-allen-and-ginter/">2026 Topps Allen &amp; Ginter</a>, the break includes a <strong>Non-Sports / Celebs</strong> spot, and we sometimes save one spot for the end of the break to keep the energy up all the way through.</p>

        <h2>Recent random break hits</h2>
        <p>From our {e(wk['product'])} random team breaks on {e(nice_date(wk['date']))}: {e(recent)}. See them all on the <a href="/hits/">Hits page</a>.</p>

        <h2>Questions</h2>
{faq([
    ("How are teams assigned?", "With Whatnot's random wheel, live on stream after the spots are filled, so everyone sees the result at the same time. See the full <a href=\"/break-rules/\">break rules</a>."),
    ("Is a random spot cheaper than a team break?", "Usually, yes. Exact spot prices depend on the product and are set during the show on Whatnot."),
    ("What sports do you run random breaks for?", "Any sport, plus non-sports when a product has them. Follow outta_nowhere_cards on Whatnot to see the next lineup."),
])}
{cta("Grab a random spot at the next break")}
      </div>
    </section>"""
    return page("/random-breaks/", "Random Team Breaks: How They Work | Outta Nowhere Cards",
                "Grab a lower-priced spot and get a team assigned live on stream. How random team breaks work at Outta Nowhere Cards, with recent hits from our Whatnot breaks.",
                [("Home", "/"), ("What is a card break?", "/card-breaks/"), ("Random breaks", "/random-breaks/")], body)


def product_page(prod, hits):
    weeks = sorted([w for w in hits if w["product"] == prod["name"]], key=lambda w: w["date"], reverse=True)
    cards = "\n".join(hit_card(h, w) for w in weeks for h in w["hits"])
    dates = ", ".join(nice_date(w["date"]) for w in weeks)
    facts = "\n".join(f"          <li>{e(f)}</li>" for f in prod.get("facts", []))
    about = "\n".join(f"        <p>{a}</p>" for a in prod.get("about", []))
    src = prod.get("source")
    src_html = (f'        <p class="source-note">Product details from the published {e(prod["name"])} checklist (via <a href="{src["url"]}" target="_blank" rel="noopener">{e(src["name"])}</a>); the checklist is subject to change.</p>' if src else "")
    hits_html = (f"""        <h2>Hits we pulled live</h2>
        <p>{e(prod['name'])} breaks on {e(dates)}.</p>
      </div>
      <div class="wrap">
        <div class="hits-grid">
{cards}
        </div>
      </div>
      <div class="wrap narrow prose">""" if weeks else "")
    body = f"""        <h1 class="page-title">{e(prod['name'])} <span>breaks</span></h1>
        <p class="page-lede">{e(prod['lede'])}</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap narrow prose">
{"        <h2>What's in a hobby box</h2>" + chr(10) + '        <ul class="checks">' + chr(10) + facts + chr(10) + "        </ul>" if facts else ""}
{"        <h2>About the product</h2>" + chr(10) + about if about else ""}
{src_html}
        <h2>How we broke it</h2>
        <p>{prod['how']} Formats: {", ".join(f'<a href="/{"random-breaks" if "andom" in f else "team-breaks"}/">{e(f.lower())}</a>' for f in prod['formats'])}.</p>
{hits_html}
        <p>Product changes show to show. See <a href="/what-we-break/">everything we've broken</a> and <a href="/release-calendar/">what's coming out next</a>.</p>
{cta()}
      </div>
    </section>"""
    first = weeks[0]["hits"][0]["_full"] if weeks else "/images/og-image.jpg"
    return page(f"/{prod['slug']}/", f"{prod['name']} Breaks | Outta Nowhere Cards",
                f"{prod['name']}: what's in the box and the hits we pulled live in Outta Nowhere Cards breaks on Whatnot.",
                [("Home", "/"), ("What we break", "/what-we-break/"), (prod["name"], f"/{prod['slug']}/")], body, og_image=first)


def hub_page(products, hits):
    rows = []
    for prod in products:
        weeks = sorted([w for w in hits if w["product"] == prod["name"]], key=lambda w: w["date"], reverse=True)
        n = sum(len(w["hits"]) for w in weeks)
        thumb = weeks[0]["hits"][0]["_card"] if weeks else None
        img = (f'<picture><source srcset="{thumb}.webp" type="image/webp"><img src="{thumb}.jpg" width="600" height="750" loading="lazy" alt="{e(prod["name"])} hit"></picture>' if thumb else "")
        last = nice_date(weeks[0]["date"]) if weeks else ""
        rows.append(f"""          <a class="product-card" href="/{prod['slug']}/">
            {img}
            <div class="product-body">
              <h2>{e(prod['name'])}</h2>
              <p>{e(prod['sport'])} · {e(", ".join(prod['formats']))}</p>
              <p class="muted">{('Last broken ' + e(last)) if last else ''}{(' · ' + str(n) + ' hits on the site') if n else ''}</p>
            </div>
          </a>""")
    body = f"""        <h1 class="page-title">What we <span>break</span></h1>
        <p class="page-lede">Any card. Any sport. Anytime. The product changes show to show, so here's everything we've ripped live on Whatnot, with the hits that came out of it.</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap">
        <div class="product-grid">
{chr(10).join(rows)}
        </div>
      </div>
      <div class="wrap narrow prose">
        <h2>What's next?</h2>
        <p>Check <a href="/#ondeck">On Deck</a> for the next show, and the <a href="/release-calendar/">sports card release calendar</a> for what's coming out from Topps, Bowman and Panini. New to breaks? Start with <a href="/card-breaks/">what a card break is</a>.</p>
{cta()}
      </div>
    </section>"""
    return page("/what-we-break/", "What We Break: Products Ripped Live | Outta Nowhere Cards",
                "Every product Outta Nowhere Cards has broken live on Whatnot, with the hits pulled from each. Baseball, football, basketball and non-sports.",
                [("Home", "/"), ("What we break", "/what-we-break/")], body)


def week_monday(iso):
    d = datetime.date.fromisoformat(iso)
    return d - datetime.timedelta(days=d.weekday())


def short_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.strftime('%a %b ')}{d.day}"


def key_date(i):
    """Where an item sits on the calendar: its pre-order date if it has one, else its release date."""
    return i.get("preorder") or i["date"]


def release_li(i, indent, note=True):
    """One calendar row. Pre-order items show the pre-order date; on/after that date the release date appears too
    (assets/main.js reveals .rc-rel). Rows hide after the release date (data-release-date)."""
    pad = " " * indent
    pre = i.get("preorder")
    tag = '<span class="rc-tag pre">Pre-order</span>' if pre else ""
    rel = (f'<span class="rc-rel" data-show-from="{pre}" hidden>Pre-orders opened {short_date(pre)} &middot; '
           f'Releases <strong>{short_date(i["date"])}</strong></span>') if pre else ""
    nt = f'<span class="rc-note">{e(i["note"])}</span>' if note and i.get("note") else ""
    tp = i.get("topps") or []
    sold = [x["format"] for x in tp if x.get("soldout")]
    if tp and len(sold) == len(tp):
        so = '<span class="rc-sold">Pre-orders sold out on Topps.com</span>'
    elif sold:
        so = f'<span class="rc-sold">Sold out on Topps.com: {e(", ".join(sold))}</span>'
    else:
        so = ""
    return (f"""{pad}<li data-release-date="{i['date']}"><time datetime="{key_date(i)}">{short_date(key_date(i))}</time>
{pad}  <span class="rc-name">{e(i['name'])}</span>
{pad}  <span class="rc-tags">{tag}<span class="rc-tag">{e(i['sport'])}</span><span class="rc-tag brand">{e(i['brand'])}</span></span>{rel}{so}{nt}</li>""")


def release_page(rel):
    today = datetime.date.today()
    items = sorted([i for i in rel["items"] if datetime.date.fromisoformat(i["date"]) >= today - datetime.timedelta(days=1)],
                   key=lambda i: (key_date(i), i["name"]))
    weeks = {}
    for i in items:
        weeks.setdefault(week_monday(key_date(i)), []).append(i)
    secs = []
    for mon, its in weeks.items():
        lis = "\n".join(release_li(i, 12) for i in its)
        secs.append(f"""        <section class="rc-week">
          <h2>Week of {mon.strftime('%B ')}{mon.day}</h2>
          <ul class="rc-list">
{lis}
          </ul>
        </section>""")
    faq_items = [(f"When does {i['name']} come out?",
                  f"{i['name']} is scheduled for {nice_date(i['date'])}, per the {i['source']}. Dates can change.", i["date"])
                 for i in items if i.get("faq")]
    faq_html = "\n".join(f"""        <details data-release-date="{d}">
          <summary>{e(q)}</summary>
          <p>{e(a)}</p>
        </details>""" for q, a, d in faq_items)
    srcs = " and ".join(f'<a href="{x["url"]}" target="_blank" rel="noopener">{e(x["name"])}</a>' for x in rel["sources"])
    checked = nice_date(rel["checked"])
    body = f"""        <h1 class="page-title">Sports card <span>release calendar</span></h1>
        <p class="page-lede">Upcoming Topps, Bowman and Panini releases for baseball, football, basketball, soccer and non-sports, week by week. Updated every week.</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap narrow prose">
        <p class="rc-disclaimer">This is what's coming out in the hobby, not a list of what we're breaking. Product changes show to show, so follow <strong>outta_nowhere_cards</strong> on Whatnot to see which releases we pick up. Dates last checked {e(checked)}.</p>
{chr(10).join(secs)}
        <p class="source-note">Dates from the {srcs}. Release dates often move; check the manufacturer before you buy.</p>

        <h2>Release date questions</h2>
{faq_html}
{faq([
    ("Does Outta Nowhere Cards break every product on this calendar?", "No. This calendar covers what's coming out across the hobby. We pick products show to show; see <a href=\"/what-we-break/\">what we've broken</a> and <a href=\"/#ondeck\">what's on deck</a>."),
    ("How often is the release calendar updated?", "Every week. Past releases drop off automatically."),
])}
{cta("See which releases we rip live")}
      </div>
    </section>"""
    return page("/release-calendar/", "Sports Card Release Calendar: Upcoming Topps, Bowman & Panini | Outta Nowhere Cards",
                "Upcoming sports card release dates for Topps, Bowman and Panini: baseball, football, basketball, soccer and non-sports, week by week. Updated weekly.",
                [("Home", "/"), ("Release calendar", "/release-calendar/")], body)


def stats_badge(st):
    return f"""        <!-- WHATNOT STATS (generated) -->
        <a class="trust-badge" href="{st['url']}/reviews" target="_blank" rel="noopener">
          <span class="stars" aria-hidden="true">★★★★★</span>
          <span><strong>{e(st['rating'])}</strong> on Whatnot</span>
          <span class="dot">·</span><span>{st['reviews']} reviews</span>
          <span class="dot">·</span><span>{e(st['sold'])} sold</span>
          <span class="dot">·</span><span>{st['followers']} followers</span>
        </a>
        <!-- /WHATNOT STATS -->"""


def rules_page():
    body = f"""        <h1 class="page-title">Break <span>rules &amp; FAQ</span></h1>
        <p class="page-lede">How breaks work at Outta Nowhere Cards: how teams are assigned, which cards you get, and when your break runs.</p>
      </div>
    </section>
    <section class="page-body">
      <div class="wrap narrow prose">
        <h2>Quick answers</h2>
        <ul class="checks">
          <li>Random teams are assigned with Whatnot's random wheel, live on stream</li>
          <li>All cards ship, base cards included</li>
          <li>Non-team and non-sports card assignments are announced during the show</li>
          <li>Breaks run during scheduled shows on Whatnot</li>
        </ul>

        <h2>How do breaks work?</h2>
        <p>You buy a spot in a break during a live show on Whatnot. When the spots are filled, the product is opened on camera, start to finish, and each card goes to the spot it belongs to. New to breaks? Read <a href="/card-breaks/">what a card break is</a>.</p>

        <h3>Team breaks</h3>
        <p>Buy a specific team and you get every card for that team. Teams are sold one at a time, so you get your team, not a pairing, unless you ask for a combo. <a href="/team-breaks/">More on team breaks</a>.</p>

        <h3>Random team breaks</h3>
        <p>Buy a spot, and once the spots are filled, teams are assigned with <strong>Whatnot's random wheel</strong>, live on stream so everyone sees the result at the same time. <a href="/random-breaks/">More on random breaks</a>.</p>

        <h2>Which cards do I get?</h2>
        <p><strong>All cards ship</strong>, base cards included. Every card for your team or spot is yours: base, rookies, inserts, parallels and hits.</p>

        <h3>What about cards that don't belong to a team?</h3>
        <p>Some products include non-team cards (like checklists or multi-team cards) or non-sports and celebrity cards. How those are assigned is <strong>announced in the show</strong> before the break, so you know before you buy. Some products, like <a href="/2026-topps-allen-and-ginter/">2026 Topps Allen &amp; Ginter</a>, get their own <strong>Non-Sports / Celebs</strong> spot.</p>

        <h2>When is my break?</h2>
        <p>Breaks run during <strong>scheduled shows</strong> on Whatnot. Follow <strong>outta_nowhere_cards</strong> and turn on alerts so you know when the next show starts; upcoming lineups are posted on <a href="/#ondeck">On Deck</a> and the ONC Facebook page.</p>

        <h2>More questions</h2>
{faq([
    ("Do I need to be watching when my break runs?", "To buy a spot or bid, you need to be in the live show. Once you own a spot, the cards are yours whether you stay to watch or not."),
    ("How do I pay?", "Everything is checked out and paid for in the Whatnot app."),
    ("Where do my cards go?", "To the address on your Whatnot account."),
    ("How do I contact ONC?", 'Email <a href="mailto:info@on-cards.com">info@on-cards.com</a>, or message us on Facebook or Whatnot.'),
])}
{cta()}
      </div>
    </section>"""
    return page("/break-rules/", "Break Rules & FAQ: How ONC Card Breaks Work | Outta Nowhere Cards",
                "Outta Nowhere Cards break rules: random teams assigned with Whatnot's random wheel, all cards ship, non-team card assignments announced in the show, breaks run during scheduled shows.",
                [("Home", "/"), ("What is a card break?", "/card-breaks/"), ("Break rules & FAQ", "/break-rules/")], body)


def write(rel, text):
    p = os.path.join(SITE, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(text); print("wrote", rel)


def reviews_block(rv, st):
    def mask(h):
        return h[0] + "***" + h[-1] if len(h) > 2 else h[0] + "***"
    cards = []
    for r in rv["reviews"]:
        d = datetime.date.fromisoformat(r["date"])
        cards.append(f"""          <figure class="review-card">
            <div class="stars" aria-label="{r['rating']} out of 5 stars">{"★" * int(r['rating'])}</div>
            <blockquote>{e(r['text'])}</blockquote>
            <figcaption>{e(mask(r['handle']))} · Whatnot buyer · {d.strftime('%B %Y')}</figcaption>
          </figure>""")
    return f"""    <!-- REVIEWS (generated by onc-media/tools/site_pages.py from site/reviews.json) -->
    <section class="reviews" id="reviews">
      <div class="wrap">
        <h2 class="section-title"><span>What buyers</span> say</h2>
        <p class="section-sub">{e(st['rating'])} stars from {st['reviews']} reviews on Whatnot. A few of our favorites:</p>
        <div class="review-grid">
{chr(10).join(cards)}
        </div>
        <div class="btn-row center"><a class="btn btn-blue btn-lg" href="{rv['source']}" target="_blank" rel="noopener"><span>Read all {st['reviews']} reviews on Whatnot</span></a></div>
      </div>
    </section>
    <!-- /REVIEWS -->"""


def home_releases_block(rel):
    today = datetime.date.today()
    items = sorted([i for i in rel["items"] if datetime.date.fromisoformat(i["date"]) >= today],
                   key=lambda i: (key_date(i), i["name"]))[:14]
    lis = "\n".join(release_li(i, 10, note=False) for i in items)
    return f"""    <!-- RELEASES (generated by onc-media/tools/site_pages.py from site/releases.json) -->
    <section class="home-releases" id="releases">
      <div class="wrap narrow">
        <h2 class="section-title"><span>Coming out</span> next</h2>
        <p class="section-sub">New Topps, Bowman and Panini releases hitting the hobby. Updated weekly.</p>
        <ul class="rc-list" data-limit="7">
{lis}
        </ul>
        <div class="btn-row center"><a class="btn btn-blue btn-lg" href="/release-calendar/"><span>Full release calendar</span></a></div>
      </div>
    </section>
    <!-- /RELEASES -->"""


def replace_block(s, a, b, new, anchor_after=None, anchor_before=None):
    if a in s:
        return s[:s.index(a)] + new + s[s.index(b) + len(b):]
    if anchor_after:
        i = s.index(anchor_after) + len(anchor_after)
        return s[:i] + "\n" + new + s[i:]
    i = s.index(anchor_before)
    return s[:i] + new + "\n\n" + s[i:]


def main():
    hits = json.load(open(os.path.join(MEDIA, "site", "hits.json")))
    products = json.load(open(os.path.join(MEDIA, "site", "products.json")))
    rel = json.load(open(os.path.join(MEDIA, "site", "releases.json")))
    stats = json.load(open(os.path.join(MEDIA, "site", "stats.json")))
    build_hit_images(hits)
    write("hits/index.html", hits_page(hits))
    write("card-breaks/index.html", card_breaks_page())
    write("team-breaks/index.html", team_breaks_page())
    write("random-breaks/index.html", random_breaks_page(hits))
    write("break-rules/index.html", rules_page())
    write("what-we-break/index.html", hub_page(products, hits))
    for prod in products:
        write(f"{prod['slug']}/index.html", product_page(prod, hits))
    write("release-calendar/index.html", release_page(rel))
    idx = os.path.join(SITE, "index.html"); s = open(idx).read()
    s = replace_block(s, "    <!-- LATEST HITS", "    <!-- /LATEST HITS -->", latest_hits_strip(hits),
                      anchor_before="    <!-- ===================== PILLARS ===================== -->")
    s = replace_block(s, "    <!-- RELEASES", "    <!-- /RELEASES -->", home_releases_block(rel),
                      anchor_before="    <!-- ===================== LIVE ON EBAY ===================== -->")
    rv = json.load(open(os.path.join(MEDIA, "site", "reviews.json")))
    s = replace_block(s, "    <!-- REVIEWS", "    <!-- /REVIEWS -->", reviews_block(rv, stats),
                      anchor_before="    <!-- ===================== PILLARS ===================== -->")
    s = replace_block(s, "        <!-- WHATNOT STATS", "        <!-- /WHATNOT STATS -->", stats_badge(stats),
                      anchor_after='        <p class="kicker">Live on Whatnot · <span>@outta_nowhere_cards</span></p>')
    open(idx, "w").write(s); print("updated index.html (latest hits, Whatnot stats)")
    pages = ["/", "/hits/", "/what-we-break/", "/release-calendar/", "/card-breaks/", "/break-rules/", "/team-breaks/", "/random-breaks/"] + \
            [f"/{p['slug']}/" for p in products]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in pages:
        sm += f'  <url><loc>{BASE}{p}</loc><lastmod>{TODAY}</lastmod><priority>{"1.0" if p == "/" else "0.8"}</priority></url>\n'
    sm += "</urlset>\n"
    write("sitemap.xml", sm)


if __name__ == "__main__":
    main()
