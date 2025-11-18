from sec_edgar_downloader import Downloader
from pathlib import Path
import csv

def download_from_edgar(t):
    dl = Downloader("MyCompanyName", "my.email@domain.com", "data/html")
    document = "10-K"
    try:
        dl.get(document, t, limit=100)
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

letter = input("Select List (L) or Enter Ticker (T)...").lower()
while letter != 'l' and letter != 't':
    letter = input("Invalid... enter L or T...").lower()

if letter == 'l':
    read_tickers("ticker_list.csv")
else:
    t = input("Enter ticker...").upper()

download_from_edgar(t)