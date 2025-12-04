import DataSetup_10X.sec_download_html as sd
from pathlib import Path
import fx_cluster as fc
from concurrent.futures import ProcessPoolExecutor
import Splitter_10X.fx_splitter_10X as sp
import Similarity_10X.fx_similarity as si
from itertools import repeat
import csv


# ---------- SETTINGS ----------
EXCEL_FILE = Path("master_files") / "master_3.xlsx"                         # your merged Excel
FORM       = "10-K"                                                         # or "10-K", "10-KT", etc.
LIMIT      = 20                                                             # filings per CIK, 20 years go back (2006 - 2025)
SAVE_DIR   = Path("data3/html")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS = 4
MAX_WORKERS2 = 16                                                             # number of threads
# -------------------------------

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


# folder.file inside files with functions
if __name__ == "__main__":
    '''
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
    '''

    #Similarity
    t_folders_path = SAVE_DIR / "sec-edgar-filings"
    tickers = [p.name for p in t_folders_path.iterdir()]
    fieldnames = ["ticker", "date_a", "date_b", "distance", "similarity", "len_a", "len_b", "sentiment"]
    with open("similarity_data3.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        with ProcessPoolExecutor(MAX_WORKERS2) as executor:
            results_iterator = executor.map(concurrency_runner, tickers, repeat(SAVE_DIR))

        print(results_iterator)

        for rows in results_iterator:
            if rows:
                writer.writerows(rows)
