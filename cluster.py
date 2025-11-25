import DataSetup_10X.sec_download_html as sd
import DataSetup_10X.fx_10X_cleaner as fc
from pathlib import Path


# ---------- SETTINGS ----------
EXCEL_FILE = Path("master_all_prova.xlsx")      # your merged Excel
FORM       = "10-K"                             # or "10-K", "10-KT", etc.
LIMIT      = 20                                 # filings per CIK, 20 years go back (2006 - 2025)
SAVE_DIR   = Path("data/html")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
MAX_WORKERS = 5                                 # number of threads
# -------------------------------



ciks = sd.load_unique_ciks()
sd.lista(ciks)

