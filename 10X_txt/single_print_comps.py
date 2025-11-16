from pathlib import Path
import make_comps as mc
import minimum_edit_distance as med
import csv


ticker = "ADBE"

ordered_data = mc.prepare_data(ticker)


print(ordered_data)

model = []
for comps in ordered_data:
    filings = comps["filing1"]
    filings2 = comps["filing2"]
    file = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings / "item1A.txt"
    file2 = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings2 / "item1A.txt"
    text = file.read_text(encoding="utf-8", errors="ignore")
    text2 = file2.read_text(encoding="utf-8", errors="ignore")
    model.append(med.min_edit_similarity(text, text2, comps, ticker))


print(model)

fieldnames = model[0].keys()
with open("similarity_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(model)