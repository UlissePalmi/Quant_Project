import os
from pathlib import Path
import fx_10X_cleaner as fc
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor

output_filename = "clean-full-submission.txt"

def cleaner(ticker, output_filename):
    folders_path = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K"
    for p in folders_path.iterdir():
        print(p)
        full_path = os.path.join(p, output_filename)
        html_content = os.path.join(p,"full-submission.txt")
        html_content = fc.print_clean_txt(html_content)
        fc.print_10X(full_path, html_content, output_filename)
    return

def worker(s, output_filename):
    print(s)
    if s.is_dir():
        ticker = s.name
        cleaner(ticker, output_filename)
    return

def clean_tickers(output_filename):
    tickerlist = Path("data") / "html" / "sec-edgar-filings"
    paths = [s for s in tickerlist.iterdir()]
    with ProcessPoolExecutor() as executor:
        list(executor.map(worker, paths, repeat(output_filename)))
    return

if __name__ == "__main__":
    letter = input("Clean List of Tickers (L) or Clean Single Ticker (T)...").lower()
    while letter != 'l' and letter != 't':
        letter = input("Invalid... Enter 'L' or 'T'...").lower()

    if letter == 'l':
        clean_tickers(output_filename)
    else:
        ticker = input("Enter Ticker to Clean: ").upper()
        cleaner(ticker, output_filename)