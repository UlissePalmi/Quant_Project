from pathlib import Path
from risk_factor_pred.consts import FORM, START_DATE, MAX_WORKERS, HTML_DIR, CIK_LIST
from risk_factor_pred.core import secDownloader as sd

# ---------- SETTINGS ----------
HTML_DIR.mkdir(parents=True, exist_ok=True)
# -------------------------------

if __name__ == "__main__":
    # Create list of ciks from excel file or request cik in input
    ciks = sd.load_unique_ciks(CIK_LIST) if sd.inputLetter() == 'l' else [input("Enter CIK...").upper()]
    
    # Download 10-K and Remove HTML tags given previously created list
    sd.lista(ciks, HTML_DIR, START_DATE, FORM, MAX_WORKERS)