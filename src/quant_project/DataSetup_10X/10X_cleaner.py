import os
from pathlib import Path
import fx_10X_cleaner as fc
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor

output_filename = "clean-full-submission.txt"

def worker(s, output_filename):
    print(s)
    if s.is_dir():
        ticker = s.name
        fc.cleaner(ticker, output_filename)
    return

def clean_tickers(output_filename):
    tickerlist = Path("data") / "html" / "sec-edgar-filings"
    paths = [s for s in tickerlist.iterdir()]
    with ProcessPoolExecutor() as executor:
        list(executor.map(worker, paths, repeat(output_filename)))
    return

if __name__ == "__main__":
    letter = input("Clean List of Tickers (L), Clean Single Ticker (T) or only delete extra (D)...").lower()
    while letter != 'l' and letter != 't' and  letter != 'd':
        letter = input("Invalid... Enter 'L' or 'T'...").lower()

    if letter == 'l':
        clean_tickers(output_filename)
    elif letter == 't':
        ticker = input("Enter Ticker to Clean: ").upper()
        fc.cleaner(ticker, output_filename)
    fc.delete_folders_pre2006("data", cutoff_year=2006)
    fc.delete_full_submission_files("data")
