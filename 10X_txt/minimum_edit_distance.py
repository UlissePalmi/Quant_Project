import re
from pathlib import Path
import sys
import make_comps as mc
import csv
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

nltk.download("vader_lexicon", quiet=True)
_sia = SentimentIntensityAnalyzer()

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
    return sum(compounds) / len(compounds)


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
        prev = cur
    return prev[n], new_words

def min_edit_similarity(text_a: str, text_b: str, dict, ticker):
    A, B = tokenize(text_a), tokenize(text_b)
    dist, new_words = levenshtein_tokens(A, B, ticker)
    denom = len(A) + len(B)
    sim = 1.0 - (dist / denom if denom else 0.0)
    return {"ticker": ticker, "date_a": dict["date1"], "date_b": dict["date2"], "distance": dist, "similarity": sim, "len_a": len(A), "len_b": len(B), "sentiment": mean_vader_compound(new_words)}


folders_path = Path("data") / "html" / "sec-edgar-filings"


ticker = "INTC"

ordered_data = mc.prepare_data(ticker)

model = []
for comps in ordered_data:
    filings = comps["filing1"]
    filings2 = comps["filing2"]
    file = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings / "item1A.txt"
    file2 = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings2 / "item1A.txt"
    text = file.read_text(encoding="utf-8", errors="ignore")
    text2 = file2.read_text(encoding="utf-8", errors="ignore")
    model.append(min_edit_similarity(text, text2, comps, ticker))

'''
fieldnames = model[0].keys()
with open("similarity_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(model)
'''




for ticker in folders_path.iterdir():
    ticker = ticker.name
    ordered_data = mc.prepare_data(ticker)
    model = []
    for comps in ordered_data:
        filings = comps["filing1"]
        filings2 = comps["filing2"]
        file = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings / "item1A.txt"
        file2 = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings2 / "item1A.txt"
        text = file.read_text(encoding="utf-8", errors="ignore")
        text2 = file2.read_text(encoding="utf-8", errors="ignore")
        model.append(min_edit_similarity(text, text2, comps, ticker))
print(model)

fieldnames = ["ticker", "date_a", "date_b", "distance", "similarity", "len_a", "len_b"]
with open("similarity_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(model)