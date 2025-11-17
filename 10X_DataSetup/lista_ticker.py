from pathlib import Path
import csv

path = Path("ticker_list.csv")
fieldnames = ["ticker"]
out_path = Path("ticker_list.csv")


with path.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    tickers = [row["ticker"].strip() for row in reader if row.get("ticker") and row["ticker"].strip()]

print(tickers)  # e.g. ['AAPL', 'MSFT', ...]



'''
tickers = [p.name for p in folders_path.iterdir()]
ticker_list = [{"ticker": t} for t in tickers]
print(ticker_list)


with out_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(ticker_list)
'''