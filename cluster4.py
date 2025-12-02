import DataSetup_10X.sec_download_html as sd
from pathlib import Path
import fx_cluster as fc
from concurrent.futures import ProcessPoolExecutor
import Splitter_10X.fx_splitter_10X as sp
import Similarity_10X.fx_similarity as si
import csv


# ---------- SETTINGS ----------
EXCEL_FILE = Path("master_files") / "master_4.xlsx"                         # your merged Excel
FORM       = "10-K"                                                         # or "10-K", "10-KT", etc.
LIMIT      = 20                                                             # filings per CIK, 20 years go back (2006 - 2025)
SAVE_DIR   = Path("data4/html")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS = 4                                                             # number of threads
# -------------------------------



# folder.file inside files with functions
if __name__ == "__main__":
    ciks = fc.load_unique_ciks(EXCEL_FILE)
    fc.lista(ciks, MAX_WORKERS, SAVE_DIR)


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
    with open("similarity_data.csv4", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for ticker in tickers:
            si.concurrency_runner(writer, ticker, SAVE_DIR)
