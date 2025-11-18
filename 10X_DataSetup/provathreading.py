import pandas as pd
from pathlib import Path
from sec_edgar_downloader import Downloader   # or sec_edgar_downloader if that's the one you installed

# ---------- SETTINGS ----------
EXCEL_FILE = Path("master_all_prova.xlsx")  # your Excel with a CIK column
CIK_COLUMN = "CIK"                          # column name in Excel
SAVE_DIR   = Path("data/html")              # where you want the filings saved
FORM       = "10-K"                         # what to download
LIMIT      = 40                             # how many filings per CIK (or whatever you want)
# -------------------------------


if __name__ == "__main__":
    df = pd.read_excel(EXCEL_FILE)

    ciks = ( df[CIK_COLUMN] .astype(str) .str.strip() .str.zfill(10) .unique() )

    print(f"Found {len(ciks)} unique CIKs")

    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    dl = Downloader("MyCompanyName", "my.email@domain.com", "data/html")

    not_found = []

    for i, cik in enumerate(ciks, start=1):
        try:
            print(f"[{i}/{len(ciks)}] Downloading {FORM} for CIK {cik}...")
            dl.get(FORM, cik, limit=LIMIT)   # <- key line
        except ValueError:
            print(f"  !! CIK {cik} not found")
            not_found.append(cik)
        else:
            print(f"  ✓ Done for {cik}")

    if not_found:
        print("\nCIKs not found:")
        for cik in not_found:
            print(" ", cik)
