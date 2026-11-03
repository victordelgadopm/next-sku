---
name: next-sku
description: Find the next products an Amazon brand should launch. Give it one ASIN or Amazon product URL and it reads public Amazon pages in the user's own Chrome, maps the brand's whole catalog and its competitors, and delivers a report with (1) what to fix on products the brand already sells, (2) gaps to fill, and (3) products to expand into, each backed by demand signals. Use when someone asks what to sell or launch next on Amazon, wants a competitor gap analysis, catalog or assortment expansion ideas, or new product research for an ASIN.
---

# Next SKU

Next SKU answers one question for an Amazon seller: **what should I launch next?**

Starting from a single ASIN, it reads public Amazon pages in a real Chrome
window on the user's computer (never logged in), maps everything the brand
already sells, finds the brands competing for the same shoppers, and
returns a report in three parts:

1. **Fix or promote what you already sell.** Products the brand has that
   trail their competitors on price, traction or quality.
2. **Gaps to fill.** Product types, sizes, pack counts, bundles, variants and
   price tiers that competitors sell and this brand does not.
3. **Products to expand into.** New product lines the same shoppers buy,
   search for, or ask for in reviews, where the brand could credibly grow.
   These grow from the brand's whole catalog, not only the starting product.

Every opportunity carries the evidence behind it. The report lays out the
data; the seller makes the call.

## Scope

- **Amazon.com (US) only.** If the user names another retailer (Target,
  Walmart) or another Amazon country site, say it is not supported yet and
  offer to run on Amazon.com instead. Do not improvise.
- **Light and full versions share one method.** This file is the full
  version (Python scripts and an HTML report). The Claude in Chrome edition
  in `chrome-edition/next-sku/SKILL.md` is the same method with smaller
  limits and a chat report.

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
| `NSKU brand "Brand" ["Brand" ...] --out RUN` | That brand's listings found by searching its name (2 pages). Keeps only listings whose brand line or title start matches, so it can miss listings whose titles do not lead with the brand |
| `NSKU autocomplete "prefix" [...] [--expand] --out RUN` | Amazon search suggestions; `--expand` also tries "prefix a" to "prefix z" |

### No Python? Use browser tools instead

If you can't run scripts but you do have a browser tool (for example Claude
in Chrome), follow `chrome-edition/next-sku/SKILL.md`. It is the light
version of this same method, with its own minimums and guardrails, and its
rules override the limits in this file. In short:

| Script command | Browser equivalent |
|---|---|
| `product ASIN` | open `https://www.amazon.com/dp/ASIN`, scroll to load carousels, read the fields listed above |
| `search "kw"` | open `https://www.amazon.com/s?k=kw` (spaces as `+`) and read page one |
| `brand "Brand"` | search the brand name and keep that brand's listings |
| `autocomplete "prefix"` | type the prefix into Amazon's search box without pressing Enter and read the suggestions |

- **Minimums, not caps.** At least 6 shopper keywords, 4 competitor brands,
  8 competitor product pages and 4 seller product pages read in full, 3
  autocomplete prefixes plus one per candidate, and both a search check and
  an autocomplete check for every candidate. If a minimum cannot be met, say
  which one and why.
- **Baseline first.** Build the seller's catalog table before comparing
  anything. Nothing the seller already sells may appear as a gap or a new
  product.
- **Compact reads.** Read pages with in-page JavaScript that returns one
  line per listing. Never read a whole Amazon page as text: it can run to
  tens of thousands of tokens and freeze the tab. Write "not captured" for
  anything you could not read.
- **Demand gate.** A candidate without both checks is "Unvalidated", not
  Strong or Moderate.
- **Reviews.** Logged out, the full review list is hidden. Use "Customers
  say" and visible snippets, and say that 1 to 3 star reviews were not read.
- **Check before reporting.** Every number must appear in your notes, and
  the coverage counts must match what you actually did.

Skip `findings.json` and the renderer: write the report straight into the
chat. If Amazon shows a "confirm you're human" page, ask the user to solve
it, then continue.

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
  best sellers rank are public signals, not sales data. Say so. "Bought in
  past month" is a floor bucket ("50+", "3K+"), not a count: never add or
  average it.
- **Brand is not seller.** Take the brand from the product page byline
  ("Visit the X Store" or "Brand: X"). "Sold by" names the seller of record,
  which can be a different company.
- **Variations share reviews.** Listings with the same ratings count and
  near-identical titles are variations of one product family. Count the
  family once for ratings and brand tallies, and keep "bought in past month"
  per listing.
- **Date and place.** Prices and availability depend on the delivery
  location Amazon shows and on the day. Record both in the report.
- **Seasonality.** "Bought in past month" reflects the current season. Flag
  seasonal categories (for example water toys in winter) so a low number is
  not read as low demand.
- **If Amazon blocks a page,** the script returns `status: "captcha"` or an
  error. Retry that item once later in the run; if it fails again, record it
  in `coverage.blocked` and keep going. If most pages are blocked, stop and
  tell the user, suggesting they solve the check in the Chrome window and try
  again in a few minutes.
- **Keep the user informed** with one short line at the start of each step.
  Don't paste raw JSON into the chat.

## Step 0: Intake and setup

1. Get the input. Accept an ASIN (10 characters, usually starting `B0`) or any
   Amazon product URL (pull the ASIN from `/dp/XXXXXXXXXX`). If the user gives
   a search instead (for example "the top non-sponsored result for matcha
   powder"), run it, take the first result not labeled Sponsored, confirm its
   ASIN on its product page, and tell the user which product you picked. If
   none was given, ask once: "Which Amazon product should I start from? Paste
   an ASIN or product link." If the user also lists more of their own ASINs,
   use them all as known catalog.
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

Note the brand (from the byline), the product's core noun (for example
"matcha powder"), format, size or count, price and unit price, best sellers
rank and leaf category, variations offered, the "From the brand" section if
present (it names the brand's other lines), and every ASIN in the related
carousels. Read the reviews and "Customers say" for wishes and complaints.

## Step 2: Map the brand's whole catalog (the baseline)

This step decides everything that follows. Do it fully before comparing
anything.

1. `NSKU brand "<Brand>" --out RUN`, and also `NSKU search "<Brand> <core noun>"`.
   The brand command keeps only listings whose brand line or title start
   matches, so it can miss listings that do not lead with the brand name.
2. If the byline links to a Brand Store, open it and list the products. If
   it cannot be read, say so.
3. Read in full (`NSKU product`) one listing for each distinct product line,
   plus every pack, size and format variation of the starting product
   (including rechargeable, multi-pack and bundle versions). Read all of them
   if the brand has fewer than five.
4. Write the catalog table: product line, ASINs, pack or size or format,
   price, rating, ratings count, bought in past month. Group variations of
   one product as a family. Rank the lines by traction (ratings and bought
   in past month).
5. Treat the catalog as a lower bound and say so in `catalog.notes`.

Every later step is checked against this table.

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

If the catalog has other product lines with traction, give each of the top
two or three at least one keyword, so expansion ideas have competitors to
study. Prefer terms autocomplete actually suggested. Avoid brand names.

## Step 4: Find the real competitors

`NSKU search "kw1" "kw2" ... --out RUN`

Tally brands across all searches (use `brands_seen`). Search cards often do
not show the brand. Take brands from product pages for the strongest
listings. For card-only listings use a brand only if the title starts with
it, otherwise record "brand not shown" and never count that as a brand or
guess. Classify:

- **Primary:** appears in 3+ of the searches, or 6+ listings overall
- **Secondary:** appears in 2 searches or 3 to 5 listings
- ignore one-off brands unless they rank in the top 5 with strong signals

Pick the top **4 to 6** competitors (Primary first), excluding the seller.
If few named brands qualify (common where listings are generic), include the
strongest generic listings by ratings and bought in past month and say so.

## Step 5: Read competitor catalogs and best sellers

1. `NSKU brand "Comp A" "Comp B" ... --out RUN`
2. Choose the 4 to 6 strongest competitor listings (most ratings or highest
   "bought in past month") and read them in one call:
   `NSKU product ASIN1 ASIN2 ... --out RUN`

These pages supply variations, price tiers, bought-together and
also-viewed products, and reviews, especially the 1 to 3 star ones that
reveal unmet needs.

## Step 6: Fix what you have, and gaps to fill (mode `gaps` or `both`)

Compare the seller's catalog table with each competitor catalog along these
axes:

| Axis | Look for |
|---|---|
| Product type | Types 2+ competitors sell |
| Format | Powder vs capsules vs sticks vs liquid, refill vs starter kit, battery vs rechargeable |
| Size and count | Trial sizes, family or bulk sizes, multi-packs |
| Bundles and kits | Bought-together pairs competitors package as one listing |
| Variants | Flavors, colors, scents, strengths competitors offer |
| Price tier | Empty budget, mid or premium bands in the category |
| Audience | Kids, pets, travel, gifting, professional, dietary needs |

**Check the catalog table first for every difference, then sort it:**

- **Seller does not sell it.** It is a gap. A gap counts when **at least 2
  competitors** sell it, or 1 competitor sells it with strong demand
  signals. Keep the 3 to 6 strongest.
- **Seller sells it and it trails the competitor version** on price,
  ratings, bought in past month or complaints in "Customers say". It is a
  **fix or promote** item, not a gap. Name the seller's ASIN, show the
  comparison, and say what to change (price or value story, quality,
  listing, reviews).
- **Seller sells it and it holds its own.** Drop it.

Same product type, format and pack at a different price is a fix (price or
value). A pack, size or format the seller does not sell is a gap.

Every gap must record the catalog rows checked. Every fix must name the
seller's listing.

## Step 7: Products to expand into (mode `expand` or `both`)

Start from the catalog's product lines, not only the starting product.
For the top two or three lines by traction, and for ideas that cross lines
(the same shopper, season or use), look at:

- items that repeat in **bought together / also bought / also viewed**
  carousels across the seller's and competitors' pages
- autocomplete branches of the core noun that point to a different product
  ("matcha whisk", "matcha latte kit", "matcha cups")
- the parent and sibling categories in the breadcrumbs
- review wishes and complaints that describe a product nobody sells well
  ("wish it came in single-serve", "too bitter for lattes")

Drop anything already in the catalog table. Keep the 3 to 6 that a brand
like this could credibly make or source, and record which catalog line each
one grows from.

## Step 8: Validate demand

For every candidate from steps 6 and 7 (cap at about 10), write a short
shopper phrase for it, then in two batched calls:

- `NSKU autocomplete "phrase1" "phrase2" ... --out RUN`
- `NSKU search "phrase1" "phrase2" ... --out RUN`

Rate demand from the evidence. A candidate with either check missing is
**Unvalidated** and cannot be rated Strong or Moderate.

- **Strong:** autocomplete suggests it, and 2+ page-one listings show
  "1K+ bought in past month" or 1,000+ ratings
- **Moderate:** autocomplete suggests it and some page-one listings show
  sales signals
- **Thin:** no autocomplete suggestion, or page one is mostly unrelated

Count a product family once when applying the thresholds. Also note the
price band of page-one listings and how many results were sponsored (heavy
ads mean costlier entry), and flag seasonal categories.

Rate **brand fit**: Strong (same category, shopper and price tier),
Moderate (same shopper, new category or format), Stretch (new shopper or
very different sourcing). Thin or Stretch items stay in the report, ordered
last, because the seller may know something the data doesn't.

Put these flags in each opportunity's risks where they apply, as things to
verify and never as legal conclusions: categories that commonly carry
compliance requirements (children's products, batteries and electrical,
food, supplements), and ideas that would copy a named competitor's branded
or design-protected product (recommend the category or feature instead).

## Step 9: Write the report

1. Write `RUN/findings.json` following `reference/findings-schema.md`.
   Order opportunities within each type by demand, then fit.
2. Before rendering, check: every number traces to `RUN/raw/`, nothing in
   the gaps is in the catalog table, nothing in the expansions is already
   sold, and the coverage counts match what was run.
3. Render it: `python "<skill dir>/scripts/render_report.py" RUN/findings.json`
4. Tell the user where `RUN/report.html` is and offer to open it. Then give
   a short chat summary: the headline, the top 3 picks with one line of
   evidence each, and anything that could not be read.

Write in plain, confident language a busy seller can skim. No hype and no
filler. Each opportunity's `what` is one sentence a seller could act on.
