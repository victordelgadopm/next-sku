---
name: next-sku
description: Find the next products an Amazon brand should launch. Give it one ASIN or Amazon product URL and it reads public Amazon pages in the user's own Chrome, maps their catalog and competitors, and delivers a report with (1) gaps to fill and (2) products to expand into, each backed by demand signals. Use when someone asks what to sell or launch next on Amazon, wants a competitor gap analysis, catalog or assortment expansion ideas, or new product research for an ASIN.
---

# Next SKU

Next SKU answers one question for an Amazon seller: **what should I launch next?**

Starting from a single ASIN, it reads public Amazon pages in a real Chrome
window on the user's computer (never logged in), learns what the brand
already sells, finds the brands competing for the same shoppers, and
returns a report in two parts:

1. **Gaps to fill.** Product types, sizes, pack counts, bundles, variants and
   price tiers that competitors sell and this brand does not.
2. **Products to expand into.** Nearby products the same shoppers buy,
   search for, or ask for in reviews, where the brand could credibly grow.

Every opportunity carries the evidence behind it. The report lays out the
data; the seller makes the call.

## Tools in this skill

All browsing goes through one helper script. Find it in this skill's base
directory (shown when the skill loads) at `scripts/nextsku.py`, and the
report renderer at `scripts/render_report.py`. Below, `NSKU` means
`python "<skill dir>/scripts/nextsku.py"` (use `python3` if `python` is not
Python 3).

| Command | What it returns |
|---|---|
| `NSKU check` | Confirms Playwright and Chrome work and Amazon loads |
| `NSKU product ASIN [ASIN ...] --out RUN` | Title, brand, price, rating, ratings count, best sellers rank, breadcrumbs, bullets, variations, related-product carousels (bought together, also viewed, sponsored), visible reviews, "Customers say" |
| `NSKU search "kw" ["kw" ...] --out RUN` | Page 1 results per keyword: brand, price, rating, ratings, "bought in past month", sponsored flag, plus a brand tally and result count |
| `NSKU brand "Brand" ["Brand" ...] --out RUN` | That brand's listings found by searching its name (2 pages) |
| `NSKU autocomplete "prefix" [...] [--expand] --out RUN` | Amazon search suggestions; `--expand` also tries "prefix a" to "prefix z" |

### No Python? Use browser tools instead

If you can't run scripts but you do have a browser tool (for example Claude
in Chrome), follow the same steps by browsing yourself. Open new tabs, keep
a short pace between pages, and record what you read in notes instead of
`RUN/raw/`:

| Script command | Browser equivalent |
|---|---|
| `product ASIN` | open `https://www.amazon.com/dp/ASIN`, scroll to load carousels and reviews, read the fields listed above |
| `search "kw"` | open `https://www.amazon.com/s?k=kw` (spaces as `+`) and read page one |
| `brand "Brand"` | search the brand name and keep that brand's listings |
| `autocomplete "prefix"` | type the prefix into Amazon's search box without pressing Enter and read the suggestions |

Use smaller limits in this mode (about 5 keywords, 3 to 4 competitors, 3
product pages, 6 opportunities). Skip `findings.json` and the renderer:
write the report straight into the chat using the same sections (headline,
top picks, gaps to fill, products to expand into, competitive landscape,
how this was built). If Amazon shows a "confirm you're human" page, ask the
user to solve it, then continue.

Always pass several items to one command instead of calling it many times.
One call opens one browser window and reuses it, which is faster and calmer
for Amazon. Every call also saves full JSON under `RUN/raw/`, so read those
files when you need more than the trimmed output.

## Ground rules

- **Public pages only.** Never log in, never add to cart, never click ads.
  The script already moves at a human pace; do not add parallel browser runs.
- **No invented numbers.** Every price, count, rank or quote in the report
  must come from a file in `RUN/raw/`. If a value was not captured, leave it
  out. Never estimate sales, revenue or margins.
- **Label proxies.** Autocomplete, "bought in past month", review counts and
  best sellers rank are public signals, not sales data. Say so.
- **If Amazon blocks a page,** the script returns `status: "captcha"` or an
  error. Retry that item once later in the run; if it fails again, record it
  in `coverage.blocked` and keep going. If most pages are blocked, stop and
  tell the user, suggesting they solve the check in the Chrome window and try
  again in a few minutes.
- **Keep the user informed** with one short line at the start of each step.
  Don't paste raw JSON into the chat.

## Step 0: Intake and setup

1. Get the input. Accept an ASIN (10 characters, usually starting `B0`) or any
   Amazon product URL (pull the ASIN from `/dp/XXXXXXXXXX`). If none was
   given, ask once: "Which Amazon product should I start from? Paste an ASIN
   or product link." If the user also lists more of their own ASINs, use them
   all as known catalog.
2. Pick the mode without asking:
   - "gaps", "what am I missing", "fill my catalog" → `gaps`
   - "similar products", "venture into", "expand", "new categories" → `expand`
   - anything else → `both` (the default)
3. Create the run folder `next-sku-runs/<ASIN>-<YYYYMMDD-HHMM>/` in the
   current directory. This is `RUN`.
4. Run `NSKU check`. If Playwright is missing, run
   `python -m pip install playwright` and check again. If no browser opens,
   ask the user to install Google Chrome (or run
   `python -m playwright install chromium`).
5. Tell the user: "A Chrome window will open and browse Amazon for about
   10 to 20 minutes. You don't need to touch it unless Amazon asks you to
   confirm you're human."

## Step 1: Read the starting product

`NSKU product <ASIN> --out RUN`

Note the brand, the product's core noun (for example "matcha powder"),
format, size or count, price and unit price, best sellers rank and leaf
category, variations offered, and every ASIN in the related carousels.
Read the reviews and "Customers say" for wishes and complaints.

## Step 2: Map the brand's own catalog

`NSKU brand "<Brand>" --out RUN`

List what the brand already sells: product types, formats, sizes and pack
counts, flavors or variants, and price points. Add the starting product's
variations. This is the baseline every gap is measured against. If the brand
search finds little (common for small brands), say so in
`catalog.notes` and lean on the starting product and its variations.

## Step 3: Build the keyword set

Run `NSKU autocomplete "<core noun>" --expand --out RUN`, plus one plain
autocomplete for the leaf category name if it differs.

From the product, its category and the suggestions, choose **6 to 8
shopper keywords** that cover different angles:

- the core product ("matcha powder")
- the format or form ("matcha tea bags", "matcha latte mix")
- the use or occasion ("matcha for baking", "matcha energy")
- the audience or need ("organic matcha", "ceremonial grade matcha")
- the bigger category ("green tea powder")
- one or two strong modifiers from autocomplete

Prefer terms autocomplete actually suggested. Avoid brand names.

## Step 4: Find the real competitors

`NSKU search "kw1" "kw2" ... --out RUN`

Tally brands across all searches (use `brands_seen`; when a result has no
brand, infer it from the start of the title). Classify:

- **Primary:** appears in 3+ of the searches, or 6+ listings overall
- **Secondary:** appears in 2 searches or 3 to 5 listings
- ignore one-off brands unless they rank in the top 5 with strong signals

Pick the top **4 to 6** competitors (Primary first), excluding the seller.

## Step 5: Read competitor catalogs and best sellers

1. `NSKU brand "Comp A" "Comp B" ... --out RUN`
2. Choose the 4 to 6 strongest competitor listings (most ratings or highest
   "bought in past month") and read them in one call:
   `NSKU product ASIN1 ASIN2 ... --out RUN`

These pages supply variations, price tiers, bought-together and
also-viewed products, and reviews, especially the 1 to 3 star ones that
reveal unmet needs.

## Step 6: Gaps to fill (mode `gaps` or `both`)

Compare the seller's catalog with each competitor catalog along these axes:

| Axis | Look for |
|---|---|
| Product type | Types 2+ competitors sell that the seller doesn't |
| Format | Powder vs capsules vs sticks vs liquid, refill vs starter kit |
| Size and count | Trial sizes, family or bulk sizes, multi-packs |
| Bundles and kits | Bought-together pairs competitors package as one listing |
| Variants | Flavors, colors, scents, strengths competitors offer |
| Price tier | Empty budget, mid or premium bands in the category |
| Audience | Kids, pets, travel, gifting, professional, dietary needs |

A gap counts when **at least 2 competitors** sell it, or 1 competitor sells
it with strong demand signals. Keep the 3 to 6 strongest.

## Step 7: Products to expand into (mode `expand` or `both`)

Look beyond the current catalog for products the same shoppers want:

- items that repeat in **bought together / also bought / also viewed**
  carousels across the seller's and competitors' pages
- autocomplete branches of the core noun that point to a different product
  ("matcha whisk", "matcha latte kit", "matcha cups")
- the parent and sibling categories in the breadcrumbs
- review wishes and complaints that describe a product nobody sells well
  ("wish it came in single-serve", "too bitter for lattes")

Keep the 3 to 6 that a brand like this could credibly make or source.

## Step 8: Validate demand

For every candidate from steps 6 and 7 (cap at about 10), write a short
shopper phrase for it, then in two batched calls:

- `NSKU autocomplete "phrase1" "phrase2" ... --out RUN`
- `NSKU search "phrase1" "phrase2" ... --out RUN`

Rate demand from the evidence:

- **Strong:** autocomplete suggests it, and 2+ page-one listings show
  "1K+ bought in past month" or 1,000+ ratings
- **Moderate:** autocomplete suggests it and some page-one listings show
  sales signals
- **Thin:** no autocomplete suggestion, or page one is mostly unrelated

Also note the price band of page-one listings and how many results were
sponsored (heavy ads mean costlier entry).

Rate **brand fit**: Strong (same category, shopper and price tier),
Moderate (same shopper, new category or format), Stretch (new shopper or
very different sourcing). Thin or Stretch items stay in the report, ordered
last, because the seller may know something the data doesn't.

## Step 9: Write the report

1. Write `RUN/findings.json` following `reference/findings-schema.md`.
   Order opportunities within each type by demand, then fit.
2. Render it: `python "<skill dir>/scripts/render_report.py" RUN/findings.json`
3. Tell the user where `RUN/report.html` is and offer to open it. Then give
   a short chat summary: the headline, the top 3 picks with one line of
   evidence each, and anything that could not be read.

Write in plain, confident language a busy seller can skim. No hype and no
filler. Each opportunity's `what` is one sentence a seller could act on.
