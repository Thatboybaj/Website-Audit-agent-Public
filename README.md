# Website Audit Agent — HTML edition

Audits any website across the **10 core areas** of the Website Audit Cheat Sheet, scores it 0–100, and returns a prioritized action plan, quick wins, an executive summary and a ready-to-send outreach email.

Two editions, same engine:

| | **HTML edition** | **No-HTML edition** |
|---|---|---|
| Output | HTML report (cheat-sheet design, screenshots) + Markdown + JSON | Markdown + JSON |
| Best for | Sending reports to clients/prospects, PDF export (print → Save as PDF) | Lead agent, n8n/Make, Supabase, Framer front end, APIs |
| `/report` endpoint | returns HTML | returns Markdown |
| Extra dependency | Jinja2 | — |

---

## 1. How the agent works

```
URL ─► Crawler ──────────────► SiteData ─► 10 area checks ─► Scoring ─► Action plan ─► Summary + email ─► Report
        • pages (BFS, ≤N)         ▲            (pass/warn/fail     (weighted   (prioritize,   (Claude or
        • robots.txt, sitemap     │             + impact/effort)    health      fix, monitor,  template)
        • link status (404s)      │                                 score)      re-audit,
        • SSL, HTTP→HTTPS         │                                             quick wins)
        • exposed files           │
        • CSS/JS/images           │
       PageSpeed Insights ────────┤  (Lighthouse lab + real-user Core Web Vitals, mobile & desktop)
       Headless browser ──────────┤  (375px + 1366px render: tap targets, contrast, overflow, CTAs, popups, screenshots)
       Claude ────────────────────┘  (copy relevance & clarity)
```

Each data source is optional — the agent degrades gracefully (`--no-psi`, `--no-browser`, `--no-ai`) and marks checks it couldn't run as *skipped* instead of guessing.

## 2. What it checks (all 10 areas)

| # | Area | Checks | Key metric |
|---|---|---|---|
| 1 | Technical SEO | Crawlability & indexing · XML sitemap · Robots.txt · Canonical tags · Noindex pages · 404 errors · Redirect chains | Crawl Errors |
| 2 | Performance | Page speed (Lighthouse) · Core Web Vitals (LCP/CLS/INP-TBT) · Image optimization · Minify CSS/JS · Caching & compression · Server response (TTFB) · Page weight | PageSpeed Score |
| 3 | Mobile Usability | Mobile friendly · Tap targets (24/44px) · Text readability · Viewport settings · No horizontal scroll · Mobile UX flow (CTA in first screen, menu, overlays) | Mobile Usability /100 |
| 4 | On-Page SEO | Title tags (length, duplicates) · Meta descriptions · Header structure · Content depth · Internal linking & orphan pages · Image alt · Open Graph & schema | Optimized Pages % |
| 5 | User Experience | Easy navigation · Clear CTA · Readability (Flesch) · Consistent design (fonts) · Forms & interactions · Low friction (popups, autoplay) | Bounce Risk |
| 6 | Conversion | Value proposition · CTA visibility above the fold · Lead capture · Trust signals · Form length · Checkout flow (e-commerce only) | Conversion Readiness % |
| 7 | Content Quality | Relevant to audience (Claude) · Clear & helpful (Claude) · Up-to-date · Thin/duplicate content · Engaging format · Keyword targeting | Content Score (A+–F) |
| 8 | Security | SSL certificate & expiry · HTTPS redirect · 6 security headers · Vulnerable JS libs, mixed content, version leaks, cookies · CMS plugins & themes · Exposed files (.git, .env, admin) | Security Score /100 |
| 9 | Accessibility | Alt text · Color contrast (WCAG AA) · Keyboard navigation · Readable fonts · ARIA/accessible names · Screen-reader readiness (lang, landmarks) | Accessibility Score (A–F) |
| 10 | Analytics & Tracking | GA4/GTM · Goal tracking · Conversion events & ad pixels · UTM misuse · Heatmaps · Data accuracy (duplicates, coverage, consent) | Tracked Goals % |

## 3. Scoring

- Each check: **pass = 1, warn = 0.5, fail = 0**, weighted by impact (high 3 · medium 2 · low 1). Skipped/info checks don't count.
- Area score = weighted average × 100.
- Overall health score = area scores weighted (Technical SEO, Performance, On-Page 12 · Mobile, Conversion, Content, Security 10 · UX, Accessibility, Analytics 8).
- Bands: **90–100 Excellent · 70–89 Good · 50–69 Needs Improvement · 30–49 Poor · 0–29 Critical**.

## 4. Action plan logic

1. **Prioritize** — priority = impact × severity ÷ effort → high-impact, easy fixes first (top 7).
2. **Fix & optimize** — every open issue grouped by area, with the fix and example URLs.
3. **Test & monitor** — the 10 key metrics as your baseline.
4. **Re-audit** — cadence from score (<50 monthly · 50–79 every 2 months · 80+ quarterly). Run with `--compare old.json` to see deltas.

**Quick wins** map to the cheat sheet: page speed · broken links · images · titles & meta · mobile usability.

## 5. Setup (local)

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium                               # for browser checks (skip with --no-browser)
cp .env.example .env                                      # add keys (all optional)
```

## 6. Usage

```bash
python -m audit_agent https://example.com                       # full audit
python -m audit_agent example.com --pages 50                    # crawl more pages
python -m audit_agent example.com --no-psi --no-browser         # fast mode (~10s)
python -m audit_agent example.com --compare reports/example-com-2026-10-01.json   # re-audit with progress
python -m audit_agent --batch prospects.txt --format json       # audit a prospect list; prints lowest scores first
python -m audit_agent example.com --show-email                  # (HTML edition) include outreach email in the report
```

Reports land in `./reports/<domain>-<date>.{html,md,json}`.

## 7. API (for your lead agent / n8n / Framer)

```bash
uvicorn api.index:app --reload
```

- `GET /health`
- `POST /audit` → JSON report
  ```json
  {"url": "https://example.com", "pages": 15, "psi": true, "browser": true, "ai": true}
  ```
- `GET /report?url=https://example.com&token=...` → HTML (HTML edition) or Markdown

Set `AUDIT_API_TOKEN` and send `Authorization: Bearer <token>`.

**Lead-gen flow:** prospect list → `POST /audit` → store `overall_score`, `action_plan.prioritize`, `outreach_email` in Supabase → low scores = warm leads → send email with the HTML report link.

## 8. Deploy

**Vercel (quick, no headless browser):** push the folder to GitHub → import in Vercel → add env vars → deploy. Browser checks auto-disable on Vercel; PSI still covers tap targets/contrast via Lighthouse. `maxDuration` is set to 300s (needs a plan that allows it; keep `pages` ≤ 15 on Hobby).

**Full features (browser checks):** deploy to Railway/Render/Fly.io with:
```
pip install -r requirements.txt && playwright install --with-deps chromium
uvicorn api.index:app --host 0.0.0.0 --port $PORT
```

## 9. Tests

```bash
pytest -q          # audits the bundled fixture site (tests/fixture_site) with known issues
```

## 10. Limits (honest)

- Bounce rate and conversion rate need analytics access — the agent reports *Bounce Risk* and *Conversion Readiness* instead.
- Goal tracking set up inside GTM can't be seen from outside; it's flagged as "verify".
- JavaScript-only sites (some SPAs) need the browser mode for accurate content checks; the crawler reads server HTML. Framer and Webflow sites are server-rendered and work fully.
- Only audit sites you own or are pitching; the crawler is polite (8 concurrent requests, respects robots.txt for crawling).
