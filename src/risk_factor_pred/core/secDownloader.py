from concurrent.futures import ThreadPoolExecutor, as_completed
from risk_factor_pred.consts import FORM, START_DATE, MAX_WORKERS, HTML_DIR, CIK_LIST
import time
import pandas as pd
from . import htmlCleaner
from sec_edgar_downloader import Downloader

def load_unique_ciks():
    df = pd.read_excel(CIK_LIST)
    ciks = df["CIK"].astype(str).str.strip()
    return ciks.tolist()

def download_for_cik(cik: str):
    # tiny delay so we don't hammer SEC (can tune this)
    time.sleep(0.1)
    dl = Downloader("MyCompanyName", "my.email@domain.com", str(HTML_DIR))
    print(f"Starting {FORM} for CIK {cik}")
    try:
        dl.get(FORM, cik, after=START_DATE)
        time.sleep(10)
        return cik, "ok", None
    except ValueError as e:
        return cik, "not_found", str(e)
    except Exception as e:
        return cik, "error", str(e)

def workerTasks(cik):
    tuple = download_for_cik(cik) 
    htmlCleaner.cleaner(str(cik.zfill(10)), output_filename = "full-submission.txt")
    return tuple

def download_n_clean(ciks):
    total = len(ciks)
    print(f"Found {total} unique CIKs")

    not_found = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(workerTasks, cik=cik): cik for cik in ciks}

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

def inputLetter():
    letter = input("Select List (L) or Enter Ticker (T)...").lower()
    while letter != 'l' and letter != 't':
        letter = input("Invalid... enter L or T...").lower()
    return letter
