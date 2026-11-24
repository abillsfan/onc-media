# ONC blog (on-cards.com/blog/)

Short reads for collectors, built by `tools/site_pages.py` from `site/blog.json`. Carl's rules (Nov 23, 2026):
- **Short:** 200–450 words, a 1–3 minute read. Entertaining and informative, Southern-casual ONC voice.
- **Card-focused, never general sports news.** Tie sports news to cards: hot rookies and their key rookie cards, what's
  releasing this week, ONC show recaps with real hits, what's moving in the hobby. Google penalizes mass-produced
  low-value posts, so one or two good posts a week beats a daily post.
- **Carl approves every post, or lets it auto-publish.** New posts are added with `"status": "draft"` and
  `"drafted_at"` (ISO time with offset); only `"published"` posts go live. Carl (Nov 23, 2026): if he hasn't replied
  within 12 hours, publish it. If he replies "hold" (or anything other than approval), set `"status": "hold"` so it
  never auto-publishes; if he asks for changes, apply them and keep it a draft until he approves or 12 hours pass.
  The "ONC Blog Auto-Publish" scheduled task (Mondays ~7:13 AM CT) publishes drafts at least 12 hours old.
- **Facts only:** release dates from site/releases.json (credit the source), hits only from site/hits.json, no invented
  prices, buyers, products or show times. No shipping/packaging talk. Don't promise ONC will break a product unless
  Whatnot shows it.
- Every post links to at least one ONC page (release calendar, a product page, /hits/) and to /alerts/.

## Post format (site/blog.json)
```json
{"slug": "kebab-case-unique", "title": "Under ~65 characters, the search phrase first", "date": "YYYY-MM-DD",
 "drafted_at": "2026-11-29T18:05:00-06:00",
 "description": "1–2 sentence summary (shown on cards and in Google)", "status": "draft",
 "tags": ["releases"], "image": "/images/... (optional)", "body": "Markdown subset"}
```
Body: paragraphs separated by a blank line, `## ` and `### ` headings, `- ` bullet lists, `**bold**`,
`[text](/path/ or https://...)` links. Nothing else.

## Publish
Set `"status": "published"`, run `python3 -I tools/site_pages.py /home/claude/onc-website`, commit and push both repos.
