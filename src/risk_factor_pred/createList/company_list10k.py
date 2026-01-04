import requests
import pandas as pd
from pathlib import Path

HEADERS = {
    "User-Agent": "Ulisse upalmier@nd.edu",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

def quarterly_master_url(year: int, qtr: int) -> str:
    return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/master.idx"

def load_master_to_dataframe(year: int, qtr: int) -> pd.DataFrame:
    """
    Download master.idx for a given year/quarter and return it as a DataFrame
    with columns: CIK, Company Name, Form Type, Date Filed, Filename.
    """
    url = quarterly_master_url(year, qtr)
    print(f"Downloading {url} ...")
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    text = r.text

    lines = text.splitlines()
    header_seen = False
    records = []

    for line in lines:
        # find the header "CIK|Company Name|Form Type|Date Filed|Filename"
        if not header_seen:
            if line.startswith("CIK|"):
                header_seen = True
            continue

        if "|" not in line:
            continue

        parts = line.split("|")
        if len(parts) != 5:
            continue  # skip malformed lines

        cik, name, form_type, filed, filename = parts
        records.append(
            {
                "CIK": cik,
                "Company Name": name,
                "Form Type": form_type,
                "Date Filed": filed,
                "Filename": filename,
            }
        )

    df = pd.DataFrame(records)
    return df

def save_master_as_excel(year: int, qtr: int, out_dir: Path | str = ".") -> Path:
    df = load_master_to_dataframe(year, qtr)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"master_{year}_QTR{qtr}.xlsx"
    df.to_excel(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    return out_path

if __name__ == "__main__":
    for j in range(2005, 2026):
        for i in range(1, 5):
            save_master_as_excel(j, i, out_dir="master_excels")
