from pathlib import Path
from typing import List, Dict, Tuple, Optional
from itertools import islice
import re

ticker = "TSLA"
filings = "0000950170-22-000796"
folderpath = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings
filepath = folderpath / "clean-full-submission.txt"
TOKENS = ("PART", "ITEM", "CONSOLIDATED", "NOTES", "SIGNATURES", "EXHIBIT")

HEAD_RE = re.compile(r'^\s*(?P<kind>item|consolidated|notes|signatures|exhibit)\b(?P<rest>.*)$', re.IGNORECASE)    # regex to find lines to split
items_list = ["1", "1A", "1B", "1C", "2", "3", "4", "5", "6", "7", "7A", "8"]

def _normalize_ws(s: str) -> str:
    s = s.replace("\xa0", " ").replace("\u2007", " ").replace("\u202f", " ")
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def classify_row(e):
    k = _norm(e.get("kind"))
    t = _norm(e.get("text"))
    if k == "exhibit" or t.startswith("exhibit") or t.startswith("exhibits") or t.startswith("exibit"):         # EXHIBIT
        return "E"
    if k == "signatures" or t.startswith("signatures") or t.startswith("signitures"):                           # SIGNATURES
        return "S"
    if k == "item" or t.startswith("item"):                                                                     # ITEM
        return "I"
    if k == "part" or t.startswith("part"):                                                                     # PART
        return "P"
    if k == "consolidated" or t.startswith("consolidated"):                                                     # CONSOLIDATED
        return "C"
    if k == "notes" or t.startswith("notes"):                                                                   # NOTES
        return "N"
    return "O"

def take_leading_digits(s: str) -> str:
    m = re.match(r"\d+", s)
    return m.group(0) if m else ""

def before_dot(s: str) -> str:
    """Return everything before the first '.'; if no dot, return the string unchanged."""
    i = s.find('.')
    return s[:i] if i != -1 else s

def extract_index_lines(text: str) -> List[Dict]:
    """
    Return a list of dicts like:
      {'line_no': 123, 'kind': 'Item', 'text': 'Item 1A. Risk Factors'}
    Only lines that START with one of TOKENS are included.
    """
    out = []
    for i, raw in enumerate(text.splitlines(), start=1):
        line = _normalize_ws(raw)
        if not line:
            continue

        m = HEAD_RE.match(line)
        if not m:
            continue

        # Rebuild a nice label, trim dot leaders / page numbers at the end
        label = m.group('kind') + m.group('rest')
        label = _normalize_ws(label)
        out.append({
            'line_no': i,
            'kind': m.group('kind').capitalize(),
            'text': label,
        })

    # optional: dedupe consecutive duplicates (common in PDFs/TOCs)
    deduped = []
    last = None
    for row in out:
        key = (row['kind'], row['text'].lower())
        if key != last:
            deduped.append(row)
        last = key
    return deduped

def _norm(s: str) -> str:
    return (s or "").strip().lower()

def split_three_by_two_signatures(entries: List[Dict]) -> Tuple[bool, Tuple[List[Dict], List[Dict], List[Dict]], Tuple[Optional[int], Optional[int]]]:
    sig_idxs = [i for i, e in enumerate(entries) if classify_row(e)=="S"]

    if len(sig_idxs) != 2:
        return False, (entries, [], []), (None, None)

    idx1, idx2 = sig_idxs[0], sig_idxs[1]

    part1 = entries[: idx1 + 1]     # include first signatures
    part2 = entries[idx1 + 1 : idx2]  # between them
    part3 = entries[idx2 : ]        # include second signatures
    return True, (part1, part2, part3), (idx1, idx2)

def split_leading_exhibits(part2: List[Dict]) -> Tuple[List[Dict], List[Dict], int]:
    i, n = 0, len(part2)
    while i < n and classify_row(part2[i])=="E":
        i += 1
    return part2[:i], part2[i:], i

def create_index(table_content_list, rest_list):
    list_lines = []
    while any("1" in str(d.get("item_n")) for d in rest_list):
        lines = []
        last_ele = 0
        for t in table_content_list:
            for r in rest_list:
                if t == r.get('item_n') and r.get('line_no') > last_ele:
                    lines.append(r)
                    last_ele = r['line_no']
                    break
        list_lines.append(lines)
        new_rest_list = []
        for l in rest_list:
            if l['line_no'] > last_ele:
                new_rest_list.append(l)
        rest_list = new_rest_list
    return list_lines

# SONO qui, controlla numeri
def order_items(e):
    item_list = [i for i in e if i.get("kind") == "Item"]
    list = []
    for i in item_list:
        list.append({
            'item_n': before_dot(i.get("text").split()[1]),
            'line_no': i.get('line_no')
            })
    return list

def final_list(list_lines):
    diff = 0
    for i in range(len(list_lines)):
        n = list_lines[i][-1]['line_no'] - list_lines[i][1]['line_no']
        if n > diff:
            num = i
    return list_lines[num]


if __name__ == "__main__":
    p = Path(filepath)
    text = p.read_text(encoding="utf-8", errors="ignore")
    index = extract_index_lines(text)


    print(f"\ntable of content: ")
    for row in index:
        print(f"{row['line_no']:>6}  {row['kind']}  {row['text']}")


    ok, (table_content, part2, exhibits_list), (i1, i2) = split_three_by_two_signatures(index)

    if not ok:
        print("Expected exactly 2 SIGNATURES; found a different count.")
    else:
        exhibits_table_content, rest, i = split_leading_exhibits(part2)

        print(f"\ntable of content: ")
        for row in table_content:
            print(f"{row['line_no']:>6}  {row['kind']}  {row['text']}")

        table_content_list = []                                                         # Create table of content
        for i in order_items(table_content):
            table_content_list.append(f"{i['item_n']}")

        items_list.extend(table_content_list[table_content_list.index(items_list[-1])+1:])
        
        rest_list = order_items(rest)                                                   # Create body
        
        list_lines = create_index(items_list, rest_list)    # Creates first list
        
        final_split = final_list(list_lines)

        print(final_split)

        page_list = [i['line_no'] for i in final_split]
        page_list.append(11849)

        for n, i in enumerate(final_split):
            start, end = page_list[n], page_list[n+1]
            with filepath.open("r", encoding="utf-8", errors="replace") as f:
                lines = list(islice(f, start - 1, end-1))
            chunk = "".join(lines)
            filename = f"item{i['item_n']}.txt"
            full_path = folderpath / filename
            with open(full_path, "w", encoding='utf-8') as f:
                f.write(chunk)