from pathlib import Path
import csv
from risk_factor_pred.core import fx_similarity as sf, secDownloader as sd


folder_dir = Path("data") / "html"
folders_path = folder_dir / "sec-edgar-filings"
SAVE_DIR = Path("data") / "tables" / "similarity.csv"
t_folders_path = Path("data") / "html" / "sec-edgar-filings"

if __name__ == "__main__":

    # Create list of ciks from excel file or request cik in input
    ciks = [p.name for p in t_folders_path.iterdir()] if sd.inputLetter() == 'l' else [input("Enter ticker...").upper()]
    
    fieldnames = ["ticker", "date_a", "date_b", "distance", "similarity", "len_a", "len_b", "sentiment"]
    with open(SAVE_DIR, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for cik in ciks:
            sf.concurrency_runner(writer, cik, folder_dir)