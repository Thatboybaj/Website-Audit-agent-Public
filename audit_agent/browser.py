"""Rendered-page checks with a headless browser (Playwright). Optional but strongly
recommended: measures tap targets, contrast, font sizes, horizontal scroll, above-the-fold
CTAs and popups the way a real visitor sees them."""
from __future__ import annotations

import base64

VIEWPORTS = {"mobile": {"width": 375, "height": 812}, "desktop": {"width": 1366, "height": 768}}

MEASURE_JS = r"""
() => {
  const CTA = /\b(get|start|book|contact|buy|try|sign ?up|schedule|request|download|shop|join|subscribe|hire|quote|demo|call|order|apply|register|let'?s talk|work with|enquire|inquire)\b/i;
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > 0.05; };
  const W = Math.min(innerWidth, screen.width), H = Math.min(innerHeight, screen.height);
  // horizontal scroll
  const docW = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0, innerWidth);
  const overflowers = [];
  if (docW > W + 2) { for (const el of document.querySelectorAll('body *')) { const r = el.getBoundingClientRect();
      if (r.right > W + 2 && r.width > 0 && overflowers.length < 5) overflowers.push(el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '')); } }
  // tap targets
  const inter = [...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,[role=button],[onclick]')].filter(vis);
  let small24 = 0, small44 = 0; const smallSamples = [];
  for (const el of inter) { const r = el.getBoundingClientRect();
    if (r.width < 24 || r.height < 24) { small24++; if (smallSamples.length < 6) smallSamples.push((el.innerText || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 40) + ` (${Math.round(r.width)}x${Math.round(r.height)})`); }
    if (r.width < 44 || r.height < 44) small44++; }
  // text, fonts, contrast
  const lum = c => { const m = c.match(/[\d.]+/g); if (!m) return null; const [r,g,b] = m.slice(0,3).map(v => { v = v/255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); }); return 0.2126*r + 0.7152*g + 0.0722*b; };
  const alpha = c => { const m = c.match(/[\d.]+/g); return m && m.length > 3 ? parseFloat(m[3]) : 1; };
  const bgOf = el => { while (el) { const s = getComputedStyle(el); if (s.backgroundImage && s.backgroundImage !== 'none') return null; if (alpha(s.backgroundColor) > 0.9) return s.backgroundColor; el = el.parentElement; } return 'rgb(255,255,255)'; };
  let textEls = 0, tiny = 0, lowContrast = 0; const contrastSamples = []; const fonts = new Set(); let minFont = 99;
  for (const el of document.querySelectorAll('body *')) {
    if (!vis(el)) continue;
    const own = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim().length > 1).map(n => n.textContent.trim()).join(' ');
    if (!own) continue;
    textEls++; const s = getComputedStyle(el); const fs = parseFloat(s.fontSize);
    fonts.add(s.fontFamily.split(',')[0].replace(/["']/g, '').trim());
    if (fs < 12) tiny++; minFont = Math.min(minFont, fs);
    const bg = bgOf(el); if (!bg) continue;
    const L1 = lum(s.color), L2 = lum(bg); if (L1 === null || L2 === null) continue;
    const ratio = (Math.max(L1,L2) + 0.05) / (Math.min(L1,L2) + 0.05);
    const large = fs >= 24 || (fs >= 18.66 && parseInt(s.fontWeight) >= 700);
    if (ratio < (large ? 3 : 4.5)) { lowContrast++; if (contrastSamples.length < 6) contrastSamples.push(`"${own.slice(0,40)}" ${ratio.toFixed(2)}:1`); }
  }
  // CTAs above fold
  const ctas = inter.filter(el => CTA.test((el.innerText || el.value || el.getAttribute('aria-label') || '').trim()));
  const aboveFold = ctas.filter(el => { const r = el.getBoundingClientRect(); return r.top < H && r.bottom > 0; });
  // overlays / popups
  let overlay = null;
  for (const el of document.querySelectorAll('body *')) { const s = getComputedStyle(el);
    if ((s.position === 'fixed' || s.position === 'sticky') && vis(el)) { const r = el.getBoundingClientRect();
      const cover = (Math.min(r.right, W) - Math.max(r.left, 0)) * (Math.min(r.bottom, H) - Math.max(r.top, 0)) / (W * H);
      if (cover > 0.3 && (!overlay || cover > overlay.cover)) overlay = { cover: Math.round(cover * 100), el: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.split(' ')[0] : '') }; } }
  const navToggle = [...document.querySelectorAll('button,[role=button],a')].filter(vis).some(el => /menu|nav|hamburger|burger|toggle/i.test((el.getAttribute('aria-label')||'') + ' ' + (el.className||'') + ' ' + (el.id||'') + ' ' + (el.innerText||'')));
  return { viewport: W, docWidth: docW, horizontalScroll: docW > W + 2, overflowers,
    interactive: inter.length, small24, small44, smallSamples,
    textElements: textEls, tinyText: tiny, minFont: minFont === 99 ? null : minFont, fontFamilies: [...fonts].slice(0, 10),
    lowContrast, contrastSamples, ctaCount: ctas.length, ctaAboveFold: aboveFold.length,
    ctaAboveFoldText: aboveFold.slice(0, 3).map(e => (e.innerText || e.value || '').trim().slice(0, 40)),
    overlay, navToggle };
}
"""


async def render(url: str, enabled: bool = True) -> dict:
    if not enabled:
        return {}
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright not installed (pip install playwright && playwright install chromium)"}
    out: dict = {}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            for name, vp in VIEWPORTS.items():
                ctx = await browser.new_context(viewport=vp, is_mobile=(name == "mobile"), has_touch=(name == "mobile"),
                                                device_scale_factor=2 if name == "mobile" else 1)
                page = await ctx.new_page()
                try:
                    await page.goto(url, wait_until="networkidle", timeout=45000)
                except Exception:
                    await page.wait_for_timeout(2000)
                await page.wait_for_timeout(1500)  # let popups/consent banners appear
                out[name] = await page.evaluate(MEASURE_JS)
                shot = await page.screenshot(type="jpeg", quality=55)
                out[name]["screenshot"] = "data:image/jpeg;base64," + base64.b64encode(shot).decode()
                await ctx.close()
            await browser.close()
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out
