from risk_factor_pred.core import fx_splitter_10X as fs, secDownloader as sd
from risk_factor_pred.consts import SEC_DIR, MAX_WORKERS
from concurrent.futures import ProcessPoolExecutor

if __name__ == "__main__":
    cik = "0000000020"
    filings = "0000893220-06-000650"

    if sd.inputLetter() == 'l':
        paths = []
        for cik in SEC_DIR.iterdir():
            if cik.is_dir():
                cik = cik.name
                folders_path = SEC_DIR / cik / "10-K"
                print(cik)
                for p in folders_path.iterdir():
                    if p.is_dir():
                        paths.append(p)

        # process all filings in parallel
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            list(executor.map(fs.try_exercize, paths))
        print(paths)
    else:
        p = SEC_DIR / cik / "10-K" / filings
        fs.try_exercize(p)