"""10. Analytics & Tracking — GA, goals, conversion events, UTMs, heatmaps, data accuracy."""
import re

from ..crawler import SiteData
from ..models import AreaResult, Check
from ._util import all_html, short

PIXELS = {
    "Google Ads": r"AW-\d{6,}|googleadservices",
    "Meta Pixel": r"fbq\(|connect\.facebook\.net/.+/fbevents",
    "LinkedIn Insight": r"snap\.licdn\.com|_linkedin_partner_id",
    "TikTok Pixel": r"analytics\.tiktok\.com|ttq\.load",
    "X/Twitter Pixel": r"static\.ads-twitter\.com|twq\(",
    "Pinterest Tag": r"pintrk\(",
}
HEATMAPS = {"Hotjar": r"hotjar", "Microsoft Clarity": r"clarity\.ms", "FullStory": r"fullstory", "Crazy Egg": r"crazyegg",
            "Mouseflow": r"mouseflow", "Lucky Orange": r"luckyorange", "PostHog": r"posthog", "Smartlook": r"smartlook"}
OTHER = {"Plausible": r"plausible\.io", "Fathom": r"usefathom", "Matomo": r"matomo|piwik", "Framer Analytics": r"events\.framer\.com",
         "Webflow Analyze": r"webflow.*analyze", "Segment": r"segment\.(com|io)/analytics", "Mixpanel": r"mixpanel", "HubSpot": r"js\.hs-scripts|hs-analytics"}


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    pages = site.html_pages
    html = all_html(site)

    ga4 = set(re.findall(r"\bG-[A-Z0-9]{6,12}\b", html))
    ua = set(re.findall(r"\bUA-\d{4,10}-\d{1,4}\b", html))
    gtm = set(re.findall(r"\bGTM-[A-Z0-9]{4,8}\b", html))
    others = [n for n, rx in OTHER.items() if re.search(rx, html, re.I)]

    # Google Analytics
    if ga4 or gtm:
        st, det = "pass", f"GA4: {', '.join(ga4) or 'via GTM'}; GTM: {', '.join(gtm) or 'none'}."
    elif ua:
        st, det = "fail", f"Only legacy Universal Analytics ({', '.join(ua)}) — it stopped collecting data in 2023."
    elif others:
        st, det = "warn", f"No Google Analytics, but uses {', '.join(others)}."
    else:
        st, det = "fail", "No analytics tool detected."
    checks.append(Check("google_analytics", "Google Analytics", st, det,
                        "Install GA4 (or GTM + GA4) on every page; link it to Search Console.", "high", "easy"))

    # Goal tracking
    events = re.findall(r"gtag\(\s*['\"]event['\"]\s*,\s*['\"]([\w-]+)", html) + re.findall(r"dataLayer\.push\(\s*\{[^}]*event['\"]?\s*:\s*['\"]([\w.-]+)", html)
    if events:
        checks.append(Check("goal_tracking", "Goal Tracking", "pass", f"Custom events found: {', '.join(sorted(set(events))[:6])}."))
    elif gtm:
        checks.append(Check("goal_tracking", "Goal Tracking", "warn", "GTM present — goals may be configured inside it (can't verify externally).",
                            "Confirm GA4 key events (form_submit, generate_lead, book_call) are marked as conversions.", "medium", "easy"))
    else:
        checks.append(Check("goal_tracking", "Goal Tracking", "fail", "No custom event/goal tracking detected.",
                            "Track key actions (form submit, booking, CTA clicks) as GA4 key events.", "high", "medium"))

    # Conversion events / ad pixels
    pix = [n for n, rx in PIXELS.items() if re.search(rx, html, re.I)]
    conv = re.search(r"['\"](generate_lead|purchase|sign_up|conversion|Lead|CompleteRegistration|Schedule|Contact)['\"]", html)
    st = "pass" if pix and conv else "warn" if pix or conv else "fail"
    checks.append(Check("conversion_events", "Conversion Events", st,
                        f"Ad/conversion pixels: {', '.join(pix) or 'none'}; conversion event calls: {'yes' if conv else 'none detected'}.",
                        "Fire a 'generate_lead'/'Lead' event on successful form or booking for GA4 and any ad platforms you run.",
                        "medium", "medium"))

    # UTM parameters
    internal_utm = sorted({short(l, site) for p in pages for l in p.internal_links if "utm_" in l})
    external_utm = sorted({l for p in pages for l in p.external_links if "utm_" in l})
    if internal_utm:
        checks.append(Check("utm", "UTM Parameters", "fail", f"{len(internal_utm)} internal link(s) carry UTM tags — this resets sessions and corrupts attribution.",
                            "Remove UTMs from internal links; use them only on external campaign links pointing to your site.",
                            "medium", "easy", pages=internal_utm[:6]))
    else:
        checks.append(Check("utm", "UTM Parameters", "pass",
                            "No UTM misuse on internal links." + (f" {len(external_utm)} outbound tagged link(s)." if external_utm else ""),
                            "Use a UTM naming convention for every email/social/ads link back to the site.", "low", "easy"))

    # Heatmaps
    hm = [n for n, rx in HEATMAPS.items() if re.search(rx, html, re.I)]
    checks.append(Check("heatmaps", "Heatmaps", "pass" if hm else "warn", f"Heatmap/session tools: {', '.join(hm) or 'none'}.",
                        "Add Microsoft Clarity (free) to see scroll depth, rage clicks and session recordings.", "low", "easy"))

    # Data accuracy
    probs = []
    if len(ga4) > 1:
        probs.append(f"{len(ga4)} different GA4 IDs")
    for gid in ga4:
        per_page = [len(re.findall(rf"config['\"]\s*,\s*['\"]{gid}", p.html)) for p in pages]
        if any(c > 1 for c in per_page):
            probs.append(f"{gid} configured twice on a page (double counting)")
    tagged = [p for p in pages if re.search(r"G-[A-Z0-9]{6,}|GTM-[A-Z0-9]{4,}|" + "|".join(OTHER.values()), p.html, re.I)]
    coverage = len(tagged) / len(pages) if pages else 0
    if pages and coverage < 1:
        probs.append(f"tracking missing on {len(pages) - len(tagged)} page(s)")
    consent = re.search(r"cookiebot|onetrust|cookieyes|termly|iubenda|consent|gtag\(['\"]consent", html, re.I)
    if (ga4 or gtm) and not consent:
        probs.append("no cookie consent / Consent Mode detected (GDPR)")
    checks.append(Check("data_accuracy", "Data Accuracy", "pass" if not probs else "warn" if len(probs) <= 1 else "fail",
                        f"Tracking on {round(coverage * 100)}% of pages." + (" Issues: " + "; ".join(probs) + "." if probs else " No duplication found."),
                        "One GA4 property, one install method, tag every page, add consent mode, exclude internal traffic.",
                        "medium", "easy", pages=[short(p.url, site) for p in pages if p not in tagged][:6]))

    tracked = sum(1 for c in checks if c.id in ("google_analytics", "goal_tracking", "conversion_events") and c.status == "pass")
    return AreaResult(10, "analytics", "Analytics & Tracking", checks, "Tracked Goals", f"{round(100 * tracked / 3)}%", weight=8)
