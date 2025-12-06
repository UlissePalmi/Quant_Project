from pathlib import Path
import fx_splitter_10X as fs
from concurrent.futures import ProcessPoolExecutor

def try_exercize(p):
    filepath = p / "clean-full-submission.txt"
    try:
        fs.version2(filepath, p)
    except:
        print("failed")
    return

if __name__ == "__main__":
    ticker = "0000008177"
    filings = "0001140361-13-014090"
    tickerlist = Path("data") / "html" / "sec-edgar-filings"

    letter = input("Select List (L) or Enter Ticker (T)...").lower()
    while letter != 'l' and letter != 't':
        letter = input("Invalid... enter L or T...").lower()

    if letter == 'l':
        paths = []
        for s in tickerlist.iterdir():
            if s.is_dir():
                ticker = s.name
                folders_path = tickerlist / ticker / "10-K"
                print(ticker)
                for p in folders_path.iterdir():
                    if p.is_dir():
                        paths.append(p)

        # process all filings in parallel
        with ProcessPoolExecutor(max_workers=3) as executor:
            list(executor.map(try_exercize, paths))
    else:
        p = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings
        try_exercize(p)