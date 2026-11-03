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
- Public pages only: never log in, add to cart or click ads. Navigate by URL.
- Product page: `https://www.amazon.com/dp/ASIN`. Search: `https://www.amazon.com/s?k=keyword+words`. Autocomplete: type into Amazon's search box without pressing Enter and read the suggestions.
- Scroll product pages to the bottom so carousels and reviews load.
- If Amazon shows a "confirm you're human" page, ask the user to solve it, then continue.
- Never invent numbers. Every price, count, rank or quote must be something you saw. Label autocomplete, "bought in past month", ratings counts and best sellers rank as public proxies, not sales data. No margin or revenue estimates.

## Steps

**0. Intake.** Get an ASIN or Amazon product URL (ASIN is the 10 characters after `/dp/`). If none, ask once. Pick the mode without asking: "gaps / what am I missing" = gaps; "similar / venture into / expand" = expand; otherwise both. Tell the user Chrome will browse Amazon for about 10 to 15 minutes.

**1. Starting product.** Read title, brand, price and unit price, rating and ratings count, best sellers rank and category, variations, bought-together / also viewed / sponsored carousels, visible reviews and "Customers say".

**2. Brand catalog.** Search the brand name and list the brand's own listings: types, formats, sizes, packs, variants, price points. This is the baseline.

**3. Keywords.** Check autocomplete for the core product noun (also try the noun plus a few letters). Choose about 5 shopper keywords covering the core product, format, use or occasion, audience or need, and the wider category. Prefer suggested terms; no brand names.

**4. Competitors.** Search each keyword (page one). Tally brands. Primary = in 3+ searches; Secondary = in 2. Pick the top 3 to 4, excluding the seller.

**5. Competitor catalogs.** Search each competitor's brand name, then open their 3 strongest listings (most ratings or highest "bought in past month") for variations, price tiers, carousels and 1 to 3 star reviews.

**6. Gaps to fill.** Compare catalogs on product type, format, size and count, bundles and kits, variants, price tier and audience. A gap counts when 2+ competitors sell it, or 1 does with strong demand. Keep the 3 strongest.

**7. Products to expand into.** Look at items repeating in bought-together / also viewed carousels, autocomplete branches pointing to a different product, parent and sibling categories, and review wishes nobody serves well. Keep the 3 a brand like this could credibly make or source.

**8. Validate demand.** For each candidate, check autocomplete and search it. Strong = suggested by autocomplete and 2+ page-one listings show 1K+ bought in past month or 1,000+ ratings. Moderate = suggested and some sales signals. Thin = otherwise. Note the page-one price band and how many results are sponsored. Rate fit: Strong (same category, shopper, price tier), Moderate (same shopper, new category or format), Stretch (new shopper or very different sourcing).

**9. Report in the chat**, plain and skimmable:
- Headline and 2 to 3 sentence summary
- Top 3 picks, one line of evidence each
- Gaps to fill: for each, name, one-sentence action, demand level and signals, price band, who sells it, customer quotes, how to stand out, risks, 1 to 3 listings to study (ASIN links)
- Products to expand into: same format
- Competitive landscape table: brand, tier, products seen, price range, where they win
- How this was built: what was read, what could not be read, and that the seller makes the call
