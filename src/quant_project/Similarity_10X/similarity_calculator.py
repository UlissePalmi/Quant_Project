from pathlib import Path
import csv
import fx_similarity as sf


SAVE_DIR = Path("data") / "html"
folders_path = SAVE_DIR / "sec-edgar-filings"

if __name__ == "__main__":

    t_folders_path = Path("data") / "html" / "sec-edgar-filings"
    tickers = [p.name for p in t_folders_path.iterdir()]
    
    letter = input("Select List (L) or Enter Ticker (T)...").lower()
    while letter != 'l' and letter != 't':
        letter = input("Invalid... enter L or T...").lower()

    fieldnames = ["ticker", "date_a", "date_b", "distance", "similarity", "len_a", "len_b", "sentiment"]
    with open("similarity_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        if letter == 't':
            tickers = input("Enter ticker...").upper()
            tickers = [tickers]
        
        for ticker in tickers:
            sf.concurrency_runner(writer, ticker, SAVE_DIR)