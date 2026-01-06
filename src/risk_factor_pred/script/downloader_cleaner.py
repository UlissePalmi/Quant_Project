from pathlib import Path
from risk_factor_pred.core import secDownloader as sd

# ---------- SETTINGS ----------
EXCEL_FILE = Path("data/tables") / "master_all.xlsx"                # Excel containing list of CIKS
FORM       = "10-K"                                                 # or "10-K", "10-KT", etc.
START_DATE = "2006-01-01"                                           # filings per CIK, only released after 2006
SAVE_DIR   = Path("data/html")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS = 4                                                     # number of threads
# -------------------------------

if __name__ == "__main__":
    # Create list of ciks from excel file or request cik in input
    ciks = sd.load_unique_ciks(EXCEL_FILE) if sd.inputLetter() == 'l' else [input("Enter CIK...").upper()]
    
    # Download 10-K and Remove HTML tags given previously created list
    sd.lista(ciks, SAVE_DIR, START_DATE, FORM, MAX_WORKERS)