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
    return info_dict

def order_filings(records):
    records_sorted = sorted(
        records,
        key=lambda r: (int(r["year"]), int(r["month"]), int(r["day"])),
        reverse=True,
    )
    return [r["filing"] for r in records_sorted]

def make_comps(ordered_filings, date_data):
    comps_list = []
    n1 = 0
    n2 = 1
    while n2 != len(ordered_filings):
        for line in date_data:
            if line["filing"] == ordered_filings[n1]:
                date1 = line["year"] + "-" + line["month"] + "-" + line["day"]
            if line["filing"] == ordered_filings[n2]:
                date2 = line["year"] + "-" + line["month"] + "-" + line["day"]
        comps = {
            "date1": date1,
            "filing1": ordered_filings[n1],
            "date2": date2,
            "filing2": ordered_filings[n2]
        }
        comps_list.append(comps)
        n1 = n1 + 1
        n2 = n2 + 1
    return comps_list

def prepare_data(ticker):
    date_data = []
    folders_path = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K"
    for i in folders_path.iterdir():
        if (Path(i) / "item1A.txt").is_file():
            filing = i.name
            date_data.append(check_date(i, filing))
    ordered_filings = order_filings(date_data)
    comps_list = make_comps(ordered_filings, date_data)                                 # List of dictionary
    return comps_list