"""Async crawler: collects everything the checks need in one pass."""
from __future__ import annotations

import asyncio
import re
import socket
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

UA = "SiteAuditAgent/1.0 (+https://brightajiboye.com)"
SKIP_EXT = re.compile(r"\.(jpg|jpeg|png|gif|webp|avif|svg|ico|pdf|zip|rar|mp4|mp3|mov|webm|css|js|json|xml|txt|woff2?|ttf|eot)(\?|$)", re.I)


@dataclass
class Page:
    url: str
    final_url: str
    status: int
    headers: dict
    html: str
    ttfb_ms: float
    total_ms: float
    size_bytes: int
    redirects: list[str] = field(default_factory=list)
    soup: Optional[BeautifulSoup] = None
    text: str = ""
    word_count: int = 0
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)

    @property
    def is_html(self) -> bool:
        return "html" in self.headers.get("content-type", "").lower()


@dataclass
class Asset:
    url: str
    kind: str          # css | js | img
    status: int = 0
    size: int = 0
    headers: dict = field(default_factory=dict)
    body: str = ""     # css/js only (first 200KB)


@dataclass
class SiteData:
    start_url: str
    origin: str
    host: str
    pages: list[Page] = field(default_factory=list)
    robots_status: int = 0
    robots_txt: str = ""
    robots: Optional[RobotFileParser] = None
    sitemap_url: str = ""
    sitemap_urls: list[str] = field(default_factory=list)
    sitemap_lastmods: list[str] = field(default_factory=list)
    link_status: dict = field(default_factory=dict)          # url -> status
    link_sources: dict = field(default_factory=dict)         # url -> [source pages]
    http_to_https: Optional[bool] = None
    ssl_info: dict = field(default_factory=dict)
    exposed: dict = field(default_factory=dict)              # path -> finding
    assets: list[Asset] = field(default_factory=list)
    psi: dict = field(default_factory=dict)                  # strategy -> parsed PSI
    browser: dict = field(default_factory=dict)              # viewport -> rendered metrics
    ai: dict = field(default_factory=dict)                   # AI evaluations
    errors: list[str] = field(default_factory=list)

    @property
    def home(self) -> Optional[Page]:
        return self.pages[0] if self.pages else None

    @property
    def html_pages(self) -> list[Page]:
        return [p for p in self.pages if p.status == 200 and p.soup is not None]

    @property
    def is_https(self) -> bool:
        return self.origin.startswith("https://")


def normalize(url: str) -> str:
    url, _ = urldefrag(url)
    p = urlparse(url)
    path = p.path or "/"
    return f"{p.scheme}://{p.netloc.lower()}{path}" + (f"?{p.query}" if p.query else "")


def same_site(url: str, host: str) -> bool:
    h = urlparse(url).netloc.lower()
    return h == host or h == f"www.{host}" or f"www.{h}" == host


class Crawler:
    def __init__(self, url: str, max_pages: int = 25, max_link_checks: int = 200, timeout: float = 15.0):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.start = normalize(url)
        p = urlparse(self.start)
        self.site = SiteData(start_url=self.start, origin=f"{p.scheme}://{p.netloc}", host=p.netloc.lower())
        self.max_pages = max_pages
        self.max_link_checks = max_link_checks
        self.client = httpx.AsyncClient(
            headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"},
            timeout=timeout, follow_redirects=True, verify=True,
            limits=httpx.Limits(max_connections=10),
        )
        self.sem = asyncio.Semaphore(8)

    # ---------------- fetch helpers ----------------
    async def fetch_page(self, url: str) -> Optional[Page]:
        async with self.sem:
            t0 = time.perf_counter()
            try:
                async with self.client.stream("GET", url) as r:
                    ttfb = (time.perf_counter() - t0) * 1000
                    body = await r.aread()
                    total = (time.perf_counter() - t0) * 1000
                    headers = {k.lower(): v for k, v in r.headers.items()}
                    page = Page(url=url, final_url=normalize(str(r.url)), status=r.status_code, headers=headers,
                                html="", ttfb_ms=round(ttfb), total_ms=round(total), size_bytes=len(body),
                                redirects=[str(h.url) for h in r.history])
                    if page.is_html:
                        page.html = body.decode(r.encoding or "utf-8", errors="replace")
                    return page
            except Exception as e:  # network errors are findings, not crashes
                self.site.errors.append(f"{url}: {type(e).__name__}: {e}")
                return Page(url=url, final_url=url, status=0, headers={}, html="", ttfb_ms=0, total_ms=0, size_bytes=0)

    async def get_text(self, url: str, limit: int = 2_000_000) -> tuple[int, str, dict]:
        try:
            async with self.sem:
                r = await self.client.get(url)
                return r.status_code, r.text[:limit], {k.lower(): v for k, v in r.headers.items()}
        except Exception:
            return 0, "", {}

    async def head_status(self, url: str) -> int:
        async with self.sem:
            try:
                r = await self.client.head(url)
                if r.status_code in (405, 403, 501):
                    r = await self.client.get(url)
                return r.status_code
            except Exception:
                return 0

    # ---------------- parse ----------------
    def parse(self, page: Page) -> None:
        if not page.html:
            return
        soup = BeautifulSoup(page.html, "lxml")
        page.soup = soup
        body = soup.body or soup
        clone = BeautifulSoup(str(body), "lxml")
        for t in clone(["script", "style", "noscript", "svg", "template"]):
            t.decompose()
        page.text = re.sub(r"\s+", " ", clone.get_text(" ")).strip()
        page.word_count = len(re.findall(r"[A-Za-zÀ-ɏ؀-ۿ]{2,}", page.text))
        base = page.final_url
        if (b := soup.find("base", href=True)):
            base = urljoin(base, b["href"])
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("mailto:", "tel:", "javascript:", "#", "data:")) or not href:
                continue
            absu = normalize(urljoin(base, href))
            if absu.startswith("http"):
                (page.internal_links if same_site(absu, self.site.host) else page.external_links).append(absu)

    # ---------------- stages ----------------
    async def crawl_pages(self) -> None:
        queue, seen = [self.start], {self.start}
        robots = self.site.robots
        while queue and len(self.site.pages) < self.max_pages:
            batch = queue[: max(1, self.max_pages - len(self.site.pages))][:8]
            queue = queue[len(batch):]
            results = await asyncio.gather(*(self.fetch_page(u) for u in batch))
            for page in results:
                if not page:
                    continue
                self.parse(page)
                self.site.pages.append(page)
                self.site.link_status[page.url] = page.status
                for link in page.internal_links:
                    self.site.link_sources.setdefault(link, [])
                    if page.url not in self.site.link_sources[link]:
                        self.site.link_sources[link].append(page.url)
                    if link not in seen and not SKIP_EXT.search(link):
                        if robots and not robots.can_fetch(UA, link) and not robots.can_fetch("*", link):
                            continue
                        seen.add(link)
                        queue.append(link)
                for link in page.external_links:
                    self.site.link_sources.setdefault(link, []).append(page.url)

    async def load_robots_and_sitemap(self) -> None:
        status, text, _ = await self.get_text(urljoin(self.site.origin, "/robots.txt"))
        self.site.robots_status = status
        if status == 200 and "<html" not in text[:500].lower():
            self.site.robots_txt = text
            rp = RobotFileParser()
            rp.parse(text.splitlines())
            self.site.robots = rp
        candidates = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", self.site.robots_txt)
        candidates += [urljoin(self.site.origin, p) for p in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml")]
        for sm in dict.fromkeys(candidates):
            st, xml, _ = await self.get_text(sm)
            if st == 200 and "<urlset" in xml or (st == 200 and "<sitemapindex" in xml):
                self.site.sitemap_url = sm
                locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)
                if "<sitemapindex" in xml:  # follow first 3 child sitemaps
                    child_locs = []
                    for child in locs[:3]:
                        cst, cxml, _ = await self.get_text(child)
                        if cst == 200:
                            child_locs += re.findall(r"<loc>\s*(.*?)\s*</loc>", cxml)
                            self.site.sitemap_lastmods += re.findall(r"<lastmod>\s*(.*?)\s*</lastmod>", cxml)
                    locs = child_locs
                self.site.sitemap_urls = locs
                self.site.sitemap_lastmods += re.findall(r"<lastmod>\s*(.*?)\s*</lastmod>", xml)
                break

    async def check_links(self) -> None:
        targets = [u for u in self.site.link_sources if u not in self.site.link_status]
        internal = [u for u in targets if same_site(u, self.site.host)]
        external = [u for u in targets if not same_site(u, self.site.host)]
        targets = (internal + external[:40])[: self.max_link_checks]
        statuses = await asyncio.gather(*(self.head_status(u) for u in targets))
        self.site.link_status.update(dict(zip(targets, statuses)))

    async def check_https_redirect(self) -> None:
        if not self.site.is_https:
            self.site.http_to_https = False
            return
        http_url = "http://" + self.site.host + "/"
        try:
            async with httpx.AsyncClient(follow_redirects=False, timeout=10, headers={"User-Agent": UA}) as c:
                r = await c.get(http_url)
                loc = r.headers.get("location", "")
                self.site.http_to_https = r.status_code in (301, 302, 307, 308) and loc.startswith("https://")
        except Exception:
            self.site.http_to_https = None

    async def check_ssl(self) -> None:
        if not self.site.is_https:
            self.site.ssl_info = {"valid": False, "error": "Site not served over HTTPS"}
            return
        host = urlparse(self.site.origin).hostname
        port = urlparse(self.site.origin).port or 443

        def _get():
            ctx = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as s:
                    return s.getpeercert(), s.version()
        try:
            cert, proto = await asyncio.to_thread(_get)
            exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            issuer = dict(x[0] for x in cert.get("issuer", []))
            self.site.ssl_info = {"valid": True, "expires": exp.isoformat(), "protocol": proto,
                                  "days_left": (exp - datetime.now(timezone.utc)).days,
                                  "issuer": issuer.get("organizationName", "")}
        except ssl.SSLCertVerificationError as e:
            self.site.ssl_info = {"valid": False, "error": str(e)}
        except Exception as e:
            self.site.ssl_info = {"valid": None, "error": f"Could not connect: {e}"}

    async def check_exposed_paths(self) -> None:
        probes = {
            "/.git/HEAD": lambda s, t, h: s == 200 and t.startswith("ref:"),
            "/.env": lambda s, t, h: s == 200 and "html" not in h.get("content-type", "") and re.search(r"^[A-Z_]+=", t, re.M),
            "/wp-config.php.bak": lambda s, t, h: s == 200 and "DB_PASSWORD" in t,
            "/phpinfo.php": lambda s, t, h: s == 200 and "phpinfo()" in t,
            "/server-status": lambda s, t, h: s == 200 and "Apache Server Status" in t,
            "/xmlrpc.php": lambda s, t, h: s in (200, 405) and "XML-RPC" in t,
            "/wp-login.php": lambda s, t, h: s == 200 and "user_login" in t,
            "/admin": lambda s, t, h: s == 200 and re.search(r"type=[\"']password", t, re.I),
        }
        async def probe(path, test):
            s, t, h = await self.get_text(urljoin(self.site.origin, path), limit=20000)
            return path, bool(test(s, t, h))
        for path, hit in await asyncio.gather(*(probe(p, f) for p, f in probes.items())):
            self.site.exposed[path] = hit

    async def collect_assets(self, limit_each: int = 12) -> None:
        home = self.site.home
        if not home or not home.soup:
            return
        base = home.final_url
        css = [urljoin(base, l["href"]) for l in home.soup.find_all("link", href=True)
               if "stylesheet" in (l.get("rel") or [])][:limit_each]
        js = [urljoin(base, s["src"]) for s in home.soup.find_all("script", src=True)][:limit_each]
        imgs = []
        for im in home.soup.find_all("img"):
            src = im.get("src") or im.get("data-src") or ""
            if src and not src.startswith("data:"):
                imgs.append(urljoin(base, src))
        imgs = list(dict.fromkeys(imgs))[: limit_each * 2]

        async def get_asset(url, kind):
            a = Asset(url=url, kind=kind)
            async with self.sem:
                try:
                    if kind == "img":
                        r = await self.client.head(url)
                        if r.status_code >= 400 or "content-length" not in r.headers:
                            r = await self.client.get(url)
                            a.size = len(r.content)
                        else:
                            a.size = int(r.headers.get("content-length", 0))
                    else:
                        r = await self.client.get(url)
                        a.size = len(r.content)
                        a.body = r.text[:200_000]
                    a.status = r.status_code
                    a.headers = {k.lower(): v for k, v in r.headers.items()}
                except Exception:
                    a.status = 0
            return a
        tasks = [get_asset(u, "css") for u in css] + [get_asset(u, "js") for u in js] + [get_asset(u, "img") for u in imgs]
        self.site.assets = list(await asyncio.gather(*tasks))

    async def run(self) -> SiteData:
        try:
            await self.load_robots_and_sitemap()
            await self.crawl_pages()
            await asyncio.gather(self.check_links(), self.check_https_redirect(), self.check_ssl(),
                                 self.check_exposed_paths(), self.collect_assets())
        finally:
            await self.client.aclose()
        return self.site
