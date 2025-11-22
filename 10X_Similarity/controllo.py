import pandas as pd
from pathlib import Path
import re

'''
df_Dataset = pd.read_csv("similarity_data.csv")
ciks = df_Dataset['ticker'].unique()
ciks = [f"{n:010d}" for n in ciks]
list_of_dict = []

for cik in ciks:
    ticker_df = df_Dataset[df_Dataset['ticker']==cik]['date_a']
    cik_list = ticker_df.astype(str).str[-4:].tolist()
    list = []
    for i in range(2006, 2026):
        if not str(i) in cik_list:
            list.append(i)
    if list:
        t_dict = {cik: list}
        list_of_dict.append(t_dict)
print(list_of_dict)
'''

df = pd.DataFrame(columns=['cik', 'year'])



similarity_df = pd.read_csv('similarity_data.csv')
similarity_df['ticker'] = similarity_df['ticker'].astype(int).map(lambda n: f"{n:010d}")

pattern = re.compile(r"^\d{10}-(\d{2})-\d{6}$")
    

root = Path("data") / "html" / "sec-edgar-filings"
for path in root.iterdir():
    cik_df = similarity_df[similarity_df['ticker'] == path.name]
    folder = path / "10-K"
    for p in folder.iterdir():
        m = pattern.match(p.name)
        yy = int(m.group(1))
        year = 1900 + yy if yy >= 70 else 2000 + yy
        row = [path.name, year]
        df.loc[len(df)] = row   # all possible

print(df.head(15))
#    folder = path / "10-K"
#    for 
