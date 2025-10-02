import re
from pathlib import Path
import sys


ticker = "ZTS"
filings = "0001555280-25-000102"
filings2 = "0001555280-24-000143"
file = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings / "item1A.txt"
file2 = Path("data") / "html" / "sec-edgar-filings" / ticker / "10-K" / filings2 / "item1A.txt"



def tokenize(text: str):
    _WORD_RE = re.compile(r"[A-Za-z']+")
    return _WORD_RE.findall(text.lower())

def levenshtein_tokens(a_tokens, b_tokens):
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
            sys.stdout.write(f"\rProgress: {pct:6.2f}%  (row {i}/{m}, col {j}/{n})")
            sys.stdout.flush()
    # after both loops finish:
        print()
        prev = cur
    return prev[n]

def min_edit_similarity(text_a: str, text_b: str):
    A, B = tokenize(text_a), tokenize(text_b)
    dist = levenshtein_tokens(A, B)
    denom = len(A) + len(B)
    sim = 1.0 - (dist / denom if denom else 0.0)
    return {"distance": dist, "similarity": sim, "len_a": len(A), "len_b": len(B)}

model = []
text = file.read_text(encoding="utf-8", errors="ignore")
text2 = file2.read_text(encoding="utf-8", errors="ignore")

model.append(min_edit_similarity(text, text2))

print(model)