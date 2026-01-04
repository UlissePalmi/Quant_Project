import pandas as pd
from pathlib import Path

# === SETTINGS ===
FILE_PATH = Path("master_all.xlsx")  # your merged Excel file
CIK_COLUMN = "CIK"
# =================


def main():
    if not FILE_PATH.exists():
        raise FileNotFoundError(f"Cannot find Excel file at: {FILE_PATH.resolve()}")

    df = pd.read_excel(FILE_PATH)

    if CIK_COLUMN not in df.columns:
        raise KeyError(f"Column '{CIK_COLUMN}' not found in {FILE_PATH.name}")

    original_rows = len(df)

    # Keep only the first row of each consecutive block of equal CIKs
    mask = df[CIK_COLUMN].astype(str).shift() != df[CIK_COLUMN].astype(str)
    df_dedup = df[mask]

    # Overwrite the same file
    df_dedup.to_excel(FILE_PATH, index=False)

    print(f"Deduped consecutive CIKs in {FILE_PATH.name}")
    print(f"Rows before: {original_rows}, rows after: {len(df_dedup)}")


if __name__ == "__main__":
    main()
