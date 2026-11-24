"""AEO (Answer Engine Optimization) checks: can AI assistants reach, read, trust and quote this site?
Nine categories, same Check/AreaResult model as the SEO audit so scoring and UI are shared."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from ..checks._util import main_text, ratio_status, short, threshold
from ..crawler import SiteData
from ..models import AreaResult, Check
from .bots import BOTS

QUESTION_RX = re.compile(r"\?\s*$|^\s*(what|how|why|when|where|who|which)\s+(is|are|was|do|does|did|can|could|should|would|will|much|many|long|often|to|you|i|we|my|your)\b", re.I)
SOCIAL_RX = re.compile(r"(linkedin\.com|twitter\.com|x\.com|instagram\.com|facebook\.com|youtube\.com|github\.com|dribbble\.com|behance\.net|tiktok\.com|crunchbase\.com|wikipedia\.org|wikidata\.org|g2\.com|clutch\.co|trustpilot\.com)/", re.I)
AUTHORITY_RX = re.compile(r"\.(gov|edu|int)(/|$)|wikipedia\.org|who\.int|nature\.com|ncbi\.nlm|statista\.com|reuters\.com|bbc\.|nytimes\.com|harvard\.edu|gartner\.com|mckinsey\.com", re.I)


# ------------------------------------------------------------------ helpers
def jsonld(site: SiteData) -> dict[str, list[dict]]:
    """Every JSON-LD object on crawled pages, grouped by @type (handles @graph and type lists)."""
    out: dict[str, list[dict]] = {}

    def walk(o, url):
        if isinstance(o, list):
            for x in o:
                walk(x, url)
        elif isinstance(o, dict):
            t = o.get("@type")
            for tt in (t if isinstance(t, list) else [t] if t else []):
                out.setdefault(str(tt), []).append({**o, "_page": url})
            for k, v in o.items():
                if k != "@type" and isinstance(v, (dict, list)):
                    walk(v, url)
    for p in site.html_pages:
        for sc in p.soup.find_all("script", type="application/ld+json"):
            try:
                walk(json.loads(sc.string or sc.get_text() or ""), p.url)
            except Exception:
                pass
    return out


def question_blocks(site: SiteData) -> list[dict]:
    """Question-style headings and the answer text that follows each."""
    qs = []
    for p in site.html_pages:
        for h in p.soup.find_all(["h2", "h3", "h4", "summary", "dt"]):
            q = h.get_text(" ", strip=True)
            if 8 <= len(q) <= 160 and QUESTION_RX.search(q):
                nxt = h.find_next(["p", "dd", "div", "ul", "ol"])
                ans = re.sub(r"\s+", " ", nxt.get_text(" ", strip=True)) if nxt else ""
                qs.append({"q": q, "a": ans[:600], "words": len(ans.split()), "page": p.url})
    seen, out = set(), []
    for x in qs:  # same Q&A repeated across pages counts once
        k = re.sub(r"\W+", " ", x["q"].lower()).strip()
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


def robots_allows(site: SiteData, bot: str) -> bool | None:
    if not site.robots:
        return True if site.robots_status in (404, 410) or not site.robots_txt else None
    return site.robots.can_fetch(bot, site.start_url)


def robots_mentions(site: SiteData, bot: str) -> bool:
    return bool(re.search(rf"(?im)^\s*user-agent:\s*{re.escape(bot)}\s*$", site.robots_txt or ""))


# ------------------------------------------------------------------ 1. crawler access
def crawler_access(site: SiteData) -> AreaResult:
    checks = []
    by_role = {"search": [], "user": [], "training": []}
    rows = []
    for b in BOTS:
        allowed = robots_allows(site, b["name"])
        live = site.bot_access.get(b["name"])
        rows.append({"bot": b["name"], "company": b["company"], "role": b["role"], "engine": b["engine"],
                     "robots": "allowed" if allowed else "blocked" if allowed is False else "unknown",
                     "explicit": robots_mentions(site, b["name"]),
                     "live": None if live is None else ("blocked" if live.get("blocked") else f"ok ({live.get('status')})")})
        by_role[b["role"]].append((b, allowed))

    blocked_search = [b["name"] for b, a in by_role["search"] if a is False]
    checks.append(Check("ai_search_bots", "AI Search Crawlers", "fail" if len(blocked_search) >= 2 else "warn" if blocked_search else "pass",
                        f"robots.txt blocks: {', '.join(blocked_search)}." if blocked_search else
                        "robots.txt lets ChatGPT search, Claude search, Perplexity, Google and Bing crawl the site.",
                        "Allow OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot and bingbot — they decide whether you can be cited.",
                        "high", "easy", pages=blocked_search, data={"bots": rows}))

    blocked_user = [b["name"] for b, a in by_role["user"] if a is False]
    checks.append(Check("ai_user_bots", "Live AI Browsing", "warn" if blocked_user else "pass",
                        f"Blocked: {', '.join(blocked_user)} — assistants can't open your page when a user asks about it." if blocked_user
                        else "ChatGPT, Claude and Perplexity can fetch pages live when users ask about you.",
                        "Allow ChatGPT-User, Claude-User and Perplexity-User in robots.txt.", "medium", "easy", pages=blocked_user))

    probed = {k: v for k, v in site.bot_access.items()}
    if probed:
        fw = [k for k, v in probed.items() if v.get("blocked")]
        st = "pass" if not fw else "fail" if any(k in fw for k in ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot", "Googlebot")) else "warn"
        checks.append(Check("ai_firewall", "Firewall / CDN Access", st,
                            f"{len(probed) - len(fw)}/{len(probed)} AI crawler requests got the real page." +
                            (f" Blocked or challenged: {', '.join(fw)}." if fw else ""),
                            "Your CDN/WAF (often Cloudflare 'Block AI bots' or bot-fight mode) is stopping AI crawlers even though robots.txt allows them. Allow verified AI search bots in the firewall.",
                            "high", "easy", pages=[f"{k}: HTTP {v.get('status')}{' + challenge page' if v.get('challenge') else ''}" for k, v in probed.items() if v.get("blocked")]))
    else:
        checks.append(Check("ai_firewall", "Firewall / CDN Access", "skip", "Live crawler probes not run."))

    train_blocked = [b["name"] for b, a in by_role["training"] if a is False]
    train_allowed = [b["name"] for b, a in by_role["training"] if a]
    checks.append(Check("ai_training", "Training Crawlers (your choice)", "info",
                        f"Training bots allowed: {', '.join(train_allowed) or 'none'}; blocked: {', '.join(train_blocked) or 'none'}. "
                        "Blocking training doesn't stop you being cited in AI search — it's a content-licensing decision.",
                        "Decide deliberately: allow for maximum AI exposure, or block GPTBot/ClaudeBot/Google-Extended/CCBot to opt out of training.",
                        "low", "easy"))

    home = site.home
    xr = (home.headers.get("x-robots-tag", "") if home else "").lower()
    meta = ""
    if home and home.soup and (m := home.soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})):
        meta = (m.get("content") or "").lower()
    noai = "noai" in meta or "noai" in xr
    noindex = "noindex" in meta or "noindex" in xr
    checks.append(Check("ai_meta", "Robots Meta for AI", "fail" if noindex else "warn" if noai else "pass",
                        "Homepage is noindex — invisible to search and AI." if noindex else
                        "'noai' directive found; some AI tools will skip the page." if noai else "No meta directives hiding the page from AI.",
                        "Remove noindex/noai from pages you want AI assistants to recommend.", "high" if noindex else "medium", "easy"))

    ok_search = len(by_role["search"]) - len(blocked_search)
    return AreaResult(1, "ai_access", "AI Crawler Access", checks, "Search bots allowed",
                      f"{ok_search}/{len(by_role['search'])}", weight=16)


# ------------------------------------------------------------------ 2. discoverability
def discoverability(site: SiteData) -> AreaResult:
    checks = []
    lt = site.llms_txt.get("llms.txt", {})
    if lt.get("found"):
        t = lt["text"]
        good = t.lstrip().startswith("# ") and re.search(r"\[[^\]]+\]\(https?://", t)
        checks.append(Check("llms_txt", "llms.txt", "pass" if good else "warn",
                            f"/llms.txt found ({lt['size']:,} bytes)" + ("" if good else ", but it lacks the '# Title' + linked-pages format."),
                            "Follow the llmstxt.org format: '# Site name', a '> summary' line, then '## Sections' of [links](url): notes.",
                            "low", "easy"))
    else:
        checks.append(Check("llms_txt", "llms.txt", "warn",
                            "No /llms.txt. It's an emerging, optional standard: a plain-text map of your key pages for AI tools. Cheap to add; no engine has confirmed ranking on it.",
                            "Publish /llms.txt (AuditPilot Pro writes one for you from your site).", "low", "easy"))
    full = site.llms_txt.get("llms-full.txt", {})
    checks.append(Check("llms_full", "llms-full.txt", "pass" if full.get("found") else "info",
                        "/llms-full.txt found." if full.get("found") else "No /llms-full.txt (optional full-text version for documentation-heavy sites)."))
    if site.sitemap_urls:
        checks.append(Check("ai_sitemap", "Sitemap for Crawlers", "pass" if site.sitemap_lastmods else "warn",
                            f"Sitemap lists {len(site.sitemap_urls)} URLs" + (" with lastmod dates." if site.sitemap_lastmods else " but no lastmod dates."),
                            "Add <lastmod> dates so AI search crawlers know what changed.", "medium", "easy"))
    else:
        checks.append(Check("ai_sitemap", "Sitemap for Crawlers", "fail", "No XML sitemap — crawlers must discover pages by links alone.",
                            "Publish sitemap.xml and reference it in robots.txt.", "medium", "easy"))
    in_robots = "sitemap:" in (site.robots_txt or "").lower()
    checks.append(Check("ai_sitemap_robots", "Sitemap in robots.txt", "pass" if in_robots else "warn",
                        "robots.txt points crawlers to the sitemap." if in_robots else "robots.txt doesn't reference the sitemap.",
                        "Add 'Sitemap: https://yourdomain/sitemap.xml' to robots.txt.", "low", "easy"))
    return AreaResult(2, "ai_discovery", "AI Discoverability", checks, "llms.txt", "yes" if lt.get("found") else "no", weight=8)


# ------------------------------------------------------------------ 3. structured data
def structured_data(site: SiteData, ld: dict, qs: list) -> AreaResult:
    checks = []
    orgs = ld.get("Organization", []) + ld.get("LocalBusiness", []) + ld.get("ProfessionalService", []) + \
           [o for k, v in ld.items() if k.endswith("Business") or k in ("Corporation", "Store", "Restaurant", "MedicalOrganization") for o in v]
    if orgs:
        o = orgs[0]
        have = [k for k in ("name", "url", "logo", "sameAs", "description") if o.get(k)]
        same = o.get("sameAs") or []
        same = same if isinstance(same, list) else [same]
        st = "pass" if len(have) >= 4 and len(same) >= 2 else "warn"
        checks.append(Check("schema_org", "Organization Schema", st,
                            f"Organization schema with {', '.join(have)}; {len(same)} sameAs profile link(s).",
                            "Include name, url, logo, description and sameAs links to your LinkedIn/social/Google profiles — this is how AI ties mentions to you.",
                            "high", "easy"))
    else:
        checks.append(Check("schema_org", "Organization Schema", "fail", "No Organization / LocalBusiness schema — AI engines can't confidently identify the business entity.",
                            "Add Organization (or LocalBusiness) JSON-LD with name, logo, sameAs, contact (Pro generates it).", "high", "easy"))
    checks.append(Check("schema_website", "WebSite Schema", "pass" if ld.get("WebSite") else "warn",
                        "WebSite schema present." if ld.get("WebSite") else "No WebSite schema (names your site for search and AI).",
                        "Add WebSite JSON-LD with name and url.", "low", "easy"))
    faq = ld.get("FAQPage", [])
    if faq:
        checks.append(Check("schema_faq", "FAQ Schema", "pass", f"FAQPage schema on {len({f['_page'] for f in faq})} page(s)."))
    elif len(qs) >= 3:
        checks.append(Check("schema_faq", "FAQ Schema", "warn", f"{len(qs)} question-and-answer blocks found but no FAQPage schema.",
                            "Mark up your Q&A blocks as FAQPage so assistants can lift exact answers (Pro generates it).", "medium", "easy"))
    else:
        checks.append(Check("schema_faq", "FAQ Schema", "warn", "No FAQ content or FAQPage schema.",
                            "Add an FAQ section answering real buyer questions, marked up with FAQPage.", "medium", "medium"))
    article_pages = [p for p in site.html_pages if re.search(r"/(blog|news|articles?|insights|posts?|journal|guides?)/.+", p.url) or p.soup.find("article")]
    arts = ld.get("Article", []) + ld.get("BlogPosting", []) + ld.get("NewsArticle", [])
    if article_pages:
        good = [a for a in arts if a.get("author") and (a.get("datePublished") or a.get("dateModified"))]
        checks.append(Check("schema_article", "Article Schema", "pass" if good else "warn" if arts else "fail",
                            f"{len(article_pages)} article-like page(s); {len(arts)} Article schema block(s), {len(good)} with author + date.",
                            "Use Article/BlogPosting schema with author (Person) and datePublished/dateModified.", "medium", "easy"))
    else:
        checks.append(Check("schema_article", "Article Schema", "info", "No articles/blog posts crawled."))
    deep = [p for p in site.html_pages if urlparse(p.url).path.strip("/").count("/") >= 1]
    if deep:
        checks.append(Check("schema_breadcrumb", "Breadcrumb Schema", "pass" if ld.get("BreadcrumbList") else "warn",
                            "BreadcrumbList present." if ld.get("BreadcrumbList") else "Nested pages have no BreadcrumbList schema.",
                            "Add BreadcrumbList so AI understands your site hierarchy.", "low", "easy"))
    offer = [k for k in ld if k in ("Product", "Service", "Offer", "AggregateRating", "Review", "Event", "Course", "HowTo")]
    checks.append(Check("schema_offer", "Offer / Service Schema", "pass" if offer else "warn",
                        f"Describes offerings with: {', '.join(offer)}." if offer else "No Service/Product/Review schema describing what you sell.",
                        "Add Service or Product schema (with Offer/Review where real) for your main offerings.", "medium", "medium"))
    types = sorted(k for k in ld if not k.startswith("_"))
    return AreaResult(3, "ai_schema", "Structured Data for AI", checks, "Schema types", str(len(types)), weight=14)


# ------------------------------------------------------------------ 4. answer-ready content
def answerability(site: SiteData, qs: list) -> AreaResult:
    checks = []
    n = len(qs)
    checks.append(Check("qa_headings", "Question-Led Headings", threshold(n, 5, 1),
                        f"{n} headings phrased as questions people ask." if n else "No headings phrased as questions.",
                        "Turn key H2/H3s into the questions buyers type into ChatGPT ('How much does X cost in Doha?').",
                        "high", "easy", pages=[q["q"] for q in qs[:6]]))
    if qs:
        direct = [q for q in qs if 15 <= q["words"] <= 90]
        checks.append(Check("answer_first", "Answer-First Paragraphs", ratio_status(len(direct), n, 0.7, 0.4),
                            f"{len(direct)}/{n} questions are followed by a direct 15–90 word answer.",
                            "Answer in the first 1–2 sentences under each question, then expand. AI quotes concise, self-contained answers.",
                            "high", "easy"))
    else:
        checks.append(Check("answer_first", "Answer-First Paragraphs", "fail", "No question/answer pairs for AI to quote.",
                            "Add a Q&A or FAQ section with 40–60 word direct answers.", "high", "medium"))
    content = [p for p in site.html_pages if p.word_count >= 300]
    structured = [p for p in content if p.soup.find(["ul", "ol", "table"])]
    checks.append(Check("lists_tables", "Lists & Tables", ratio_status(len(structured), len(content), 0.7, 0.4),
                        f"{len(structured)}/{len(content)} substantial pages use lists or tables.",
                        "Use bullet lists, numbered steps and comparison tables — they're the easiest blocks for AI to extract.",
                        "medium", "easy"))
    home_txt = main_text(site.home) if site.home and site.home.soup else ""
    first = " ".join(home_txt.split()[:80]).lower()
    definitional = bool(re.search(r"\b(is an?|are an?|we are|we're an?|helps|provides|specialis|specializ)\b", first))
    checks.append(Check("definition", "Clear Definition Up Top", "pass" if definitional else "warn",
                        "Homepage opens with a plain statement of what the business is/does." if definitional else
                        "The first lines don't plainly say what the business is and does.",
                        "Open with one sentence AI can quote: '[Name] is a [what] that helps [who] [outcome] in [where].'",
                        "high", "easy"))
    words = sorted(p.word_count for p in site.html_pages) or [0]
    med = words[len(words) // 2]
    checks.append(Check("depth", "Content Depth", threshold(med, 600, 300),
                        f"Median page length {med} words.",
                        "Expand key pages with specifics — prices, process, timelines, locations, examples. Thin pages rarely get cited.",
                        "medium", "medium"))
    stats = len(re.findall(r"\b\d{1,3}(?:[,.]\d{3})*\s?(?:%|percent|clients|projects|years|customers|users|x)\b", " ".join(p.text for p in site.html_pages), re.I))
    checks.append(Check("facts", "Specific Facts & Numbers", threshold(stats, 5, 2),
                        f"{stats} concrete figures (percentages, counts, years) found.",
                        "Add verifiable specifics (results, years in business, numbers of clients/projects). AI prefers citing precise facts.",
                        "medium", "easy"))
    return AreaResult(4, "ai_answers", "Answer-Ready Content", checks, "Q&A blocks", str(n), weight=16)


# ------------------------------------------------------------------ 5. entity & trust
def entity_trust(site: SiteData, ld: dict) -> AreaResult:
    checks = []
    links = [(a.get("href", ""), a.get_text(" ", strip=True).lower()) for p in site.html_pages for a in p.soup.find_all("a", href=True)]
    about = any(re.search(r"/about|/team|/company|/who-we-are|/our-story", h, re.I) or t in ("about", "about us", "our story", "team") for h, t in links)
    checks.append(Check("about_page", "About / Team Page", "pass" if about else "fail",
                        "About/team page linked." if about else "No About or Team page found.",
                        "Publish an About page with who you are, history, credentials and real people.", "high", "easy"))
    html = "\n".join(p.html for p in site.html_pages)
    contact_bits = [n for n, rx in (("phone", r"tel:"), ("email", r"mailto:"), ("address", r"\"address\"|<address|streetAddress")) if re.search(rx, html, re.I)]
    checks.append(Check("contact_nap", "Contact & Location (NAP)", "pass" if len(contact_bits) >= 2 else "warn" if contact_bits else "fail",
                        f"Contact details found: {', '.join(contact_bits) or 'none'}.",
                        "Show name, address/city and phone consistently (and in LocalBusiness schema). AI answers to 'near me' queries rely on it.",
                        "high", "easy"))
    socials = sorted({urlparse(h).netloc.replace("www.", "") for h, _ in links if SOCIAL_RX.search(h)})
    same = []
    for o in ld.get("Organization", []) + ld.get("LocalBusiness", []):
        s = o.get("sameAs") or []
        same += s if isinstance(s, list) else [s]
    checks.append(Check("social_profiles", "Profiles Across the Web", "pass" if len(socials) >= 3 else "warn" if socials else "fail",
                        f"Links to {len(socials)} external profiles ({', '.join(socials[:5]) or 'none'}); {len(same)} in schema sameAs.",
                        "Link your LinkedIn, Google Business Profile, Clutch/Trustpilot, etc., and list them in sameAs — AI cross-checks the entity.",
                        "medium", "easy", pages=socials[:8]))
    reviews = re.search(r"testimonial|review|★|⭐|rated \d|trustpilot|clutch\.co|google reviews|what (our )?clients say", html, re.I)
    checks.append(Check("reviews", "Reviews & Testimonials", "pass" if reviews else "warn",
                        "Reviews/testimonials present." if reviews else "No reviews or testimonials found.",
                        "Show named testimonials and link to third-party reviews; AI favours brands others vouch for.", "medium", "medium"))
    authors = re.search(r"rel=[\"']author|class=[\"'][^\"']*author|\"author\"\s*:|\bby\s+[A-Z][a-z]+\s+[A-Z][a-z]+", html)
    checks.append(Check("authors", "Named Authors / Experts", "pass" if authors else "warn",
                        "Named authors/experts found." if authors else "No named authors or experts on content.",
                        "Add bylines with short bios and credentials (E-E-A-T) on articles and service pages.", "medium", "easy"))
    ext = {h for p in site.html_pages for h in p.external_links if AUTHORITY_RX.search(h)}
    checks.append(Check("citations_out", "Cites Authoritative Sources", "pass" if len(ext) >= 2 else "warn" if ext else "info",
                        f"{len(ext)} links to authoritative sources (.gov/.edu/research/major publishers).",
                        "Back claims with links to credible sources — content that cites sources is more likely to be cited.", "low", "easy"))
    names = []
    home = site.home
    if home and home.soup:
        if (m := home.soup.find("meta", property="og:site_name")):
            names.append(m.get("content", "").strip())
        if home.soup.title and home.soup.title.string:
            parts = re.split(r"\s[|–—-]\s", home.soup.title.string.strip())
            names.append(parts[-1] if len(parts) > 1 else parts[0])
    for o in ld.get("Organization", [])[:1]:
        names.append(str(o.get("name", "")).strip())
    names = [n for n in names if n]
    norm = {re.sub(r"[^a-z0-9]", "", n.lower()) for n in names}
    checks.append(Check("brand_consistency", "Consistent Brand Name", "pass" if len(norm) <= 1 and names else "warn",
                        f"Brand name signals: {', '.join(dict.fromkeys(names)) or 'none'}.",
                        "Use one exact brand name in the title, og:site_name and Organization schema.", "medium", "easy"))
    score = sum(c.status == "pass" for c in checks)
    return AreaResult(5, "ai_trust", "Entity & Trust (E-E-A-T)", checks, "Trust signals", f"{score}/{len(checks)}", weight=14)


# ------------------------------------------------------------------ 6. freshness
def freshness(site: SiteData, ld: dict) -> AreaResult:
    checks = []
    dates = []
    for objs in ld.values():
        for o in objs:
            for k in ("dateModified", "datePublished"):
                if isinstance(o.get(k), str):
                    dates.append(o[k][:10])
    for p in site.html_pages:
        for prop in ("article:modified_time", "article:published_time", "og:updated_time"):
            if (m := p.soup.find("meta", property=prop)) and m.get("content"):
                dates.append(m["content"][:10])
        for t in p.soup.find_all("time", datetime=True)[:5]:
            dates.append(t["datetime"][:10])
    dates = sorted(d for d in dates if re.match(r"\d{4}-\d{2}-\d{2}", d))
    checks.append(Check("dates_marked", "Machine-Readable Dates", "pass" if dates else "warn",
                        f"Latest marked date: {dates[-1]}." if dates else "No datePublished/dateModified or <time> markup.",
                        "Mark publish/update dates in schema and <time datetime>; AI weighs recency.", "medium", "easy"))
    lm = sorted(l[:10] for l in site.sitemap_lastmods if re.match(r"\d{4}-\d{2}-\d{2}", l))
    newest = (lm[-1] if lm else None) or (dates[-1] if dates else None)
    if newest:
        age = (datetime.now(timezone.utc).date() - datetime.strptime(newest, "%Y-%m-%d").date()).days
        checks.append(Check("recency", "Recently Updated", threshold(age, 90, 365, higher_better=False),
                            f"Most recent update signal: {newest} ({age} days ago).",
                            "Refresh key pages quarterly — update facts, prices, examples and the modified date.", "medium", "medium"))
    else:
        checks.append(Check("recency", "Recently Updated", "warn", "No update dates anywhere — AI can't tell if the content is current.",
                            "Add lastmod to your sitemap and dateModified to key pages.", "medium", "easy"))
    years = [int(y) for p in site.html_pages for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", p.html, re.I)]
    cy = datetime.now().year
    checks.append(Check("copyright_year", "Current Copyright Year", "pass" if years and min(years) >= cy - 1 else "warn",
                        f"Footer year: {min(years) if years else 'none'}.", "Keep the footer year current (looks abandoned otherwise).", "low", "easy"))
    return AreaResult(6, "ai_fresh", "Freshness", checks, "Last update", newest or "unknown", weight=8)


# ------------------------------------------------------------------ 7. AI-readable rendering
def rendering(site: SiteData) -> AreaResult:
    checks = []
    home = site.home
    raw = home.word_count if home else 0
    rendered = (site.browser.get("desktop") or {}).get("renderedWords") if isinstance(site.browser.get("desktop"), dict) else None
    if rendered:
        ratio = raw / rendered if rendered else 1
        checks.append(Check("raw_html", "Content Without JavaScript", threshold(ratio, 0.7, 0.4),
                            f"{min(100, round(ratio * 100))}% of the visible text is in the raw HTML ({raw} of {rendered} words). Most AI crawlers don't run JavaScript.",
                            "Server-render (SSR/SSG) the main content so it's in the HTML response — e.g. Astro/Next static output, Framer/Webflow publish.",
                            "high", "hard", data={"raw": raw, "rendered": rendered}))
        metric = f"{min(100, round(ratio * 100))}%"
    else:
        scripts = len(home.soup.find_all("script")) if home and home.soup else 0
        shell = bool(home and home.soup and home.soup.find(id=re.compile(r"^(root|app|__next|__nuxt)$")) and raw < 80)
        checks.append(Check("raw_html", "Content Without JavaScript", "fail" if shell else "pass" if raw >= 150 else "warn",
                            "Page looks like an empty JavaScript app shell — AI crawlers see almost nothing." if shell else
                            f"{raw} words readable in raw HTML ({scripts} scripts).",
                            "Server-render the main content so it's in the HTML response.", "high", "hard"))
        metric = f"{raw} words"
    h1_raw = bool(home and home.soup and home.soup.find("h1") and home.soup.find("h1").get_text(strip=True))
    checks.append(Check("h1_raw", "Headline in HTML", "pass" if h1_raw else "fail",
                        "Main headline is present in the raw HTML." if h1_raw else "No H1 text in the raw HTML (missing or injected by JavaScript / shown as an image).",
                        "Put the main headline as real <h1> text in the HTML.", "medium", "easy"))
    ttfb = home.ttfb_ms if home else 0
    checks.append(Check("bot_speed", "Fast Response for Crawlers", threshold(ttfb, 800, 2000, higher_better=False),
                        f"Server responds in ~{round(ttfb)} ms.", "AI fetchers time out quickly — use a CDN/static hosting.", "medium", "medium"))
    imgs = [i for p in site.html_pages for i in p.soup.find_all("img")]
    alt = [i for i in imgs if (i.get("alt") or "").strip()]
    checks.append(Check("img_text", "Images Described in Text", ratio_status(len(alt), len(imgs), 0.9, 0.6),
                        f"{len(alt)}/{len(imgs)} images have descriptive alt text (AI reads alt, not pixels).",
                        "Describe meaningful images in alt text; never put key messages only inside images.", "low", "easy"))
    return AreaResult(7, "ai_render", "AI-Readable Rendering", checks, "HTML-visible", metric, weight=14)


# ------------------------------------------------------------------ 8. snippet & citation controls
def snippet_controls(site: SiteData) -> AreaResult:
    checks = []
    restricted = []
    nosnip_attr = 0
    for p in site.html_pages:
        meta = " ".join((m.get("content") or "").lower() for m in p.soup.find_all("meta", attrs={"name": re.compile(r"^(robots|googlebot)$", re.I)}))
        xr = p.headers.get("x-robots-tag", "").lower()
        both = meta + " " + xr
        if "nosnippet" in both or re.search(r"max-snippet:\s*0\b", both):
            restricted.append(short(p.url, site))
        nosnip_attr += len(p.soup.find_all(attrs={"data-nosnippet": True}))
    checks.append(Check("nosnippet", "Snippets Allowed", "fail" if restricted else "pass",
                        f"{len(restricted)} page(s) forbid snippets — Google's AI Overviews and others can't quote them." if restricted else
                        "No nosnippet / max-snippet:0 restrictions.",
                        "Remove nosnippet and max-snippet:0 from pages you want quoted in AI answers.", "high", "easy", pages=restricted[:6]))
    if nosnip_attr:
        checks.append(Check("data_nosnippet", "data-nosnippet Blocks", "warn", f"{nosnip_attr} elements are excluded from snippets with data-nosnippet.",
                            "Make sure key answers aren't inside data-nosnippet elements.", "low", "easy"))
    home = site.home
    if home and home.soup:
        og = [k for k in ("og:title", "og:description", "og:image") if home.soup.find("meta", property=k)]
        checks.append(Check("og_preview", "Link Previews in Chats", "pass" if len(og) == 3 else "warn",
                            f"Open Graph: {', '.join(og) or 'none'} — used when your link is shared in AI chats and messaging apps.",
                            "Add og:title, og:description and og:image.", "medium", "easy"))
        canon = home.soup.find("link", rel=lambda v: v and "canonical" in v)
        checks.append(Check("canonical_ai", "Canonical URL", "pass" if canon else "warn",
                            "Canonical set — AI engines consolidate citations to one URL." if canon else "No canonical URL on the homepage.",
                            "Add <link rel=\"canonical\"> to every page.", "low", "easy"))
        desc = home.soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        checks.append(Check("summary_meta", "Quotable Summary", "pass" if desc and len(desc.get("content", "")) >= 70 else "warn",
                            "Meta description gives a quotable one-line summary." if desc and len(desc.get("content", "")) >= 70 else
                            "Meta description missing or too short to summarise the business.",
                            "Write a 140–160 character description that states what you do, for whom, and where.", "medium", "easy"))
    return AreaResult(8, "ai_snippets", "Snippet & Citation Controls", checks, "Snippets", "blocked" if restricted else "allowed", weight=10)


# ------------------------------------------------------------------ 9. brand clarity (AI-judged)
def brand_clarity(site: SiteData) -> AreaResult:
    checks = []
    ev = site.ai.get("aeo") or {}
    if ev.get("clarity") is not None:
        c = ev["clarity"]
        checks.append(Check("ai_clarity", "Clear to an AI Reader", threshold(c, 8, 5),
                            f"AI clarity rating {c}/10. {ev.get('clarity_note', '')}",
                            ev.get("clarity_fix") or "State what you do, for whom, and where in the first lines.", "high", "easy"))
        missing = ev.get("missing") or []
        checks.append(Check("ai_missing", "Facts AI Can't Find", "pass" if not missing else "warn" if len(missing) <= 2 else "fail",
                            "AI found everything it needs to recommend you." if not missing else "Missing: " + "; ".join(missing[:6]) + ".",
                            "Add the missing facts to your homepage/About page in plain text.", "high", "easy", pages=missing[:8]))
        checks.append(Check("ai_description", "How AI Would Describe You", "info", ev.get("ai_description", "")))
        metric = f"{c}/10"
    else:
        home = site.home
        txt = main_text(home) if home and home.soup else ""
        h1 = home.soup.find("h1").get_text(" ", strip=True) if home and home.soup and home.soup.find("h1") else ""
        st = "pass" if h1 and len(txt.split()) >= 150 else "warn"
        checks.append(Check("ai_clarity", "Clear to an AI Reader", st,
                            f"Heuristic only (AI review not run): headline '{h1[:70]}' + {len(txt.split())} words of body copy.",
                            "Run with AI enabled for a full clarity review.", "high", "easy"))
        metric = "n/a"
    return AreaResult(9, "ai_clarity", "Brand Clarity for AI", checks, "Clarity", metric, weight=10)


def run_all(site: SiteData) -> tuple[list[AreaResult], dict]:
    ld = jsonld(site)
    qs = question_blocks(site)
    areas = [crawler_access(site), discoverability(site), structured_data(site, ld, qs), answerability(site, qs),
             entity_trust(site, ld), freshness(site, ld), rendering(site), snippet_controls(site), brand_clarity(site)]
    return areas, {"jsonld_types": sorted(ld), "questions": qs[:20], "jsonld": ld}
