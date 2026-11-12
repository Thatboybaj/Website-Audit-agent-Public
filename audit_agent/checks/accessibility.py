"""9. Accessibility — alt text, contrast, keyboard, readable fonts, ARIA labels, screen-reader readiness."""
import re

from ..crawler import SiteData
from ..models import AreaResult, Check
from ._util import bm, psi_audit, psi_cat, ratio_status, threshold, all_html


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    pages = site.html_pages
    home = site.home
    m = bm(site, "desktop") or bm(site, "mobile")

    # Alt text (meaningful)
    imgs = [i for p in pages for i in p.soup.find_all("img")]
    bad = [i for i in imgs if not i.has_attr("alt") or re.fullmatch(r"(image|img|photo|picture|\S+\.(jpe?g|png|webp|gif))", i.get("alt", "").strip(), re.I)]
    checks.append(Check("alt_text", "Alt Text for Images", ratio_status(len(imgs) - len(bad), len(imgs), 0.95, 0.8),
                        f"{len(imgs) - len(bad)}/{len(imgs)} images have meaningful (or intentionally empty) alt text.",
                        "Describe what the image shows/means; use alt=\"\" only for decoration.", "high", "easy",
                        pages=list({i.get('src', '')[:90] for i in bad})[:8]))

    # Color contrast
    if m and m["textElements"]:
        low = m["lowContrast"]
        ratio = low / m["textElements"]
        checks.append(Check("contrast", "Color Contrast", threshold(ratio, 0.02, 0.1, False),
                            f"{low}/{m['textElements']} text elements fail WCAG AA contrast (4.5:1, 3:1 large).",
                            "Darken light-grey text / adjust button colours to reach ≥4.5:1.", "high", "easy",
                            pages=m["contrastSamples"]))
    elif (a := psi_audit(site, "color-contrast")):
        checks.append(Check("contrast", "Color Contrast", "pass" if a["score"] == 1 else "fail", "Lighthouse color-contrast audit.",
                            "Raise text/background contrast to ≥4.5:1.", "high", "easy"))
    else:
        checks.append(Check("contrast", "Color Contrast", "skip", "Needs browser rendering or PSI."))

    # Keyboard navigation
    html = all_html(site) + "\n".join(a.body for a in site.assets if a.kind == "css")
    issues = []
    pos_tab = len(re.findall(r"tabindex=[\"']?[1-9]", html))
    if pos_tab:
        issues.append(f"{pos_tab} positive tabindex value(s)")
    if re.search(r":focus\s*\{[^}]*outline:\s*(none|0)", html) and ":focus-visible" not in html:
        issues.append("focus outline removed without :focus-visible replacement")
    clickable_divs = sum(len(p.soup.find_all(["div", "span"], onclick=True)) for p in pages)
    if clickable_divs:
        issues.append(f"{clickable_divs} clickable div/span without keyboard support")
    skip = home and home.soup and home.soup.find("a", href=re.compile(r"^#(main|content|skip)", re.I))
    if not skip:
        issues.append("no 'skip to content' link")
    checks.append(Check("keyboard", "Keyboard Navigation", "pass" if len(issues) <= 1 and not pos_tab else "warn" if len(issues) <= 2 else "fail",
                        "Keyboard-friendly." if not issues else "; ".join(issues).capitalize() + ".",
                        "Use real <button>/<a> elements, keep visible focus styles, add a skip link, avoid positive tabindex.",
                        "medium", "easy"))

    # Readable fonts
    if m and m["textElements"]:
        checks.append(Check("readable_fonts", "Readable Fonts", threshold(m["tinyText"] / m["textElements"], 0.03, 0.12, False),
                            f"Smallest rendered text {m['minFont']}px; {m['tinyText']} text blocks under 12px.",
                            "Body text ≥16px, line-height ≥1.5, avoid thin weights on light backgrounds.", "medium", "easy"))
    else:
        tiny = [s for s in re.findall(r"font-size:\s*([0-9.]+)px", html) if float(s) < 12]
        checks.append(Check("readable_fonts", "Readable Fonts", "warn" if tiny else "pass",
                            f"{len(tiny)} declarations under 12px (static scan).", "Body text ≥16px.", "medium", "easy"))

    # ARIA labels / accessible names
    unnamed = []
    for p in pages:
        for el in p.soup.find_all(["a", "button"]):
            name = el.get_text(" ", strip=True) or el.get("aria-label") or el.get("aria-labelledby") or el.get("title")
            if not name:
                img = el.find("img", alt=True)
                name = img.get("alt") if img else ""
            if not name:
                unnamed.append(f"<{el.name}> {str(el.get('href') or el.get('class') or '')[:60]}")
        for i in p.soup.find_all(["input", "select", "textarea"]):
            if (i.get("type") or "").lower() in ("hidden", "submit", "button", "image"):
                continue
            iid = i.get("id")
            if not (i.get("aria-label") or i.get("aria-labelledby") or (iid and p.soup.find("label", attrs={"for": iid})) or i.find_parent("label")):
                unnamed.append(f"<{i.name} name='{i.get('name', '')}'> without label")
    checks.append(Check("aria_labels", "Aria Labels", "pass" if not unnamed else "warn" if len(unnamed) <= 5 else "fail",
                        f"{len(unnamed)} interactive element(s) without an accessible name (icon links, unlabeled inputs).",
                        "Add aria-label to icon-only links/buttons and <label> to every form field.", "medium", "easy",
                        pages=list(dict.fromkeys(unnamed))[:8]))

    # Screen-reader readiness
    sr = []
    if home and home.soup:
        s = home.soup
        if not (s.html and s.html.get("lang")):
            sr.append("missing <html lang>")
        for lm, sel in (("main", "main"), ("nav", "nav"), ("header", "header"), ("footer", "footer")):
            if not s.find(sel) and not s.find(attrs={"role": {"main": "main", "nav": "navigation", "header": "banner", "footer": "contentinfo"}[lm]}):
                sr.append(f"no <{lm}> landmark")
        if not s.title:
            sr.append("missing <title>")
    psi_a11y = psi_cat(site, "accessibility")
    det = ("Landmarks, lang and title present." if not sr else "; ".join(sr).capitalize() + ".") + \
          (f" Lighthouse accessibility: {psi_a11y}/100." if psi_a11y is not None else "")
    st = "pass" if not sr else "warn" if len(sr) <= 2 else "fail"
    if psi_a11y is not None and psi_a11y < 70:
        st = "fail"
    checks.append(Check("screen_reader", "Screen Reader Test", st, det,
                        "Use semantic HTML5 landmarks and lang attribute; then test with VoiceOver/NVDA for 5 minutes.",
                        "medium", "easy"))

    area = AreaResult(9, "accessibility", "Accessibility", checks, "Accessibility Score", weight=8)
    area.compute_score()
    sc = area.score
    area.key_metric_value = "A" if sc >= 90 else "B" if sc >= 75 else "C" if sc >= 60 else "D" if sc >= 45 else "F"
    return area
