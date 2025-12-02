from pathlib import Path
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import sys
import re

nltk.download("vader_lexicon", quiet=True)
_sia = SentimentIntensityAnalyzer()


# --------------------------------------------------------------------------------------------------------------------
#                                                MAKE COMPS FUNCTIONS
# --------------------------------------------------------------------------------------------------------------------


def check_date(folder, filing):
    file = folder / "clean-full-submission.txt"
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

def prepare_data(ticker, SAVE_DIR):
    date_data = []
    folders_path = SAVE_DIR / "sec-edgar-filings" / ticker / "10-K"
    for i in folders_path.iterdir():
        if (Path(i) / "item1A.txt").is_file():
            filing = i.name
            date_data.append(check_date(i, filing))
    ordered_filings = order_filings(date_data)
    comps_list = make_comps(ordered_filings, date_data)                                 # List of dictionary
    return comps_list

def process_comps(comps, ticker, SAVE_DIR):
    filings = comps["filing1"]
    filings2 = comps["filing2"]
    file = SAVE_DIR / "sec-edgar-filings" / ticker / "10-K" / filings / "item1A.txt"
    file2 = SAVE_DIR / "sec-edgar-filings" / ticker / "10-K" / filings2 / "item1A.txt"
    text = file.read_text(encoding="utf-8", errors="ignore")
    text2 = file2.read_text(encoding="utf-8", errors="ignore")
    return min_edit_similarity(text, text2, comps, ticker)

def concurrency_runner(writer, ticker, SAVE_DIR):
    #try:
    ordered_data = prepare_data(ticker, SAVE_DIR)
    model = []
    print("funzia")
    with ProcessPoolExecutor(max_workers=3) as executor:
        model = list(executor.map(process_comps, ordered_data, repeat(ticker), repeat(SAVE_DIR)))
        writer.writerows(model)
    #except:
    #    print("Skipped")



# --------------------------------------------------------------------------------------------------------------------
#                                                SIMILARITY FUNCTIONS
# --------------------------------------------------------------------------------------------------------------------


def tokenize(text: str):
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
    # Classic Wagner–Fischer with two rows
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
        #print()
        prev = cur
    return prev[n], new_words

def min_edit_similarity(text_a: str, text_b: str, dict, ticker):
    A, B = tokenize(text_a), tokenize(text_b)
    dist, new_words = levenshtein_tokens(A, B, ticker)
    denom = len(A) + len(B)
    sim = 1.0 - (dist / denom if denom else 0.0)
    return {"ticker": ticker, "date_a": dict["date1"], "date_b": dict["date2"], "distance": dist, "similarity": sim, "len_a": len(A), "len_b": len(B), "sentiment": mean_vader_compound(new_words)}
