"""Command line: python -m audit_agent https://example.com [options]"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from urllib.parse import urlparse

from .agent import run_audit
from .report_md import to_json, to_markdown

try:
    from .report_html import to_html
    HAS_HTML = True
except ImportError:  # No-HTML edition
    HAS_HTML = False


def load_env(path: str = ".env") -> None:
    if os.path.exists(path):
        for line in open(path):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", urlparse(url if "//" in url else "https://" + url).netloc.lower()).strip("-")


async def audit_one(url: str, a) -> dict:
    report = await run_audit(url, max_pages=a.pages, use_psi=not a.no_psi, use_browser=not a.no_browser,
                             use_ai=not a.no_ai, compare_path=a.compare, sender=a.sender,
                             log=(lambda *_: None) if a.quiet else print)
    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, f"{slug(url)}-{report['audited_at'][:10]}")
    formats = [f.strip() for f in a.format.split(",")]
    if "json" in formats:
        open(base + ".json", "w").write(to_json(report))
    if "md" in formats:
        open(base + ".md", "w").write(to_markdown(report))
    if "html" in formats:
        if HAS_HTML:
            open(base + ".html", "w").write(to_html(report, brand=a.brand, show_email=a.show_email))
        else:
            print("  (HTML not available in the No-HTML edition — skipped)")
    print(f"  saved → {base}.{{{','.join(f for f in formats if f != 'html' or HAS_HTML)}}}")
    return report


def main() -> None:
    load_env()
    p = argparse.ArgumentParser(prog="audit_agent", description="Website audit agent — 10 core areas, health score, action plan.")
    p.add_argument("url", nargs="?", help="Site to audit (or use --batch)")
    p.add_argument("--batch", help="Text file with one URL per line (prospect list)")
    p.add_argument("--pages", type=int, default=25, help="Max pages to crawl (default 25)")
    p.add_argument("--format", default="html,md,json" if HAS_HTML else "md,json", help="Comma list: html,md,json")
    p.add_argument("--out", default="reports", help="Output folder")
    p.add_argument("--compare", help="Previous JSON report to show progress (re-audit)")
    p.add_argument("--no-psi", action="store_true", help="Skip Google PageSpeed Insights")
    p.add_argument("--no-browser", action="store_true", help="Skip headless-browser rendering")
    p.add_argument("--no-ai", action="store_true", help="Skip Claude (summary/content/email use templates)")
    p.add_argument("--sender", default=os.getenv("AUDIT_SENDER", "Bright"), help="Name used in the outreach email")
    p.add_argument("--brand", default=os.getenv("AUDIT_BRAND", "brightajiboye.com"), help="Footer brand on HTML report")
    p.add_argument("--show-email", action="store_true", help="Include the outreach email in the HTML report")
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args()

    urls = [a.url] if a.url else []
    if a.batch:
        urls += [l.strip() for l in open(a.batch) if l.strip() and not l.startswith("#")]
    if not urls:
        p.error("give a URL or --batch file")

    async def go():
        rows = []
        for u in urls:
            try:
                r = await audit_one(u, a)
                rows.append((r["url"], r["overall_score"], r["band"]["label"]))
            except Exception as e:
                print(f"✗ {u}: {e}", file=sys.stderr)
        if len(rows) > 1:
            print("\nBatch results (lowest score = hottest lead):")
            for u, s, b in sorted(rows, key=lambda x: x[1]):
                print(f"  {s:>3}  {b:<18} {u}")
    asyncio.run(go())


if __name__ == "__main__":
    main()
