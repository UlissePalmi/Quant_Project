import pandas as pd
from pathlib import Path
import re

df = pd.DataFrame(columns=['cik', 'year'])

similarity_df = pd.read_csv('similarity_data.csv')
similarity_df['ticker'] = similarity_df['ticker'].astype(int).map(lambda n: f"{n:010d}")

pattern = re.compile(r"^\d{10}-(\d{2})-\d{6}$")

def find_year(pname):
    m = pattern.match(pname)
    yy = int(m.group(1))
    year = 1900 + yy if yy >= 70 else 2000 + yy
    return year

root = Path("data") / "html" / "sec-edgar-filings"

for path in root.iterdir():
    folder = path / "10-K"
    cik_df = similarity_df[similarity_df['ticker'] == path.name]
    if cik_df.empty:
        #print(f"No rows found for ticker {path.name}")
        years = [find_year(p.name) for p in folder.iterdir()]
    
    else:
        a = cik_df["date_a"].tolist()
        a.append(cik_df["date_b"].iloc[-1])
        a = [i[:4] for i in a]
        
        # p.name is the ticker
        years = [str(find_year(p.name)) for p in folder.iterdir() if not str(find_year(p.name)) in a]
        
    rows = [[path.name, year] for year in years]
    for row in rows:
        df.loc[len(df)] = row

print(df)

df.to_csv("missing.csv")