import pandas as pd
from pathlib import Path

FOLDER = Path("master_excels")          # folder with your per-quarter excels
OUTPUT_FILE = Path("master_all.xlsx")   # merged output file


if __name__ == "__main__":
    dfs = []

    for path in FOLDER.iterdir():
        print(f"Reading {path.name}...")
        df = pd.read_excel(path)

        # optional: keep track of which file each row came from
        df["Source_File"] = path.name

        dfs.append(df)

    if dfs:
        merged = pd.concat(dfs, ignore_index=True)

        merged.to_excel(OUTPUT_FILE, index=False)
        print(f"Merged {len(dfs)} files into {OUTPUT_FILE.resolve()}")
        print(f"Total rows: {len(merged)}")
