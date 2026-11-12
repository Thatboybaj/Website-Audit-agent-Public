"""6. Conversion Optimization — value prop, CTA visibility, lead capture, trust, forms, checkout."""
import re

from ..crawler import SiteData
from ..models import AreaResult, Check
from ._util import CTA_RE, bm, all_html

GENERIC_H1 = re.compile(r"^(welcome|home|homepage|hello|hi|untitled|about us)\b", re.I)
TRUST = {
    "testimonials": r"testimonial|what (our )?clients say|reviews?\b|★|⭐|rated \d|trustpilot|g2\.com|clutch",
    "client logos": r"trusted by|our clients|as seen (in|on)|featured (in|on)|partners|brands we('ve)? worked",
    "case studies / results": r"case stud|portfolio|our work|results|\d+%\s*(increase|growth|more)",
    "guarantee / risk reversal": r"guarantee|money.back|no risk|cancel anytime|free trial",
    "credentials / awards": r"award|certified|accredited|years of experience|\d+\+?\s*(clients|projects|customers)",
    "privacy policy": r"privacy",
    "contact details": r"tel:|mailto:|\+\d[\d\s-]{7,}|address",
}
ECOM = re.compile(r"add to cart|add-to-cart|shopping cart|checkout|cdn\.shopify|woocommerce|snipcart|/cart\b|data-product", re.I)


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    home = site.home
    soup = home.soup if home else None
    if not soup:
        return AreaResult(6, "conversion", "Conversion Optimization",
                          [Check("value_prop", "Strong Value Props", "skip", "Homepage not loaded.")], "Conversion Readiness", "n/a")
    html = all_html(site)

    # Value proposition
    h1 = soup.find("h1")
    h1t = h1.get_text(" ", strip=True) if h1 else ""
    sub = h1.find_next(["p", "h2"]) if h1 else None
    subt = sub.get_text(" ", strip=True) if sub else ""
    words = len(h1t.split())
    if not h1t:
        st, det = "fail", "No H1 headline on the homepage."
    elif GENERIC_H1.match(h1t) or words < 3:
        st, det = "fail", f"Headline is generic: “{h1t}”."
    elif words > 16 or not subt:
        st, det = "warn", f"Headline “{h1t[:80]}” is {'long' if words > 16 else 'missing a supporting subheadline'}."
    else:
        st, det = "pass", f"Headline: “{h1t[:80]}” + supporting line."
    checks.append(Check("value_prop", "Strong Value Props", st, det,
                        "Lead with outcome + audience in ≤10 words (e.g. 'Framer websites that turn visitors into booked calls'), then a 1-line how.",
                        "high", "easy", data={"h1": h1t, "sub": subt[:200]}))

    # CTA visibility
    m, d = bm(site, "mobile"), bm(site, "desktop")
    if m and d:
        both = m["ctaAboveFold"] and d["ctaAboveFold"]
        st = "pass" if both else "warn" if (m["ctaAboveFold"] or d["ctaAboveFold"]) else "fail"
        det = f"CTA above the fold — desktop: {'yes' if d['ctaAboveFold'] else 'no'}, mobile: {'yes' if m['ctaAboveFold'] else 'no'}" + \
              (f" ({', '.join(d['ctaAboveFoldText'][:2])})." if d['ctaAboveFoldText'] else ".")
    else:
        # static: CTA in the first ~20% of body links
        links = soup.find_all(["a", "button"])
        early = [l for l in links[: max(5, len(links) // 5)] if CTA_RE.search(l.get_text(" ", strip=True))]
        st = "pass" if early else "warn"
        det = f"CTA near top of page: {early[0].get_text(' ', strip=True)[:40]}." if early else "No CTA near the top of the page (static scan)."
    checks.append(Check("cta_visibility", "CTA Visibility", st, det,
                        "Place the primary CTA in the hero on desktop and mobile, with contrasting colour.", "high", "easy"))

    # Lead capture
    email_input = re.search(r"type=[\"']email|name=[\"'][^\"']*email", html, re.I)
    booking = re.search(r"calendly\.com|cal\.com|hubspot.*meetings|tidycal|savvycal|acuityscheduling", html, re.I)
    chat = re.search(r"intercom|crisp\.chat|tawk\.to|drift\.com|wa\.me|whatsapp|hubspot.*conversations|livechat", html, re.I)
    contact = re.search(r"mailto:|tel:", html, re.I)
    found = [n for n, v in (("email form", email_input), ("booking link", booking), ("live chat/WhatsApp", chat), ("mailto/tel", contact)) if v]
    st = "pass" if (email_input or booking) else "warn" if found else "fail"
    checks.append(Check("lead_capture", "Lead Capture", st,
                        f"Lead capture methods: {', '.join(found) if found else 'none found'}.",
                        "Add a short contact/booking form or Calendly embed and a lead magnet (free audit, checklist).",
                        "high", "medium"))

    # Trust signals
    hits = [k for k, rx in TRUST.items() if re.search(rx, html, re.I)]
    st = "pass" if len(hits) >= 4 else "warn" if len(hits) >= 2 else "fail"
    checks.append(Check("trust_signals", "Trust Signals", st, f"{len(hits)}/{len(TRUST)} trust signals: {', '.join(hits) or 'none'}.",
                        "Add testimonials with names/photos, client logos, case-study numbers and clear contact details.",
                        "high", "medium", pages=[k for k in TRUST if k not in hits]))

    # Form optimization
    forms = soup.find_all("form") or [f for p in site.html_pages for f in p.soup.find_all("form")][:5]
    if forms:
        counts = [len([i for i in f.find_all(["input", "select", "textarea"]) if (i.get("type") or "").lower() not in ("hidden", "submit", "button")]) for f in forms]
        worst = max(counts)
        st = "pass" if worst <= 5 else "warn" if worst <= 8 else "fail"
        checks.append(Check("form_optimization", "Form Optimization", st,
                            f"Largest lead form has {worst} visible fields (fields per form: {counts}).",
                            "Cut to the essentials (name, email, one qualifier); every extra field lowers completion.", "medium", "easy"))
    else:
        checks.append(Check("form_optimization", "Form Optimization", "info", "No forms on crawled pages."))

    # Checkout flow (e-commerce only)
    if ECOM.search(html):
        cart = re.search(r"href=[\"'][^\"']*/(cart|checkout)", html, re.I)
        pay = re.search(r"visa|mastercard|paypal|apple ?pay|google ?pay|stripe|klarna", html, re.I)
        probs = [p for p, ok in (("no visible cart/checkout link", cart), ("no payment method badges", pay), ("not on HTTPS", site.is_https)) if not ok]
        checks.append(Check("checkout_flow", "Checkout Flow", "pass" if not probs else "warn" if len(probs) == 1 else "fail",
                            "E-commerce detected. " + ("Checkout basics in place." if not probs else "Issues: " + ", ".join(probs) + "."),
                            "Offer guest checkout, show payment badges and shipping costs early, keep checkout to ≤3 steps.",
                            "high", "medium"))
    else:
        checks.append(Check("checkout_flow", "Checkout Flow", "info", "Not an e-commerce site — checkout not applicable."))

    area = AreaResult(6, "conversion", "Conversion Optimization", checks, "Conversion Readiness", weight=10)
    area.compute_score()
    area.key_metric_value = f"{area.score}%"
    return area
