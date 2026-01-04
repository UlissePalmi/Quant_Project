import pandas as pd
from pathlib import Path

# === SETTINGS ===
FILE_PATH = Path("master_excels") # <- put your real path here
FORM_COLUMN = "Form Type"
# =================

KEEP_FORMS = ["10-K", "10KSB", "10-KT"]

if __name__ == "__main__":
    for i in FILE_PATH.iterdir():
        df = pd.read_excel(i)

        # Keep only rows where Form Type is exactly one of the forms above
        mask = df[FORM_COLUMN].astype(str).isin(KEEP_FORMS)
        df_filtered = df[mask]

        df_filtered.to_excel(i, index=False)

        print(f"Cleaned {i.name}")
        print(f"Kept {len(df_filtered)} rows out of {len(df)}")

