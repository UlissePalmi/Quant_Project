from sec_edgar_downloader import Downloader
from pathlib import Path
import re
import os
import csv

def download_from_edgar(t):
    dl = Downloader("MyCompanyName", "my.email@domain.com", "data/html")

    #ticker = input("Inserire ticker: ")
    document = "10-K"
    try:
        dl.get(document, t, limit=40)
    except ValueError:
        print(f"Ticker {t} not found\n")
        not_found_ticker.append(t)
    else:
        print(f"Success: ticker {t} found\n")
    return

def read_tickers(csv_path: str) -> list[str]:
    """
    Reads a CSV that has tickers (any header name). Uses the first column,
    strips whitespace, uppercases, and de-dupes while preserving order.
    """
    tickers = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        for row in r:
            if not row:
                continue
            cell = (row[0] or "").strip().upper()
            if not cell or cell in {"TICKER", "TICKERS"}:
                # skip header-like first cell
                continue
            tickers.append(cell)
    # de-dupe, keep order
    seen = set()
    out = []
    for t in tickers:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out

not_found_ticker = []
'''
csv_path = Path.cwd() / "company_list.csv"
ticker_list = read_tickers(csv_path)

root = Path("data")/ "html" / "sec-edgar-filings"
done_ticker = sorted([p.name for p in root.iterdir() if p.is_dir()])



for t in ticker_list:
    if not t in done_ticker:
        download_from_edgar(t)
    else:
        print(f"Ticker {t} is already downloaded\n")
'''

t = "A"
download_from_edgar(t)