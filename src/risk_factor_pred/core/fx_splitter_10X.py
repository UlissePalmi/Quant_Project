from pathlib import Path
from typing import List, Dict, Tuple, Optional
from itertools import islice
import re
import time

def _normalize_ws(s: str) -> str:
    """
    Replaces common non-breaking spaces with regular spaces, collapses runs of
    whitespace to a single space, and strips leading/trailing whitespace.
    """
    s = s.replace("\xa0", " ").replace("\u2007", " ").replace("\u202f", " ")
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def before_dot(s: str) -> str:
    """
    Return everything before the first '.'; if no dot, return the string unchanged.
    """
    i = s.find('.')
    return s[:i] if i != -1 else s

def item_dict_builder(path):
    """
    Build an ordered list of detected 10-K 'Item' headings with line numbers.

    Reads the file at 'path', scans line-by-line for headings that look like
    'Item 1.', 'Item 1A.', etc., and returns a list of dictionaries containing:
      - item_n: normalized item token (e.g., "1", "1A")
      - line_no: 1-indexed line number where the heading appears
        # Change to length of words/char post 'Item <num>.'
        # Must add 'Item <num> and <num>.'
    Consecutive duplicate item tokens are removed (deduped) to reduce noise.
    """

    text = path.read_text(encoding="utf-8", errors="ignore")
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

def number_of_rounds(item_dict, bool):
    """
    Extract numeric item components and estimate how many full 'rounds' of items exist.

    For each entry in `item_dict:` list[dict], extracts only digits from the `item_n` field and
    converts them to integers. 
    Then estimates the number of repeated "rounds" of the table-of-contents items by
    counting occurrences of `max_num` and `max_num - 1`.
    """
    out = []
    for items in item_dict:
        digits = "".join(ch for ch in items.get("item_n") if ch.isdigit() and ch)
        out.append(digits)
    listAllItems = [int(i) for i in out]

    # sometimes "Item 400" exists
    while max(listAllItems) > 20:
        listAllItems.remove(max(listAllItems))
    
    max_num = max(listAllItems)

    # Double check the number of rounds is correct
    rounds = [i for i in listAllItems if i==max_num]
    rounds2 = [i for i in listAllItems if i==max_num-1]
    rounds = rounds2 if rounds > rounds2 else rounds
    
    if bool == True:
        return len(rounds)
    else:
        print(listAllItems)
        return listAllItems

def table_content_builder(item_dict):
    """
    Builds a `tableContent` starting from common early 10-K item labels and then extends it
    up to the maximum item number observed in `item_dict` (including optional suffix letters A/B/C).

    Returns: list[str]
    eg ['1', '1A', '1B', '1C', '2', ...]
    """
    listAllItems = number_of_rounds(item_dict, bool=False)
    tableContent = ["1", "1A", "1B", "1C", "1D", "2", "3", "4", "5", "6", "7", "7A", "8"]
    letters_tuple = ("","A","B","C")
    for n in range(int(tableContent[-1])+1,max(listAllItems)+1):
        n = str(n)
        for l in letters_tuple:
            tableContent.append(n + l)    
    return tableContent

def final_list(tableContent, item_dict):
    """
    Makes a list of dict that contains the actual items

    First, builds multiple candidate sequences of item headings by scanning in item_dict.
    Secondly, Selects the candidate that is most probably the item list

    Returns list[dict]: The selected sequence (list of dicts with 'Item number' and 'Item line').
    """

    list_lines = []
    last_ele = 0
    for _ in range(number_of_rounds(item_dict, bool=True)):
        lines = []
        for itemTC in tableContent:
            for r in item_dict:
                if itemTC == r.get('item_n') and r.get('line_no') > last_ele:
                    lines.append(r)
                    last_ele = r['line_no']
                    break
        list_lines.append(lines)

    diff = 0
    for i in range(len(list_lines)):
        n = list_lines[i][-1]['line_no'] - list_lines[i][1]['line_no']
        if n > diff:
            num = i
            diff = n
    return list_lines[num]

def print_items(filepath, final_split, p):
    """
    Write per-item text files by slicing the input document between detected item headings.

    For each entry in `final_split`, this function:
      - takes the line range from its `line_no` to the next item heading's `line_no`,
      - writes the extracted chunk to `p/item<ITEM>.txt` (e.g., item1A.txt).

    Parameters
    ----------
    filepath : pathlib.Path
        Path to the full cleaned filing text (e.g., clean-full-submission.txt).
    final_split : list[dict]
        Selected sequence of headings (output of `final_list`), containing 'item_n' and 'line_no'.
    p : pathlib.Path
        Output directory where item files will be written (typically the filing folder).

    Returns
    -------
    None

    Side Effects
    ------------
    Writes multiple `item*.txt` files to disk.

    Notes
    -----
    The function currently appends a hard-coded terminal line number (11849) as the
    end boundary. This should ideally be replaced by the actual file length to
    avoid truncation or out-of-range assumptions.
    """
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

def version2(path, p):
    """
    End-to-end item-splitting routine for a single filing text file.

    Pipeline:
      1) detect item headings and line numbers (`item_dict_builder`),
      2) compute numeric item list and estimate number of rounds (`digits_only_list`),
      3) build candidate item labels (`table_content_builder`),
      4) construct candidate item sequences (`make_item_loops`),
      5) select the best sequence (`final_list`),
      6) write out per-item text files (`print_items`).

    Parameters
    ----------
    path : pathlib.Path
        Path to the cleaned filing text file (e.g., clean-full-submission.txt).
    p : pathlib.Path
        Output directory where per-item files will be written.

    Returns
    -------
    None

    Side Effects
    ------------
    Writes item files to disk and prints intermediate debugging output.
    """
    item_dict = item_dict_builder(path)                                                       # Make list of dict indicating all item n. and line n. for each item 
    tableContent = table_content_builder(item_dict)
    print_items(path, final_list(tableContent, item_dict), p)
    time.sleep(0.5)

def try_exercize(p):
    """
    Attempt to split a single filing into per-item text files, swallowing failures.

    Constructs the expected cleaned filing path `p/clean-full-submission.txt` and runs
    `version2(...)`. If any exception occurs, prints "failed" and returns.

    Parameters
    ----------
    p : pathlib.Path
        Filing directory containing `clean-full-submission.txt`.

    Returns
    -------
    None

    Notes
    -----
    Catching all exceptions with a bare `except:` makes debugging difficult and can
    hide real errors. Consider catching `Exception as e` and printing/logging `e`.
    """
    filepath = p / "full-submission.txt"
    try:
        version2(filepath, p)
    except:
        print("failed")
    return