from sec_edgar_downloader import Downloader
import re
import os

def remove_xbrl_xml_blocks(html_content): # Removes entire XBRL/XML blocks and individual XBRL tags from HTML content.
    pattern_blocks = re.compile(r'(<XBRL.*?>.*?</XBRL>)|(<XML.*?>.*?</XML>)', re.DOTALL)
    pattern_tags = re.compile(r'</?ix:.*?>')

    # Apply the patterns to the content
    clean_content = re.sub(pattern_blocks, '', html_content)
    clean_content = re.sub(pattern_tags, '', clean_content)
    return clean_content

def _ends_with_tag(piece: str) -> bool:
    """
    True if `piece` (a single segment) ends with an HTML-like tag: ...>
    We only look at this segment's tail; that's enough because the
    'current line' end always equals the last appended segment's end.
    """
    s = piece.rstrip()
    if not s.endswith(">"):
        return False
    # look back a little to find a '<' before the closing '>'
    tail = s[-300:] if len(s) > 300 else s
    i = tail.rfind("<")
    return i != -1 and "\n" not in tail[i:]

def _starts_with_tag(line: str) -> bool:
    """True if the (next) line starts with a tag after leading spaces: <..."""
    return line.lstrip().startswith("<")

def soft_unwrap_html_lines(html: str) -> str:
    """
    Replace a newline with a single space *only when*:
      - the current (combined) line does NOT end with an HTML tag, and
      - the next line does NOT start with an HTML tag.
    Preserves all other newlines and tags.
    """
    lines = html.splitlines()
    if not lines:
        return html

    out_lines = []

    # We'll build the current logical line as a list of segments
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
    # The re.DOTALL flag is crucial to match across multiple lines
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
    
    pattern = re.compile(r'<B>', re.IGNORECASE | re.DOTALL)         #   REMOVE TO FIND ITEMS!!!!!
    html_content = re.sub(pattern, '\n', html_content)

    pattern = re.compile(r'</B>', re.IGNORECASE)                    #   REMOVE TO FIND ITEMS!!!!!
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

def prepend_newline_to_p(html_content): #     Finds every <p> tag and inserts a newline character before it
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

def break_on_item_heads(text: str) -> str:
    """
    Ensure each 'Item <num><opt letter>.' starts on its own line.
    Example heads: 'Item 1.', 'Item 12.', 'Item 1A.', 'Item 12b .'
    """
    _HEAD_DETECT = re.compile(r'\s*item\b\s*\d+[A-Za-z]?\s*\.', re.IGNORECASE)
    
    out = []
    last = 0

    for m in _HEAD_DETECT.finditer(text):
        start = m.start()

        # If we're not at the very beginning and not already at a newline,
        # insert a newline before this head.
        if start > 0 and text[start-1] != '\n':
            out.append(text[last:start])
            out.append('\n')
            last = start

    out.append(text[last:])

    # Optional tidy-up: remove leading spaces at the start of lines we just created
    # (keeps any indentation that was already after a real newline)
    s = ''.join(out)                     # <-- join the list!
    return re.sub(r'[ \t]+\n', '\n', s)  # tidy spaces before newlines


def clean_html(file_content):
    cleaned = soft_unwrap_html_lines(file_content)
    cleaned = get_from_sec_document(cleaned)
    
    cleaned = get_content_before_sequence(cleaned)                     # cuts after <SEQUENCE>2
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

def print_10X(full_path, html_content, output_filename):
    with open(full_path, "w", encoding='utf-8') as new_file:
        new_file.write(html_content)
    print("\nCleaned content saved in {}".format(output_filename))

# un top: regex for html cleaning



# on bottom: renaming functions

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


