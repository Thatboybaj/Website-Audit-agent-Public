"""7. Content Quality — relevance, clarity, freshness, thin content, format, keyword targeting.
Uses Claude for relevance/clarity when ANTHROPIC_API_KEY is set; heuristics otherwise."""
import hashlib
import re
from collections import Counter
from datetime import datetime

from ..crawler import SiteData
from ..models import AreaResult, Check
from ._util import flesch, main_text, ratio_status, threshold, short

STOP = set("the a an and or for to of in on with your you our we is are be at by from this that it as best top how what".split())


def grade(score: int) -> str:
    return "A+" if score >= 95 else "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"


def run(site: SiteData) -> AreaResult:
    checks: list[Check] = []
    pages = site.html_pages
    home = site.home
    ai = site.ai.get("content") or {}
    text = main_text(home) if home and home.soup else ""

    # Relevant to audience
    if ai.get("relevance") is not None:
        r = ai["relevance"]
        checks.append(Check("relevance", "Relevant to Audience", threshold(r, 8, 5), f"AI rating {r}/10 — {ai.get('relevance_note', '')}",
                            ai.get("relevance_fix") or "Speak to one audience's problems and desired outcomes.", "high", "medium"))
    else:
        you = len(re.findall(r"\byou(r|rs)?\b", text, re.I))
        we = len(re.findall(r"\b(we|our|us|i|my)\b", text, re.I))
        ratio = you / max(1, we)
        checks.append(Check("relevance", "Relevant to Audience", threshold(ratio, 1.0, 0.5),
                            f"Customer focus: {you} 'you/your' vs {we} 'we/our/I' mentions (ratio {ratio:.1f}; aim ≥1).",
                            "Rewrite copy around the reader's problem and outcome ('you get…') rather than about yourself.",
                            "high", "medium"))

    # Clear & helpful
    fl = flesch(text)
    if ai.get("clarity") is not None:
        checks.append(Check("clarity", "Clear & Helpful", threshold(ai["clarity"], 8, 5), f"AI rating {ai['clarity']}/10 — {ai.get('clarity_note', '')}",
                            ai.get("clarity_fix") or "State what you do, for whom, and the next step.", "medium", "medium"))
    else:
        helpful = bool(re.search(r"faq|frequently asked|how it works|process|step \d|pricing", text, re.I))
        st = "pass" if (fl or 0) >= 50 and helpful else "warn" if (fl or 0) >= 35 or helpful else "fail"
        checks.append(Check("clarity", "Clear & Helpful", st,
                            f"Readability {fl if fl is not None else 'n/a'}; FAQ/process/pricing content: {'yes' if helpful else 'no'}.",
                            "Add a 'How it works' section and FAQ answering real buyer objections.", "medium", "medium"))

    # Up to date
    year = datetime.now().year
    years = [int(y) for p in pages for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", p.html, re.I)]
    newest_lastmod = max((l[:10] for l in site.sitemap_lastmods), default="")
    stale = bool(years) and min(years) < year - 1
    old_lastmod = newest_lastmod and newest_lastmod < f"{year - 1}-{datetime.now():%m-%d}"
    st = "fail" if stale and old_lastmod else "warn" if stale or old_lastmod else "pass"
    checks.append(Check("up_to_date", "Up-to-Date", st,
                        f"Oldest footer copyright year: {min(years) if years else 'none'}; newest sitemap lastmod: {newest_lastmod or 'n/a'}.",
                        "Update the copyright year automatically, refresh stats/case studies and remove outdated offers.",
                        "low", "easy"))

    # No thin content + duplicates
    thin = [f"{short(p.url, site)} ({p.word_count} words)" for p in pages if p.word_count < 300]
    hashes = Counter(hashlib.md5(main_text(p)[:5000].encode()).hexdigest() for p in pages if p.word_count > 50)
    dups = sum(c - 1 for c in hashes.values() if c > 1)
    st = ratio_status(len(pages) - len(thin), len(pages), 0.85, 0.6)
    if dups and st == "pass":
        st = "warn"
    checks.append(Check("thin_content", "No Thin Content", st,
                        f"{len(thin)} thin page(s) under 300 words; {dups} near-duplicate page(s).",
                        "Merge or expand thin pages; give every page a unique purpose.", "medium", "medium", pages=thin[:8]))

    # Engaging format
    walls = []
    for p in pages:
        if p.word_count < 150:
            continue
        heads = len(p.soup.find_all(["h2", "h3"]))
        media = len(p.soup.find_all(["img", "video", "picture", "iframe"]))
        lists = len(p.soup.find_all(["ul", "ol"]))
        if heads < p.word_count / 400 or (media == 0 and lists == 0):
            walls.append(f"{short(p.url, site)} — {p.word_count} words, {heads} subheads, {media} media")
    eligible = len([p for p in pages if p.word_count >= 150])
    checks.append(Check("engaging_format", "Engaging Format", ratio_status(eligible - len(walls), eligible, 0.85, 0.6),
                        f"{eligible - len(walls)}/{eligible} content pages use subheadings, lists or media to break up text.",
                        "Add a subheading every ~300 words, bullets, visuals and pull-quotes.", "low", "easy", pages=walls[:8]))

    # Keyword targeting
    misses = []
    for p in pages:
        t = (p.soup.title.string or "") if p.soup.title and p.soup.title.string else ""
        kws = [w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in STOP][:3]
        if not kws:
            misses.append(f"{short(p.url, site)} — no keyword in title")
            continue
        h1 = (p.soup.find("h1").get_text(" ") if p.soup.find("h1") else "").lower()
        first = " ".join(p.text.lower().split()[:150])
        if not any(k in h1 for k in kws) or not any(k in first for k in kws):
            misses.append(f"{short(p.url, site)} — '{kws[0]}' not in H1/intro")
    checks.append(Check("keyword_targeting", "Keyword Targeting", ratio_status(len(pages) - len(misses), len(pages), 0.8, 0.5),
                        f"{len(pages) - len(misses)}/{len(pages)} pages repeat their title keyword in the H1 and opening copy.",
                        "Pick one primary keyword per page and use it in title, H1, URL, intro and an image alt.", "medium", "easy",
                        pages=misses[:8]))

    area = AreaResult(7, "content", "Content Quality", checks, "Content Score", weight=10)
    area.compute_score()
    area.key_metric_value = grade(area.score)
    return area
