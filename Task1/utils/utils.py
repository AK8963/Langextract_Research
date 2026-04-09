import re
from difflib import SequenceMatcher
import sys
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    LEVEL_1_KEYWORDS, FALSE_HEADING_PATTERNS, MAX_HEADING_LENGTH
)

# Check if a heading extracted by the LLM actually exists in the original text
def is_valid_heading_in_text(heading_text: str, full_text: str, threshold: float = 0.85) -> bool:
    """Check if heading exists in text with fuzzy matching."""
    normalized_heading = " ".join(heading_text.split()).lower()
    normalized_full = " ".join(full_text.split()).lower()
    if normalized_heading in normalized_full:
        return True
    num_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', heading_text)
    if num_match:
        number_part, title_part = num_match.groups()
        title_normalized = " ".join(title_part.split()).lower()
        if number_part in full_text and title_normalized in normalized_full:
            return True
    heading_len = len(normalized_heading)
    for i in range(len(normalized_full) - heading_len + 1):
        window = normalized_full[i:i + heading_len + 10]
        ratio = SequenceMatcher(None, normalized_heading, window[:heading_len]).ratio()
        if ratio >= threshold:
            return True
    return False

# Assign a hierarchical level (1, 2, 3, etc.) to a heading
def determine_heading_level(text: str) -> int:
    """Determine heading level from text pattern or markdown # prefix."""
    text = text.strip()
    md_match = re.match(r'^(#{1,6})\s+', text)
    if md_match:
        return len(md_match.group(1))

    if re.match(r'^(Chapter|Part)\s+', text, re.IGNORECASE): # Level 1
        return 1
    if any(kw in text.lower() for kw in LEVEL_1_KEYWORDS):
        if not re.match(r'^\d+\.', text):
            return 1

    if re.match(r'^\d+\.\d+\.\d+\.\d+\.\d+', text): # Level 5
        return 5

    if re.match(r'^\d+\.\d+\.\d+\.\d+', text): # Level 4
        return 4
    if re.match(r'^\d+\.\d+\.\d+', text):
        return 4

    if re.match(r'^\d+\.\d+\s', text): # Level 3
        return 3

    if re.match(r'^\d+\.?\s', text): # Level 2
        return 2

    if len(text) < 60 and not text.endswith(('.', ',', ':', ';')): # Unnumbered
        if re.match(r'^[A-Z]', text):  # Starts with capital
            return 2
    return 2


# Find the approximate starting position of a heading in the text
def find_heading_position(heading_text: str, full_text: str) -> int:
    """Find position of heading in document."""
    normalized_heading = " ".join(heading_text.split()).lower()
    normalized_full = " ".join(full_text.split()).lower()
    
    pos = normalized_full.find(normalized_heading)
    if pos >= 0:
        return pos
    
    num_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', heading_text)
    if num_match:
        title_part = " ".join(num_match.group(2).split()).lower()
        pos = normalized_full.find(title_part)
        if pos >= 0:
            return pos
    
    return float('inf')


#  Identify and filter out page numbers
def is_page_marker(text: str) -> bool:
    """Check if text is a page number marker."""
    text = text.strip()
    return bool(re.match(r'^(Page\s+)?\d+(\s+of\s+\d+)?$', text, re.IGNORECASE))


# To identify and reject text that looks like a heading but is likely something else
def is_false_heading(text: str) -> bool:
    """
    Check if text matches patterns that indicate it's NOT a valid heading.
    Returns True if it's a false positive (figure caption, body text, etc.)
    """
    text = text.strip()
    
    # Check against known false patterns
    for pattern in FALSE_HEADING_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # Too long to be a heading (likely body text)
    if len(text) > MAX_HEADING_LENGTH:
        return True
    
    # Contains sentence-ending punctuation mid-text (likely body text)
    # Exception: short numbered HEADINGS like "1. OVERVIEW" have ". " + capital,
    # but numbered STEPS like "9. At the 3rd pop-up enter..." should be rejected.
    if re.search(r'[.!?]\s*[A-Z]', text):
        num_match = re.match(r'^\d+(\.\d+)*\.?\s*(.+)$', text)
        if num_match:
            content = num_match.group(2).lstrip('. ').strip()
            # A true numbered heading is SHORT, does NOT end with a full-stop,
            # and does NOT start with an article/preposition or verb phrase.
            _sentence_starters = (
                r'^(At|The|If|In|On|When|After|Before|Once|You|For|To|A|An|'
                r'This|That|It|Click|Enter|Place|Scan|Remove|Pull|Open|Login|'
                r'Close|Select|Press|Wait|Proceed|Ensure)\s'
            )
            is_heading_like = (
                not text.rstrip().endswith('.')
                and len(text.strip()) <= 70
                and not re.match(_sentence_starters, content, re.IGNORECASE)
            )
            if not is_heading_like:
                return True
        else:
            return True
    
    # Contains multiple commas (likely a list or body text)
    if text.count(',') > 2:
        return True
    
    # Starts with lowercase (likely continuation of text)
    if text and text[0].islower():
        return True
    
    # Pure numbers or page-like patterns
    if re.match(r'^[\d\s.,-]+$', text):
        return True
    
    # Contains "..." or excessive dots (TOC artifacts)
    if '...' in text or text.count('.') > 5:
        return True

    # Text ending with a period is a sentence, not a heading
    # (exception: bare section numbers like "1." or "1.2.")
    if text.endswith('.') and not re.match(r'^\d+(\. \d+)*\.$', text.strip()):
        return True

    return False


# To differentiate between a short, standalone heading and a sentence
def is_likely_body_text(text: str, full_text: str) -> bool:
    """
    Check if text appears to be body text rather than a heading.
    Uses context from the full document.
    """
    text = text.strip()
    body_indicators = [
        r'^(The|A|An|This|That|These|Those|It|We|They|In|On|At|For|With|From)\s+\w+\s+\w+',
        r'\s+(is|are|was|were|has|have|had|will|would|could|should|can|may|might)\s+',
    ]
    for indicator in body_indicators:
        if re.search(indicator, text, re.IGNORECASE):
            # But allow if it's a proper numbered heading
            if re.match(r'^\d+(\.\d+)*\s+', text):
                return False
            # Or if it's a known section keyword
            if any(kw in text.lower() for kw in LEVEL_1_KEYWORDS):
                return False
            return True
    return False


# To clean a text chunk before sending it to the LLM.
def preprocess_chunk(chunk: str) -> str:
    """
    Clean up chunk text before sending to LLM.
    Removes problematic content (code blocks, tables, equations) that can
    confuse the model, while preserving heading lines intact.
    """
    chunk = re.sub(r'\n{4,}', '\n\n\n', chunk) # Remove excessive whitespace

    chunk = re.sub(r'[∑∏∫∂√∞≤≥≠±×÷αβγδεθλμσπΣΠ]+', ' ', chunk)  # Remove mathematical symbols

    chunk = re.sub(r'\$[^$]+\$', ' [MATH] ', chunk) # Remove inline LaTeX-like expressions
    chunk = re.sub(r'\\[a-z]+\{[^}]*\}', ' [LATEX] ', chunk, flags=re.IGNORECASE)

    # Remove fenced code blocks (``` ... ```) completely
    chunk = re.sub(r'```[\s\S]*?```', '[CODE BLOCK]', chunk)

    # Collapse markdown tables into a single [TABLE] placeholder.
    # A table is a run of lines that start with | (data rows) or are separator
    # rows like |---|---|. We replace the entire run with one marker so the LLM
    # still gets enough non-empty context and doesn't return malformed output.
    lines = chunk.split('\n')
    cleaned_lines = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        is_table_row = (
            re.match(r'^\|', stripped) and re.search(r'\|', stripped[1:])
        ) or re.match(r'^\|[-| :]+\|', stripped)
        if is_table_row:
            if not in_table:
                cleaned_lines.append('[TABLE]')
                in_table = True
            # Skip actual table lines (replaced by single [TABLE] marker)
        else:
            in_table = False
            # Replace lines that are purely code (start with code keyword at line start)
            if re.match(r'^\s{0,4}(import|from|print|def|class|plt\.|tc\.|model)\b', line):
                cleaned_lines.append('[CODE LINE]')
            # Truncate very long non-heading lines
            elif len(stripped) > 300 and not stripped.startswith('#'):
                cleaned_lines.append(stripped[:200] + '...')
            else:
                cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


# To act as a fallback mechanism for finding headings if the LLM fails.
def extract_headings_regex(chunk: str) -> list:
    """
    Fallback regex-based heading extraction when LLM fails.
    Supports both markdown # headings and numbered headings.
    Returns list of heading dicts.
    """
    headings = []
    lines = chunk.split('\n')
    markdown_heading_re = re.compile(
        r'^(#{1,6})\s+\*{0,2}\s*(.*?)\s*\*{0,2}\s*$'
    )
    # Pre-build a set of line indices that are within 2 lines of an image reference
    # (captions often appear one blank line after the image tag)
    image_re = re.compile(r'^!\[.*?\]\(.*?\)\s*$')
    lines_after_image = set()
    for idx, ln in enumerate(lines):
        if image_re.match(ln.strip()):
            for offset in (1, 2):
                if idx + offset < len(lines):
                    lines_after_image.add(idx + offset)
    heading_patterns = [
        (r'^(\d+)\s+([A-Z][A-Za-z][A-Za-z\s\-&()]+)$', 2),
        (r'^(\d+\.)\s*([A-Z][A-Za-z][A-Za-z\s\-&()]+)$', 2),
        (r'^(\d+\.\d+)\s+([A-Z][A-Za-z][A-Za-z\s\-&()]+)$', 3),
        (r'^(\d+\.\d+\.)\s*([A-Z][A-Za-z][A-Za-z\s\-&()]+)$', 3),
        (r'^(\d+\.\d+\.\d+)\s+([A-Z][A-Za-z][A-Za-z\s\-&()]+)$', 4),
        (r'^(\d+\.\d+\.\d+\.)\s*([A-Za-z\s\-&()]+)$', 4),
        (r'^(\d+\.\d+\.\d+\.\d+)\s+([A-Za-z\s\-&()]+)$', 4),
        (r'^(Chapter|Part)\s+[\dIVXLC]+[:\s]*(.*)$', 1),
        (r'^(Abstract|Introduction|Conclusion|References|Acknowledgments?|Contents|Bibliography|Appendix|Methodology|Appendices)$', 2),
        (r'^([A-Z][A-Z][A-Z\s]{1,37})$', 2),
        (r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,5})$', 2),
    ]
    for line_idx, line in enumerate(lines):
        raw_line = line
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Skip lines that are image captions (immediately follow an image marker)
        if line_idx in lines_after_image:
            continue

        # Check for markdown heading first
        md_match = markdown_heading_re.match(line)
        if md_match:
            heading_text = md_match.group(2).strip()
            # Strip ALL ** bold markers (e.g. "1. **OVERVIEW**" → "1. OVERVIEW")
            heading_text = re.sub(r'\*+', '', heading_text).strip()
            if heading_text and len(heading_text) >= 2 and not is_false_heading(heading_text):
                # Use content-based level determination: more reliable than
                # markdown hash count when authors use inconsistent heading depths
                # (e.g. #### for top-level numbered sections like "1. OVERVIEW")
                level = determine_heading_level(heading_text)
                headings.append({
                    "text": heading_text,
                    "level": level,
                    "source": "regex"
                })
            continue

        if len(line) > MAX_HEADING_LENGTH:
            continue

        # Skip lines that look like table rows
        if '|' in line:
            continue

        if is_false_heading(line):
            continue

        special_count = sum(1 for c in line if c in '=+*/^{}[]∑∏∫')
        if special_count > 3:
            continue

        for pattern, level in heading_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                heading_text = line
                if re.match(r'^\d+\.\d+\.\d+\.\d+', line):
                    level = 5
                elif re.match(r'^\d+\.\d+\.\d+', line):
                    level = 4
                elif re.match(r'^\d+\.\d+', line):
                    level = 3
                elif re.match(r'^\d+\.?\s', line):
                    level = 2

                headings.append({
                    "text": heading_text,
                    "level": level,
                    "source": "regex"
                })
                break

    return headings


# To prepare text for accurate duplicate detection.
def normalize_for_dedup(text):
    """Normalize text for duplicate detection - handles different dash chars, etc."""
    text = text.lower()
    text = re.sub(r'[–—−‐‑‒―]', '-', text)
    text = re.sub(r'\s*-\s*', '-', text)
    text = ' '.join(text.split())
    text = text.strip('.:;,')
    return text


# find the exact start and end character positions of a heading line.
def find_heading_in_original(heading_text: str, full_text: str, search_start: int = 0) -> tuple:
    """
    Find the exact position of a heading in the original text.
    Handles markdown headings with # prefixes and **bold** wrappers.
    Returns (start_pos, end_pos) of the heading line, or (-1, -1) if not found.
    """
    search_area = full_text[search_start:]

    # Try markdown heading pattern: ^#{1,6} **text** or ^#{1,6} text
    md_pattern = re.compile(
        r'^#{1,6}\s*\*{0,2}\s*' + re.escape(heading_text.strip()) + r'\s*\*{0,2}\s*$',
        re.MULTILINE | re.IGNORECASE
    )
    match = md_pattern.search(search_area)
    if match:
        return (search_start + match.start(), search_start + match.end())

    # Try direct text match (no # prefix)
    heading_escaped = re.escape(heading_text.strip())
    match = re.search(heading_escaped, search_area, re.IGNORECASE)
    if match:
        return (search_start + match.start(), search_start + match.end())

    # Try bold-wrapped variant: **heading_text**
    bold_pattern = re.escape(f'**{heading_text.strip()}**')
    match = re.search(bold_pattern, search_area, re.IGNORECASE)
    if match:
        return (search_start + match.start(), search_start + match.end())

    if len(heading_text) > 30:
        short_pattern = re.escape(heading_text[:30].strip())
        match = re.search(short_pattern, search_area, re.IGNORECASE)
        if match:
            return (search_start + match.start(), search_start + match.end())

    num_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', heading_text)
    if num_match:
        title_part = num_match.group(2).strip()
        title_escaped = re.escape(title_part)
        match = re.search(title_escaped, search_area, re.IGNORECASE)
        if match:
            return (search_start + match.start(), search_start + match.end())

    return (-1, -1)




# PRINT HELPERS
def print_header(text: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_step(step_num: int, text: str):
    """Print a step indicator."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 50)


def extract_document_title_from_text(full_text: str) -> dict | None:
    """
    Extract the document title from a work-instruction style markdown table.

    Handles two table formats used in Zebra work-instruction documents:

      Format A (FetchRobotics style) – product name on SAME row as WORK INSTRUCTIONS:
        | WORK INSTRUCTIONS<br>PRODUCT NAME | ... |
        | –<br>ACTION1,<br>ACTION2<br>Work Instruction No. | ... |

      Format B (PTO Kitting style) – product name on SEPARATE row:
        | WORK INSTRUCTIONS | ... |
        | PRODUCT<br>NAME   | ... |
        | Work Instruction No. | ... |

      Format C (inline heading style):
        #### **WORK INSTRUCTIONS Org** PRODUCT TITLE **Work Instruction No. ...**

    Returns a level-1 heading dict, e.g.:
      {"text": "CART CONNECT100 – UNPACK, CHARGE, REPACK", "level": 1, ...}
      {"text": "PTO KITTING PROCESS", "level": 1, ...}
    """
    lines = full_text.split('\n')

    # Format C: inline markdown heading containing WORK INSTRUCTIONS
    # e.g. #### **WORK INSTRUCTIONS Zebra Technologies** ROLLERTOP (RT)100 – UNPACK, CHARGE, REPACK **Work Instruction No. ...
    for line in lines:
        stripped = line.strip()
        if re.match(r'^#{1,6}\s*\*\*WORK\s+INSTRUCTIONS', stripped, re.IGNORECASE):
            m = re.search(
                r'\*\*WORK\s+INSTRUCTIONS[^*]*\*\*\s+(.+?)\s+\*\*Work\s+Instruction',
                stripped, re.IGNORECASE
            )
            if m:
                title = m.group(1).strip()
                if title:
                    return {"text": title, "level": 1, "source": "title_parse", "chunk_index": 0}
    product_name = None
    action_parts = []
    in_title_table = False

    for line in lines:
        stripped = line.strip()

        if not stripped.startswith('|'):
            if in_title_table and product_name:
                break
            continue

        # Skip separator rows like |---|---|
        if re.match(r'^\|[-| :]+\|$', stripped):
            continue

        # Isolate the first cell
        first_cell_match = re.match(r'^\|([^|]+)', stripped)
        if not first_cell_match:
            continue
        first_cell = first_cell_match.group(1).strip()

        # Expand <br> into parts
        br_parts = [p.strip() for p in re.split(r'<br\s*/?>', first_cell, flags=re.IGNORECASE)]
        br_parts = [p for p in br_parts if p]

        if not in_title_table:
            # Detect the WORK INSTRUCTIONS row (it may be any br_part on the row)
            wi_idx = None
            for idx, part in enumerate(br_parts):
                if re.match(r'^WORK\s+INSTRUCTIONS?$', part, re.IGNORECASE):
                    wi_idx = idx
                    break
            if wi_idx is not None:
                in_title_table = True
                # Format A: product name is the next br_part on the same row
                if wi_idx + 1 < len(br_parts):
                    product_name = br_parts[wi_idx + 1].strip()
            continue

        # --- Inside the title table ---

        # Skip rows that are clearly header/metadata labels
        if br_parts and re.match(
            r'^(CONFIDENTIAL|Work Instruction No\.?|Revision No\.?|WORK INSTRUCTIONS?)',
            br_parts[0], re.IGNORECASE
        ):
            continue

        # Subtitle row (Format A): first br_part is a dash variant
        if br_parts and re.match(r'^[\-\u2013\u2014\u2212]$', br_parts[0]):
            for part in br_parts[1:]:
                if re.match(r'Work Instruction', part, re.IGNORECASE):
                    break
                clean = part.rstrip(',').strip()
                if clean:
                    action_parts.append(clean)
            break  # fully captured

        # Format B: product name is on a separate row — capture it
        if product_name is None:
            name_parts = []
            for part in br_parts:
                if re.match(r'^(Work Instruction No\.?|Revision No\.?)', part, re.IGNORECASE):
                    break
                name_parts.append(part)
            if name_parts:
                product_name = ' '.join(name_parts)
            continue

        # product_name found and no subtitle row → this is a Format-B doc, stop here
        if re.match(r'^(Work Instruction No\.?|Revision No\.?)', br_parts[0] if br_parts else '', re.IGNORECASE):
            break

    if product_name and action_parts:
        title = f"{product_name} \u2013 {', '.join(action_parts)}"
        return {"text": title, "level": 1, "source": "title_parse", "chunk_index": 0}

    if product_name:
        return {"text": product_name, "level": 1, "source": "title_parse", "chunk_index": 0}

    return None


def print_metrics_table(metrics: dict):
    """Print a formatted metrics table."""
    print(f"\n{'='*60}")
    print("                    EXTRACTION METRICS")
    print(f"{'='*60}")
    
    print(f"{'Document Statistics':<35}{'Value':>20}")
    print(f"{'-'*55}")
    print(f"{'  Document Length':<35}{metrics['doc_length']:>15,} chars")
    print(f"{'  Total Chunks Processed':<35}{metrics['total_chunks']:>20}")
    print(f"{'  Chunk Size':<35}{metrics['chunk_size']:>20}")
    
    print(f"\n{'Heading Extraction':<35}{'Count':>20}")
    print(f"{'-'*55}")
    print(f"{'  Raw Headings Extracted':<35}{metrics['raw_headings']:>20}")
    print(f"{'  Valid Unique Headings':<35}{metrics['valid_headings']:>20}")
    print(f"{'  Rejected (False Pattern)':<35}{metrics['rejected_false']:>20}")
    print(f"{'  Rejected (Body Text)':<35}{metrics['rejected_body']:>20}")
    print(f"{'  Rejected (Duplicate)':<35}{metrics['rejected_duplicate']:>20}")
    print(f"{'  Rejected (Not in Text)':<35}{metrics['rejected_not_found']:>20}")
    
    print(f"\n{'Heading Levels Breakdown':<35}{'Count':>20}")
    print(f"{'-'*55}")
    for level, count in sorted(metrics['level_counts'].items()):
        print(f"{'  Level ' + str(level):<35}{count:>20}")
    
    print(f"\n{'Output Statistics':<35}{'Value':>20}")
    print(f"{'-'*55}")
    print(f"{'  Output Chunks Created':<35}{metrics['output_chunks']:>20}")
    print(f"{'  LLM Successes':<35}{metrics['llm_success']:>20}")
    print(f"{'  Regex Fallbacks Used':<35}{metrics['regex_fallbacks']:>20}")
    
    if metrics['raw_headings'] > 0:
        accuracy = (metrics['valid_headings'] / metrics['raw_headings']) * 100
        print(f"\n{'  Validation Rate':<35}{accuracy:>19.1f}%")
    
    print(f"{'='*60}\n")


# def compute_ancestral_path(sorted_headings: list) -> list:
#     """
#     Given a list of headings sorted by document position, compute the full
#     ancestral path for each heading (e.g. 'Root > Parent > Child').
#     Returns the same list with 'ancestral_path' added to each dict.
#     """
#     ancestor_stack = []  # list of dicts with 'level' and 'text'
#     result = []

#     for h in sorted_headings:
#         level = h.get("level", 2)
#         text = h.get("text", "")

#         # Pop stack entries at the same or deeper level
#         while ancestor_stack and ancestor_stack[-1]["level"] >= level:
#             ancestor_stack.pop()

#         # Build the breadcrumb path
#         if ancestor_stack:
#             path = " > ".join([a["text"] for a in ancestor_stack] + [text])
#         else:
#             path = text  # Root heading has no ancestors

#         h_copy = dict(h)
#         h_copy["ancestral_path"] = path
#         result.append(h_copy)

#         # Push current heading onto ancestor stack
#         ancestor_stack.append({"level": level, "text": text})

#     return result


# def scan_for_missed_headings(full_text: str, existing_headings: list) -> list:
#     """
#     Scan the full document text for headings that might have been missed.
#     Handles both markdown # headings and numbered headings.
#     Returns list of heading dicts for headings not already in existing_headings.
#     """
#     missed = []

#     existing_normalized = set()
#     for h in existing_headings:
#         norm = ' '.join(h["text"].lower().split())
#         existing_normalized.add(norm)
#         num_match = re.match(r'^(\d+(?:\.\d+)*)', h["text"])
#         if num_match:
#             existing_normalized.add(num_match.group(1))

#     # Scan for markdown # headings first (highest priority for markdown docs)
#     md_heading_re = re.compile(
#         r'^(#{1,6})\s+\*{0,2}\s*(.*?)\s*\*{0,2}\s*$',
#         re.MULTILINE
#     )
#     for match in md_heading_re.finditer(full_text):
#         hashes = match.group(1)
#         text = match.group(2).strip()
#         # Strip remaining bold markers
#         text = re.sub(r'\*+', '', text).strip()
#         if not text or len(text) < 2:
#             continue

#         norm = ' '.join(text.lower().split())
#         if norm in existing_normalized:
#             continue

#         if is_false_heading(text):
#             continue

#         level = len(hashes)
#         missed.append({
#             "text": text,
#             "level": level,
#             "source": "full_scan"
#         })
#         existing_normalized.add(norm)

#     # Scan for numbered headings (for non-markdown content)
#     heading_patterns = [
#         (re.compile(r'^[ \t]*(\d+)\.\s+([A-Z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 2),
#         (re.compile(r'^[ \t]*(\d+)\s+([A-Z][A-Za-z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 2),
#         (re.compile(r'^[ \t]*(\d+\.\d+)\.?\s+([A-Z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 3),
#         (re.compile(r'^[ \t]*(\d+\.\d+\.\d+)\.?\s+([A-Z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 4),
#         (re.compile(r'^[ \t]*(\d+\.\d+\.\d+\.\d+)\.?\s+([A-Z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 5),
#     ]
    
#     standalone_headings = [
#         "Methodology", "Appendices", "Appendix", "Future Recommendations",
#         "Implementation Results", "Summary", "Overview", "Background",
#         "Discussion", "Results", "Analysis", "Findings"
#     ]
    
#     for heading_pattern, default_level in heading_patterns:
#         for match in heading_pattern.finditer(full_text):
#             number = match.group(1)
#             title = match.group(2).strip()
#             full_heading = f"{number} {title}"
            
#             norm_heading = ' '.join(full_heading.lower().split())
            
#             if norm_heading in existing_normalized:
#                 continue
            
#             if is_false_heading(full_heading):
#                 continue
            
#             if len(title) < 3:
#                 continue
            
#             level = determine_heading_level(full_heading)
            
#             missed.append({
#                 "text": full_heading,
#                 "level": level,
#                 "source": "full_scan"
#             })
            
#             existing_normalized.add(norm_heading)
    
#     for heading in standalone_headings:
#         pattern = re.compile(r'^[\s]*(' + re.escape(heading) + r')[\s]*$', re.MULTILINE | re.IGNORECASE)
#         for match in pattern.finditer(full_text):
#             matched_text = match.group(1).strip()
#             norm = ' '.join(matched_text.lower().split())
            
#             if norm in existing_normalized:
#                 continue
            
#             if is_false_heading(matched_text):
#                 continue
            
#             missed.append({
#                 "text": matched_text,
#                 "level": 2,
#                 "source": "full_scan"
#             })
#             existing_normalized.add(norm)
    
#     return missed