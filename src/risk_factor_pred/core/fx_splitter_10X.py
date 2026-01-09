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

    Reads the file at `path`, scans line-by-line for headings that look like
    'Item 1.', 'Item 1A.', etc., and returns a list of dictionaries containing:
      - item_n: normalized item token (e.g., "1", "1A")
      - line_no: 1-indexed line number where the heading appears

    Consecutive duplicate item tokens are removed (deduped) to reduce noise.

    Parameters
    ----------
    path : pathlib.Path
        Path to a cleaned filing text file (e.g., clean-full-submission.txt).

    Returns
    -------
    list[dict]
        List of dicts with keys {'item_n', 'line_no'} in file order.

    Notes
    -----
    The current regex matches lines beginning with "Item" or "Items" followed by
    a digit. It may miss headings that are not line-start aligned or that include
    unusual punctuation/formatting.
    """
                                                                                         # Filepath -> List[Dict] {'item_n': 'x', 'line_no': y}
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

def digits_only_list(item_dict):
    """
    Extract numeric item components and estimate how many full 'rounds' of items exist.

    For each entry in `item_dict`, extracts only digits from the `item_n` field and
    converts them to integers. It then applies a heuristic:
      - drop extreme maxima above 20 (to ignore cases like "Item 400"),
      - compute `max_num` as the maximum remaining item number,
      - estimate the number of repeated "rounds" of the table-of-contents items by
        counting occurrences of `max_num` and `max_num - 1`.

    Parameters
    ----------
    item_dict : list[dict]
        Output from `item_dict_builder`, containing 'item_n' values.

    Returns
    -------
    tuple[list[int], int]
        (out_num, n_rounds)
        - out_num: numeric item values (one per element in item_dict)
        - n_rounds: estimated number of repeated item sequences in the document

    Notes
    -----
    This is heuristic logic intended to handle filings with repeated headings
    (e.g., table of contents plus the actual section headers).
    """
    out = []
    for items in item_dict:
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
    """
    Construct a canonical list of possible item labels and return it with the item dict.

    Builds an `items_list` starting from common early 10-K item labels
    (e.g., 1, 1A, 1B, 2, ..., 8) and then extends it up to the maximum item
    number observed in `item_dict` (including optional suffix letters A/B/C).

    Parameters
    ----------
    item_dict : list[dict]
        Output from `item_dict_builder`.

    Returns
    -------
    tuple[list[str], list[dict]]
        (items_list, item_dict)
        - items_list: candidate item labels in expected order (strings like "9A")
        - item_dict: the input list (returned for convenience)
    """
    out_num, _ = digits_only_list(item_dict)
    items_list = ["1", "1A", "1B", "1C", "1D", "2", "3", "4", "5", "6", "7", "7A", "8"]
    letters_tuple = ("","A","B","C")
    for n in range(int(items_list[-1])+1,max(out_num)+1):
        n = str(n)
        for l in letters_tuple:
            items_list.append(n + l)
    
    return items_list, item_dict

def make_item_loops(item_list, max_item, n_rounds, item_dict):
    """
    Build multiple candidate sequences of item headings by scanning forward in the file.

    The function attempts to construct `n_rounds` sequences of items. For each round,
    it scans `item_dict` in increasing line-number order and selects the first
    occurrence of each `item_list` label that appears after the last selected line.

    Parameters
    ----------
    item_list : list[str]
        Candidate item labels in expected order.
    max_item : int
        Maximum numeric item (currently not used by this implementation).
    n_rounds : int
        Number of sequences ("rounds") to construct.
    item_dict : list[dict]
        Detected item headings with line numbers.

    Returns
    -------
    list[list[dict]]
        A list of candidate sequences. Each sequence is a list of dicts from `item_dict`
        corresponding to detected headings in that round.

    Notes
    -----
    This is a greedy matching algorithm. It does not validate that the selected
    headings are the "true" section boundaries; it relies on downstream selection
    (see `final_list`) to pick the best candidate.
    """
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
    """
    Select the candidate item sequence that spans the most lines.

    Given multiple candidate sequences produced by `make_item_loops`, this function
    chooses the sequence with the largest line-number span (heuristically treating
    that as the "actual" item headings rather than a shorter table-of-contents block).

    Parameters
    ----------
    list_lines : list[list[dict]]
        Candidate sequences of item-heading dicts.

    Returns
    -------
    list[dict]
        The selected sequence (list of dicts with 'item_n' and 'line_no').

    Notes
    -----
    The current span calculation uses:
        last_line - second_line
    which assumes at least two items exist in each candidate. If a candidate
    sequence is too short, this can raise an IndexError.
    """
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

    print(item_dict)
    out_num, n_rounds = digits_only_list(item_dict)
    print(out_num)
    item_list, _ = table_content_builder(item_dict)
    list_lines = make_item_loops(item_list, max(out_num), n_rounds, item_dict)
    final_split = final_list(list_lines)                                                        # Identifies the list of dict that covers the most lines (aka actual items)
    print_items(path, final_split, p)
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
    filepath = p / "clean-full-submission.txt"
    try:
        version2(filepath, p)
    except:
        print("failed")
    return