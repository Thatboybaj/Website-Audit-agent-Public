"""5. User Experience — navigation, CTA, readability, consistent design, forms, friction."""
import re

from ..crawler import SiteData
from ..models import AreaResult, Check
from ._util import CTA_RE, bm, flesch, main_text, all_html, threshold, short


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    home = site.home
    soup = home.soup if home else None
    pages = site.html_pages
    if not soup:
        return AreaResult(5, "ux", "User Experience", [Check("nav", "Easy Navigation", "skip", "Homepage not loaded.")],
                          "Bounce Risk", "n/a", weight=8)

    # Easy navigation
    nav = soup.find("nav") or soup.find(attrs={"role": "navigation"}) or soup.find("header")
    nav_links = [a for a in nav.find_all("a", href=True)] if nav else []
    labels = {a.get_text(" ", strip=True) for a in nav_links if a.get_text(strip=True)}
    consistent = sum(1 for p in pages if p.soup.find("nav") or p.soup.find("header")) / max(1, len(pages))
    if not nav:
        st, det = "fail", "No <nav> or header navigation found."
    elif len(labels) > 12:
        st, det = "warn", f"{len(labels)} top-level nav items — too many choices (Hick's law)."
    elif consistent < 0.9:
        st, det = "warn", f"Navigation missing on {round((1 - consistent) * 100)}% of pages."
    else:
        st, det = "pass", f"Clear navigation with {len(labels)} items, present on {round(consistent * 100)}% of pages."
    checks.append(Check("navigation", "Easy Navigation", st, det,
                        "Keep 5–7 clearly-labelled top nav items, the same on every page, plus a footer sitemap.",
                        "medium", "medium", pages=sorted(labels)[:12]))

    # Clear CTA
    ctas = [el.get_text(" ", strip=True) for el in soup.find_all(["a", "button"]) if CTA_RE.search(el.get_text(" ", strip=True) or "")]
    ctas += [i.get("value", "") for i in soup.find_all("input", type="submit") if CTA_RE.search(i.get("value", ""))]
    uniq = list(dict.fromkeys(c[:40] for c in ctas if c))
    m = bm(site, "desktop")
    if not uniq:
        st, det = "fail", "No action-oriented call-to-action found on the homepage."
    elif m and not m["ctaAboveFold"]:
        st, det = "warn", f"{len(uniq)} CTAs found but none visible above the fold on desktop."
    elif len(uniq) > 8:
        st, det = "warn", f"{len(uniq)} different CTAs compete for attention."
    else:
        st, det = "pass", f"Clear CTA(s): {', '.join(uniq[:4])}."
    checks.append(Check("clear_cta", "Clear CTA", st, det,
                        "Use one primary, specific CTA (e.g. 'Book a free call') repeated through the page.", "high", "easy",
                        pages=uniq[:8]))

    # Readability
    text = main_text(home)
    score = flesch(text)
    long_paras = [p for p in soup.find_all("p") if len(p.get_text().split()) > 120]
    if score is None:
        checks.append(Check("readability", "Good Readability", "info", "Not enough body copy to score readability."))
    else:
        st = threshold(score, 60, 40)
        if long_paras and st == "pass":
            st = "warn"
        checks.append(Check("readability", "Good Readability", st,
                            f"Flesch reading ease {score} (60+ = easy). {len(long_paras)} paragraph(s) over 120 words.",
                            "Shorten sentences, use plain words, break long paragraphs, add subheadings and bullets.",
                            "medium", "easy", data={"flesch": score}))

    # Consistent design
    html = all_html(site) + "\n".join(a.body for a in site.assets if a.kind == "css")
    fams = m["fontFamilies"] if m else list(dict.fromkeys(f.strip().strip("'\"").split(",")[0]
                                                         for f in re.findall(r"font-family:\s*([^;}\"]+)", html)))[:10]
    fams = [f for f in fams if f and not f.lower().startswith(("var(", "inherit", "-apple", "system-ui", "sans-serif", "serif", "monospace"))]
    titles = {(p.soup.title.string or "").split("|")[-1].split("–")[-1].split("-")[-1].strip() for p in pages if p.soup.title and p.soup.title.string}
    st = "pass" if len(fams) <= 3 else "warn" if len(fams) <= 5 else "fail"
    checks.append(Check("consistent_design", "Consistent Design", st,
                        f"{len(fams)} font families in use ({', '.join(fams[:5])}); "
                        f"{len(titles)} title-suffix variant(s) across pages.",
                        "Limit to 2 typefaces, use a shared style system (colour/text styles) and consistent components.",
                        "low", "medium"))

    # Forms & interactions
    forms = [f for p in pages for f in p.soup.find_all("form")]
    unlabeled, bad_type = 0, 0
    for f in forms:
        for i in f.find_all(["input", "select", "textarea"]):
            t = (i.get("type") or "text").lower()
            if t in ("hidden", "submit", "button"):
                continue
            iid = i.get("id")
            if not (i.get("aria-label") or i.get("aria-labelledby") or (iid and f.find("label", attrs={"for": iid})) or i.find_parent("label")):
                unlabeled += 1
            if "email" in (i.get("name", "") + i.get("placeholder", "")).lower() and t not in ("email",):
                bad_type += 1
    if not forms:
        checks.append(Check("forms", "Forms & Interactions", "info", "No forms found on crawled pages."))
    else:
        st = "pass" if unlabeled == 0 and bad_type == 0 else "warn" if unlabeled <= 3 else "fail"
        checks.append(Check("forms", "Forms & Interactions", st,
                            f"{len(forms)} form(s): {unlabeled} field(s) without labels, {bad_type} email field(s) not using type=email.",
                            "Give every field a visible label, correct input types, inline validation and a clear submit label.",
                            "medium", "easy"))

    # Low friction
    friction = []
    mm = bm(site, "mobile")
    if mm and mm["overlay"]:
        friction.append(f"overlay covers {mm['overlay']['cover']}% of mobile screen on load")
    if soup.find(["video", "audio"], autoplay=True) and not soup.find("video", muted=True):
        friction.append("autoplaying media with sound")
    if re.search(r"(class|id)=[\"'][^\"']*(popup|modal|newsletter-pop|exit-intent)", home.html, re.I):
        friction.append("popup/modal markup detected")
    if soup.find("a", target="_blank", href=re.compile(r"^/")):
        friction.append("internal links open in new tabs")
    checks.append(Check("low_friction", "Low Friction", "pass" if not friction else "warn" if len(friction) == 1 else "fail",
                        "No friction patterns detected." if not friction else "Friction: " + "; ".join(friction) + ".",
                        "Delay popups (scroll/exit intent), avoid autoplay sound, keep internal links in the same tab.",
                        "medium", "easy"))

    area = AreaResult(5, "ux", "User Experience", checks, "Bounce Risk", weight=8)
    area.compute_score()
    area.key_metric_value = "Low" if area.score >= 80 else "Medium" if area.score >= 55 else "High"
    return area
