# Next SKU

**Find the products to grow your brand on Amazon.**

Enter one ASIN. Next SKU maps your whole catalog and your competitors, then
shows what to fix, which gaps to fill and which new products are worth
launching.

Next SKU is a [Claude Code](https://claude.com/claude-code) skill. Claude
drives a real Chrome window on your own computer, reads public Amazon pages
(no login, no seller account, no paid data tools), and writes you a clean
report.

## What you get

A one-page report (`report.html`) with three parts:

1. **Fix or promote what you already sell.** Products you have that trail
   competitors on price, traction or quality.
2. **Gaps to fill.** Product types, formats, sizes, pack counts, bundles,
   variants and price tiers your competitors sell and you don't.
3. **Products to expand into.** New product lines your shoppers already buy,
   search for, or ask for in reviews, grown from your whole catalog.

Your catalog is mapped first, and nothing you already sell is ever listed as
a gap or a new product.

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
2. Maps your whole catalog on Amazon (every product line, pack and size).
3. Builds a shopper keyword set from Amazon autocomplete.
4. Searches those keywords and finds the brands that keep showing up.
5. Reads competitor catalogs and best sellers.
6. Compares catalogs to separate what to fix from what is missing, and scans
   related products and reviews for expansion ideas.
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

### No install: Claude in Chrome

Don't use Claude Code? If you have the Claude in Chrome extension, start a
new Claude chat and paste:

> Using Claude in Chrome, run Next SKU on ASIN B0XXXXXXXX. Read the method
> at https://github.com/victordelgadopm/next-sku/blob/main/skills/next-sku/SKILL.md
> and follow its steps by browsing Amazon in Chrome yourself instead of
> running the Python scripts. Don't log in or click ads. Give me the gaps
> to fix, fill and expand into, with the evidence for each.

Claude browses Amazon in your own Chrome and writes the report in the chat.
This version is lighter (smaller minimums) and has no HTML report. It
follows the same method and the same three outputs.

**Want it saved to your Claude account?** Download
[`chrome-edition/next-sku.zip`](chrome-edition/next-sku.zip), then in Claude
go to **Settings > Capabilities > Skills > Upload skill** and pick the zip.
After that, just say "Run Next SKU on ASIN B0XXXXXXXX" in any chat with the
Chrome extension on.

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
- **Amazon.com (US)** only for now. Prices and availability depend on the
  day and delivery location, so the report records both.
- **Your catalog is a lower bound.** Search can miss listings that don't
  lead with your brand name. The report says how complete it is.

## Depth levels

| Level | How | Good for |
|---|---|---|
| Light | Claude in Chrome, report in chat | A fast first read of one ASIN |
| Standard | Claude Code, scripts and HTML report | Repeatable runs with saved raw data |
| Deep | Custom build on the same method | Storefront crawls, review mining, monitoring, exports |

The method, the `findings.json` schema and the report renderer are separate
on purpose, so a deeper build reuses them. Other retailers (Target, Walmart)
would be added as one adapter per platform, each tested live. They are not
supported today.

## Files

```
.claude-plugin/          plugin and marketplace manifests
skills/next-sku/
  SKILL.md               the research playbook Claude follows
  scripts/nextsku.py     browser helper (product, search, brand, autocomplete)
  scripts/render_report.py
  reference/findings-schema.md
chrome-edition/          no-install skill for Claude accounts (+ .zip)
examples/                sample report
```

## About

Built by [Victor Delgado](https://victordelgadopm.github.io), a product
leader who has taken consumer products from first idea to launch and growth
on Amazon, Target and Walmart.

MIT License.
