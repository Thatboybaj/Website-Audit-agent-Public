"""8. Security — SSL, HTTPS redirect, headers, vulnerabilities, plugins/themes, access control."""
import re

from ..crawler import SiteData
from ..models import AreaResult, Check
from ._util import all_html

HEADERS = {
    "strict-transport-security": "HSTS",
    "content-security-policy": "CSP",
    "x-frame-options": "X-Frame-Options",
    "x-content-type-options": "X-Content-Type-Options",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
}
# library -> (regex capturing version, minimum safe version)
LIBS = {
    "jQuery": (r"jquery[.-]?(\d+\.\d+\.\d+)(?:\.min)?\.js|jQuery v(\d+\.\d+\.\d+)", (3, 5, 0)),
    "Bootstrap": (r"bootstrap[@/.-]v?(\d+\.\d+\.\d+)", (4, 3, 1)),
    "AngularJS": (r"angular[.-]?(1\.\d+\.\d+)", (2, 0, 0)),
    "Lodash": (r"lodash[@/.-](\d+\.\d+\.\d+)", (4, 17, 21)),
    "Moment.js": (r"moment[@/.-](\d+\.\d+\.\d+)", (2, 29, 4)),
}


def ver(s: str) -> tuple:
    return tuple(int(x) for x in s.split(".")[:3])


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    home = site.home
    h = home.headers if home else {}
    html = all_html(site) + "\n".join(a.url + "\n" + a.body[:3000] for a in site.assets if a.kind == "js")

    # SSL certificate
    s = site.ssl_info
    if s.get("valid") is True:
        d = s["days_left"]
        st = "pass" if d > 30 else "warn" if d > 7 else "fail"
        checks.append(Check("ssl", "SSL Certificate", st, f"Valid {s.get('protocol', '')} cert from {s.get('issuer') or 'CA'}; expires in {d} days.",
                            "Enable auto-renewal (Let's Encrypt / host-managed SSL).", "high", "easy"))
    elif s.get("valid") is False:
        checks.append(Check("ssl", "SSL Certificate", "fail", f"SSL problem: {s.get('error')}",
                            "Install a valid TLS certificate covering the apex and www domains.", "high", "easy"))
    else:
        checks.append(Check("ssl", "SSL Certificate", "skip", f"Couldn't verify certificate ({s.get('error', 'unknown')})."))

    # HTTPS redirect
    if site.http_to_https is True:
        checks.append(Check("https_redirect", "HTTPS Redirect", "pass", "http:// permanently redirects to https://."))
    elif site.http_to_https is False:
        checks.append(Check("https_redirect", "HTTPS Redirect", "fail",
                            "HTTP version does not redirect to HTTPS." if site.is_https else "Site is served over plain HTTP.",
                            "Force HTTPS with a 301 redirect at the host/CDN and enable HSTS.", "high", "easy"))
    else:
        checks.append(Check("https_redirect", "HTTPS Redirect", "skip", "Could not test the HTTP → HTTPS redirect."))

    # Security headers
    present = [name for k, name in HEADERS.items() if k in h]
    if "x-frame-options" not in h and "frame-ancestors" in h.get("content-security-policy", ""):
        present.append("X-Frame-Options")
    missing = [n for n in HEADERS.values() if n not in present]
    checks.append(Check("security_headers", "Security Headers", "pass" if len(present) >= 5 else "warn" if len(present) >= 3 else "fail",
                        f"{len(present)}/6 security headers set" + (f"; missing: {', '.join(missing)}." if missing else "."),
                        "Add missing headers at your host/CDN (Cloudflare Transform Rules, Vercel/Netlify headers config).",
                        "medium", "easy", pages=missing))

    # Vulnerabilities
    vulns = []
    for lib, (rx, safe) in LIBS.items():
        for m in re.finditer(rx, html, re.I):
            v = next(g for g in m.groups() if g)
            if ver(v) < safe:
                vulns.append(f"{lib} {v} (update to ≥{'.'.join(map(str, safe))})")
                break
    if site.is_https and home and home.soup:
        mixed = [t.get("src") or t.get("href") for t in home.soup.find_all(["img", "script", "link", "iframe"])
                 if (t.get("src") or t.get("href") or "").startswith("http://")]
        if mixed:
            vulns.append(f"{len(mixed)} mixed-content (http://) resource(s)")
    for hk in ("server", "x-powered-by", "x-aspnet-version"):
        if re.search(r"\d", h.get(hk, "")):
            vulns.append(f"{hk} header discloses version: {h[hk]}")
    sc = h.get("set-cookie", "")
    if sc and ("secure" not in sc.lower() or "httponly" not in sc.lower()):
        vulns.append("cookie set without Secure/HttpOnly")
    checks.append(Check("vulnerabilities", "Vulnerabilities", "pass" if not vulns else "warn" if len(vulns) <= 2 else "fail",
                        "No known-vulnerable libraries or leaks detected." if not vulns else f"{len(vulns)} issue(s) found.",
                        "Update outdated libraries, remove version banners, serve all assets over HTTPS.", "high", "medium",
                        pages=vulns))

    # Plugins & themes (CMS fingerprint)
    gen = home.soup.find("meta", attrs={"name": "generator"}) if home and home.soup else None
    gen_v = gen.get("content", "") if gen else ""
    plugins = sorted(set(re.findall(r"/wp-content/plugins/([a-z0-9_-]+)/", html)))
    theme = re.search(r"/wp-content/themes/([a-z0-9_-]+)/", html)
    cms = "WordPress" if "wp-content" in html else "Framer" if "framer" in html.lower() and "framerusercontent" in html else \
          "Webflow" if "webflow" in html.lower() else "Shopify" if "cdn.shopify" in html else gen_v.split(" ")[0] or "Unknown"
    if cms == "WordPress":
        exposed_ver = bool(re.search(r"\d", gen_v)) or bool(re.search(r"ver=\d", html))
        st = "warn" if exposed_ver or len(plugins) > 15 else "pass"
        det = f"WordPress with {len(plugins)} detectable plugin(s)" + (f", theme '{theme.group(1)}'" if theme else "") + \
              ("; version numbers exposed." if exposed_ver else ".")
        checks.append(Check("plugins_themes", "Plugins & Themes", st, det,
                            "Keep core/plugins/themes updated, remove unused plugins, hide version strings.", "high", "easy",
                            pages=plugins[:15]))
    else:
        checks.append(Check("plugins_themes", "Plugins & Themes", "pass",
                            f"Platform: {cms}. Hosted/managed platform — no exposed plugin versions." if cms != "Unknown"
                            else "No CMS plugin/theme fingerprints exposed."))

    # Access control
    crit = [p for p in ("/.git/HEAD", "/.env", "/wp-config.php.bak", "/phpinfo.php", "/server-status") if site.exposed.get(p)]
    soft = [p for p in ("/xmlrpc.php", "/wp-login.php", "/admin") if site.exposed.get(p)]
    listing = any("<title>Index of /" in p.html for p in site.pages)
    if crit or listing:
        checks.append(Check("access_control", "Access Control", "fail",
                            "Sensitive files publicly accessible: " + ", ".join(crit + (["directory listing"] if listing else [])),
                            "Block these paths immediately at the server and rotate any exposed secrets.", "high", "easy", pages=crit))
    else:
        checks.append(Check("access_control", "Access Control", "warn" if soft else "pass",
                            "Default login/XML-RPC endpoints are public: " + ", ".join(soft) if soft else "No exposed sensitive files or admin endpoints found.",
                            "Move/rate-limit admin login, enable 2FA, disable XML-RPC if unused." if soft else "", "medium", "easy",
                            pages=soft))

    area = AreaResult(8, "security", "Security", checks, "Security Score", weight=10)
    area.compute_score()
    area.key_metric_value = f"{area.score}/100"
    return area
