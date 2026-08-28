# Int

## MDComputers Product Scraper

[`scrape_mdcomputers/scrape_mdcomputers.py`](scrape_mdcomputers/scrape_mdcomputers.py) scrapes product names, prices, availability, and product URLs from MDComputers search results.

### Requirements

```bash
python3 -m pip install requests beautifulsoup4
```

### Usage

```bash
python3 scrape_mdcomputers/scrape_mdcomputers.py "external harddrive"
python3 scrape_mdcomputers/scrape_mdcomputers.py "external harddrive" --pages 2 --out results.csv
```

The default output file is `mdcomputers_results.csv`. Use `--delay` to control the pause between page requests.
