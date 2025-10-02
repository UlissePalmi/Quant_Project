from pathlib import Path
from typing import List, Dict, Tuple, Optional
from itertools import islice
import re
import time

ticker = "AFL"
filings = "0000004977-22-000058"
folderpath = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings
folders_path = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K"
filepath = folderpath / "clean-full-submission.txt"
tickerlist = Path("data") / "html" / "sec-edgar-filings"
TOKENS = ("ITEM")

def _normalize_ws(s: str) -> str:
    s = s.replace("\xa0", " ").replace("\u2007", " ").replace("\u202f", " ")
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def before_dot(s: str) -> str:
    """Return everything before the first '.'; if no dot, return the string unchanged."""
    i = s.find('.')
    return s[:i] if i != -1 else s

def extract_index_lines(p):                                                                                     # Filepath -> List[Dict] {'line_no': x, 'kind': 'y', 'text': 'z'}
    text = p.read_text(encoding="utf-8", errors="ignore")
    out = []
    HEAD_RE = re.compile(r'^\s*(?P<kind>item)\b(?P<rest>.*)$', re.IGNORECASE)                                   # Regex to find lines to split

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
    #print(deduped)
    return deduped

def digits_only_list(item_dict):
    out = []
    for items in item_dict:
        if not str(items.get('item_n', ''))[:1].isdigit():
            continue
        s = str(items.get("item_n"))
        digits = "".join(ch for ch in s if ch.isdigit() and ch)
        out.append(digits)
    out_num = [int(i) for i in out]
    #print(f"out_num: {out_num}")
    while max(out_num) > 20:
        out_num.remove(max(out_num))
        #print(out_num)
    max_num = max(out_num)
    out_num = [int(i) for i in out]
    
    #print(max_num)
    rounds = [i for i in out_num if i==max_num]
    rounds2 = [i for i in out_num if i==max_num-1]
    #print(rounds, rounds2)
    if rounds > rounds2:
        rounds = rounds2
    return out_num, len(rounds)

def table_content_builder(item_dict):
    i = 0
    out_num, n_rounds = digits_only_list(item_dict)
    items_list = ["1", "1A", "1B", "1C", "2", "3", "4", "5", "6", "7", "7A", "8"]
    #print(f"n_rounds: {n_rounds}")
    letters_tuple = ("","A","B","C")
    for n in range(int(items_list[-1])+1,max(out_num)+1):
        n = str(n)
        for l in letters_tuple:
            items_list.append(n + l)
    
    return items_list, item_dict

def make_item_loops(item_list, max_item, n_rounds, item_dict):
    list_lines = []
    #print(item_dict)
    #print(f"item_list: {item_list}")
    last_ele = 0
    boh = 0
    while boh != n_rounds:
        lines = []
        for t in item_list:
            for r in item_dict:
                if t == r.get('item_n') and r.get('line_no') > last_ele:
                    lines.append(r)
                    last_ele = r['line_no']
                    break
        boh = boh + 1
        #print(f"lines: {lines}")
        list_lines.append(lines)
    #print(list_lines)
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
    #print(len(list_lines))
    for i in range(len(list_lines)):
        n = list_lines[i][-1]['line_no'] - list_lines[i][1]['line_no']
        #print(n)
        if n > diff:
            num = i
            diff = n
    return list_lines[num]

def print_items(filepath, final_split, p):
    page_list = [i['line_no'] for i in final_split]
    page_list.append(11849)

    for n, i in enumerate(final_split):
        start, end = page_list[n], page_list[n+1]
        with filepath.open("r", encoding="utf-8", errors="replace") as f:
            lines = list(islice(f, start - 1, end-1))
        chunk = "".join(lines)
        filename = f"item{i['item_n']}.txt"

        full_path = p / filename
        #print(full_path)
        #folderpath
        with open(full_path, "w", encoding='utf-8') as f:
            f.write(chunk)
    print("okkkkk")

def version2(filepath, p):
    pat = Path(filepath)                                                                              
    main_lines = extract_index_lines(pat)                                                             # Extracts main lines 
    item_dict = get_items_dict(main_lines)
    out_num, n_rounds = digits_only_list(item_dict)

    item_list, rest_list = table_content_builder(item_dict)
    list_lines = make_item_loops(item_list, max(out_num), n_rounds, item_dict)
    final_split = final_list(list_lines)                                                        # Identifies the list of dict that covers the most lines (aka actual items)
    print_items(filepath, final_split, p)
    time.sleep(0.5)
    


for s in tickerlist.iterdir():
    #print(s)
    if s.is_dir():
        ticker = s.name
        folders_path = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K"
        print(ticker)
        for p in folders_path.iterdir():
            filepath = p / "clean-full-submission.txt"
            #print(p)
            try:
                version2(filepath, p)
            except:
                print("failed")





































'''
def complete_split(filepath):
    p = Path(filepath)                                                                              
    main_lines = extract_index_lines(p)                                                             # Extracts main lines 
    item_dict = get_items_dict(main_lines)                                                          # Makes list of dictionary with all items
    print(item_dict) 
    
    # Find highest number
    table_content_list, rest_list = table_content_builder(item_dict)
    
    rounds = digits_only_list(item_dict)
    input("Enter...")
    #table_content, rest_list = table_content_starter(item_dict)                                     # Splits in 2 lists of dictionaries: table of content and body
    #table_content_list = table_content_finisher(table_content)                                      # Creates a list with all the number of items
    list_lines = create_index(table_content_list, rest_list)                                        # Creates first list
    final_split = final_list(list_lines)                                                            # Identifies the list of dict that covers the most lines (aka actual items)

    return final_split
'''