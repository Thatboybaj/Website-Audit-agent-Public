"""1. Technical SEO — crawlability, sitemap, robots, canonicals, noindex, 404s."""
from ..crawler import SiteData, UA, same_site
from ..models import AreaResult, Check
from ._util import sample, short


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    home = site.home

    # Crawlability & indexing
    blocked = site.robots is not None and not site.robots.can_fetch("Googlebot", site.start_url)
    home_ok = bool(home and home.status == 200)
    xrobots_noindex = bool(home and "noindex" in home.headers.get("x-robots-tag", "").lower())
    if not home_ok:
        checks.append(Check("crawlability", "Crawlability & Indexing", "fail",
                            f"Homepage returned HTTP {home.status if home else 'no response'}.",
                            "Make sure the homepage returns 200 OK to crawlers.", "high", "medium"))
    elif blocked or xrobots_noindex:
        checks.append(Check("crawlability", "Crawlability & Indexing", "fail",
                            "Homepage is blocked by robots.txt or an X-Robots-Tag: noindex header.",
                            "Remove the Disallow rule / noindex header for pages you want ranked.", "high", "easy"))
    else:
        checks.append(Check("crawlability", "Crawlability & Indexing", "pass",
                            f"Homepage is crawlable; {len(site.html_pages)} live pages discovered via internal links."))

    # XML sitemap
    if site.sitemap_url and site.sitemap_urls:
        foreign = [u for u in site.sitemap_urls if not same_site(u, site.host)]
        st = "warn" if foreign else "pass"
        checks.append(Check("xml_sitemap", "XML Sitemap", st,
                            f"Found {short(site.sitemap_url, site)} with {len(site.sitemap_urls)} URLs"
                            + (f"; {len(foreign)} point to another domain." if foreign else "."),
                            "Keep only canonical, same-domain URLs in the sitemap." if foreign else "", "medium", "easy"))
    elif site.sitemap_url:
        checks.append(Check("xml_sitemap", "XML Sitemap", "warn", "Sitemap exists but lists no URLs.",
                            "Regenerate the sitemap so it lists every indexable page.", "medium", "easy"))
    else:
        checks.append(Check("xml_sitemap", "XML Sitemap", "fail", "No XML sitemap found at /sitemap.xml or in robots.txt.",
                            "Generate a sitemap.xml (Framer/Webflow/WordPress can auto-generate) and submit it in Google Search Console.",
                            "medium", "easy"))

    # robots.txt
    if site.robots_txt:
        disallow_all = any(l.strip().lower() in ("disallow: /",) for l in site.robots_txt.splitlines())
        has_sm = "sitemap:" in site.robots_txt.lower()
        if disallow_all and blocked:
            checks.append(Check("robots_txt", "Robots.txt", "fail", "robots.txt contains 'Disallow: /' that blocks the whole site.",
                                "Remove 'Disallow: /' for User-agent: * on the live site.", "high", "easy"))
        else:
            checks.append(Check("robots_txt", "Robots.txt", "pass" if has_sm else "warn",
                                "robots.txt present" + ("" if has_sm else " but does not reference the sitemap."),
                                "" if has_sm else "Add 'Sitemap: https://yourdomain/sitemap.xml' to robots.txt.", "low", "easy"))
    else:
        checks.append(Check("robots_txt", "Robots.txt", "warn", f"No robots.txt (HTTP {site.robots_status}).",
                            "Add a robots.txt that allows crawling and lists your sitemap.", "low", "easy"))

    # Canonical tags
    pages = site.html_pages
    missing, offsite = [], []
    for p in pages:
        c = p.soup.find("link", rel=lambda v: v and "canonical" in v)
        if not c or not c.get("href"):
            missing.append(short(p.url, site))
        elif c["href"].startswith("http") and not same_site(c["href"], site.host):
            offsite.append(short(p.url, site))
    if not pages:
        st = "skip"
    else:
        st = "pass" if not missing and not offsite else "warn" if len(missing) < len(pages) else "fail"
    checks.append(Check("canonical", "Canonical Tags", st,
                        f"{len(pages) - len(missing)}/{len(pages)} pages declare a canonical URL"
                        + (f"; {len(offsite)} canonicalise to another domain." if offsite else "."),
                        "Add <link rel=\"canonical\"> pointing to the preferred URL on every page.", "medium", "easy",
                        pages=sample(missing + offsite, 8)))

    # Noindex pages
    noindex = []
    for p in pages:
        m = p.soup.find("meta", attrs={"name": lambda v: v and v.lower() in ("robots", "googlebot")})
        if (m and "noindex" in (m.get("content") or "").lower()) or "noindex" in p.headers.get("x-robots-tag", "").lower():
            noindex.append(short(p.url, site))
    home_noindex = "/" in noindex or (home and short(home.url, site) in noindex)
    checks.append(Check("noindex", "Noindex Pages", "fail" if home_noindex else "warn" if noindex else "pass",
                        f"{len(noindex)} crawled page(s) are set to noindex." if noindex else "No unintended noindex pages found.",
                        "Remove noindex from pages that should rank (keep it only on thank-you/admin/legal duplicates).",
                        "high" if home_noindex else "medium", "easy", pages=sample(noindex, 8)))

    # 404 errors / broken links
    broken = {u: s for u, s in site.link_status.items() if s >= 400 or s == 0}
    broken_int = {u: s for u, s in broken.items() if same_site(u, site.host)}
    broken_ext = {u: s for u, s in broken.items() if not same_site(u, site.host)}
    detail_pages = [f"{short(u, site)} → {s or 'timeout'} (linked from {short(site.link_sources.get(u, ['?'])[0], site)})"
                    for u, s in list(broken_int.items())[:8]]
    n = len(broken_int)
    checks.append(Check("broken_links", "404 Errors", "pass" if n == 0 else "warn" if n <= 3 else "fail",
                        f"{n} broken internal link(s), {len(broken_ext)} broken external link(s) out of {len(site.link_status)} checked.",
                        "Fix or 301-redirect broken URLs and update the links pointing to them.", "high", "easy",
                        pages=detail_pages + [f"{u} → {s or 'timeout'}" for u, s in list(broken_ext.items())[:4]]))

    # Redirect chains
    chains = [f"{short(p.url, site)} ({len(p.redirects)} hops)" for p in site.pages if len(p.redirects) > 1]
    checks.append(Check("redirect_chains", "Redirect Chains", "warn" if chains else "pass",
                        f"{len(chains)} page(s) redirect through multiple hops." if chains else "No multi-hop redirect chains.",
                        "Point links directly at the final URL; collapse chains into a single 301.", "low", "easy", pages=chains[:6]))

    return AreaResult(1, "technical_seo", "Technical SEO", checks, "Crawl Errors", str(n), weight=12)
