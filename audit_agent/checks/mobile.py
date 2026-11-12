"""3. Mobile Usability — mobile friendly, tap targets, text readability, viewport, horizontal scroll, mobile UX flow."""
import re

from ..crawler import SiteData
from ..models import AreaResult, Check
from ._util import bm, psi_audit, threshold, all_html, short


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    home = site.home
    m = bm(site, "mobile")
    vp_tag = home.soup.find("meta", attrs={"name": "viewport"}) if home and home.soup else None
    vp = (vp_tag.get("content") or "").replace(" ", "").lower() if vp_tag else ""

    # Mobile friendly (overall)
    pages_no_vp = [short(p.url, site) for p in site.html_pages if not p.soup.find("meta", attrs={"name": "viewport"})]
    friendly = "width=device-width" in vp and (not m or not m["horizontalScroll"])
    checks.append(Check("mobile_friendly", "Mobile Friendly", "pass" if friendly and not pages_no_vp else "fail" if not vp else "warn",
                        "Responsive viewport set and layout fits a 375px screen." if friendly else
                        "Page is not fully mobile-friendly (missing responsive viewport or content overflows).",
                        "Use a responsive layout with <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">.",
                        "high", "medium", pages=pages_no_vp[:6]))

    # Tap targets
    if m:
        bad = m["small24"]
        ratio = bad / m["interactive"] if m["interactive"] else 0
        checks.append(Check("tap_targets", "Tap Targets", threshold(ratio, 0.05, 0.2, False),
                            f"{bad}/{m['interactive']} tappable elements are smaller than 24×24px (WCAG 2.2); "
                            f"{m['small44']} are under the recommended 44×44px.",
                            "Give links/buttons at least 44×44px hit areas (padding) and 8px spacing.", "medium", "easy",
                            pages=m["smallSamples"]))
    elif (a := psi_audit(site, "tap-targets")):
        checks.append(Check("tap_targets", "Tap Targets", "pass" if (a["score"] or 0) >= 0.9 else "warn",
                            f"Lighthouse tap-target audit: {a.get('display') or a['score']}.",
                            "Give links/buttons at least 44×44px hit areas.", "medium", "easy"))
    else:
        checks.append(Check("tap_targets", "Tap Targets", "skip", "Needs browser rendering (enable --browser)."))

    # Text readability on mobile
    if m and m["textElements"]:
        ratio = m["tinyText"] / m["textElements"]
        checks.append(Check("text_readability", "Text Readability", threshold(ratio, 0.03, 0.15, False),
                            f"{m['tinyText']}/{m['textElements']} text blocks render below 12px on mobile (smallest {m['minFont']}px).",
                            "Use ≥16px body text on mobile and ≥12px for captions/legal text.", "medium", "easy"))
    else:
        small = re.findall(r"font-size:\s*([0-9.]+)px", all_html(site))
        tiny = [s for s in small if float(s) < 12]
        checks.append(Check("text_readability", "Text Readability", "warn" if tiny else "pass",
                            f"{len(tiny)} inline font-size declarations under 12px (static scan)." if tiny else
                            "No tiny inline font sizes found (static scan).",
                            "Use ≥16px body text on mobile.", "medium", "easy"))

    # Viewport settings
    if not vp:
        st, det = "fail", "No viewport meta tag."
    elif "user-scalable=no" in vp or "user-scalable=0" in vp or re.search(r"maximum-scale=1(\.0)?(,|$)", vp):
        st, det = "warn", f"Viewport disables zoom ({vp}) — hurts accessibility."
    elif "width=device-width" in vp:
        st, det = "pass", f"Viewport: {vp}"
    else:
        st, det = "warn", f"Viewport not responsive: {vp}"
    checks.append(Check("viewport", "Viewport Settings", st, det,
                        "Use content=\"width=device-width, initial-scale=1\" and allow pinch-zoom.", "high", "easy"))

    # Horizontal scroll
    if m:
        checks.append(Check("horizontal_scroll", "No Horizontal Scroll", "fail" if m["horizontalScroll"] else "pass",
                            f"Content is {m['docWidth']}px wide on a {m['viewport']}px screen." if m["horizontalScroll"]
                            else "Content fits the mobile viewport.",
                            "Find the overflowing element(s) and set max-width:100% / fix fixed widths.", "high", "easy",
                            pages=m["overflowers"]))
    elif (a := psi_audit(site, "content-width")):
        checks.append(Check("horizontal_scroll", "No Horizontal Scroll", "pass" if a["score"] == 1 else "fail",
                            "Lighthouse content-width audit.", "Fix elements wider than the viewport.", "high", "easy"))
    else:
        checks.append(Check("horizontal_scroll", "No Horizontal Scroll", "skip", "Needs browser rendering."))

    # Mobile UX flow
    if m:
        problems = []
        if not m["ctaAboveFold"]:
            problems.append("no call-to-action visible in the first mobile screen")
        if not m["navToggle"] and m["interactive"] > 12:
            problems.append("no obvious mobile menu toggle")
        if m["overlay"]:
            problems.append(f"a fixed overlay covers {m['overlay']['cover']}% of the screen on load ({m['overlay']['el']})")
        checks.append(Check("mobile_ux_flow", "Mobile UX Flow", "pass" if not problems else "warn" if len(problems) == 1 else "fail",
                            "Mobile first screen has a CTA, navigation and no blocking overlays." if not problems else
                            "Issues: " + "; ".join(problems) + ".",
                            "Put the primary CTA in the first mobile screen, use a clear menu button, delay/shrink popups.",
                            "medium", "medium"))
    else:
        checks.append(Check("mobile_ux_flow", "Mobile UX Flow", "skip", "Needs browser rendering."))

    area = AreaResult(3, "mobile", "Mobile Usability", checks, "Mobile Usability", weight=10)
    area.compute_score()
    area.key_metric_value = f"{area.score}/100"
    return area
