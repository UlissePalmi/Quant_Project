from pathlib import Path
from typing import List, Dict, Tuple, Optional
from itertools import islice
import re
import time

def _normalize_ws(s: str) -> str:
    s = s.replace("\xa0", " ").replace("\u2007", " ").replace("\u202f", " ")
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def before_dot(s: str) -> str:
    """Return everything before the first '.'; if no dot, return the string unchanged."""
    i = s.find('.')
    return s[:i] if i != -1 else s

def item_dict_builder(p):                                                                                      # Filepath -> List[Dict] {'item_n': 'x', 'line_no': y}
    text = p.read_text(encoding="utf-8", errors="ignore")
    out = []
    HEAD_RE = re.compile(r'^\s*(?P<kind>items?)\b\s*(?P<rest>[0-9].*)$', re.IGNORECASE)                                # Regex to find lines to split

    for i, raw in enumerate(text.splitlines(), start=1):
        line = _normalize_ws(raw)
        if not line:
            continue
        m = HEAD_RE.match(line)
        if not m or not m.group('rest'):
            continue
        label = m.group('rest')

        out.append({
            'item_n': before_dot(_normalize_ws(label).split()[0]).upper(),
            'line_no': i,
        })

    # dedupe consecutive duplicates
    deduped = []
    last = None
    for row in out:
        key = row['item_n'].lower()
        if key != last:
            deduped.append(row)
        last = key
    return deduped

def digits_only_list(item_dict):
    out = []
    for items in item_dict:
        #print(str(items.get('item_n'))[:1])
        #if not str(items.get('item_n'))[:1].isdigit():
        #    continue
        #s = str(items.get("item_n"))
        digits = "".join(ch for ch in items.get("item_n") if ch.isdigit() and ch)
        out.append(digits)
    out_num = [int(i) for i in out]

    # sometimes "Item 400" exists
    while max(out_num) > 20:
        out_num.remove(max(out_num))
    
    max_num = max(out_num)
    out_num = [int(i) for i in out]
    rounds = [i for i in out_num if i==max_num]
    rounds2 = [i for i in out_num if i==max_num-1]
    if rounds > rounds2:
        rounds = rounds2
    return out_num, len(rounds)

def table_content_builder(item_dict):
    out_num, _ = digits_only_list(item_dict)
    items_list = ["1", "1A", "1B", "1C", "1D", "2", "3", "4", "5", "6", "7", "7A", "8"]
    letters_tuple = ("","A","B","C")
    for n in range(int(items_list[-1])+1,max(out_num)+1):
        n = str(n)
        for l in letters_tuple:
            items_list.append(n + l)
    
    return items_list, item_dict

def make_item_loops(item_list, max_item, n_rounds, item_dict):
    list_lines = []
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
        with open(full_path, "w", encoding='utf-8') as f:
            f.write(chunk)
    print("okkkkk")

def version2(filepath, p):
    path = Path(filepath)                                                                              
    item_dict = item_dict_builder(path)                                                       # Make list of dict indicating all item n. and line n. for each item 
    print(item_dict)
    out_num, n_rounds = digits_only_list(item_dict)
    print(out_num)
    item_list, _ = table_content_builder(item_dict)
    list_lines = make_item_loops(item_list, max(out_num), n_rounds, item_dict)
    final_split = final_list(list_lines)                                                        # Identifies the list of dict that covers the most lines (aka actual items)
    print_items(filepath, final_split, p)
    time.sleep(0.5)

def try_exercize(p):
    filepath = p / "clean-full-submission.txt"
    try:
        version2(filepath, p)
    except:
        print("failed")
    return