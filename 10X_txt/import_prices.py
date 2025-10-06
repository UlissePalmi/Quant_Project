import yfinance as yf
import csv
from pathlib import Path


filepath = Path("data.csv")

with filepath.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)  # uses first row as headers
    for row in reader:
        first = row.get(reader.fieldnames[0], "")
        second = row.get(reader.fieldnames[1], "")
        print(first, second) 



#open csv and for each line do:

# get ticker and final date in a list
# 
# based on date assume the stock has been bought at the begining of the next month and held for 6 months
# 
# what is the return
#  


# write a new csv file with old data plus return
apple = yf.Ticker("AAPL")