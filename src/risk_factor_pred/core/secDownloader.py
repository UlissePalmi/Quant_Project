from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import pandas as pd
from risk_factor_pred.core import htmlCleaner
from sec_edgar_downloader import Downloader
from pathlib import Path

def load_unique_ciks(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
    ciks = df["CIK"].astype(str).str.strip()
    return ciks.tolist()

def download_for_cik(cik: str, SAVE_DIR, StartDate, FORM):
    # tiny delay so we don't hammer SEC (can tune this)
    time.sleep(0.1)
    dl = Downloader("MyCompanyName", "my.email@domain.com", str(SAVE_DIR))
    print(f"Starting {FORM} for CIK {cik}")
    try:
        dl.get(FORM, cik, after=StartDate)
        time.sleep(10)
        return cik, "ok", None
    except ValueError as e:
        return cik, "not_found", str(e)
    except Exception as e:
        return cik, "error", str(e)

def download_n_clean(cik, SAVE_DIR, StartDate, FORM):
    tuple = download_for_cik(cik, SAVE_DIR, StartDate, FORM)
    padded_cik = str(cik.zfill(10))
    htmlCleaner.cleaner(padded_cik, output_filename = "full-submission.txt")
    return tuple

def lista(ciks, SAVE_DIR, StartDate, FORM, MAX_WORKERS):

    total = len(ciks)
    print(f"Found {total} unique CIKs")

    not_found = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_n_clean, cik=cik, save_dir=SAVE_DIR, start_date=StartDate, form=FORM): cik for cik in ciks}

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
