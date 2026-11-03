---
name: next-sku
description: Find the next products an Amazon brand should launch from one ASIN, by browsing public Amazon pages with Claude in Chrome. Use for what to sell next on Amazon, competitor gap analysis, or catalog expansion ideas.
---

# Next SKU (Claude in Chrome edition)

Next SKU answers one question for an Amazon seller: **what should I launch next?** From one ASIN it browses public Amazon pages in the user's own Chrome (never logged in), learns what the brand sells, finds the brands competing for the same shoppers, and reports:

1. **Gaps to fill:** product types, formats, sizes, pack counts, bundles, variants and price tiers competitors sell and this brand does not.
2. **Products to expand into:** nearby products the same shoppers buy together, search for, or ask for in reviews.

The full open source version (with Python scripts and an HTML report for Claude Code) lives at https://github.com/victordelgadopm/next-sku.

## Browsing rules

- Use Claude in Chrome. Open new tabs; close the ones you opened when done.
- Public pages only: never log in, add to cart or click ads. Navigate by URL. One tab at a time, with a short pause between pages.
- Product page: `https://www.amazon.com/dp/ASIN`. Search: `https://www.amazon.com/s?k=keyword+words`. Autocomplete: type into Amazon's search box without pressing Enter and read the suggestions.
- Scroll product pages to the bottom so carousels load.
- If Amazon shows a "confirm you're human" page, ask the user to solve it, then continue.
- Never invent numbers. Every price, count, rank or quote must be something you saw. Label autocomplete, "bought in past month", ratings counts and best sellers rank as public proxies, not sales data. No margin or revenue estimates.

## Reading pages without flooding the chat

- Never read a whole Amazon search or product page as page text. These pages can run to tens of thousands of tokens, which truncates results and can freeze the tab. Pull only the fields below with in-page JavaScript and return one compact line per listing. When a batch tool is available, batch several navigations and reads into one call.
- Fields per listing: ASIN, brand, start of title (about 60 characters), price, size or count, rating, ratings count, "bought in past month", sponsored (yes or no). On product pages also: best sellers rank and category, variations, Subscribe & Save offered. If a field cannot be read, write "not captured". Do not fill it from memory, and do not infer it from the title unless the title states it.
- Search results: read the ASIN from each result card, drop duplicates by ASIN, read the first 15 cards, and mark which are sponsored. Many titles do not name a brand. Read the brand line on the card; if there is none, record "unbranded" and never guess a brand.
- Starting point for search cards (check the first output looks right, and adjust if Amazon changes its markup):

```js
[...document.querySelectorAll('[data-component-type="s-search-result"]')].slice(0,15).map((c,i)=>{
  const l=c.innerText.split('\n').map(x=>x.trim()).filter(Boolean);
  const n=(c.querySelector('[aria-label*="ratings"]')?.getAttribute('aria-label')||'').replace(' ratings','');
  const b=(c.innerText.match(/([\d.,K+]+)\s*bought in past month/)||['',''])[1];
  return [i+1,c.dataset.asin,(l.find(x=>x.length>25)||'').slice(0,60),c.querySelector('.a-price .a-offscreen')?.innerText,n,b,/Sponsored/.test(c.innerText)?'SP':''].join('|')
}).join('\n')
```

- Autocomplete: clear the search box (select all, then type) before each new prefix, and confirm the suggestions shown match the prefix you typed. Leftover text from the previous prefix gives wrong suggestions.
- If a page returns nothing or the tab stops responding, wait a few seconds and try once more. If it still fails, open a new tab (old tab ids stop working). Never retry the same page more than twice. Record what you could not read in the coverage section.
- Reviews: logged out, Amazon hides the full review list ("Sign in to see customer reviews"). Use the "Customers say" summary and any review snippets on the product page, and say in the report that 1 to 3 star reviews could not be read.
- Keep notes: one line per listing using the fields above, in a notes file if you can write files, otherwise in a running block in the chat. The report may only cite numbers that appear in your notes.

## Minimums (floors, not targets)

Do at least this much, and more in wide categories:

| Item | Minimum |
|---|---|
| Shopper keywords searched (page one each) | 6, aim for 8 |
| Autocomplete prefixes read | 3, plus one per candidate |
| Competitor brands chosen | 4, aim for 5 |
| Brand catalog searches | the seller and every chosen competitor |
| Competitor product pages read in full | 8, at least 2 per top competitor |
| Candidates validated | every candidate (at least 6), each with an autocomplete check and a search check |
| Opportunities reported | 3 to 6 gaps and 3 to 6 products to expand into |

If a minimum is not met (blocked page, too few brands in the category, tab failures), do not continue silently. Say which one and why in the Data coverage section of the report.

## Steps

**0. Intake.** Get an ASIN or Amazon product URL (ASIN is the 10 characters after `/dp/`). If the user gives a search instead (for example "the top non-sponsored result for matcha powder"), run that search, take the first result not labeled Sponsored, confirm its ASIN on its product page, and tell the user which product you picked. If there is neither, ask once. Pick the mode without asking: "gaps / what am I missing" = gaps; "similar / venture into / expand" = expand; otherwise both. Tell the user Chrome will browse Amazon for about 15 to 25 minutes.

**1. Starting product.** Read title, brand, price and unit price, rating and ratings count, best sellers rank and category, variations, bought-together / also viewed / sponsored carousels, and "Customers say".

**2. Brand catalog.** Search the brand name and list the brand's own listings: types, formats, sizes, packs, variants, price points. This is the baseline. If the brand search finds little, say so and lean on the starting product's variations.

**3. Keywords.** Check autocomplete for the core product noun (also try the noun plus a few letters). Choose 6 to 8 shopper keywords covering the core product, format, use or occasion, audience or need, and the wider category. Prefer suggested terms; no brand names.

**4. Competitors.** Search each keyword (page one). Tally brands by distinct ASIN, not by repeated cards. Primary = in 3+ searches or 6+ listings; Secondary = in 2 searches or 3 to 5 listings. Pick the top 4 to 5, excluding the seller. If fewer than 4 named brands qualify (common in categories full of unbranded listings), add the strongest unbranded listings by ratings and "bought in past month" and say so.

**5. Competitor catalogs.** Search each competitor's brand name and list their catalog (types, sizes, packs, prices, ratings). Then open at least 8 strong competitor listings in full (most ratings or highest "bought in past month", at least 2 per top competitor) for variations, price tiers, carousels and "Customers say". Do not describe a brand's catalog from search titles alone.

**6. Gaps to fill.** Compare catalogs on product type, format, size and count, bundles and kits, variants, price tier and audience. A gap counts when 2+ competitors sell it, or 1 does with strong demand. Keep the 3 to 6 strongest.

**7. Products to expand into.** Look at items repeating in bought-together / also viewed carousels, autocomplete branches pointing to a different product, parent and sibling categories, and review wishes nobody serves well. Keep the 3 to 6 a brand like this could credibly make or source.

**8. Validate demand.** For every candidate from steps 6 and 7, write a short shopper phrase, check it in autocomplete, and search it. Record both in your notes. A candidate with either check missing is "Unvalidated" and cannot be rated Strong or Moderate. Strong = suggested by autocomplete and 2+ page-one listings show 1K+ bought in past month or 1,000+ ratings. Moderate = suggested and some sales signals. Thin = otherwise. Note the page-one price band and how many results are sponsored. Rate fit: Strong (same category, shopper, price tier), Moderate (same shopper, new category or format), Stretch (new shopper or very different sourcing). Put Thin and Stretch items last; do not drop them.

**9. Check before reporting.** Confirm all of these, and fix anything that fails:
- Every number in the report appears in your notes.
- The counts in the Data coverage table match what you actually did (count the searches and pages in your notes; do not estimate).
- Every opportunity has a demand label, and its autocomplete and search checks are in your notes.
- Brand and catalog claims come from a brand search or product page, not from titles alone.
- Anything unread, blocked or skipped is listed in Data coverage.

**10. Report in the chat**, plain and skimmable:
- Headline and 2 to 3 sentence summary
- Top 3 picks, one line of evidence each
- Data coverage: a table of each minimum against what was done, plus anything blocked, skipped or not captured (including that 1 to 3 star reviews were not readable)
- Product types found: type, listings seen, brands selling it, whether the seller has it
- Gaps to fill: for each, name, one-sentence action, demand level and the checks behind it, price band, who sells it (ASIN, price, rating, bought in past month), what customers say, how to stand out, risks, 1 to 3 listings to study (ASIN links)
- Products to expand into: same format
- Pricing: size or pack ladder by brand with price, and price per unit only where both numbers were seen on the page
- Competitive landscape table: brand, tier, products seen, price range, where they win
- How this was built: what was read, what could not be read, and that the seller makes the call
