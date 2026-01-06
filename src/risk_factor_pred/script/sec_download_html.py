from pathlib import Path
from risk_factor_pred.core import secDownloader as sd

# ---------- SETTINGS ----------
EXCEL_FILE = Path("data/tables") / "master_all_prova.xlsx"          # your merged Excel
FORM       = "10-K"                                                 # or "10-K", "10-KT", etc.
START_DATE = "2006-01-01"                                           # filings per CIK, only released after 2006
SAVE_DIR   = Path("data/html")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS = 4                                                     # number of threads
# -------------------------------

if __name__ == "__main__":

    letter = input("Select List (L) or Enter Ticker (T)...").lower()
    while letter != 'l' and letter != 't':
        letter = input("Invalid... enter L or T...").lower()

    if letter == 'l':
        ciks = sd.load_unique_ciks(EXCEL_FILE)
    else:
        ciks = [input("Enter ticker...").upper()]

    sd.lista(ciks, SAVE_DIR, START_DATE, FORM, MAX_WORKERS)