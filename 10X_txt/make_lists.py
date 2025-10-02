from pathlib import Path

ticker = "ZTS"
folders_path = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K"




def check_date(folder, filing):
    file = folder / "clean-full-submission.txt"
    with open(file, "r", encoding="utf-8", errors="replace") as f:
        for n_line, line in enumerate(f, start = 1):
            hay = line.lower()
            if filing in hay:
                #print(hay)
                date = hay.partition(":")[2].lstrip()
                #print(date)
                break
    info_dict = {
        "year": date[:4],
        "month": date[4:6],
        "day": date[6:8],
        "filing": filing
    }
    date_data.append(info_dict)







date_data = []

for i in folders_path.iterdir():
    if (Path(i) / "item1A.txt").is_file():
        filing = i.name
        check_date(i, filing)



print(date_data)