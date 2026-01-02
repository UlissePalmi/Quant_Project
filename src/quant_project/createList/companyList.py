import requests
import time
from datetime import date
from pathlib import Path


HEADERS = {"User-Agent": "Ulisse upalmier@nd.edu"}  # SEC requires this

def quarterly_master_url(year, qtr):
    return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/master.idx"

def iter_master_lines(year, qtr):
    url = quarterly_master_url(year, qtr)
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    lines = r.text.splitlines()
    # skip header; data starts after a line that begins with "CIK|" in newer formats
    for line in lines:
        if line.startswith("CIK|"):
            header_seen = True
            continue
        if "|" in line:
            yield line

def get_10k_filing_urls(start_date, end_date):
    urls = []
    for year in range(start_date.year, end_date.year + 1):
        for qtr in range(1, 5):
            for line in iter_master_lines(year, qtr):
                cik, name, form_type, filed, filename = line.split("|")

                # 1) Only 10-K-type forms
                if not form_type.startswith("10-K"):
                    continue

                # 2) Only filings in your date range
                filed_date = date.fromisoformat(filed)
                if not (start_date <= filed_date <= end_date):
                    continue

                # 3) Only companies whose name starts with "A"
                #    Names in the index are usually uppercase already, but we normalize just in case
                if not name.strip().upper().startswith("A"):
                    continue

                urls.append("https://www.sec.gov/Archives/" + filename)

    return urls

OUTPUT_DIR = Path(__file__).resolve().parent / "filings"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
start = date(2024, 1, 1)
end   = date(2025, 12, 31)
filing_urls = get_10k_filing_urls(start, end)

print("Total 10-K filings:", len(filing_urls))

# Then download them, respecting rate limits:
for i, url in enumerate(filing_urls, 1):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    out_path = OUTPUT_DIR / f"10k_{i}.txt"
    with open(out_path, "wb") as f:
        f.write(resp.content)
