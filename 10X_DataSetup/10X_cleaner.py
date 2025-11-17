import os
from pathlib import Path
import sec_txt_cleaning_def as cr

output_filename = "clean-full-submission.txt"

def clean_tickers():
    tickerlist = Path("data") / "html" / "sec-edgar-filings"
    for s in tickerlist.iterdir():
        print(s)
        if s.is_dir():
            ticker = s.name
            folders_path = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K"
            print(ticker)
            for p in folders_path.iterdir():
                print(p)
                full_path = os.path.join(p, output_filename)
                html_content = os.path.join(p,"full-submission.txt")
                html_content = cr.print_clean_txt(html_content)
                cr.print_10X(full_path, html_content, output_filename)

def clean_single_ticker():
    ticker = input("Enter Ticker to Clean: ").upper()
    folders_path = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K"
    for p in folders_path.iterdir():
        print(p)
        full_path = os.path.join(p, output_filename)
        html_content = os.path.join(p,"full-submission.txt")
        html_content = cr.print_clean_txt(html_content)
        cr.print_10X(full_path, html_content, output_filename)

letter = input("Clean List of Tickers (L) or Clean Single Ticker (T)...").lower()
while letter != 'l' and letter != 't':
    letter = input("Invalid... Enter 'L' or 'T'...").lower()

if letter == 'l':
    clean_tickers()
else:
    clean_single_ticker()
