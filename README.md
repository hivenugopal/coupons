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

`ui/` is a React + Vite app that browses the `results.csv` produced by the CLI.
It reads the CSV live from the `files/` folder (no copy step needed), so run
the CLI with `--output` (or the `config.ini` defaults) first to populate it.

```bash
cd ui
npm install
npm run dev
```

Open the printed local URL to search offers by state/city and reveal a coupon
code with the "Claim Code" button.
