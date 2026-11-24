"""Detect the technology behind a site from its HTML, headers and asset URLs."""
from __future__ import annotations

import re

from .crawler import SiteData

# category -> [(name, regex over html+asset urls, header test)]
SIGNATURES = {
    "Platform / CMS": [
        ("WordPress", r"/wp-content/|/wp-includes/|wp-json", None),
        ("Webflow", r"webflow\.com|data-wf-page|wf-site", None),
        ("Framer", r"framerusercontent\.com|framer\.com/m/|__framer", None),
        ("Shopify", r"cdn\.shopify\.com|Shopify\.theme", None),
        ("Wix", r"static\.wixstatic\.com|wix-bolt|_wixCssImports", None),
        ("Squarespace", r"squarespace\.com|static1\.squarespace", None),
        ("Ghost", r"ghost-(?:portal|sdk)|content=\"Ghost", None),
        ("HubSpot CMS", r"hs-scripts\.com|hubspot\.net/hub", None),
        ("Drupal", r"Drupal\.settings|/sites/default/files", None),
        ("Joomla", r"/media/jui/|content=\"Joomla", None),
        ("Storyblok", r"storyblok", None),
        ("Sanity", r"cdn\.sanity\.io", None),
        ("Contentful", r"ctfassets\.net", None),
    ],
    "Framework": [
        ("Next.js", r"/_next/static|__NEXT_DATA__", None),
        ("Nuxt", r"/_nuxt/|__NUXT__", None),
        ("Astro", r"/_astro/|astro-island", None),
        ("Gatsby", r"___gatsby|/page-data/", None),
        ("SvelteKit", r"/_app/immutable|__sveltekit", None),
        ("Remix", r"__remixContext", None),
        ("Angular", r"ng-version=", None),
        ("Vue", r"data-v-[0-9a-f]{6,}|vue(?:\.min)?\.js", None),
        ("React", r"react(?:-dom)?(?:\.production)?(?:\.min)?\.js|data-reactroot", None),
        ("jQuery", r"jquery[.-]", None),
        ("Tailwind CSS", r"\b(?:tw-|md:flex|lg:grid-cols)", None),
        ("Bootstrap", r"bootstrap(?:\.min)?\.(?:css|js)", None),
    ],
    "Hosting / CDN": [
        ("Vercel", None, lambda h: "x-vercel-id" in h or "vercel" in h.get("server", "").lower()),
        ("Netlify", None, lambda h: "x-nf-request-id" in h or "netlify" in h.get("server", "").lower()),
        ("Cloudflare", None, lambda h: "cf-ray" in h or "cloudflare" in h.get("server", "").lower()),
        ("Fastly", None, lambda h: "x-fastly-request-id" in h or "fastly" in h.get("via", "").lower()),
        ("AWS CloudFront", None, lambda h: "x-amz-cf-id" in h),
        ("GitHub Pages", None, lambda h: "github.com" in h.get("server", "").lower()),
        ("Nginx", None, lambda h: "nginx" in h.get("server", "").lower()),
        ("Apache", None, lambda h: "apache" in h.get("server", "").lower()),
        ("LiteSpeed", None, lambda h: "litespeed" in h.get("server", "").lower()),
    ],
    "Analytics": [
        ("Google Analytics 4", r"\bG-[A-Z0-9]{6,12}\b|gtag/js", None),
        ("Google Tag Manager", r"GTM-[A-Z0-9]{4,8}", None),
        ("Microsoft Clarity", r"clarity\.ms", None),
        ("Hotjar", r"hotjar", None),
        ("Plausible", r"plausible\.io", None),
        ("Meta Pixel", r"fbq\(|fbevents\.js", None),
        ("Vercel Analytics", r"/_vercel/insights|va\.vercel-scripts", None),
        ("PostHog", r"posthog", None),
    ],
    "Marketing & sales": [
        ("HubSpot", r"js\.hs-scripts|hs-analytics", None),
        ("Mailchimp", r"list-manage\.com|mailchimp", None),
        ("Klaviyo", r"klaviyo", None),
        ("Calendly", r"calendly\.com", None),
        ("Intercom", r"intercom", None),
        ("Crisp", r"crisp\.chat", None),
        ("Tawk.to", r"tawk\.to", None),
        ("WhatsApp chat", r"wa\.me/|api\.whatsapp\.com", None),
        ("LeadPilot", r"leadpilot", None),
    ],
    "Payments": [
        ("Stripe", r"js\.stripe\.com", None),
        ("PayPal", r"paypal\.com/sdk", None),
        ("Paystack", r"paystack", None),
        ("Lemon Squeezy", r"lemonsqueezy", None),
    ],
    "Fonts & media": [
        ("Google Fonts", r"fonts\.googleapis\.com", None),
        ("Adobe Fonts", r"use\.typekit\.net", None),
        ("YouTube embeds", r"youtube\.com/embed|youtube-nocookie", None),
        ("Vimeo", r"player\.vimeo\.com", None),
        ("Cloudinary", r"res\.cloudinary\.com", None),
    ],
}


def detect(site: SiteData) -> list[dict]:
    home = site.home
    if not home:
        return []
    blob = "\n".join(p.html[:400_000] for p in site.html_pages[:5]) + "\n" + "\n".join(a.url for a in site.assets)
    gen = ""
    if home.soup and (g := home.soup.find("meta", attrs={"name": "generator"})):
        gen = g.get("content", "")
    found = []
    for cat, sigs in SIGNATURES.items():
        for name, rx, htest in sigs:
            hit = (rx and re.search(rx, blob, re.I)) or (htest and htest(home.headers)) or (gen and name.split()[0].lower() in gen.lower())
            if hit:
                found.append({"category": cat, "name": name})
    return found
