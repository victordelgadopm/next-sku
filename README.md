# Next SKU

**Find the products to grow your brand on Amazon.**

Enter one ASIN. Next SKU maps your catalog and competitors, then shows the
gaps to fill and the new products worth launching.

Next SKU is a [Claude Code](https://claude.com/claude-code) skill. Claude
drives a real Chrome window on your own computer, reads public Amazon pages
(no login, no seller account, no paid data tools), and writes you a clean
report.

## What you get

A one-page report (`report.html`) with two parts:

1. **Gaps to fill.** Product types, formats, sizes, pack counts, bundles,
   variants and price tiers your competitors sell and you don't.
2. **Products to expand into.** Nearby products your shoppers already buy
   together, search for, or ask for in reviews, where your brand could grow.

Every opportunity shows the evidence behind it: what shoppers type into
Amazon search, how much page one is selling, review depth, price band, how
crowded the ads are, who already sells it, what customers complain about,
and how you could stand out.

See the format in [`examples/sample-report.html`](examples/sample-report.html)
(illustrative data with made-up brands).

## How it works

From your starting ASIN, Next SKU:

1. Reads your product page: category, rank, variations, bought-together
   items and reviews.
2. Maps your current catalog on Amazon.
3. Builds a shopper keyword set from Amazon autocomplete.
4. Searches those keywords and finds the brands that keep showing up.
5. Reads competitor catalogs and best sellers.
6. Compares catalogs to find gaps, and scans related products and reviews
   for expansion ideas.
7. Validates each idea with live demand signals.
8. Writes the report.

A typical run takes 10 to 20 minutes. You can watch Chrome work, or ignore
it.

## Install

You need [Claude Code](https://claude.com/claude-code), Python 3.9+ and
Google Chrome.

In Claude Code, run:

```
/plugin marketplace add victordelgadopm/next-sku
/plugin install next-sku@next-sku
```

Then install the browser library once:

```
python -m pip install playwright
```

## Use it

Just ask Claude in plain words:

> What should I launch next? My product is B0XXXXXXXX

> Find gaps in my catalog: amazon.com/dp/B0XXXXXXXX

> Use this ASIN to find similar products I could expand into: B0XXXXXXXX

Reports are saved to `next-sku-runs/<ASIN>-<date>/report.html` in the
folder where you started Claude Code, with all raw page data in `raw/`.

## Good to know

- **Public data only.** Next SKU never logs in, adds to cart or clicks ads,
  and it browses at a human pace. You're responsible for using it in line
  with Amazon's terms.
- **If Amazon asks you to confirm you're human,** solve the check in the
  Chrome window and Next SKU carries on.
- **Signals, not sales data.** Autocomplete, "bought in past month", review
  counts and best sellers rank are public proxies. Margins and sourcing
  costs aren't included. The report lays out the evidence; you make the call.
- **Amazon.com (US)** only for now.

## Files

```
.claude-plugin/          plugin and marketplace manifests
skills/next-sku/
  SKILL.md               the research playbook Claude follows
  scripts/nextsku.py     browser helper (product, search, brand, autocomplete)
  scripts/render_report.py
  reference/findings-schema.md
examples/                sample report
```

## About

Built by [Victor Delgado](https://victordelgadopm.github.io), a product
leader who has taken consumer products from first idea to launch and growth
on Amazon, Target and Walmart.

MIT License.
