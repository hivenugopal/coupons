"""Command-line interface for couponfinder."""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .crawler import FetchError, fetch_html, fetch_rendered_html
from .extractor import extract_coupon_codes, extract_offer_details
from .models import CouponCode, OfferDetails

CSV_FIELDNAMES = [
    "url",
    "code",
    "confidence",
    "source",
    "price",
    "location",
    "store_name",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "expires",
    "error",
]


def _print_table(headers: List[str], rows: List[List[str]]) -> None:
    """Print rows as a simple column-aligned table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def format_row(row: List[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    print(format_row(headers))
    print(format_row(["-" * w for w in widths]))
    for row in rows:
        print(format_row(row))


def _read_urls_from_file(path: str) -> List[str]:
    """Read one URL per line from a text file, ignoring blank lines and '#' comments."""
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def _load_config(path: str) -> Dict[str, str]:
    """Parse `key="value"` settings (e.g. input-file, output-file) from a config file, if it exists."""
    config_path = Path(path)
    if not config_path.exists():
        return {}

    config: Dict[str, str] = {}
    for raw_line in config_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def _write_csv(path: str, rows: List[dict]) -> None:
    """Append result rows to a pipe-delimited CSV file, writing the header only if it's new/empty."""
    out_path = Path(path)
    write_header = not out_path.exists() or out_path.stat().st_size == 0
    with open(out_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, delimiter="|")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="couponfinder",
        description="Crawl web pages and find coupon codes using naming-pattern detection.",
    )
    parser.add_argument("urls", nargs="*", help="One or more page URLs to crawl")
    parser.add_argument(
        "--input-file",
        metavar="PATH",
        help="Text file with one URL per line (lines starting with # are ignored)",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default="config.ini",
        help='Config file providing default input-file/output-file paths (key="value" lines, default: config.ini)',
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Append all results to a pipe-delimited CSV file at PATH (created with a header if it doesn't exist)",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render pages with a headless browser first (for JS-injected codes; requires the 'render' extra)",
    )
    parser.add_argument(
        "--click",
        metavar="SELECTOR",
        help=(
            "CSS selector to click after rendering, to reveal a code shown only after an action "
            "(e.g. 'Redeem Now'). Warning: on real offer sites this may perform an irreversible "
            "one-time redemption. Implies --render."
        ),
    )
    parser.add_argument(
        "--wait-for",
        metavar="SELECTOR",
        help="CSS selector to wait for before capturing the page (e.g. the element that holds the code)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = _load_config(args.config)
    input_file = args.input_file or config.get("input-file")
    output_file = args.output or config.get("output-file")

    urls = list(dict.fromkeys([*args.urls, *(_read_urls_from_file(input_file) if input_file else [])]))
    if not urls:
        parser.error("Provide at least one URL, or --input-file (or config input-file) with one URL per line")

    all_results: List[CouponCode] = []
    all_details: List[OfferDetails] = []
    csv_rows: List[dict] = []
    exit_code = 0

    for url in urls:
        try:
            if args.render or args.click or args.wait_for:
                html = fetch_rendered_html(
                    url,
                    timeout=args.timeout,
                    wait_selector=args.wait_for,
                    click_selector=args.click,
                )
            else:
                html = fetch_html(url, timeout=args.timeout)
        except FetchError as exc:
            print(f"error: {exc}", file=sys.stderr)
            exit_code = 1
            csv_rows.append({field: "" for field in CSV_FIELDNAMES} | {"url": url, "error": str(exc)})
            continue

        codes = extract_coupon_codes(html, url=url)
        details_list = extract_offer_details(html, url=url)
        all_results.extend(codes)

        if not args.json:
            print(f"\n{url}")
            _print_table(
                ["Price", "Location", "Expires"],
                [[d.price or "-", d.location or "-", d.expires or "-"] for d in details_list],
            )
            print()
            if codes:
                _print_table(
                    ["Code", "Confidence", "Source"],
                    [[c.code, c.confidence, c.source] for c in codes],
                )
            else:
                print("no coupon codes found")
        else:
            all_details.extend(details_list)

        for details in details_list:
            base_row = {
                "url": url,
                "price": details.price or "",
                "location": details.location or "",
                "store_name": details.store_name or "",
                "address_line1": details.address_line1 or "",
                "address_line2": details.address_line2 or "",
                "city": details.city or "",
                "state": details.state or "",
                "expires": details.expires or "",
                "error": "",
            }
            if codes:
                for c in codes:
                    csv_rows.append({**base_row, "code": c.code, "confidence": c.confidence, "source": c.source})
            else:
                csv_rows.append({**base_row, "code": "", "confidence": "", "source": ""})

    if output_file:
        _write_csv(output_file, csv_rows)
        print(f"\nAppended {len(csv_rows)} row(s) to {output_file}", file=sys.stderr)

    if args.json:
        payload = [
            {**d.__dict__, "codes": [c.__dict__ for c in all_results if c.url == d.url]} for d in all_details
        ]
        print(json.dumps(payload, indent=2))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
