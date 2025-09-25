import csv
import os
from pathlib import Path
import sec_txt_cleaning as cr
from sec_edgar_downloader import Downloader

ticker = "AAPL"
output_filename = "clean-full-submission.txt"

folders_path = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K"


for p in folders_path.iterdir():
    print(p)
    full_path = os.path.join(p, output_filename)
    html_content = os.path.join(p,"full-submission.txt")
    html_content = cr.print_clean_txt(html_content)
    cr.print_10X(full_path, html_content, output_filename)
    
