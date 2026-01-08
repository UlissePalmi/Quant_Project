from itertools import repeat
from concurrent.futures import ProcessPoolExecutor
from nltk.sentiment import SentimentIntensityAnalyzer
from risk_factor_pred.consts import SEC_DIR
import nltk
import sys
import re

nltk.download("vader_lexicon", quiet=True)
_sia = SentimentIntensityAnalyzer()

# --------------------------------------------------------------------------------------------------------------------
#                                                MAKE COMPS FUNCTIONS
# --------------------------------------------------------------------------------------------------------------------

def check_date(folder):
    """
    Finds the date the 10-K was released.
    
    The function reads the `SEC_DIR/<ticker>/10-K/<filing_id>/full-submission.txt` file
    line-by-line and searches for: <filing_id>: YYYYMMDD. When it finds a matching line,
    it parses the portion after ':' and returns:
        a dictionary
            year
            month
            day
            filing  
    """
    filing = folder.name
    file = folder / "full-submission.txt"
    with open(file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            hay = line.lower()
            if filing in hay:
                date = hay.partition(":")[2].lstrip()
                break
    info_dict = {
        "year": date[:4],
        "month": date[4:6],
        "day": date[6:8],
        "filing": filing
    }
    return info_dict

def order_filings(records):
    """
    Sort filing metadata records in reverse chronological order and return filing IDs.

    Parameters
    ----------
    records : list[dict]
        Each dict must include "year", "month", "day" and "filing" keys.

    Returns
    -------
    list[str]
        Filing identifiers ordered from most recent to oldest.
    """
    records_sorted = sorted(
        records,
        key=lambda r: (int(r["year"]), int(r["month"]), int(r["day"])),
        reverse=True,
    )

    out = []
    for r in records_sorted:
        filing_id = r["filing"]
        filing_date = f"{int(r['year']):04d}-{int(r['month']):02d}-{int(r['day']):02d}"
        out.append([filing_id, filing_date])
    return out

def make_comps(cik):
    """
    Prepare consecutive 10-K Item 1A comparison pairs for a given cik.

    The function scans SEC_DIR/<ticker>/10-K/* and keeps only filings that
    contain an extracted `item1A.txt`. It then orders filings by date and
    constructs consecutive pairwise comparisons.

    Returns list[dict]
    """
    date_data = []
    folders_path = SEC_DIR / cik / "10-K"
    for i in folders_path.iterdir():
        date_data.append(check_date(i) if (i / "item1A.txt").is_file() else None) 
    
    ordered_filings = order_filings(date_data)

    comps_list = []
    for n in range(1, len(ordered_filings)):
        comps_list.append({
            "date1": ordered_filings[n - 1][1],
            "filing1": ordered_filings[n - 1][0],
            "date2": ordered_filings[n][1],
            "filing2": ordered_filings[n][0]
        })
    
    return comps_list


# ---------------------------------------------------------------------------------------



def process_comps(comps, ticker):
    """
    Compute similarity metrics for a single consecutive filing comparison.

    Loads `item1A.txt` for two filings (newer vs older) and computes token-level
    Levenshtein distance, similarity, and sentiment statistics for newly introduced
    words (relative to the older filing).

    Parameters
    ----------
    comps : dict
        Comparison dict containing "filing1", "filing2", "date1", "date2".
    ticker : str
        Ticker/CIK folder name under SEC_DIR.

    Returns
    -------
    dict
        Output of `min_edit_similarity`, including ticker, dates, distance, similarity,
        token lengths, and sentiment of newly introduced words.

    Raises
    ------
    FileNotFoundError
        If either `item1A.txt` is missing.
    """
    filings = comps["filing1"]
    filings2 = comps["filing2"]
    file = SEC_DIR / ticker / "10-K" / filings / "item1A.txt"
    file2 = SEC_DIR / ticker / "10-K" / filings2 / "item1A.txt"
    text = file.read_text(encoding="utf-8", errors="ignore")
    text2 = file2.read_text(encoding="utf-8", errors="ignore")
    return min_edit_similarity(text, text2, comps, ticker)

def concurrency_runner(writer, cik):
    """
    Compute similarity features for a ticker and write results using multiprocessing.

    The function prepares consecutive filing comparisons and then uses a
    ProcessPoolExecutor to parallelize `process_comps` across comparisons.
    The resulting dictionaries are written via `writer.writerows(model)`.

    Parameters
    ----------
    writer : csv.DictWriter | csv.writer-like
        Writer object with a `.writerows(...)` method. For dict outputs, a
        `csv.DictWriter` is recommended.
    ticker : str
        Ticker/CIK folder name under SEC_DIR.

    Returns
    -------
    None

    Side Effects
    ------------
    - Reads multiple `item1A.txt` files from disk.
    - Writes rows to the provided writer.
    - Prints status messages.

    Notes
    -----
    The function currently catches all exceptions silently ("Skipped").
    For research reproducibility, prefer logging the exception and ticker.
    """

    try:
        ordered_data = make_comps(cik)
        model = []
        print("funzia")
        with ProcessPoolExecutor(max_workers=3) as executor:
            model = list(executor.map(process_comps, ordered_data, repeat(cik)))
            writer.writerows(model)
    except:
        print("Skipped")



# --------------------------------------------------------------------------------------------------------------------
#                                                SIMILARITY FUNCTIONS
# --------------------------------------------------------------------------------------------------------------------


def tokenize(text: str):
    """
    Tokenize text into lowercase word tokens.

    Uses a simple regex that matches sequences of ASCII letters and apostrophes.
    This is intentionally lightweight and avoids external tokenizers.

    Parameters
    ----------
    text : str
        Input text.

    Returns
    -------
    list[str]
        List of lowercase tokens.
    """
    _WORD_RE = re.compile(r"[A-Za-z']+")
    return _WORD_RE.findall(text.lower())

def mean_vader_compound(words) -> float:
    """
    Average VADER 'compound' score over a list of single-word strings.
    Returns 0.0 for an empty list.
    """
    compounds = []
    for w in words:
        w = (w or "").strip()
        scores = {"compound": 0.0} if not w else _sia.polarity_scores(w)
        compounds.append(scores["compound"])
    if len(compounds) != 0:
        return sum(compounds) / len(compounds)
    else:
        return 0

def levenshtein_tokens(a_tokens, b_tokens, ticker):
    """
    Compute token-level Levenshtein edit distance using a two-row dynamic program.

    Implements Wagner–Fischer (edit distance) over token sequences. For memory
    efficiency, the function ensures the second sequence is the shorter one.

    Parameters
    ----------
    a_tokens : list[str]
        Tokens from document A (newer filing in your usage).
    b_tokens : list[str]
        Tokens from document B (older filing in your usage).
    ticker : str
        Used only for progress printing.

    Returns
    -------
    tuple[int, list[str]]
        (distance, new_words) where:
          - distance is the Levenshtein edit distance between token sequences,
          - new_words are tokens present in `a_tokens` but not in `b_tokens`
            (set difference, not edit-alignment-based).

    Notes
    -----
    The progress printing should be driven by the i/j loop. In the current code,
    `j` is referenced outside its loop and `new_words` computation is indented
    inside the outer loop; this should be corrected for clarity and correctness.
    """
    m, n = len(a_tokens), len(b_tokens)
    if n > m:
        # ensure n <= m for memory efficiency
        a_tokens, b_tokens = b_tokens, a_tokens
        m, n = n, m

    prev = list(range(n + 1))  # row 0..n
    for i in range(1, m + 1):
        cur = [i] + [0]*n
        ai = a_tokens[i-1]
        for j in range(1, n + 1):
            cost = 0 if ai == b_tokens[j-1] else 1
            cur[j] = min(
                prev[j] + 1,      # deletion
                cur[j-1] + 1,     # insertion
                prev[j-1] + cost  # substitution (0 if match)
            )

        if (j % 1000 == 0) or (j == n):  # adjust 1000 for your speed/verbosity
            done_cells = (i - 1) * n + j
            total_cells = m * n
            pct = (done_cells / total_cells) * 100 if total_cells else 100.0
            sys.stdout.write(f"\rTicker: {ticker} Progress: {pct:6.2f}%  (row {i}/{m}, col {j}/{n})")
            sys.stdout.flush()

        b_set = set(b_tokens)
        new_words = [t for t in a_tokens if t not in b_set]
    # after both loops finish:
        print()
        prev = cur
    return prev[n], new_words

def min_edit_similarity(text_a: str, text_b: str, dict, ticker):
    """
    Compute disclosure-change features from two texts using edit distance and sentiment.

    Steps:
      1) tokenize both texts,
      2) compute token-level Levenshtein distance,
      3) convert distance into a normalized similarity score:
           similarity = 1 - dist / (len(A) + len(B)),
      4) identify tokens in A not present in B and compute their mean VADER sentiment.

    Parameters
    ----------
    text_a : str
        Newer period text (Item 1A).
    text_b : str
        Older period text (Item 1A).
    dict : dict
        Metadata dict containing "date1" and "date2".
    ticker : str
        Firm identifier, stored in output and used for progress printing.

    Returns
    -------
    dict
        Dictionary containing:
          - ticker, date_a, date_b,
          - distance (int), similarity (float),
          - len_a, len_b (token counts),
          - sentiment (float): mean compound score of newly introduced words.
    """
    A, B = tokenize(text_a), tokenize(text_b)
    dist, new_words = levenshtein_tokens(A, B, ticker)
    denom = len(A) + len(B)
    sim = 1.0 - (dist / denom if denom else 0.0)
    return {"ticker": ticker, "date_a": dict["date1"], "date_b": dict["date2"], "distance": dist, "similarity": sim, "len_a": len(A), "len_b": len(B), "sentiment": mean_vader_compound(new_words)}
