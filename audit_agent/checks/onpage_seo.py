"""4. On-Page SEO — titles, meta descriptions, headings, content, internal links, alt text (+ OG/schema)."""
from collections import Counter

from ..crawler import SiteData, normalize
from ..models import AreaResult, Check
from ._util import ratio_status, short


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    pages = site.html_pages
    n = len(pages) or 1
    optimized = 0

    titles, descs = {}, {}
    bad_title, bad_desc, bad_h = [], [], []
    for p in pages:
        u = short(p.url, site)
        t = (p.soup.title.string or "").strip() if p.soup.title and p.soup.title.string else ""
        titles[u] = t
        d_tag = p.soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
        d = (d_tag.get("content") or "").strip() if d_tag else ""
        descs[u] = d
        h1s = p.soup.find_all("h1")
        levels = [int(h.name[1]) for h in p.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]
        skipped = any(b - a > 1 for a, b in zip(levels, levels[1:]))
        t_ok = 30 <= len(t) <= 60
        d_ok = 70 <= len(d) <= 160
        h_ok = len(h1s) == 1 and not skipped
        if not t_ok:
            bad_title.append(f"{u} — {'missing' if not t else f'{len(t)} chars'}")
        if not d_ok:
            bad_desc.append(f"{u} — {'missing' if not d else f'{len(d)} chars'}")
        if not h_ok:
            bad_h.append(f"{u} — {len(h1s)} H1" + (", skipped heading level" if skipped else ""))
        optimized += t_ok and d_ok and h_ok

    dup_t = [t for t, c in Counter(v for v in titles.values() if v).items() if c > 1]
    dup_d = [d for d, c in Counter(v for v in descs.values() if v).items() if c > 1]

    st = ratio_status(len(pages) - len(bad_title), len(pages), 0.9, 0.6)
    if dup_t and st == "pass":
        st = "warn"
    checks.append(Check("title_tags", "Title Tags", st,
                        f"{len(pages) - len(bad_title)}/{len(pages)} titles are 30–60 chars; {len(dup_t)} duplicated title(s).",
                        "Write a unique 50–60 char title per page: Primary keyword – Benefit | Brand.", "high", "easy",
                        pages=bad_title[:8] + [f"duplicate: “{t[:60]}”" for t in dup_t[:3]]))

    st = ratio_status(len(pages) - len(bad_desc), len(pages), 0.9, 0.6)
    if dup_d and st == "pass":
        st = "warn"
    checks.append(Check("meta_descriptions", "Meta Descriptions", st,
                        f"{len(pages) - len(bad_desc)}/{len(pages)} meta descriptions are 70–160 chars; {len(dup_d)} duplicated.",
                        "Write a unique 140–160 char description with the keyword and a reason to click.", "medium", "easy",
                        pages=bad_desc[:8]))

    checks.append(Check("header_structure", "Header Structure", ratio_status(len(pages) - len(bad_h), len(pages), 0.9, 0.6),
                        f"{len(pages) - len(bad_h)}/{len(pages)} pages have exactly one H1 and a logical H2→H3 order.",
                        "Use one H1 per page (the main topic) and don't skip heading levels.", "medium", "easy", pages=bad_h[:8]))

    # Content quality (on-page): word count + text/HTML ratio
    thin = [f"{short(p.url, site)} — {p.word_count} words" for p in pages if p.word_count < 300]
    ratios = [len(p.text) / max(1, len(p.html)) for p in pages]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0
    checks.append(Check("onpage_content", "Content Quality", ratio_status(len(pages) - len(thin), len(pages), 0.8, 0.5),
                        f"{len(pages) - len(thin)}/{len(pages)} pages have 300+ words; avg text-to-HTML ratio {avg_ratio:.0%}.",
                        "Expand key pages with specific, helpful copy that answers the searcher's question.", "medium", "medium",
                        pages=thin[:8]))

    # Internal linking
    inbound = Counter()
    for p in pages:
        for l in set(p.internal_links):
            inbound[l] += 1
    avg_links = sum(len(set(p.internal_links)) for p in pages) / n
    crawled = {normalize(p.url) for p in pages}
    orphans = [short(u, site) for u in site.sitemap_urls if normalize(u) not in crawled and inbound.get(normalize(u), 0) == 0][:20]
    st = "pass" if avg_links >= 5 and not orphans else "warn" if avg_links >= 2 else "fail"
    checks.append(Check("internal_linking", "Internal Linking", st,
                        f"Avg {avg_links:.0f} unique internal links per page; {len(orphans)} sitemap page(s) not linked from crawled pages.",
                        "Link related pages contextually with descriptive anchor text; link to orphan pages from nav or content.",
                        "medium", "easy", pages=orphans[:8]))

    # Image alt text
    imgs = [i for p in pages for i in p.soup.find_all("img")]
    with_alt = [i for i in imgs if i.has_attr("alt")]
    missing = list({i.get("src", "")[:90] for i in imgs if not i.has_attr("alt")})
    checks.append(Check("image_alt", "Image Alt Text", ratio_status(len(with_alt), len(imgs), 0.95, 0.75),
                        f"{len(with_alt)}/{len(imgs)} images have alt attributes.",
                        "Add descriptive alt text to meaningful images (alt=\"\" for decorative ones).", "medium", "easy",
                        pages=missing[:8]))

    # Social + structured data (bonus)
    home = site.home
    if home and home.soup:
        og = all(home.soup.find("meta", attrs={"property": f"og:{k}"}) for k in ("title", "description", "image"))
        ld = home.soup.find_all("script", type="application/ld+json")
        checks.append(Check("social_schema", "Open Graph & Schema", "pass" if og and ld else "warn",
                            f"Open Graph tags: {'complete' if og else 'incomplete'}; JSON-LD blocks: {len(ld)}.",
                            "Add og:title/description/image for share previews and Organization/LocalBusiness JSON-LD schema.",
                            "low", "easy"))

    pct = round(100 * optimized / n) if pages else 0
    return AreaResult(4, "onpage_seo", "On-Page SEO", checks, "Optimized Pages", f"{pct}%", weight=12)
