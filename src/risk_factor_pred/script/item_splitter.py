from pathlib import Path
from risk_factor_pred.core import fx_splitter_10X as fs, secDownloader as sd
from concurrent.futures import ProcessPoolExecutor

def try_exercize(p):
    filepath = p / "full-submission.txt"
    try:
        fs.version2(filepath, p)
    except:
        print("failed")
    return

if __name__ == "__main__":
    ticker = "0000010329"
    filings = "0001437749-18-000767"

    tickerlist = Path("data") / "html" / "sec-edgar-filings"

    if sd.inputLetter() == 'l':
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