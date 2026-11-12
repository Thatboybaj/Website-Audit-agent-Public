"""2. Performance — page speed, Core Web Vitals, images, minification, caching, server response."""
import re

from ..crawler import SiteData
from ..models import AreaResult, Check
from ._util import psi_audit, psi_cat, threshold, sample


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    home = site.home
    perf_m, perf_d = psi_cat(site, "performance", "mobile"), psi_cat(site, "performance", "desktop")

    # Page speed
    if perf_m is not None:
        checks.append(Check("page_speed", "Page Speed", threshold(perf_m, 90, 50),
                            f"PageSpeed score — mobile {perf_m}/100, desktop {perf_d if perf_d is not None else 'n/a'}/100.",
                            "Compress images, defer non-critical JS, remove unused CSS/JS, use a CDN.", "high", "medium",
                            data={"mobile": perf_m, "desktop": perf_d}))
        speed_metric = f"{perf_m}/100"
    elif home and home.status:
        load = home.total_ms
        st = threshold(load, 1200, 3000, higher_better=False)
        checks.append(Check("page_speed", "Page Speed", st,
                            f"HTML downloaded in {load} ms (PageSpeed API unavailable — enable for full Lighthouse data).",
                            "Reduce page weight and server time; enable PSI_API_KEY for a full Lighthouse audit.", "high", "medium"))
        speed_metric = {"pass": "Fast", "warn": "Average", "fail": "Slow"}[st]
    else:
        checks.append(Check("page_speed", "Page Speed", "skip", "Homepage could not be loaded."))
        speed_metric = "n/a"

    # Core Web Vitals (field data first, then lab)
    field = (site.psi.get("mobile") or {}).get("field", {})
    lcp = psi_audit(site, "largest-contentful-paint")
    cls = psi_audit(site, "cumulative-layout-shift")
    tbt = psi_audit(site, "total-blocking-time")
    if field.get("LARGEST_CONTENTFUL_PAINT_MS"):
        cats = {k: v["category"] for k, v in field.items() if k in ("LARGEST_CONTENTFUL_PAINT_MS", "CUMULATIVE_LAYOUT_SHIFT_SCORE", "INTERACTION_TO_NEXT_PAINT")}
        bad = [k for k, v in cats.items() if v == "SLOW"]
        avg = [k for k, v in cats.items() if v == "AVERAGE"]
        st = "fail" if bad else "warn" if avg else "pass"
        det = ", ".join(f"{k.split('_')[0]} {field[k]['p75']} ({field[k]['category'].lower()})" for k in cats)
        checks.append(Check("core_web_vitals", "Core Web Vitals", st, f"Real-user (CrUX) p75: {det}.",
                            "Optimise the LCP element (preload hero image), reserve space for media to stop layout shift, break up long JS tasks.",
                            "high", "hard", data={"source": "field", **cats}))
    elif lcp and cls:
        lcp_s, cls_v, tbt_ms = (lcp["value"] or 0) / 1000, cls["value"] or 0, (tbt or {}).get("value") or 0
        stats = [threshold(lcp_s, 2.5, 4.0, False), threshold(cls_v, 0.1, 0.25, False), threshold(tbt_ms, 200, 600, False)]
        st = "fail" if "fail" in stats else "warn" if "warn" in stats else "pass"
        checks.append(Check("core_web_vitals", "Core Web Vitals", st,
                            f"Lab (mobile): LCP {lcp_s:.1f}s, CLS {cls_v:.2f}, TBT {tbt_ms:.0f}ms (targets: ≤2.5s, ≤0.1, ≤200ms).",
                            "Optimise the LCP element (preload hero image), set width/height on media, defer heavy scripts.",
                            "high", "hard", data={"source": "lab", "lcp": lcp_s, "cls": cls_v, "tbt": tbt_ms}))
    else:
        checks.append(Check("core_web_vitals", "Core Web Vitals", "skip",
                            "Needs PageSpeed Insights data (run with PSI enabled)."))

    # Image optimization
    imgs = [a for a in site.assets if a.kind == "img" and a.status == 200]
    heavy = [a for a in imgs if a.size > 200_000]
    legacy = [a for a in imgs if re.search(r"\.(jpe?g|png|gif|bmp)(\?|$)", a.url, re.I) and a.size > 30_000]
    tags = home.soup.find_all("img") if home and home.soup else []
    no_dims = [t for t in tags if not (t.get("width") and t.get("height"))]
    lazy = [t for t in tags if t.get("loading") == "lazy"]
    issues = len(heavy) * 2 + len(legacy)
    st = "pass" if issues == 0 else "warn" if len(heavy) <= 2 else "fail"
    if psi_audit(site, "uses-optimized-images") and (psi_audit(site, "uses-optimized-images")["score"] or 1) < 0.9:
        st = "fail" if st == "fail" else "warn"
    checks.append(Check("image_optimization", "Image Optimization", st,
                        f"{len(imgs)} homepage images checked: {len(heavy)} over 200KB, {len(legacy)} in legacy formats, "
                        f"{len(no_dims)} without width/height, {len(lazy)} lazy-loaded.",
                        "Convert to WebP/AVIF, resize to display size, add width/height and loading=\"lazy\" below the fold.",
                        "high", "easy", pages=[f"{a.url} ({a.size // 1024}KB)" for a in sample(sorted(heavy, key=lambda a: -a.size), 6)]))

    # Minify CSS/JS
    code = [a for a in site.assets if a.kind in ("css", "js") and a.status == 200 and a.size > 2000 and a.body]
    unmin = []
    for a in code:
        lines = a.body.count("\n") + 1
        if len(a.body) / lines < 80 and not re.search(r"\.min\.(js|css)", a.url):
            unmin.append(a)
    if psi_audit(site, "unminified-css") or psi_audit(site, "unminified-javascript"):
        psi_bad = [k for k in ("unminified-css", "unminified-javascript") if ((psi_audit(site, k) or {}).get("score") or 1) < 0.9]
    else:
        psi_bad = []
    st = "pass" if not unmin and not psi_bad else "warn" if len(unmin) <= 2 else "fail"
    checks.append(Check("minify", "Minify CSS/JS", st,
                        f"{len(code) - len(unmin)}/{len(code)} CSS/JS files appear minified.",
                        "Enable minification in your build/hosting (Framer & Webflow do this automatically on publish).",
                        "medium", "easy", pages=[f"{a.url} ({a.size // 1024}KB)" for a in unmin[:6]]))

    # Caching & compression
    static = [a for a in site.assets if a.status == 200]
    def max_age(h):
        m = re.search(r"max-age=(\d+)", h.get("cache-control", ""))
        return int(m.group(1)) if m else 0
    cached = [a for a in static if max_age(a.headers) >= 7 * 86400 or "immutable" in a.headers.get("cache-control", "")]
    compressed = bool(home and home.headers.get("content-encoding") in ("gzip", "br", "zstd", "deflate"))
    ratio = len(cached) / len(static) if static else 1
    st = "pass" if ratio >= 0.8 and compressed else "warn" if ratio >= 0.4 or compressed else "fail"
    checks.append(Check("caching", "Caching", st,
                        f"{len(cached)}/{len(static)} static assets cached ≥7 days; HTML compression: "
                        f"{home.headers.get('content-encoding', 'none') if home else 'n/a'}.",
                        "Serve static assets with long Cache-Control (1 year + fingerprinted filenames) and enable Brotli/Gzip.",
                        "medium", "easy"))

    # Server response
    if home and home.status:
        ttfb = home.ttfb_ms
        psi_ttfb = psi_audit(site, "server-response-time")
        ttfb_val = psi_ttfb["value"] if psi_ttfb and psi_ttfb.get("value") is not None else ttfb
        checks.append(Check("server_response", "Server Response", threshold(ttfb_val, 600, 1500, False),
                            f"Time to first byte ≈ {round(ttfb_val)} ms (target < 600 ms). Server: {home.headers.get('server', 'unknown')}.",
                            "Use a CDN/edge hosting, enable full-page caching, upgrade slow hosting.", "medium", "medium"))

    # Page weight
    total = (home.size_bytes if home else 0) + sum(a.size for a in site.assets)
    checks.append(Check("page_weight", "Page Weight", threshold(total / 1e6, 2.0, 4.0, False),
                        f"Homepage weight ≈ {total / 1e6:.1f} MB across {len(site.assets) + 1} sampled requests.",
                        "Remove unused libraries, lazy-load media and third-party embeds.", "medium", "medium"))

    return AreaResult(2, "performance", "Performance", checks, "PageSpeed Score", speed_metric, weight=12)
