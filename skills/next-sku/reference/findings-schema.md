# findings.json schema

`scripts/render_report.py` turns this file into `report.html`. Every number
and quote must come from the raw files in `RUN/raw/`. Leave a field out
rather than guessing.

```json
{
  "mode": "both",                       // "gaps" | "expand" | "both"
  "generated_at": "2026-11-03 10:42",
  "headline": "Three gaps and two new lines worth testing next",
  "summary": "Two or three sentences: what the brand sells today, who it competes with, and the biggest takeaway.",
  "top_picks": [                        // up to 3, one line each
    "Single-serve stick packs: 4 of 5 competitors sell them and page one moves 1K+ a month"
  ],

  "seed": {
    "asin": "B0XXXXXXXX",
    "title": "Product title",
    "brand": "Brand",
    "price": "$24.99",
    "rating": "4.5 out of 5 stars",
    "category": "Grocery > Tea > Matcha",
    "bsr": "#12 in Matcha"
  },

  "catalog": {
    "notes": "One sentence on how the catalog was read and any limits.",
    "products": [
      { "asin": "B0XXXXXXXX", "title": "...", "price": "$24.99", "ratings": "1,234" }
    ]
  },

  "competitors": [
    {
      "brand": "Competitor",
      "tier": "Primary",                // "Primary" | "Secondary"
      "products_seen": 14,
      "price_range": "$12 to $38",
      "strengths": "Wide size range, owns the budget tier",
      "why": "Ranked in 5 of 7 searches"
    }
  ],

  "opportunities": [
    {
      "type": "gap",                    // "gap" (mode 1) | "expand" (mode 2)
      "name": "Single-serve stick packs",
      "what": "One sentence the seller can act on.",
      "demand": {
        "level": "strong",              // "strong" | "moderate" | "thin"
        "autocomplete_terms": ["matcha sticks", "matcha packets single serve"],
        "autocomplete": true,           // false when no suggestion was found
        "search_results": "over 1,000 results",
        "bought_past_month": "3 of top 10 show 1K+ bought in past month",
        "top_review_counts": "Top 3 listings: 8,200 / 3,100 / 950 ratings",
        "bsr": "#3,412 in Grocery",     // optional
        "sponsored_share": "5 of 22 page-one results sponsored"
      },
      "price_band": "$14 to $26",
      "fit": "strong",                  // "strong" | "moderate" | "stretch"
      "competitors_selling": ["Competitor A", "Competitor B"],
      "evidence": [
        "Short factual bullet tied to something observed"
      ],
      "customer_signals": [
        "Short review quote or paraphrase, max 3"
      ],
      "differentiation": "How this brand could stand out.",
      "risks": "What could make it hard (ads, price war, sourcing).",
      "example_listings": [
        { "asin": "B0YYYYYYYY", "brand": "Competitor A", "price": "$18.99" }
      ]
    }
  ],

  "coverage": {
    "pages_read": 46,
    "searches": ["matcha powder", "matcha latte mix"],
    "blocked": ["brand: Some Brand (captcha)"],
    "notes": "Optional note on anything partial."
  }
}
```

Comments above are for reference only. The real file must be valid JSON.
