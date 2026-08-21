"""Fetch a URL (or read a local HTML file) and print the extracted text plus any matches.

Useful for debugging why couponfinder did or didn't find a code on a given page:

    python scripts/inspect_page.py https://offers.greatclips.com/tuyspvO
    python scripts/inspect_page.py saved_page.html
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from couponfinder.crawler import fetch_html  # noqa: E402
from couponfinder.extractor import clean_text, extract_coupon_codes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="URL to fetch, or path to a local .html file")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    if args.source.startswith(("http://", "https://")):
        html = fetch_html(args.source, timeout=args.timeout)
        url = args.source
    else:
        html = Path(args.source).read_text(encoding="utf-8")
        url = args.source

    print("=" * 30, "RAW HTML LENGTH:", len(html), "=" * 30)
    print("=" * 30, "EXTRACTED TEXT", "=" * 30)
    print(clean_text(html))

    print("=" * 30, "MATCHES", "=" * 30)
    results = extract_coupon_codes(html, url=url)
    if not results:
        print("no coupon codes found")
    for result in results:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
