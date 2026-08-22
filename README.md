# couponfinder

Crawl web pages and automatically detect coupon codes by recognizing their
naming patterns: keywords like "promo code" / "use code", HTML markers such
as `data-code` attributes or `coupon`-flavored class names, and common code
shapes like `SAVE20` or `WELCOME15`.

## Install

```bash
pip install -e ".[dev]"
```

## CLI usage

```bash
couponfinder https://example.com/deals
couponfinder https://example.com/deals --json

# crawl many URLs from a file (one per line, '#' lines ignored) and write a
# pipe-delimited CSV report
couponfinder --input-file urls.txt --output results.csv

# or configure the paths once in config.ini (key="value" lines: input-file,
# output-file) and just run:
couponfinder
```

## Library usage

```python
from couponfinder import find_coupon_codes

codes = find_coupon_codes("https://example.com/deals")
for c in codes:
    print(c.code, c.confidence, c.source)
```

`extract_offer_details()` (in `extractor.py`) additionally pulls the offer's
price, expiration date, and valid location out of the page text, and the CLI
prints all of it in column format:

```
https://example.com/deals
Price  Location                                                      Expires
-----  ------------------------------------------------------------  ----------
$9.99  Great Clips Eagle Eye Plaza at 4840 Asbury Rd in Dubuque, IA  10/09/2026

Code    Confidence  Source
------  ----------  ---------------
2MXK6M  high        bracket_segment
```

## How it works

1. `crawler.py` fetches the raw HTML for each URL.
2. `extractor.py` strips `<script>`/`<style>` tags, then looks for candidate
   coupon codes in four ways, from most to least reliable:
   - HTML elements whose class/id/data-attributes look coupon-related.
   - Text segments explicitly wrapped in literal `<...>` markers (common on
     deal sites that highlight the description, terms, and code this way) —
     only tokens mixing letters and digits inside those segments are taken.
   - Text following keywords such as "promo code", "use code", "discount code".
   - Standalone uppercase alphanumeric tokens that look like codes.
3. Candidates are deduplicated and ranked by confidence (`high`, `medium`, `low`).
4. `extract_offer_details()` separately scans the same cleaned text for the
   offer price (`$9.99`), expiration date (`Expires 10/09/2026`), and valid
   location (`Valid at ...` / `Valid only at ...`).

## Tests

```bash
pytest
```

## Web UI

The web application is a React + Vite frontend deployed with Vercel Functions.
Offers are stored in Supabase PostgreSQL. The UI loads offer metadata from
`/api/offers`; it deliberately loads an individual code only after a visitor
clicks **Claim Code**.

```bash
cd ui
npm install
npm run dev
```

For local API development, install the Vercel CLI and run `vercel dev` from the
repository root. Do not use `files/urls.txt` for the deployed app: paste URLs
into the **Admin** tab instead.

### Deploy to Vercel and Supabase

1. In the Supabase SQL editor, run
   `supabase/migrations/001_couponfinder.sql`.
2. Create a Vercel project from this repository. The included `vercel.json`
   builds `ui/` and deploys the Python files in `api/` as serverless functions.
3. Add these Vercel environment variables:

   ```text
   DATABASE_URL=postgresql://...     # use the Supabase pooler connection string
   DB_SCHEMA=coupons
   DB_TABLE=gc_coupons
   ADMIN_API_TOKEN=<long-random-secret>
   ALLOWED_COUPON_HOSTS=offers.greatclips.com
   ```

4. In the deployed **Admin** tab, enter `ADMIN_API_TOKEN`, paste up to ten
   allowed HTTPS URLs, and select **Fetch Coupons**. The protected
   `/api/fetch-coupons` endpoint fetches raw HTML, extracts the offer data, and
   upserts it into Supabase.

Vercel serverless Python functions cannot run the project's Playwright browser
workflow. The deployed Admin page therefore uses raw HTML only and may not
capture coupon codes that appear only after JavaScript rendering or a
redemption click.

Keep `DATABASE_URL` and `ADMIN_API_TOKEN` only in deployment environment
variables, never in `config.ini` or frontend `VITE_*` variables.
