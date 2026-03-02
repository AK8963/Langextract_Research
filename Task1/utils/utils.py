import re
from difflib import SequenceMatcher
import sys

# Import configuration
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    LEVEL_1_KEYWORDS, FALSE_HEADING_PATTERNS, MAX_HEADING_LENGTH
)


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


def determine_heading_level(text: str) -> int:
    """Determine heading level from text pattern."""
    text = text.strip()
    
    # Level 1: Document titles, chapters
    if re.match(r'^(Chapter|Part)\s+', text, re.IGNORECASE):
        return 1
    if any(kw in text.lower() for kw in LEVEL_1_KEYWORDS):
        if not re.match(r'^\d+\.', text):  # Not numbered
            return 1
    
    # Level 5: X.X.X.X.X (deep nesting)
    if re.match(r'^\d+\.\d+\.\d+\.\d+\.\d+', text):
        return 5
    
    # Level 4: X.X.X.X or X.X.X (sub-subsections)
    if re.match(r'^\d+\.\d+\.\d+\.\d+', text):
        return 4
    if re.match(r'^\d+\.\d+\.\d+', text):
        return 4
    
    # Level 3: X.X (subsections)
    if re.match(r'^\d+\.\d+\s', text):
        return 3
    
    # Level 2: X. or X (major sections)
    if re.match(r'^\d+\.?\s', text):
        return 2
    
    # Unnumbered but standalone title-like text (short, no punctuation at end)
    if len(text) < 60 and not text.endswith(('.', ',', ':', ';')):
        if re.match(r'^[A-Z]', text):  # Starts with capital
            return 2
    
    return 2  # Default


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


def is_page_marker(text: str) -> bool:
    """Check if text is a page number marker."""
    text = text.strip()
    return bool(re.match(r'^(Page\s+)?\d+(\s+of\s+\d+)?$', text, re.IGNORECASE))


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
    if re.search(r'[.!?]\s+[A-Z]', text):
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
    
    return False


def is_likely_body_text(text: str, full_text: str) -> bool:
    """
    Check if text appears to be body text rather than a heading.
    Uses context from the full document.
    """
    text = text.strip()
    
    # Common body text indicators
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


def preprocess_chunk(chunk: str) -> str:
    """
    Clean up chunk text before sending to LLM.
    Removes problematic content that can confuse the model.
    """
    # Remove excessive whitespace
    chunk = re.sub(r'\n{4,}', '\n\n\n', chunk)
    
    # Remove mathematical equations more aggressively
    chunk = re.sub(r'[∑∏∫∂√∞≤≥≠±×÷αβγδεθλμσπΣΠ]+', ' ', chunk)
    chunk = re.sub(r'\b[a-z]\s*[=<>]\s*[a-z0-9\s+\-*/^]+', ' [FORMULA] ', chunk, flags=re.IGNORECASE)
    
    # Remove long sequences of special characters (equations, formulas)
    chunk = re.sub(r'[=+\-*/^_{}\[\]()]{10,}', ' [EQUATION] ', chunk)
    
    # Remove inline LaTeX-like expressions
    chunk = re.sub(r'\$[^$]+\$', ' [MATH] ', chunk)
    chunk = re.sub(r'\\[a-z]+\{[^}]*\}', ' [LATEX] ', chunk, flags=re.IGNORECASE)
    
    # Remove code blocks
    chunk = re.sub(r'(import|from|print|def|class|for|while|if|else)\s+[\w\s.(),=\'"\[\]]+', ' [CODE] ', chunk)
    
    # Remove algorithm pseudocode markers
    chunk = re.sub(r'Algorithm\s+\d+[:\s].*?(?=\n\n|$)', ' [ALGORITHM] ', chunk, flags=re.DOTALL)
    
    # Remove very long lines (likely tables or code)
    lines = chunk.split('\n')
    cleaned_lines = []
    for line in lines:
        if re.match(r'^\s*(import|from|print|def|class|plt\.|tc\.|model)', line):
            cleaned_lines.append(' [CODE LINE] ')
        elif len(line) > 300:
            cleaned_lines.append(line[:200] + '...')
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def extract_headings_regex(chunk: str) -> list:
    """
    Fallback regex-based heading extraction when LLM fails.
    Returns list of heading dicts.
    """
    headings = []
    lines = chunk.split('\n')
    
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
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3 or len(line) > MAX_HEADING_LENGTH:
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


def scan_for_missed_headings(full_text: str, existing_headings: list) -> list:
    """
    Scan the full document text for numbered headings that might have been missed.
    Returns list of heading dicts for headings not already in existing_headings.
    """
    missed = []
    
    existing_normalized = set()
    for h in existing_headings:
        norm = ' '.join(h["text"].lower().split())
        existing_normalized.add(norm)
        num_match = re.match(r'^(\d+(?:\.\d+)*)', h["text"])
        if num_match:
            existing_normalized.add(num_match.group(1))
    
    heading_patterns = [
        (re.compile(r'^[ \t]*(\d+)\.\s+([A-Z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 2),
        (re.compile(r'^[ \t]*(\d+)\s+([A-Z][A-Za-z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 2),
        (re.compile(r'^[ \t]*(\d+\.\d+)\.?\s+([A-Z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 3),
        (re.compile(r'^[ \t]*(\d+\.\d+\.\d+)\.?\s+([A-Z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 4),
        (re.compile(r'^[ \t]*(\d+\.\d+\.\d+\.\d+)\.?\s+([A-Z][A-Za-z0-9 \t\-&()]+)[ \t]*$', re.MULTILINE), 5),
    ]
    
    standalone_headings = [
        "Methodology", "Appendices", "Appendix", "Future Recommendations",
        "Implementation Results", "Summary", "Overview", "Background",
        "Discussion", "Results", "Analysis", "Findings"
    ]
    
    for heading_pattern, default_level in heading_patterns:
        for match in heading_pattern.finditer(full_text):
            number = match.group(1)
            title = match.group(2).strip()
            full_heading = f"{number} {title}"
            
            norm_heading = ' '.join(full_heading.lower().split())
            
            if norm_heading in existing_normalized:
                continue
            
            if is_false_heading(full_heading):
                continue
            
            if len(title) < 3:
                continue
            
            level = determine_heading_level(full_heading)
            
            missed.append({
                "text": full_heading,
                "level": level,
                "source": "full_scan"
            })
            
            existing_normalized.add(norm_heading)
    
    for heading in standalone_headings:
        pattern = re.compile(r'^[\s]*(' + re.escape(heading) + r')[\s]*$', re.MULTILINE | re.IGNORECASE)
        for match in pattern.finditer(full_text):
            matched_text = match.group(1).strip()
            norm = ' '.join(matched_text.lower().split())
            
            if norm in existing_normalized:
                continue
            
            if is_false_heading(matched_text):
                continue
            
            missed.append({
                "text": matched_text,
                "level": 2,
                "source": "full_scan"
            })
            existing_normalized.add(norm)
    
    return missed


def normalize_for_dedup(text):
    """Normalize text for duplicate detection - handles different dash chars, etc."""
    text = text.lower()
    text = re.sub(r'[–—−‐‑‒―]', '-', text)
    text = re.sub(r'\s*-\s*', '-', text)
    text = ' '.join(text.split())
    text = text.strip('.:;,')
    return text


def find_heading_in_original(heading_text: str, full_text: str, search_start: int = 0) -> tuple:
    """
    Find the exact position of a heading in the original text.
    Returns (start_pos, end_pos) of the heading, or (-1, -1) if not found.
    """
    heading_escaped = re.escape(heading_text.strip())
    match = re.search(heading_escaped, full_text[search_start:], re.IGNORECASE)
    if match:
        return (search_start + match.start(), search_start + match.end())
    
    if len(heading_text) > 30:
        short_pattern = re.escape(heading_text[:30].strip())
        match = re.search(short_pattern, full_text[search_start:], re.IGNORECASE)
        if match:
            return (search_start + match.start(), search_start + match.end())
    
    num_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', heading_text)
    if num_match:
        title_part = num_match.group(2).strip()
        title_escaped = re.escape(title_part)
        match = re.search(title_escaped, full_text[search_start:], re.IGNORECASE)
        if match:
            return (search_start + match.start(), search_start + match.end())
    
    return (-1, -1)


# ==========================================================
# PRINT HELPERS
# ==========================================================
def print_header(text: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_step(step_num: int, text: str):
    """Print a step indicator."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 50)


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
