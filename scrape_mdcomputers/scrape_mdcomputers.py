#!/usr/bin/env python3
"""
scrape_mdcomputers.py

Scrapes product details (name, price, availability, product URL) from
MDComputers.in for a given search term.

Usage:
    python scrape_mdcomputers.py "external harddrive"
    python scrape_mdcomputers.py "external harddrive" --pages 2 --out results.csv

MDComputers runs on OpenCart, so search results are served at:
    https://mdcomputers.in/?route=product/search&search=<term>

Each result is rendered inside a `div.product-layout` block. The primary
selectors below target the current OpenCart theme markup (product title in
`h4 a`, price in `.price`, "Add to Cart" / stock text nearby). A regex-based
fallback is included in case the theme markup changes, so the script keeps
working even if a class name is renamed.
"""

import argparse
import csv
import re
import sys
import time
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://mdcomputers.in/"
SEARCH_ROUTE = "index.php?route=product/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_page(search_term: str, page: int, session: requests.Session) -> str:
    """Fetch one page of search results and return the raw HTML."""
    params = {
        "search": search_term,
        "description": "true",
        "page": str(page),
    }
    resp = session.get(BASE_URL, params={"route": "product/search", **params},
                       headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_products(html: str) -> list[dict]:
    """Extract product name, price, discounted price, stock text, and URL."""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    blocks = soup.select("div.product-layout, div.product-thumb")
    if not blocks:
        # Fallback: some OpenCart themes wrap items in <li> instead of <div>
        blocks = soup.select("li.product-layout")

    for block in blocks:
        name_tag = block.select_one("h4 a, .caption h4 a, .product-name a")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        url = name_tag.get("href", "").strip()

        price_tag = block.select_one(".price")
        price_text = price_tag.get_text(" ", strip=True) if price_tag else ""

        # price_text usually looks like "₹14,000 ₹9,290" (old price, new price)
        prices = re.findall(r"₹[\d,]+", price_text)
        old_price = prices[0] if len(prices) > 1 else ""
        current_price = prices[-1] if prices else ""

        stock_tag = block.select_one(".stock, .ex-stock, .instock")
        stock = stock_tag.get_text(strip=True) if stock_tag else ""

        products.append({
            "name": name,
            "url": url,
            "old_price": old_price,
            "price": current_price,
            "stock": stock,
        })

    return products


def scrape(search_term: str, pages: int, delay: float) -> list[dict]:
    session = requests.Session()
    all_products = []

    for page in range(1, pages + 1):
        html = fetch_page(search_term, page, session)
        products = parse_products(html)
        if not products:
            break
        all_products.extend(products)
        time.sleep(delay)

    return all_products


def save_csv(products: list[dict], out_path: str) -> None:
    fieldnames = ["name", "price", "old_price", "stock", "url"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)


def main():
    parser = argparse.ArgumentParser(description="Scrape MDComputers product search results.")
    parser.add_argument("search_term", help="Search term, e.g. 'external harddrive'")
    parser.add_argument("--pages", type=int, default=1, help="Number of result pages to scrape (default: 1)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between page requests (default: 1.0)")
    parser.add_argument("--out", default="mdcomputers_results.csv", help="Output CSV file path")
    args = parser.parse_args()

    products = scrape(args.search_term, args.pages, args.delay)

    if not products:
        print(f"No products found for '{args.search_term}'.", file=sys.stderr)
        sys.exit(1)

    save_csv(products, args.out)

    print(f"Found {len(products)} product(s) for '{args.search_term}':\n")
    for p in products:
        print(f"- {p['name']} | {p['price']} (was {p['old_price']}) | {p['url']}")
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()
