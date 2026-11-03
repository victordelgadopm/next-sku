#!/usr/bin/env python3
"""Render a Next SKU findings.json into a single self-contained report.html.

Usage:
  python render_report.py RUN_DIR/findings.json [--out RUN_DIR/report.html]

The schema is documented in reference/findings-schema.md.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path

DEMAND_LEVELS = {"strong": "Strong", "moderate": "Moderate", "thin": "Thin"}
FIT_LEVELS = {"strong": "Strong fit", "moderate": "Moderate fit", "stretch": "Stretch"}


def e(v) -> str:
    return html.escape("" if v is None else str(v))


def amz(asin: str) -> str:
    return f"https://www.amazon.com/dp/{e(asin)}"


def chips(items, cls="chip"):
    return "".join(f'<span class="{cls}">{e(i)}</span>' for i in items if i)


def bullet_list(items, cls=""):
    items = [i for i in (items or []) if i]
    if not items:
        return ""
    return f'<ul class="{cls}">' + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"


def render_opportunity(o: dict, n: int) -> str:
    d = o.get("demand") or {}
    level = (d.get("level") or "").lower()
    fit = (o.get("fit") or "").lower()
    signals = []
    if d.get("autocomplete_terms"):
        signals.append(("Shoppers search it", ", ".join(d["autocomplete_terms"][:4])))
    elif d.get("autocomplete") is False:
        signals.append(("Shoppers search it", "No autocomplete signal found"))
    if d.get("search_results"):
        signals.append(("Search results", d["search_results"]))
    if d.get("bought_past_month"):
        signals.append(("Top sellers move", d["bought_past_month"]))
    if d.get("top_review_counts"):
        signals.append(("Review depth", d["top_review_counts"]))
    if d.get("bsr"):
        signals.append(("Best sellers rank", d["bsr"]))
    if d.get("sponsored_share"):
        signals.append(("Paid competition", d["sponsored_share"]))
    if o.get("price_band"):
        signals.append(("Price band", o["price_band"]))
    sig_html = "".join(
        f'<div class="sig"><div class="sig-k">{e(k)}</div><div class="sig-v">{e(v)}</div></div>' for k, v in signals
    )
    examples = "".join(
        f'<a class="asin" href="{amz(x.get("asin"))}" target="_blank" rel="noopener">'
        f'<span class="asin-id">{e(x.get("asin"))}</span>{e(x.get("brand") or "")}'
        f'{(" · " + e(x.get("price"))) if x.get("price") else ""}</a>'
        for x in (o.get("example_listings") or [])[:6]
        if x.get("asin")
    )
    voices = "".join(f'<blockquote>{e(v)}</blockquote>' for v in (o.get("customer_signals") or [])[:3])
    return f"""
<article class="opp">
  <header class="opp-head">
    <div class="opp-num">{n:02d}</div>
    <div class="opp-titles">
      <h3>{e(o.get("name"))}</h3>
      <p class="opp-what">{e(o.get("what"))}</p>
    </div>
    <div class="opp-badges">
      {f'<span class="badge d-{e(level)}">Demand: {e(DEMAND_LEVELS.get(level, level.title()))}</span>' if level else ''}
      {f'<span class="badge f-{e(fit)}">{e(FIT_LEVELS.get(fit, fit.title()))}</span>' if fit else ''}
    </div>
  </header>
  {f'<div class="sigs">{sig_html}</div>' if sig_html else ''}
  <div class="opp-body">
    <div>
      <h4>What the data shows</h4>
      {bullet_list(o.get("evidence"))}
      {f'<h4>Who already sells it</h4><p class="chips">{chips(o.get("competitors_selling") or [])}</p>' if o.get("competitors_selling") else ''}
    </div>
    <div>
      {f'<h4>What customers say</h4>{voices}' if voices else ''}
      {f'<h4>How you could stand out</h4><p>{e(o.get("differentiation"))}</p>' if o.get("differentiation") else ''}
      {f'<h4>Watch out for</h4><p>{e(o.get("risks"))}</p>' if o.get("risks") else ''}
    </div>
  </div>
  {f'<div class="examples"><span class="ex-label">Listings to study</span>{examples}</div>' if examples else ''}
</article>"""


def render(f: dict) -> str:
    seed = f.get("seed") or {}
    opps = f.get("opportunities") or []
    gaps = [o for o in opps if (o.get("type") or "").lower() == "gap"]
    expand = [o for o in opps if (o.get("type") or "").lower() == "expand"]
    fixes = [o for o in opps if (o.get("type") or "").lower() == "fix"]
    mode = (f.get("mode") or "both").lower()
    catalog = f.get("catalog") or {}
    comps = f.get("competitors") or []
    cov = f.get("coverage") or {}
    generated = f.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")

    n = 0
    fix_html = ""
    for o in fixes:
        n += 1
        fix_html += render_opportunity(o, n)
    gap_html = ""
    for o in gaps:
        n += 1
        gap_html += render_opportunity(o, n)
    exp_html = ""
    for o in expand:
        n += 1
        exp_html += render_opportunity(o, n)

    comp_rows = "".join(
        f"<tr><td><strong>{e(c.get('brand'))}</strong>"
        f"{('<div class=muted>' + e(c.get('why')) + '</div>') if c.get('why') else ''}</td>"
        f"<td>{e(c.get('tier'))}</td><td>{e(c.get('products_seen'))}</td>"
        f"<td>{e(c.get('price_range'))}</td><td>{e(c.get('strengths'))}</td></tr>"
        for c in comps
    )
    cat_products = sorted(
        catalog.get("products") or [], key=lambda p: (p.get("line") or "").lower()
    )
    cat_rows = "".join(
        f"<tr><td>{e(p.get('line'))}</td>"
        f'<td><a href="{amz(p.get("asin"))}" target="_blank" rel="noopener">{e(p.get("asin"))}</a></td>'
        f"<td>{e(p.get('title'))}</td><td>{e(p.get('pack'))}</td><td>{e(p.get('price'))}</td>"
        f"<td>{e(p.get('rating'))}</td><td>{e(p.get('ratings'))}</td><td>{e(p.get('bought'))}</td></tr>"
        for p in cat_products
    )
    min_rows = "".join(
        f"<tr><td>{e(m.get('item'))}</td><td>{e(m.get('floor'))}</td><td>{e(m.get('done'))}</td></tr>"
        for m in (cov.get("minimums") or [])
    )
    not_captured = cov.get("not_captured") or []
    top_picks = "".join(f"<li>{e(t)}</li>" for t in (f.get("top_picks") or [])[:3])
    blocked = cov.get("blocked") or []

    sections = []
    if mode in ("gaps", "both") and (fixes or mode == "both"):
        sections.append(
            f"""<section id="fix"><div class="sec-head"><span class="kicker">Part 1</span><h2>Fix or promote what you already sell</h2>
            <p>Products you have that trail the competition. Improve these before adding new ones.</p></div>
            {fix_html or '<p class="empty">Nothing in your current catalog clearly trails its competitors.</p>'}</section>"""
        )
    if mode in ("gaps", "both"):
        sections.append(
            f"""<section id="gaps"><div class="sec-head"><span class="kicker">Part 2</span><h2>Gaps to fill</h2>
            <p>Products, sizes, packs and price points your competitors sell that your catalog doesn't.</p></div>
            {gap_html or '<p class="empty">No clear gaps found in this run.</p>'}</section>"""
        )
    if mode in ("expand", "both"):
        sections.append(
            f"""<section id="expand"><div class="sec-head"><span class="kicker">Part 3</span><h2>Products to expand into</h2>
            <p>Nearby products your customers already buy, search for or ask for, where your brand could grow.</p></div>
            {exp_html or '<p class="empty">No clear expansion paths found in this run.</p>'}</section>"""
        )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Next SKU report: {e(seed.get("brand") or seed.get("asin"))}</title>
<style>
:root {{
  --bg:#F5F3EE; --paper:#FFFFFF; --ink:#16181D; --muted:#5D6270; --line:#E3E0D8;
  --accent:#0F6E5A; --accent-soft:#E2F2EC; --amber:#B86A00; --amber-soft:#FCEFD9;
  --red:#A23B2A; --red-soft:#F8E3DE; --chip:#F0EEE8;
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#111317; --paper:#1A1D23; --ink:#ECEDEF; --muted:#A2A7B3; --line:#2C3038;
    --accent:#4CC9A4; --accent-soft:#163029; --amber:#F2B45A; --amber-soft:#33281A; --red:#F08B78; --red-soft:#3A221E; --chip:#242830; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif; }}
.wrap {{ max-width:1080px; margin:0 auto; padding:32px 20px 64px; }}
a {{ color:var(--accent); }}
.top {{ display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:28px; }}
.logo {{ font-weight:800; letter-spacing:-.02em; font-size:20px; }}
.logo span {{ color:var(--accent); }}
.meta {{ color:var(--muted); font-size:13px; text-align:right; }}
.hero {{ background:var(--paper); border:1px solid var(--line); border-radius:18px; padding:28px; display:grid; grid-template-columns:1.4fr 1fr; gap:28px; }}
.hero h1 {{ font-size:30px; line-height:1.15; margin:0 0 12px; letter-spacing:-.02em; }}
.hero p.sum {{ color:var(--muted); margin:0 0 16px; font-size:17px; }}
.picks {{ margin:0; padding-left:20px; }} .picks li {{ margin:4px 0; font-weight:600; }}
.seed {{ background:var(--bg); border-radius:14px; padding:18px; font-size:14px; }}
.seed .lbl {{ text-transform:uppercase; letter-spacing:.08em; font-size:11px; color:var(--muted); font-weight:700; }}
.seed .t {{ font-weight:650; margin:6px 0 10px; }}
.kv {{ display:grid; grid-template-columns:auto 1fr; gap:4px 12px; }} .kv dt {{ color:var(--muted); }} .kv dd {{ margin:0; }}
nav.jump {{ display:flex; gap:10px; margin:22px 0 6px; flex-wrap:wrap; }}
nav.jump a {{ text-decoration:none; background:var(--paper); border:1px solid var(--line); padding:7px 14px; border-radius:999px; color:var(--ink); font-size:14px; }}
section {{ margin-top:40px; }}
.sec-head h2 {{ font-size:26px; margin:2px 0 4px; letter-spacing:-.01em; }}
.sec-head p {{ color:var(--muted); margin:0 0 18px; }}
.kicker {{ font-size:12px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); }}
.opp {{ background:var(--paper); border:1px solid var(--line); border-radius:16px; padding:22px; margin-bottom:16px; }}
.opp-head {{ display:grid; grid-template-columns:auto 1fr auto; gap:16px; align-items:start; }}
.opp-num {{ font-size:28px; font-weight:800; color:var(--accent); line-height:1; min-width:44px; }}
.opp h3 {{ margin:0; font-size:20px; }}
.opp-what {{ margin:4px 0 0; color:var(--muted); }}
.opp-badges {{ display:flex; flex-direction:column; gap:6px; align-items:flex-end; }}
.badge {{ font-size:12px; font-weight:700; padding:4px 10px; border-radius:999px; white-space:nowrap; background:var(--chip); }}
.d-strong, .f-strong {{ background:var(--accent-soft); color:var(--accent); }}
.d-moderate, .f-moderate {{ background:var(--amber-soft); color:var(--amber); }}
.d-thin, .f-stretch {{ background:var(--red-soft); color:var(--red); }}
.sigs {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin:18px 0 6px; }}
.sig {{ background:var(--bg); border-radius:10px; padding:10px 12px; }}
.sig-k {{ font-size:11px; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); font-weight:700; }}
.sig-v {{ font-size:14px; font-weight:600; margin-top:2px; }}
.opp-body {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:8px; }}
.opp h4 {{ font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:14px 0 6px; }}
.opp ul {{ margin:0; padding-left:18px; }} .opp li {{ margin:3px 0; }} .opp p {{ margin:0; }}
blockquote {{ margin:6px 0; padding:8px 12px; border-left:3px solid var(--amber); background:var(--amber-soft); border-radius:0 8px 8px 0; font-style:italic; font-size:15px; }}
.chips {{ display:flex; flex-wrap:wrap; gap:6px; }}
.chip {{ background:var(--chip); border-radius:999px; padding:3px 10px; font-size:13px; }}
.examples {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:16px; padding-top:14px; border-top:1px dashed var(--line); }}
.ex-label {{ font-size:12px; color:var(--muted); font-weight:700; margin-right:4px; }}
.asin {{ font-size:13px; text-decoration:none; border:1px solid var(--line); border-radius:8px; padding:4px 9px; color:var(--ink); }}
.asin-id {{ font-family:ui-monospace,Menlo,Consolas,monospace; color:var(--accent); margin-right:6px; }}
table {{ width:100%; border-collapse:collapse; background:var(--paper); border:1px solid var(--line); border-radius:14px; overflow:hidden; font-size:14px; }}
th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ font-size:12px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); background:var(--bg); }}
.muted {{ color:var(--muted); font-size:13px; }}
.tablewrap {{ overflow-x:auto; }}
.empty {{ color:var(--muted); font-style:italic; }}
footer {{ margin-top:40px; color:var(--muted); font-size:13px; border-top:1px solid var(--line); padding-top:16px; }}
@media (max-width:760px) {{
  .hero, .opp-body {{ grid-template-columns:1fr; }}
  .opp-head {{ grid-template-columns:auto 1fr; }} .opp-badges {{ grid-column:1 / -1; flex-direction:row; align-items:center; }}
  .hero h1 {{ font-size:24px; }}
}}
</style></head><body><div class="wrap">
<div class="top"><div class="logo">Next <span>SKU</span></div>
<div class="meta">{e(generated)}{("<br>Data as of " + e(f.get("data_as_of"))) if f.get("data_as_of") else ""}<br>{e(len(opps))} opportunities{(" · " + e(cov.get("pages_read")) + " pages read") if cov.get("pages_read") else ""}</div></div>

<div class="hero">
  <div>
    <h1>{e(f.get("headline") or "Your next products to launch")}</h1>
    <p class="sum">{e(f.get("summary"))}</p>
    {f'<div class="kicker">Start here</div><ol class="picks">{top_picks}</ol>' if top_picks else ''}
  </div>
  <div class="seed">
    <div class="lbl">Starting product</div>
    <div class="t"><a href="{amz(seed.get("asin"))}" target="_blank" rel="noopener">{e(seed.get("title"))}</a></div>
    <dl class="kv">
      <dt>Brand</dt><dd>{e(seed.get("brand"))}</dd>
      <dt>ASIN</dt><dd>{e(seed.get("asin"))}</dd>
      <dt>Price</dt><dd>{e(seed.get("price"))}</dd>
      <dt>Rating</dt><dd>{e(seed.get("rating"))}</dd>
      <dt>Category</dt><dd>{e(seed.get("category"))}</dd>
      <dt>Rank</dt><dd>{e(seed.get("bsr"))}</dd>
    </dl>
  </div>
</div>

<nav class="jump">
  {'<a href="#fix">Fix or promote (' + str(len(fixes)) + ')</a>' if mode in ("gaps","both") and (fixes or mode == "both") else ''}
  {'<a href="#gaps">Gaps to fill (' + str(len(gaps)) + ')</a>' if mode in ("gaps","both") else ''}
  {'<a href="#expand">Products to expand into (' + str(len(expand)) + ')</a>' if mode in ("expand","both") else ''}
  <a href="#landscape">Competitive landscape</a>
  <a href="#method">How this was built</a>
</nav>

{''.join(sections)}

<section id="landscape"><div class="sec-head"><span class="kicker">Context</span><h2>Competitive landscape</h2>
<p>{e(catalog.get("notes") or "Brands that showed up most often across your category searches.")}</p></div>
<div class="tablewrap"><table><thead><tr><th>Brand</th><th>Tier</th><th>Products seen</th><th>Price range</th><th>Where they win</th></tr></thead>
<tbody>{comp_rows or '<tr><td colspan=5 class=empty>No competitor data.</td></tr>'}</tbody></table></div>
{('<h3 style="margin-top:28px">Your catalog as seen on Amazon</h3><div class="tablewrap"><table><thead><tr><th>Line</th><th>ASIN</th><th>Product</th><th>Pack</th><th>Price</th><th>Rating</th><th>Ratings</th><th>Bought past month</th></tr></thead><tbody>' + cat_rows + '</tbody></table></div><p class="muted">A lower bound: listings the run could not find are not shown. Bought past month is a floor bucket, not a count.</p>') if cat_rows else ''}
</section>

<footer id="method">
<strong>How this was built.</strong> Next SKU read public Amazon.com pages (search results, product pages, autocomplete and visible reviews) without logging in,
then compared your catalog with the brands that compete for the same shoppers.
Demand signals such as autocomplete, "bought in past month", review counts and best sellers rank are public proxies, not sales data.
Margins and sourcing costs are not included. The report lays out the evidence; you make the call.
{('<br><br><strong>Searches run:</strong> ' + e(", ".join(cov.get("searches") or []))) if cov.get("searches") else ''}
{('<br><strong>Could not read:</strong> ' + e(", ".join(blocked))) if blocked else ''}
{('<br><strong>Not captured:</strong> ' + e(", ".join(not_captured))) if not_captured else ''}
{('<br>' + e(cov.get("notes"))) if cov.get("notes") else ''}
{('<div class="tablewrap" style="margin-top:12px"><table><thead><tr><th>Minimum</th><th>Floor</th><th>Done</th></tr></thead><tbody>' + min_rows + '</tbody></table></div>') if min_rows else ''}
</footer>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    try:
        data = json.loads(args.findings.read_text(encoding="utf-8"))
    except Exception as err:
        print(f"Could not read {args.findings}: {err}", file=sys.stderr)
        sys.exit(1)
    out = args.out or args.findings.with_name("report.html")
    out.write_text(render(data), encoding="utf-8")
    print(str(out.resolve()))


if __name__ == "__main__":
    main()
