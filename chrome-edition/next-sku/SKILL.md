---
name: next-sku
description: Find the next products an Amazon brand should launch from one ASIN, by browsing public Amazon pages with Claude in Chrome. Use for what to sell next on Amazon, competitor gap analysis, or catalog expansion ideas.
---

# Next SKU (Claude in Chrome edition)

Next SKU answers one question for an Amazon seller: **what should I launch next?** From one ASIN it browses public Amazon pages in the user's own Chrome (never logged in), maps everything the brand already sells, finds the brands competing for the same shoppers, and reports three things:

1. **Fix or promote what you already sell:** products the brand has that trail competitors on price, traction or quality.
2. **Gaps to fill:** product types, formats, sizes, pack counts, bundles, variants and price tiers competitors sell and this brand does not.
3. **Products to expand into:** new product lines the same shoppers buy, search for, or ask for in reviews. These grow from the brand's whole catalog, not only the starting product.

The full open source version (with Python scripts and an HTML report for Claude Code) lives at https://github.com/victordelgadopm/next-sku.

Amazon.com (US) only. If the user names another retailer or another Amazon country site, say it is not supported yet and offer to run on Amazon.com instead.

## Browsing rules

- Use Claude in Chrome. Open new tabs; close the ones you opened when done.
- Public pages only: never log in, add to cart or click ads. Navigate by URL. One tab at a time, with a short pause between pages.
- Product page: `https://www.amazon.com/dp/ASIN`. Search: `https://www.amazon.com/s?k=keyword+words`. Autocomplete: type into Amazon's search box without pressing Enter and read the suggestions.
- Scroll product pages to the bottom so carousels load.
- If Amazon shows a "confirm you're human" page, ask the user to solve it, then continue.
- Never invent numbers. Every price, count, rank or quote must be something you saw. Label autocomplete, "bought in past month", ratings counts and best sellers rank as public proxies, not sales data. No margin or revenue estimates.
- Record the date of the run and the delivery location Amazon shows. Prices and availability depend on both.

## Reading pages without flooding the chat

- Never read a whole Amazon search or product page as page text. These pages can run to tens of thousands of tokens, which truncates results and can freeze the tab. Pull only the fields below with in-page JavaScript and return one compact line per listing. When a batch tool is available, batch several navigations and reads into one call. Keep each JavaScript result short (roughly 800 characters shows reliably), so read in several small calls rather than one large one.
- Fields per listing: ASIN, brand, start of title (about 60 characters), price, size or count, rating, ratings count, "bought in past month", sponsored (yes or no). On product pages also: best sellers rank and category, variations. If a field cannot be read, write "not captured". Do not fill it from memory, and do not infer it from the title unless the title states it. Best sellers rank is often unreadable, so do not rely on it.
- Do not use Subscribe & Save as a signal. The text appears on pages that do not offer it, so it cannot be read reliably.
- **Brand comes from the product page.** Search cards usually have no brand line. Take the brand from the byline on the product page ("Visit the X Store" or "Brand: X"). For a card you did not open, use a brand only if the title starts with it; otherwise record "brand not shown". Never guess, and never count "brand not shown" as a brand. "Sold by" names the seller of record, which can be a different company.
- **Searching a brand name can return nothing.** Brand searches match titles, so they miss listings that do not lead with the brand name. A result of 0 does not mean the brand has no other products. Use the brand's Store page when the byline links to one, and say how complete the list is.
- **Variation families.** Listings with the same ratings count and near-identical titles are variations of one product family and share reviews. Count the family once for ratings and brand tallies. Keep "bought in past month" per listing.
- **"Bought in past month" is a floor bucket** ("50+", "1K+", "3K+"), not a count. Never add or average it.
- Search results: read the ASIN from each result card, drop duplicates by ASIN, read the first 15 cards, and mark which are sponsored. Sponsored cards often dominate page one.
- Starting point for search cards (check the first output looks right, and adjust if Amazon changes its markup):

```js
[...document.querySelectorAll('[data-component-type="s-search-result"]')].slice(0,15).map((c,i)=>{
  const l=c.innerText.split('\n').map(x=>x.trim()).filter(Boolean);
  const n=(c.querySelector('[aria-label*="ratings"]')?.getAttribute('aria-label')||'').replace(' ratings','');
  const b=(c.innerText.match(/([\d.,K+]+)\s*bought in past month/)||['',''])[1];
  return [i+1,c.dataset.asin,(l.find(x=>x.length>25)||'').slice(0,60),c.querySelector('.a-price .a-offscreen')?.innerText,n,b,/Sponsored/.test(c.innerText)?'SP':''].join('|')
}).join('\n')
```

- Autocomplete: clear the search box with ctrl+a (cmd+a may not clear it) before each new prefix, and confirm the suggestions shown match the prefix you typed. Leftover text from the previous prefix gives wrong suggestions.
- If a read is blocked by an output filter, retry the same read once; it usually passes. If a page returns nothing or the tab stops responding, wait a few seconds and try once more. If it still fails, open a new tab (old tab ids stop working). Never retry the same page more than twice. Record what you could not read in the coverage section.
- Reviews: logged out, Amazon hides the full review list ("Sign in to see customer reviews"). Use the "Customers say" summary and any review snippets on the product page, and say in the report that 1 to 3 star reviews could not be read.
- Keep notes: one line per listing using the fields above, in a notes file if you can write files, otherwise in a running block in the chat. The report may only cite numbers that appear in your notes.

## Minimums (floors, not targets)

Do at least this much, and more in wide categories:

| Item | Minimum |
|---|---|
| Seller product pages read in full | 4, covering every distinct product line found (all of them if fewer than 5) |
| Shopper keywords searched (page one each) | 6, aim for 8 |
| Autocomplete prefixes read | 3, plus one per candidate |
| Competitor brands chosen | 4, aim for 5 |
| Brand catalog checks | the seller and every chosen competitor |
| Competitor product pages read in full | 8, at least 2 per top competitor |
| Candidates validated | every candidate (at least 6), each with an autocomplete check and a search check |
| Opportunities reported | 3 to 6 gaps and 3 to 6 products to expand into, plus every fix item that holds up |

If a minimum is not met (blocked page, too few brands in the category, tab failures), do not continue silently. Say which one and why in the Data coverage section of the report.

## Steps

**0. Intake.** Get an ASIN or Amazon product URL (ASIN is the 10 characters after `/dp/`). If the user gives a search instead (for example "the top non-sponsored result for matcha powder"), run that search, take the first result not labeled Sponsored, confirm its ASIN on its product page, and tell the user which product you picked. If there is neither, ask once. If the user lists more of their own ASINs, use them all as known catalog. Pick the mode without asking: "gaps / what am I missing" = gaps; "similar / venture into / expand" = expand; otherwise both. Tell the user Chrome will browse Amazon for about 15 to 25 minutes.

**1. Starting product.** Read title, brand (from the byline), price and unit price, rating and ratings count, best sellers rank and category if readable, variations, the "From the brand" section if present, bought-together / also viewed / sponsored carousels, and "Customers say".

**2. Map the brand's whole catalog (the baseline).** This step decides everything after it, so finish it before comparing anything.
- Search the brand name and also "brand + core noun". If the byline links to a Store page, open it and list the products.
- Open one listing for each distinct product line, plus every pack, size and format version of the starting product (rechargeable, multi-pack, bundle). Open all of them if the brand has fewer than 5.
- Write a catalog table: product line, ASINs, pack or size or format, price, rating, ratings count, bought in past month. Group variations of one product as a family. Rank the lines by traction.
- Treat the table as a lower bound and say so. Everything later is checked against it.

**3. Keywords.** Check autocomplete for the core product noun (also try the noun plus a few letters). Choose 6 to 8 shopper keywords covering the core product, format, use or occasion, audience or need, and the wider category. If the catalog has other lines with traction, give each of the top two or three one keyword. Prefer suggested terms; no brand names.

**4. Competitors.** Search each keyword (page one). Tally brands by distinct product family, not by repeated cards, taking brands from product pages where you can. Primary = in 3+ searches or 6+ listings; Secondary = in 2 searches or 3 to 5 listings. Pick the top 4 to 5, excluding the seller. If fewer than 4 named brands qualify (common in categories full of unbranded listings), add the strongest unbranded listings by ratings and "bought in past month" and say so.

**5. Competitor catalogs.** Check each competitor's catalog (types, sizes, packs, prices, ratings) through its Store page or brand search. Then open at least 8 strong competitor listings in full (most ratings or highest "bought in past month", at least 2 per top competitor) for variations, price tiers, carousels and "Customers say". Do not describe a brand's catalog from search titles alone.

**6. Fix what you have, then find gaps.** Compare the catalog table with each competitor catalog on product type, format, size and count, bundles and kits, variants, price tier and audience. Look every difference up in the catalog table first, then sort it:
- The seller does not sell it: it is a **gap**. A gap counts when 2+ competitors sell it, or 1 does with strong demand. Keep the 3 to 6 strongest.
- The seller sells it but it trails the competitor version on price, ratings, bought in past month or complaints: it is a **fix or promote** item, not a gap. Name the seller's ASIN and the comparison, and say what to change.
- The seller sells it and it holds its own: drop it.

The same product type, format and pack at a different price is a fix. A pack, size or format the seller does not sell is a gap. Nothing the seller already sells may appear as a gap.

**7. Products to expand into.** Start from the catalog's product lines, not only the starting product. For the top two or three lines by traction, and for ideas that cross lines (same shopper, season or use), look at items repeating in bought-together / also viewed carousels, autocomplete branches pointing to a different product, parent and sibling categories, and review wishes nobody serves well. Drop anything already in the catalog table. Keep the 3 to 6 a brand like this could credibly make or source, and say which catalog line each grows from.

**8. Validate demand.** For every gap and expansion candidate, write a short shopper phrase, check it in autocomplete, and search it. Record both in your notes. A candidate with either check missing is "Unvalidated" and cannot be rated Strong or Moderate. Strong = suggested by autocomplete and 2+ page-one listings show 1K+ bought in past month or 1,000+ ratings (count a variation family once). Moderate = suggested and some sales signals. Thin = otherwise. Note the page-one price band, how many results are sponsored, and whether the category is seasonal (a low number in the off season is not low demand). Rate fit: Strong (same category, shopper, price tier), Moderate (same shopper, new category or format), Stretch (new shopper or very different sourcing). Put Thin and Stretch items last; do not drop them. In risks, flag things to verify (never legal conclusions): categories that commonly carry compliance requirements (children's products, batteries and electrical, food, supplements), and ideas that would copy a named competitor's branded or design-protected product.

**9. Check before reporting.** Confirm all of these, and fix anything that fails:
- Every number in the report appears in your notes.
- Nothing in the gaps or expansions is in the catalog table. Search the table for each one.
- The counts in the Data coverage table match what you actually did (count the searches and pages in your notes; do not estimate).
- Every opportunity has a demand label, and its autocomplete and search checks are in your notes.
- Brand and catalog claims come from a brand search, Store page or product page, not from titles alone.
- Anything unread, blocked or skipped is listed in Data coverage.

**10. Report in the chat**, plain and skimmable:
- Headline and 2 to 3 sentence summary, with the run date and delivery location
- Top 3 picks, one line of evidence each
- Data coverage: a table of each minimum against what was done, plus anything blocked, skipped or not captured (including that 1 to 3 star reviews were not readable)
- The brand's catalog today: the table from step 2
- Fix or promote: for each, the seller's ASIN, the competitor comparison, and what to change
- Gaps to fill: for each, name, one-sentence action, demand level and the checks behind it, price band, who sells it (ASIN, price, rating, bought in past month), what customers say, how to stand out, risks, 1 to 3 listings to study (ASIN links)
- Products to expand into: same format, plus which catalog line it grows from
- Pricing: size or pack ladder by brand with price, and price per unit only where both numbers were seen on the page
- Competitive landscape table: brand, tier, products seen, price range, where they win
- How this was built: what was read, what could not be read, and that the seller makes the call
