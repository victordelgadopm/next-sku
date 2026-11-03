#!/usr/bin/env python3
"""Next SKU browser helper.

Reads public Amazon.com pages in a real Chrome window on your own computer
(not logged in) and returns clean JSON for Claude to analyze.

Commands
  check                         Confirm Playwright and Chrome are ready.
  product ASIN [ASIN ...]       Product page: title, brand, price, rating,
                                review count, best sellers rank, category,
                                bullets, variations, related-product
                                carousels, visible reviews, "Customers say".
  search "keyword" [...]        Search results page: every organic and
                                sponsored result with brand, price, rating,
                                reviews and "bought in past month".
  brand "Brand Name" [...]      Approximates a brand's catalog by searching
                                the brand name and keeping that brand's items.
  autocomplete "prefix" [...]   Amazon search suggestions for each prefix.
                                --expand also tries "prefix a" ... "prefix z".

Common options
  --out DIR        Folder for this run. Raw JSON is saved to DIR/raw/.
  --pages N        Result pages to read for search/brand (default 1 / 2).
  --headless       Hide the browser window (more likely to get blocked).

Each command prints JSON to stdout. Text fields are trimmed so the output
stays readable; the files in DIR/raw/ hold the same data.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import string
import sys
import time
import urllib.parse
from pathlib import Path

BASE = "https://www.amazon.com"
PROFILE_DIR = Path(os.environ.get("NEXTSKU_PROFILE", Path.home() / ".next-sku" / "browser-profile"))
CAPTCHA_WAIT_SECONDS = 120


# --------------------------------------------------------------------------
# Browser
# --------------------------------------------------------------------------

def _require_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        print(
            "Playwright is not installed. Run:\n"
            "  python -m pip install playwright\n"
            "then run this command again.",
            file=sys.stderr,
        )
        sys.exit(3)


class Browser:
    """One real browser window, reused for every page in a command."""

    def __init__(self, headless: bool = False):
        from playwright.sync_api import sync_playwright

        self.headless = headless
        self._pw = sync_playwright().start()
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        opts = dict(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled"],
        )
        custom = os.environ.get("NEXTSKU_BROWSER_PATH")
        attempts = [{"executable_path": custom}] if custom else [
            {"channel": "chrome"},
            {"channel": "msedge"},
            {},  # Playwright's own Chromium, if installed
        ]
        last_err = None
        for extra in attempts:
            try:
                self.ctx = self._pw.chromium.launch_persistent_context(**opts, **extra)
                self.engine = extra.get("channel") or ("custom" if custom else "chromium")
                break
            except Exception as err:  # try the next option
                last_err = err
        else:
            self._pw.stop()
            print(
                "Could not open a browser. Install Google Chrome, or run:\n"
                "  python -m playwright install chromium\n"
                f"Details: {last_err}",
                file=sys.stderr,
            )
            sys.exit(4)
        self.page = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        self._first = True

    def close(self):
        try:
            self.ctx.close()
        finally:
            self._pw.stop()

    def goto(self, url: str) -> dict:
        """Open a page at a human pace. Returns {"ok": bool, "status": str}."""
        if not self._first:
            time.sleep(random.uniform(2.5, 5.0))
        self._first = False
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception as err:
            return {"ok": False, "status": f"load_error: {err.__class__.__name__}"}
        self._settle()
        state = self._page_state()
        if state == "captcha":
            if self.headless:
                return {"ok": False, "status": "captcha"}
            print(
                "\nAmazon wants to confirm you're human. Please solve the check in "
                f"the Chrome window. Waiting up to {CAPTCHA_WAIT_SECONDS} seconds...",
                file=sys.stderr,
            )
            deadline = time.time() + CAPTCHA_WAIT_SECONDS
            while time.time() < deadline:
                time.sleep(3)
                state = self._page_state()
                if state != "captcha":
                    break
            if state == "captcha":
                return {"ok": False, "status": "captcha"}
            self._settle()
        if state == "error":
            return {"ok": False, "status": "amazon_error_page"}
        return {"ok": True, "status": "ok"}

    def _settle(self):
        """Scroll down in steps so lazy sections (carousels, reviews) load."""
        try:
            for frac in (0.25, 0.5, 0.75, 1.0):
                self.page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {frac})")
                time.sleep(random.uniform(0.4, 0.8))
            self.page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

    def _page_state(self) -> str:
        try:
            return self.page.evaluate(
                """() => {
                  const t = (document.title || '').toLowerCase();
                  const body = (document.body && document.body.innerText || '').slice(0, 3000).toLowerCase();
                  if (document.querySelector('form[action*="validateCaptcha"]') ||
                      t.includes('robot check') ||
                      body.includes('enter the characters you see below') ||
                      body.includes("confirm you're not a robot") ||
                      body.includes('continue shopping') && body.includes('click the button below')) return 'captcha';
                  if (t.includes('page not found') || body.includes("sorry! something went wrong") ||
                      body.includes("we couldn't find that page")) return 'error';
                  return 'ok';
                }"""
            )
        except Exception:
            return "ok"


# --------------------------------------------------------------------------
# In-page extractors (run inside the browser)
# --------------------------------------------------------------------------

PRODUCT_JS = r"""
() => {
  const q = (s, r = document) => r.querySelector(s);
  const qa = (s, r = document) => Array.from(r.querySelectorAll(s));
  const txt = (el) => el ? el.textContent.replace(/\s+/g, ' ').trim() : null;
  const out = {};

  out.title = txt(q('#productTitle'));
  let by = txt(q('#bylineInfo'));
  if (by) by = by.replace(/^Visit the\s+/i, '').replace(/\s+Store$/i, '').replace(/^Brand:\s*/i, '');
  out.brand = by;
  out.price = txt(q('#corePrice_feature_div .a-price .a-offscreen')) ||
              txt(q('#corePriceDisplay_desktop_feature_div .a-price .a-offscreen')) ||
              txt(q('#apex_desktop .a-price .a-offscreen')) ||
              txt(q('.a-price .a-offscreen'));
  out.unit_price = txt(q('#corePriceDisplay_desktop_feature_div .pricePerUnit')) ||
                   txt(q('#corePrice_feature_div .a-size-small .a-price'));
  const star = q('#acrPopover');
  out.rating = star ? (star.getAttribute('title') || txt(star)) : null;
  out.ratings_count = txt(q('#acrCustomerReviewText'));
  out.bought_past_month = txt(q('#social-proofing-faceout-title-tk_bought')) ||
    (qa('span, div').map(txt).find(t => t && /bought in past month/i.test(t) && t.length < 60) || null);
  out.breadcrumbs = qa('#wayfinding-breadcrumbs_feature_div li a').map(txt).filter(Boolean);
  out.bullets = qa('#feature-bullets li span.a-list-item, #feature-bullets li').map(txt)
                  .filter(Boolean).filter((v, i, a) => a.indexOf(v) === i).slice(0, 8);

  // Product details table / list (BSR, dimensions, first available, etc.)
  const details = {};
  qa('#productDetails_detailBullets_sections1 tr, #productDetails_techSpec_section_1 tr, #technicalSpecifications_section_1 tr, #prodDetails tr').forEach(tr => {
    const k = txt(q('th', tr)); const v = txt(q('td', tr));
    if (k && v) details[k] = v;
  });
  qa('#detailBullets_feature_div li, #detailBulletsWrapper_feature_div li').forEach(li => {
    const b = q('.a-text-bold', li);
    if (!b) return;
    const k = txt(b).replace(/[:‏‎]/g, '').trim();
    const v = txt(li).replace(txt(b), '').replace(/[‏‎]/g, '').trim();
    if (k && v) details[k] = v;
  });
  out.details = details;
  const bsrText = Object.entries(details).find(([k]) => /best sellers rank/i.test(k));
  const bsrSource = bsrText ? bsrText[1] : ((document.body.innerText.match(/Best Sellers Rank[\s\S]{0,400}/) || [''])[0]);
  out.best_sellers_rank = [];
  (bsrSource || '').replace(/#([\d,]+)\s+in\s+([^#(\n]+)/g, (m, n, cat) => {
    out.best_sellers_rank.push({ rank: parseInt(n.replace(/,/g, ''), 10), category: cat.trim() });
  });

  // Variations (sizes, flavors, colors, pack counts)
  const variations = {};
  qa('[id^="variation_"]').forEach(box => {
    const label = txt(q('.a-form-label', box)) || box.id.replace('variation_', '');
    const opts = qa('li[title], option', box).map(li => (li.getAttribute('title') || txt(li) || '').replace(/^Click to select\s*/i, ''))
                  .filter(t => t && !/^select$/i.test(t));
    if (opts.length) variations[label.replace(/:$/, '')] = Array.from(new Set(opts)).slice(0, 30);
  });
  qa('[id^="inline-twister-row-"]').forEach(row => {
    const label = txt(q('.inline-twister-dim-title, .a-color-secondary', row)) || row.id.replace('inline-twister-row-', '');
    const opts = qa('li', row).map(li => txt(q('.swatch-title-text-display, .a-button-text, span.a-size-base', li)) || li.getAttribute('title') || '')
                  .filter(Boolean);
    if (opts.length) variations[label.replace(/:.*$/, '').trim()] = Array.from(new Set(opts)).slice(0, 30);
  });
  out.variations = variations;

  // Related-product carousels: Frequently bought together, also viewed, sponsored, compare, etc.
  const carousels = [];
  const seen = new Set();
  qa('div.a-carousel-container, div[data-a-carousel-options], #similarities_feature_div, [cel_widget_id*="sims"], [cel_widget_id*="sp_detail"]').forEach(c => {
    const head = txt(q('h2, h3, .a-carousel-heading', c)) || txt(q('h2, h3', c.parentElement || c));
    const items = qa('[data-asin], li[data-adfeedbackdetails], li.a-carousel-card', c).map(it => {
      let asin = it.getAttribute('data-asin');
      const a = q('a[href*="/dp/"]', it);
      if (!asin && a) { const m = a.getAttribute('href').match(/\/dp\/([A-Z0-9]{10})/); if (m) asin = m[1]; }
      const img = q('img', it);
      const title = txt(q('.p13n-sc-truncate, .sponsored-products-truncator-truncated, [class*="truncate"], a span', it)) || (img && img.getAttribute('alt'));
      const price = txt(q('.a-price .a-offscreen', it)) || txt(q('.p13n-sc-price', it));
      return asin && title ? { asin, title: title.slice(0, 160), price } : null;
    }).filter(Boolean);
    if (!head || !items.length) return;
    const key = head + items.map(i => i.asin).join(',');
    if (seen.has(key)) return; seen.add(key);
    carousels.push({ heading: head.slice(0, 80), items: items.filter((v, i, a) => a.findIndex(x => x.asin === v.asin) === i).slice(0, 15) });
  });
  out.related = carousels.slice(0, 10);

  // "Customers say" summary and the reviews shown on the page
  const cs = q('#product-summary, [data-hook="cr-product-insights-cards"], #cr-product-insights-cards');
  out.customers_say = cs ? txt(cs).slice(0, 1200) : null;
  out.review_aspects = qa('[data-hook="cr-insights-aspect-link"], #aspect-button-group-0 button, [id^="aspect-button"]').map(txt).filter(Boolean).slice(0, 20);
  out.reviews = qa('[data-hook="review"]').map(r => ({
    stars: txt(q('[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]', r)),
    title: (txt(q('[data-hook="review-title"]', r)) || '').replace(/^[\d.]+ out of 5 stars\s*/, ''),
    body: (txt(q('[data-hook="review-body"]', r)) || '').replace(/Read more$/, '').trim(),
  })).filter(r => r.body).slice(0, 12);

  return out;
}
"""

SEARCH_JS = r"""
() => {
  const q = (s, r = document) => r.querySelector(s);
  const qa = (s, r = document) => Array.from(r.querySelectorAll(s));
  const txt = (el) => el ? el.textContent.replace(/\s+/g, ' ').trim() : null;
  const info = txt(q('[data-component-type="s-result-info-bar"] h2, .s-breadcrumb h2, .s-desktop-toolbar h2, [cel_widget_id*="UPPER-RESULT_INFO_BAR"]'));
  const results = [];
  qa('div[data-component-type="s-search-result"][data-asin]').forEach((card, i) => {
    const asin = card.getAttribute('data-asin');
    if (!asin) return;
    const h2 = q('h2', card);
    const title = (h2 && (h2.getAttribute('aria-label') || txt(h2))) || null;
    const brandLine = txt(q('[data-cy="title-recipe"] .a-row .a-size-base-plus, [data-cy="title-recipe"] h2 + * .a-size-base-plus, h5 .a-size-base-plus', card));
    const ratingEl = q('[aria-label*="out of 5 stars"], i[class*="a-star"] .a-icon-alt', card);
    const rating = ratingEl ? (ratingEl.getAttribute('aria-label') || txt(ratingEl)) : null;
    const countEl = q('[aria-label$="ratings"], [aria-label$="rating"], a[href*="customerReviews"] span, span.s-underline-text', card);
    const ratings_count = countEl ? (countEl.getAttribute('aria-label') || txt(countEl)) : null;
    const text = txt(card) || '';
    const boughtEl = qa('span', card).find(e => /bought in past month/i.test(e.textContent) && e.textContent.length < 50);
    const bought = boughtEl ? txt(boughtEl) : null;
    const sponsored = /\bSponsored\b/.test(text.slice(0, 400)) || !!q('.puis-sponsored-label-text, .s-sponsored-label-text', card);
    results.push({
      position: i + 1,
      asin,
      title: title ? title.replace(/^Sponsored Ad\s*-\s*/i, '').slice(0, 200) : null,
      brand: brandLine,
      price: txt(q('.a-price:not(.a-text-price) .a-offscreen', card)),
      list_price: txt(q('.a-price.a-text-price .a-offscreen', card)),
      unit_price: (text.match(/\((\$[\d.,]+\s*\/\s*[^)]+)\)/) || [null, null])[1],
      rating,
      ratings_count,
      bought_past_month: bought,
      sponsored,
      best_seller: /Best Seller/.test(text.slice(0, 300)),
      amazons_choice: /Amazon's\s+Choice|Overall Pick/i.test(text.slice(0, 300)),
    });
  });
  const brands = qa('#brandsRefinements li, #filter-p_123 li, [id*="p_89"] li, [id*="p_123"] li').map(txt).filter(Boolean).slice(0, 40);
  return { result_info: info, results, brand_filter: brands };
}
"""


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def _slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "item"


def _save(out_dir: Path | None, name: str, data) -> None:
    if not out_dir:
        return
    raw = out_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _trim(obj, limit=500):
    if isinstance(obj, str):
        return obj if len(obj) <= limit else obj[:limit] + "..."
    if isinstance(obj, list):
        return [_trim(x, limit) for x in obj]
    if isinstance(obj, dict):
        return {k: _trim(v, limit) for k, v in obj.items()}
    return obj


def _log(msg: str):
    print(msg, file=sys.stderr, flush=True)


def cmd_product(b: Browser, asins, out_dir):
    results = []
    for raw in asins:
        asin = _parse_asin(raw)
        if not asin:
            results.append({"input": raw, "status": "invalid_asin"})
            continue
        url = f"{BASE}/dp/{asin}"
        _log(f"Reading product {asin} ...")
        nav = b.goto(url)
        if not nav["ok"]:
            item = {"asin": asin, "url": url, "status": nav["status"]}
        else:
            item = {"asin": asin, "url": url, "status": "ok", **b.page.evaluate(PRODUCT_JS)}
            if not item.get("title"):
                item["status"] = "no_product_found"
        _save(out_dir, f"product-{asin}", item)
        results.append(item)
    return results


def _search_pages(b: Browser, keyword: str, pages: int, extra: str = ""):
    pages_out = []
    for p in range(1, pages + 1):
        url = f"{BASE}/s?k={urllib.parse.quote_plus(keyword)}{extra}" + (f"&page={p}" if p > 1 else "")
        _log(f'Searching "{keyword}" page {p} ...')
        nav = b.goto(url)
        if not nav["ok"]:
            pages_out.append({"page": p, "url": url, "status": nav["status"], "results": []})
            break
        data = b.page.evaluate(SEARCH_JS)
        pages_out.append({"page": p, "url": url, "status": "ok", **data})
        if not data["results"]:
            break
    return pages_out


def _summarize_search(keyword, pages):
    results = [r for pg in pages for r in pg.get("results", [])]
    brands = {}
    for r in results:
        name = r.get("brand") or "(brand not shown)"
        brands[name] = brands.get(name, 0) + 1
    return {
        "keyword": keyword,
        "status": pages[0]["status"] if pages else "no_pages",
        "result_info": pages[0].get("result_info") if pages else None,
        "result_count_read": len(results),
        "sponsored_count": sum(1 for r in results if r.get("sponsored")),
        "brands_seen": dict(sorted(brands.items(), key=lambda kv: -kv[1])),
        "brand_filter": pages[0].get("brand_filter", []) if pages else [],
        "results": results,
    }


def cmd_search(b: Browser, keywords, pages, out_dir):
    out = []
    for kw in keywords:
        summary = _summarize_search(kw, _search_pages(b, kw, pages))
        _save(out_dir, f"search-{_slug(kw)}", summary)
        out.append(summary)
    return out


def cmd_brand(b: Browser, brands, pages, out_dir):
    out = []
    for brand in brands:
        pages_data = _search_pages(b, brand, pages)
        items = []
        key = brand.lower()
        for pg in pages_data:
            for r in pg.get("results", []):
                title = (r.get("title") or "").lower()
                rb = (r.get("brand") or "").lower()
                if rb == key or title.startswith(key) or (key in title[: len(key) + 20]):
                    items.append(r)
        seen, uniq = set(), []
        for r in items:
            if r["asin"] not in seen:
                seen.add(r["asin"])
                uniq.append(r)
        summary = {
            "brand": brand,
            "status": pages_data[0]["status"] if pages_data else "no_pages",
            "method": "Amazon search for the brand name, keeping that brand's listings",
            "products_found": len(uniq),
            "products": uniq,
        }
        _save(out_dir, f"brand-{_slug(brand)}", summary)
        out.append(summary)
    return out


def cmd_autocomplete(b: Browser, prefixes, expand, out_dir):
    out = []
    # Load the home page once so the request carries normal cookies.
    b.goto(BASE + "/")
    for prefix in prefixes:
        tries = [prefix] + ([f"{prefix} {c}" for c in string.ascii_lowercase] if expand else [])
        suggestions = []
        for t in tries:
            url = (
                "https://completion.amazon.com/api/2017/suggestions?"
                + urllib.parse.urlencode({"mid": "ATVPDKIKX0DER", "alias": "aps", "prefix": t, "limit": 11})
            )
            try:
                resp = b.ctx.request.get(url, timeout=20000)
                data = resp.json() if resp.ok else {}
                for s in data.get("suggestions", []):
                    v = s.get("value")
                    if v and v not in suggestions:
                        suggestions.append(v)
            except Exception as err:
                _log(f"Autocomplete failed for '{t}': {err.__class__.__name__}")
            time.sleep(random.uniform(0.6, 1.4))
        item = {"prefix": prefix, "expanded": expand, "has_suggestions": bool(suggestions), "suggestions": suggestions}
        _save(out_dir, f"autocomplete-{_slug(prefix)}", item)
        out.append(item)
    return out


def _parse_asin(s: str):
    s = s.strip()
    m = re.search(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})", s, re.I)
    if m:
        return m.group(1).upper()
    if re.fullmatch(r"[A-Za-z0-9]{10}", s):
        return s.upper()
    return None


def main():
    ap = argparse.ArgumentParser(description="Next SKU browser helper (public Amazon pages, not logged in).")
    ap.add_argument("command", choices=["check", "product", "search", "brand", "autocomplete"])
    ap.add_argument("items", nargs="*")
    ap.add_argument("--out", type=Path, default=None, help="Run folder; raw JSON goes to OUT/raw/")
    ap.add_argument("--pages", type=int, default=None)
    ap.add_argument("--expand", action="store_true", help="autocomplete: also try 'prefix a' .. 'prefix z'")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--full", action="store_true", help="Print untrimmed JSON")
    args = ap.parse_args()

    _require_playwright()
    if args.command != "check" and not args.items:
        ap.error(f"'{args.command}' needs at least one item")

    b = Browser(headless=args.headless)
    try:
        if args.command == "check":
            nav = b.goto(BASE + "/")
            result = {"browser": b.engine, "profile": str(PROFILE_DIR), "amazon_reachable": nav["ok"], "status": nav["status"]}
        elif args.command == "product":
            result = cmd_product(b, args.items, args.out)
        elif args.command == "search":
            result = cmd_search(b, args.items, args.pages or 1, args.out)
        elif args.command == "brand":
            result = cmd_brand(b, args.items, args.pages or 2, args.out)
        else:
            result = cmd_autocomplete(b, args.items, args.expand, args.out)
    finally:
        b.close()

    print(json.dumps(result if args.full else _trim(result), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
