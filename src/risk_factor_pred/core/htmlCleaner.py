from risk_factor_pred.consts import SEC_DIR
import re
from typing import List
import os

# --------------------------------------------------------------------------------------------------------------------
#                                              REGEX FOR HTML CLEANING
# --------------------------------------------------------------------------------------------------------------------

def remove_xbrl_xml_blocks(html_content): # Removes entire XBRL/XML blocks and individual XBRL tags from HTML content.
    pattern_blocks = re.compile(r'(<XBRL.*?>.*?</XBRL>)|(<XML.*?>.*?</XML>)', re.DOTALL)
    pattern_tags = re.compile(r'</?ix:.*?>')
    clean_content = re.sub(pattern_blocks, '', html_content)
    clean_content = re.sub(pattern_tags, '', clean_content)
    return clean_content

def _ends_with_tag(piece: str) -> bool: # Checks if line end with html tag
    s = piece.rstrip()
    if not s.endswith(">"):
        return False
    tail = s[-300:] if len(s) > 300 else s
    i = tail.rfind("<")
    return i != -1 and "\n" not in tail[i:]

def _starts_with_tag(line: str) -> bool: # Checks if line starts with html tag
    return line.lstrip().startswith("<")

def soft_unwrap_html_lines(html: str) -> str: # Removes /n if sentence is ongoing
    lines = html.splitlines()
    if not lines:
        return html

    out_lines = []

    parts = [lines[0].rstrip("\r")]
    cur_ends_with_tag = _ends_with_tag(parts[-1])

    for raw_next in lines[1:]:
        nxt = raw_next.rstrip("\r")
        next_starts_tag = _starts_with_tag(nxt)

        if (not cur_ends_with_tag) and (not next_starts_tag):
            # join: ensure exactly one space at the boundary
            if parts[-1] and parts[-1].endswith((" ", "\t")):
                parts[-1] = parts[-1].rstrip()
            parts.append(" ")
            parts.append(nxt.lstrip())
            # after joining, the 'current line' ends as nxt ends
            cur_ends_with_tag = _ends_with_tag(nxt)
        else:
            # flush current logical line
            out_lines.append("".join(parts))
            # start a new logical line
            parts = [nxt]
            cur_ends_with_tag = _ends_with_tag(nxt)

    # flush the last line
    out_lines.append("".join(parts))
    return "\n".join(out_lines)

def remove_head_with_regex(html_content): # Uses regex to remove the <head> section.
    pattern = re.compile(r'<head>.*?</head>', re.DOTALL | re.IGNORECASE)
    clean_content = re.sub(pattern, '', html_content)
    return clean_content

def remove_style_with_regex(html_content): # Uses regex to remove the 'style' attribute from all tags.
    pattern = re.compile(r'\sstyle=(["\']).*?\1', re.IGNORECASE)
    clean_content = re.sub(pattern, '', html_content)
    return clean_content

def remove_id_with_regex(html_content):  # Uses regex to remove the 'id' attribute from all tags
    pattern = re.compile(r'\s+id=(["\']).*?\1', re.IGNORECASE)
    clean_content = re.sub(pattern, '', html_content)
    return clean_content

def remove_align_with_regex(html_content):  # Uses regex to remove the 'id' attribute from all tags
    pattern = re.compile(r'\s+align=(["\']).*?\1', re.IGNORECASE)
    clean_content = re.sub(pattern, '', html_content)
    return clean_content

def remove_part_1(html_content): # Cleans comments, tables, img, span
    pattern = re.compile(r'<!--.*?-->', re.DOTALL)
    html_content = re.sub(pattern, '', html_content)
    
    pattern = re.compile(r'<img.*?>', re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    html_content = html_content.replace('<span>', '').replace('</span>', '').replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
    html_content = html_content.replace('&nbsp;', ' ').replace('&#146;', "'")

    pattern = re.compile(r'&#\d{3};')
    html_content = re.sub(pattern, ' ', html_content)

    return html_content

def loop_clean(html_content):
    p_pattern = re.compile(r'<p>\s*</p>', re.DOTALL | re.IGNORECASE)
    div_pattern = re.compile(r'<div>\s*</div>', re.IGNORECASE)
    while True:
        pre_cleaning_content = html_content
        
        html_content = re.sub(p_pattern, '', html_content)
        html_content = re.sub(div_pattern, '', html_content)

        if html_content == pre_cleaning_content:
            break

    return html_content

def remove_numeric_entities(s: str) -> str:
    return re.sub(r'&#(?:\d{1,8}|[xX][0-9A-Fa-f]{1,8});', '', s)

def unwrap_tags(html_content): # Removes matching <ix...> and </ix...> tags but keeps the content between them.
    pattern = re.compile(r'<ix:[a-zA-Z0-9_:]+.*?>', re.IGNORECASE)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</ix:[a-zA-Z0-9_:]+>', re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<html.*?>', re.IGNORECASE | re.DOTALL)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</html>', re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<font.*?>', re.IGNORECASE | re.DOTALL)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</font>', re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<br.*?>', re.IGNORECASE | re.DOTALL)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<hr.*?>', re.IGNORECASE | re.DOTALL)
    html_content = re.sub(pattern, '', html_content)
    
    pattern = re.compile(r'<B>', re.IGNORECASE | re.DOTALL)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</B>', re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<center>', re.IGNORECASE | re.DOTALL)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</center>', re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<a.*?>', re.IGNORECASE | re.DOTALL)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</a>', re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<table.*?>', re.DOTALL | re.IGNORECASE)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</table>', re.DOTALL | re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<tr.*?>', re.DOTALL | re.IGNORECASE)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</tr>', re.DOTALL | re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    pattern = re.compile(r'<td.*?>', re.DOTALL | re.IGNORECASE)
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</td>', re.DOTALL | re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)

    return html_content

def clean_lines(text_content): # Removes all lines that are empty/contain only whitespace and removes leading whitespace from the remaining lines
    cleaned_lines = [line.lstrip() for line in text_content.splitlines() if line.strip()]
    return '\n'.join(cleaned_lines)

def prepend_newline_to_p(html_content): # Finds every <p> tag and inserts a newline character before it
    pattern = re.compile(r'<p.*?>', re.IGNORECASE)
    processed_text = re.sub(pattern, r'\n\g<0>', html_content)    
    return processed_text

def strip_all_html_tags(html_content): # Removes all HTML tags from a string.
    pattern = re.compile(r'<.*?>')
    clean_text = re.sub(pattern, '', html_content)
    return clean_text

def remove_xbrli_measure(html_content): # Uses regex to find and remove the entire <xbrli:measure> ... </xbrli:measure> block.
    pattern = re.compile(r'<xbrli:([a-zA-Z0-9_:]+).*?>.*?</xbrli:\1>', re.DOTALL | re.IGNORECASE)
    html_content = re.sub(pattern, '', html_content)
    return html_content

def get_from_sec_document(html_content: str) -> str:
    pattern = re.compile(r'<SEC-DOCUMENT>.*\Z', re.DOTALL)
    match = re.search(pattern, html_content)
    return match.group(0) if match else html_content

def get_content_before_sequence(html_content):
    pattern = re.compile(r'^.*?(?=<SEQUENCE>2)', re.DOTALL)
    match = re.search(pattern, html_content)
    return match.group() if match else html_content

def break_on_item_heads(text: str) -> str: # Inserts \n before each item
    _HEAD_DETECT = re.compile(r'\s*item\b\s*\d+[A-Za-z]?\s*\.', re.IGNORECASE)
    out = []
    last = 0
    for m in _HEAD_DETECT.finditer(text):
        start = m.start()
        if start > 0 and text[start-1] != '\n':
            out.append(text[last:start])
            out.append('\n')
            last = start
    out.append(text[last:])
    s = ''.join(out)                     # <-- join the list!
    return re.sub(r'[ \t]+\n', '\n', s)  # tidy spaces before newlines

def clean_html(file_content):
    cleaned = soft_unwrap_html_lines(file_content)
    cleaned = get_from_sec_document(cleaned)
    
    cleaned = get_content_before_sequence(cleaned)                          # cuts after <SEQUENCE>2
    cleaned = remove_head_with_regex(cleaned)
    
    cleaned = remove_style_with_regex(cleaned)
    cleaned = remove_id_with_regex(cleaned)
    cleaned = remove_align_with_regex(cleaned)
    
    cleaned = remove_part_1(cleaned)
    cleaned = unwrap_tags(cleaned)                                          # Removes useless tags
    cleaned = remove_xbrli_measure(cleaned)
    
    cleaned = loop_clean(cleaned)                                           # LOOP : empty tags

    cleaned = prepend_newline_to_p(cleaned)
    cleaned = clean_lines(cleaned)

    cleaned = strip_all_html_tags(cleaned)
    cleaned = remove_numeric_entities(cleaned)
    cleaned = break_on_item_heads(cleaned)
    return cleaned

def print_clean_txt(html_content):
    try:
        with open(html_content, 'r', encoding='utf-8') as file:
            file_content = file.read()
        cleaned = clean_html(file_content)
    except FileNotFoundError:
        print(f"Error: The file '{html_content}' was not found.")
    return cleaned


# --------------------------------------------------------------------------------------------------------------------
#                                                Cleaning 'Items'
# --------------------------------------------------------------------------------------------------------------------

def cleaning_items(html_content):
    html_content = merge_I_tem(html_content)
    html_content = ensure_space_after_item(html_content)
    html_content = merge_item_with_number_line(html_content)
    return merge_item_number_with_suffix(html_content)

def merge_I_tem(content: str) -> str: # Finds lines with 'I' & next line starts with 'tem' then merge them
    lines = content.splitlines()  # split into lines without keeping '\n'
    new_lines = []
    i = 0

    while i < len(lines):
        # Make sure there *is* a next line to look at
        if (
            lines[i].strip() == "I" and
            i + 1 < len(lines) and
            lines[i + 1].lstrip().startswith("tem")
        ):
            merged_line = "I" + lines[i + 1].lstrip()  # e.g. "Item 1. ..."
            new_lines.append(merged_line)
            i += 2  # skip the next line because we've merged it
        else:
            new_lines.append(lines[i])
            i += 1
    return "\n".join(new_lines)

def ensure_space_after_item(text: str) -> str:  # Ensures every 'Item'/'Items' is followed by a space
    return re.sub(r'\b(Items?)\b(?=\S)', r'\1 ', text)


def merge_item_with_number_line(text: str) -> str: # If a line is just 'Item'/'Items' and the following line starts with a number merges them
    lines = text.splitlines()
    new_lines = []
    i = 0

    while i < len(lines):
        current = lines[i].strip()

        # Check if this line is exactly 'Item' or 'Items'
        if current in ("Item", "Items") and i + 1 < len(lines):
            next_raw = lines[i + 1]
            # Remove leading spaces to inspect the first real character
            next_stripped_leading = next_raw.lstrip()

            # Check if next line starts with a digit
            if next_stripped_leading and next_stripped_leading[0].isdigit():
                # Merge: 'Item' + space + next line (without leading spaces)
                merged = f"{current} {next_stripped_leading}"
                new_lines.append(merged)
                i += 2  # skip the next line (already merged)
                continue

        # Default: keep line as-is
        new_lines.append(lines[i])
        i += 1

    return "\n".join(new_lines)

def merge_item_number_with_suffix(text: str) -> str:
    """
    If a line is 'Item {number}' only, and the following line starts with either:
      - a single letter and a dot (e.g., 'A. Risk Factors')
      - or just a dot (e.g., '. Risk Factors')
    then merge them into one line: 'Item 1A. Risk Factors' or 'Item 1. Risk Factors'.
    """
    lines = text.splitlines()
    new_lines = []
    i = 0

    while i < len(lines):
        current_stripped = lines[i].strip()

        # Match 'Item {number}' (e.g., 'Item 1', 'Item 12')
        if re.fullmatch(r'Item\s+\d+', current_stripped) and i + 1 < len(lines):
            next_raw = lines[i + 1]
            next_stripped = next_raw.lstrip()

            # Next line starts with 'A.' or 'b.' etc, OR with just '.'
            if re.match(r'[A-Za-z]\.', next_stripped) or next_stripped.startswith('.'):
                merged = current_stripped + next_stripped  # e.g. 'Item 1' + 'A. Risk Factors'
                new_lines.append(merged)
                i += 2
                continue

        # Default: keep line as-is
        new_lines.append(lines[i])
        i += 1
    return "\n".join(new_lines)

# --------------------------------------------------------------------------------------------------------------------
#                                              MERGES THE FUNCTIONS
# --------------------------------------------------------------------------------------------------------------------

def print_10X(full_path, html_content, output_filename):
    with open(full_path, "w", encoding='utf-8') as new_file:
        new_file.write(html_content)
    print("\nCleaned content saved in {}".format(output_filename))

def cleaner(ticker, output_filename):
    folders_path = SEC_DIR / ticker / "10-K"
    for p in folders_path.iterdir():
        print(p)
        full_path = os.path.join(p, output_filename)
        html_content = os.path.join(p,"full-submission.txt")
        html_content = print_clean_txt(html_content)                    # html removal
        html_content = cleaning_items(html_content)
        print_10X(full_path, html_content, output_filename)
    return
