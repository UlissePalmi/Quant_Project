import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
#import fx_10X_cleaner as fc
import DataSetup_10X.fx_10X_cleaner as fc

from sec_edgar_downloader import Downloader

# ---------- SETTINGS ----------
EXCEL_FILE = Path("master_all_prova.xlsx")      # your merged Excel
FORM       = "10-K"                             # or "10-K", "10-KT", etc.
LIMIT      = 20                                 # filings per CIK, 20 years go back (2006 - 2025)
SAVE_DIR   = Path("data/html")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS = 4                                 # number of threads
# -------------------------------


def load_unique_ciks():
    df = pd.read_excel(EXCEL_FILE)
    ciks = df["CIK"].astype(str).str.strip()
    return ciks.tolist()


def download_for_cik(cik: str):
    # tiny delay so we don't hammer SEC (can tune this)
    time.sleep(0.1)
    dl = Downloader("MyCompanyName", "my.email@domain.com", str(SAVE_DIR))

    thread_name = threading.current_thread().name
    print(f"[{thread_name}] Starting {FORM} for CIK {cik}")

    try:
        dl.get(FORM, cik, limit=LIMIT)
        time.sleep(10)
        padded_cik = str(cik.zfill(10))
        print(padded_cik)
        fc.delete_cik_pre2006(cutoff_year=2006, cik=padded_cik)
        fc.cleaner(padded_cik, output_filename = "clean-full-submission.txt")
        fc.del_full_submission_files(padded_cik)
        return cik, "ok", None
    except ValueError as e:
        return cik, "not_found", str(e)
    except Exception as e:
        return cik, "error", str(e)

def lista(ciks):

    total = len(ciks)
    print(f"Found {total} unique CIKs")

    not_found = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_for_cik, cik): cik for cik in ciks}

        # as_completed lets them run in parallel; we consume results as they finish
        for idx, future in enumerate(as_completed(futures), start=1):
            cik, status, err = future.result()
            print(f"[{idx}/{total}] CIK {cik}: {status}")
            if status == "not_found":
                not_found.append(cik)
            elif status == "error":
                errors.append((cik, err))

    if not_found:
        print("\nCIKs not found:")
        for cik in not_found:
            print(" ", cik)

    if errors:
        print("\nCIKs with errors:")
        for cik, err in errors:
            print(f" {cik}: {err}")
    
    return

if __name__ == "__main__":

    letter = input("Select List (L) or Enter Ticker (T)...").lower()
    while letter != 'l' and letter != 't':
        letter = input("Invalid... enter L or T...").lower()

    if letter == 'l':
        ciks = load_unique_ciks()
    else:
        ciks = [input("Enter ticker...").upper()]

    lista(ciks)

