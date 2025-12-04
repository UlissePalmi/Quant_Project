from pathlib import Path
import fx_cluster as fc
from concurrent.futures import ProcessPoolExecutor
import Splitter_10X.fx_splitter_10X as sp
import Similarity_10X.fx_similarity as si
from itertools import repeat
import shutil
import csv

# Lines that change: 12, 15, 57
# ---------- SETTINGS ----------
EXCEL_FILE = Path("master_files") / "master_1.xlsx"                         # your merged Excel
FORM       = "10-K"                                                         # or "10-K", "10-KT", etc.
LIMIT      = 20                                                             # filings per CIK, 20 years go back (2006 - 2025)
SAVE_DIR   = Path("data1/html")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS = 6
MAX_WORKERS2 = 24                                                           # number of threads
# -------------------------------

# folder.file inside files with functions
if __name__ == "__main__":
    ciks = fc.load_unique_ciks(EXCEL_FILE)
    fc.lista(ciks, MAX_WORKERS, SAVE_DIR)

    checker_path = SAVE_DIR / "sec-edgar-filings"
    for ticker_folder in checker_path.iterdir():
        if not ticker_folder.is_dir():
            continue
        if not any(ticker_folder.rglob('*.txt')):
            try:
                shutil.rmtree(ticker_folder)
            except Exception as e:
                print(f"Error deleting {ticker_folder.name}: {e}")


    # Splitting
    ciklist = SAVE_DIR / "sec-edgar-filings"
    paths = []
    for s in ciklist.iterdir():
        if s.is_dir():
            cik = s.name
            folders_path = ciklist / cik / "10-K"
            print(cik)
            for p in folders_path.iterdir():
                if p.is_dir():
                    paths.append(p)

    # process all filings in parallel
    with ProcessPoolExecutor() as executor:
        list(executor.map(sp.try_exercize, paths))

    #Similarity
    t_folders_path = SAVE_DIR / "sec-edgar-filings"
    tickers = [p.name for p in t_folders_path.iterdir()]
    fieldnames = ["ticker", "date_a", "date_b", "distance", "similarity", "len_a", "len_b", "sentiment"]
    with open("similarity_data1.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        with ProcessPoolExecutor(MAX_WORKERS2) as executor:
            results_iterator = executor.map(si.concurrency_runner, tickers, repeat(SAVE_DIR))

        print(results_iterator)

        for rows in results_iterator:
            if rows:
                writer.writerows(rows)
