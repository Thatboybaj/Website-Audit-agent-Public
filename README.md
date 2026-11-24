# AuditPilot — SEO + AI search (AEO) audits

AuditPilot audits any website for **search engines (SEO)** and **AI answer engines (AEO)** — ChatGPT search, Perplexity, Claude, Google AI Overviews, Bing Copilot — in about a minute.

- **Free:** full SEO audit (10 areas, 70+ checks), health score, action plan, PDF/HTML report, and an AI-search readiness *score* as a teaser.
- **Pro:** the full AEO audit (9 categories, 40+ checks), AI crawler + firewall test, AI answer visibility test, ready-to-paste fixes (llms.txt, schema, robots.txt), AI-written summary and outreach email, competitor comparison, white-label PDFs.

Pro is unlocked with **access codes** for now (no payment gateway yet). Paid detail is removed **on the server**, so it never reaches a free user's browser.

---

## What's checked

**SEO (free)** — Technical SEO · Performance · Mobile · On-page SEO · UX · Conversion · Content · Security · Accessibility · Analytics. New in v2: soft-404 handling, www/non-www consolidation, structured-data validity, favicon, hreflang, broken images, security.txt.

**AEO (Pro)**

| # | Category | What it checks |
|---|---|---|
| 1 | AI Crawler Access | robots.txt rules for 14 AI crawlers (search vs live-fetch vs training), **live requests as each bot** to catch CDN/firewall blocks, noindex/noai |
| 2 | AI Discoverability | llms.txt (emerging, optional standard), llms-full.txt, sitemap + lastmod |
| 3 | Structured Data for AI | Organization/LocalBusiness (+sameAs), WebSite, FAQPage, Article (author + dates), Breadcrumb, Service/Product |
| 4 | Answer-Ready Content | question-led headings, answer-first paragraphs, lists/tables, a quotable definition, depth, specific facts |
| 5 | Entity & Trust (E-E-A-T) | About page, NAP/contact, profiles across the web, reviews, named authors, cited sources, consistent brand name |
| 6 | Freshness | machine-readable dates, recency, copyright year |
| 7 | AI-Readable Rendering | % of content in raw HTML vs rendered (AI crawlers mostly don't run JS), H1 in HTML, response speed, alt text |
| 8 | Snippet & Citation Controls | nosnippet / max-snippet, data-nosnippet, Open Graph, canonical, quotable summary |
| 9 | Brand Clarity for AI | Claude reads the homepage like an answer engine: clarity score, missing facts, how AI would describe you |

**AI answer visibility test (Pro)** — asks real answer engines (Claude with web search, Perplexity Sonar) the questions buyers ask, then reports share of voice, citations vs mentions, and which competitors get cited instead.

**Generated fixes (Pro)** — llms.txt, robots.txt AI-crawler block, Organization + WebSite + FAQPage JSON-LD, a quotable intro sentence. Built only from facts on the site (AI drafts are labelled for review).

---

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env          # add keys (all optional)
uvicorn api.index:app --reload   # open http://127.0.0.1:8000
```

CLI:
```bash
python -m audit_agent example.com                    # SEO + AEO, HTML/MD/JSON in ./reports
python -m audit_agent example.com --visibility       # + AI answer visibility test
python -m audit_agent example.com --no-aeo           # SEO only
python -m audit_agent --batch prospects.txt --format json
```

Tests (no network or keys needed): `pytest -q`

## Selling it (before a payment gateway)

1. Put codes in `PRO_CODES` (e.g. `PRO-AMAKA-7Q2,PRO-STUDIO-K9`).
2. Customer clicks **Request access** → the form goes to `LEAD_WEBHOOK_URL` (and Vercel logs).
3. You take payment however you like, then send them the code **or a magic link**: `https://your-app/?code=PRO-AMAKA-7Q2`.
4. Later: set `CHECKOUT_URL` to your Lemon Squeezy/Paystack/Stripe link and have its webhook add codes (or user plans in Supabase). The app's `plans.py` is the only place that changes.

## Deploy

**Vercel** (current): push to GitHub → Vercel redeploys. Add env vars in Settings → Environment Variables, then Redeploy. On Vercel there's no headless browser: tap-target/contrast/screenshot checks and the raw-vs-rendered comparison fall back to HTML heuristics, and PDF uses the print dialog.

**Full features** (browser checks + real PDF files): Railway / Render / Fly.io
```
pip install -r requirements.txt && playwright install --with-deps chromium
uvicorn api.index:app --host 0.0.0.0 --port $PORT
```

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/` | web app · `/?url=site.com` auto-runs · `/?code=…` unlocks Pro |
| GET | `/embed` | iframe audit form for your site/portfolio |
| POST | `/api/run` | `{url, pages, ai}` → report redacted to the caller's plan (`x-pro-code` header / owner bearer token) |
| POST | `/api/visibility` | Pro · `{url, brand, questions[]}` |
| POST | `/api/unlock` · `/api/lead` | code check · lead capture |
| POST | `/render` · `/pdf` | `{report, branding}` → HTML / PDF (white-label for Pro) |
| POST | `/audit` · GET `/report` · GET `/health` | owner/integrations |

## Limits to be honest about

- In-memory rate limits reset when Vercel starts a new instance — fine for launch, move to a database with accounts later.
- Bot probes imitate each crawler's user agent; firewalls that verify crawler IPs may treat the real bots differently.
- llms.txt is an emerging proposal; no major engine has confirmed using it for ranking, so it's weighted low.
- AI visibility answers vary run to run; treat share of voice as a trend, not an exact number.
