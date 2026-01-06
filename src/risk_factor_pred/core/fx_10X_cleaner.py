import re

# --------------------------------------------------------------------------------------------------------------------
#                                                ?RENAMING FILES?
# --------------------------------------------------------------------------------------------------------------------

def get_from_sec_document(html_content: str) -> str:
    pattern = re.compile(r'<SEC-DOCUMENT>.*\Z', re.DOTALL)
    match = re.search(pattern, html_content)
    return match.group(0) if match else html_content

def strip_all_html_tags(html_content): # Removes all HTML tags from a string.
    pattern = re.compile(r'<.*?>')
    clean_text = re.sub(pattern, '', html_content)
    return clean_text


def extract_first_line(filepath) -> str | None:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            first_line = strip_all_html_tags(get_from_sec_document(f.read()).readline()).replace(".txt", '').replace(" ", '').replace(":", '_').replace("\n", '')
    except OSError as e:
        print(f"[ERROR] Cannot open {filepath.name}: {e}")
    return first_line

def name_10X(ticker, document, html_content):
    end_name = extract_first_line(html_content).split('_')[1]
    end_name = f"{end_name[:4]}-{end_name[4:6]}-{end_name[6:]}"
    return f"{ticker}_{document}_{end_name}.txt"

# --------------------------------------------------------------------------------------------------------------------
#                                                SPACE CLEANER
# --------------------------------------------------------------------------------------------------------------------