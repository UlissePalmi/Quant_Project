from concurrent.futures import ThreadPoolExecutor, as_completed
import DataSetup_10X.fx_10X_cleaner as fc
import Similarity_10X.fx_similarity as fs
from sec_edgar_downloader import Downloader
from concurrent.futures import ProcessPoolExecutor
import Similarity_10X.fx_similarity as si
from itertools import repeat
from pathlib import Path
import pandas as pd
import threading
import shutil
import time
import re
import os

FORM       = "10-K"                             # or "10-K", "10-KT", etc.
LIMIT      = 20                                 # filings per CIK, 20 years go back (2006 - 2025)

def load_unique_ciks(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
    ciks = df["CIK"].astype(str).str.strip()
    return ciks.tolist()


def lista(ciks, MAX_WORKERS, SAVE_DIR):
    total = len(ciks)
    print(f"Found {total} unique CIKs")

    not_found = []
    errors = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_for_cik, cik, SAVE_DIR): cik for cik in ciks}

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

def download_for_cik(cik, SAVE_DIR):
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
        delete_cik_pre2006(padded_cik, SAVE_DIR, cutoff_year=2006)
        cleaner(padded_cik, SAVE_DIR, output_filename = "clean-full-submission.txt")
        del_full_submission_files(padded_cik, SAVE_DIR)
        return cik, "ok", None
    except ValueError as e:
        return cik, "not_found", str(e)
    except Exception as e:
        return cik, "error", str(e)
    

# --------------------------------------------------------------------------------------------------------------------
#                                                SPACE CLEANER
# --------------------------------------------------------------------------------------------------------------------


def delete_cik_pre2006(cik, SAVE_DIR, cutoff_year):
    pattern = re.compile(r"^\d{10}-(\d{2})-\d{6}$")
    folder = SAVE_DIR / "sec-edgar-filings" / cik / "10-K"
    print(folder)
    if not os.path.exists(folder):
        print("skipped pre 2006")
        return

    matches = []

    for p in folder.iterdir():
        m = pattern.match(p.name)
        yy = int(m.group(1))
        year = 1900 + yy if yy >= 70 else 2000 + yy
        if year < cutoff_year:
            matches.append(p)
            print(f"Deleting: {p} (year={year})")
            shutil.rmtree(p)

def cleaner(ticker, SAVE_DIR, output_filename):
    folders_path = SAVE_DIR / "sec-edgar-filings" / ticker / "10-K"
    for p in folders_path.iterdir():
        print(p)
        full_path = os.path.join(p, output_filename)
        html_content = os.path.join(p,"full-submission.txt")
        html_content = fc.print_clean_txt(html_content)                    # html removal
        html_content = fc.cleaning_items(html_content)
        fc.print_10X(full_path, html_content, output_filename)
    return

def del_full_submission_files(cik, SAVE_DIR):
    folder = SAVE_DIR / "sec-edgar-filings" / cik / "10-K"
    count = 0

    for path in folder.rglob("full-submission.txt"):
        count += 1
        print(f"Deleting: {path}")
        path.unlink()  # delete the file

    print(f"\nTotal {'deleted'}: {count}")
    return













def concurrency_runner(ticker, SAVE_DIR):
    try:
        ordered_data = si.prepare_data(ticker, SAVE_DIR)
        model = []
        for comp in ordered_data:
            model.append(si.process_comps(comp, ticker, SAVE_DIR))
        return model
    except:
        print("Skipped")

def prepare_data(ticker, SAVE_DIR):
    date_data = []
    folders_path = SAVE_DIR / "sec-edgar-filings" / ticker / "10-K"
    for i in folders_path.iterdir():
        if (Path(i) / "item1A.txt").is_file():
            filing = i.name
            date_data.append(si.check_date(i, filing))
    ordered_filings = si.order_filings(date_data)
    comps_list = si.make_comps(ordered_filings, date_data)                                 # List of dictionary
    return comps_list

def process_comps(comps, ticker, SAVE_DIR):
    filings = comps["filing1"]
    filings2 = comps["filing2"]
    file = SAVE_DIR / "sec-edgar-filings" / ticker / "10-K" / filings / "item1A.txt"
    file2 = SAVE_DIR / "sec-edgar-filings" / ticker / "10-K" / filings2 / "item1A.txt"
    text = file.read_text(encoding="utf-8", errors="ignore")
    text2 = file2.read_text(encoding="utf-8", errors="ignore")
    return si.min_edit_similarity(text, text2, comps, ticker)