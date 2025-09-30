from pathlib import Path
from typing import List, Dict, Tuple, Optional
from itertools import islice
import re

ticker = "ADBE"
filings = "0000796343-09-000007"
folderpath = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings
filepath = folderpath / "clean-full-submission.txt"
TOKENS = ("ITEM")

items_list = ["1", "1A", "1B", "1C", "2", "3", "4", "5", "6", "7", "7A", "8"]

def _normalize_ws(s: str) -> str:
    s = s.replace("\xa0", " ").replace("\u2007", " ").replace("\u202f", " ")
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def before_dot(s: str) -> str:
    """Return everything before the first '.'; if no dot, return the string unchanged."""
    i = s.find('.')
    return s[:i] if i != -1 else s

def extract_index_lines(p):                                                                                     #  Filepath -> List[Dict] {'line_no': x, 'kind': 'y', 'text': 'z'}
    text = p.read_text(encoding="utf-8", errors="ignore")
    out = []
    HEAD_RE = re.compile(r'^\s*(?P<kind>item)\b(?P<rest>.*)$', re.IGNORECASE)    # regex to find lines to split

    for i, raw in enumerate(text.splitlines(), start=1):
        line = _normalize_ws(raw)
        if not line:
            continue

        m = HEAD_RE.match(line)
        if not m:
            continue

        label = m.group('kind') + m.group('rest')
        label = _normalize_ws(label)
        out.append({
            'line_no': i,
            'kind': m.group('kind').capitalize(),
            'text': label,
        })

    # dedupe consecutive duplicates
    deduped = []
    last = None
    for row in out:
        key = (row['kind'], row['text'].lower())
        if key != last:
            deduped.append(row)
        last = key
    return deduped

def table_content_starter(item_list):
    i = 0
    
    for n, item in enumerate(item_list):
        if item['item_n'] == "1":
            i = i + 1
        if i == 2:
            table_of_content = item_list[:n]
            rest = item_list[n:]
            return table_of_content, rest

def table_content_finisher(table_content):
    table_content_list = []                                                                         # Create table of content
    for i in table_content:
        table_content_list.append(i.get("item_n"))

    # Merge the table of contents
    items_list.extend(table_content_list[table_content_list.index(items_list[-1])+1:])
    return items_list

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
        #print(list_lines)
        new_rest_list = []
        for l in rest_list:
            if l['line_no'] > last_ele:
                new_rest_list.append(l)
        rest_list = new_rest_list
    return list_lines

def get_items_dict(main_lines):
    item_list = [i for i in main_lines if i.get("kind") == "Item"]
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

def print_items(filepath, final_split):
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

def complete_split(filepath):
    p = Path(filepath)                                                                              
    main_lines = extract_index_lines(p)                                                             # Extracts main lines  

    item_dict = get_items_dict(main_lines)                                                          # Makes list of dictionary with all items

    table_content, rest_list = table_content_starter(item_dict)                                     # Splits in 2 lists of dictionaries: table of content and body

    table_content_list = table_content_finisher(table_content)                                      # Creates a list with all the number of items

    return table_content_list, rest_list


table_content_list, rest_list = complete_split(filepath)

list_lines = create_index(table_content_list, rest_list)    # Creates first list

final_split = final_list(list_lines)

print_items(filepath, final_split)
