"""
run4.py

Processes a JSON/JSONL file of text chunks using a cascading context
approach with an Ollama model. It extracts key lines from each chunk,
builds a growing context, and enriches the metadata of subsequent chunks.

At the end of the run, it collects detailed performance and processing
metrics and generates a formatted Excel report using the
'make_results_excel.py' script.

Run from the command line, for example:
    python run4.py input_data.json output_data.json
"""

import json
import sys
import copy
import re
import requests
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Note: Excel report generation removed — output will be written to JSON only.


# ============ Configuration ============
# Extract only 1 new line per chunk by default to keep context minimal
DEFAULT_LINES_PER_LEVEL = 1      # NEW lines to extract from each chunk's content
# Disable trimming by default (0 or None disables trimming in trim_to_chars)
DEFAULT_MAX_SUMMARY_CHARS = 0    # 0 = no trimming

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma2:2b"

def call_ollama(prompt: str, max_tokens: int = 400) -> Dict[str, Any]:
    """
    Call Ollama API with the configured model.

    Args:
        prompt: The prompt to send to the model.
        max_tokens: Maximum tokens in the response.

    Returns:
        The full JSON response dictionary from the Ollama API,
        or a dictionary with an 'error' key if the call fails.
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1,  # Very low for deterministic extraction
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"   Warning: Ollama API error: {e}")
        return {"error": str(e), "response": ""}

def extract_snippets_with_ollama(
    text: str,
    headings: List[str],
    num_lines: int,
    max_chars: int = 800
) -> Tuple[str, Dict[str, Any]]:
    """
    Use Ollama to extract exact snippets from text.
    Separates existing context from raw content, keeps ALL context, and extracts NEW lines.

    Args:
        text: Text to extract from.
        headings: List of relevant headings for context.
        num_lines: Number of NEW lines to extract.
        max_chars: Maximum characters for total output.

    Returns:
        A tuple containing:
        - The extracted snippets as formatted text.
        - The statistics dictionary from the Ollama call.
    """
    if not text.strip():
        return "", {}

    heading_context = " > ".join(h.replace(".....", "").strip() for h in headings[:2]) if headings else "Document"

    context_lines, raw_content_lines = split_context_and_content(text)
    kept_context = "\n".join(context_lines)

    ollama_stats = {}
    new_extractions = ""

    if raw_content_lines and num_lines > 0:
        raw_text = "\n".join(raw_content_lines)
        new_extractions, ollama_stats = extract_new_lines_with_ollama(raw_text, heading_context, num_lines)
    # If the extractor returned nothing, fall back to a single metadata heading line
    if not new_extractions:
        if headings:
            first_h = headings[0].replace(".....", "").strip()
            if first_h:
                new_extractions = f"{heading_context}: {first_h}"
    
    # Only keep existing explicit context lines and the NEW extractions.
    # Do NOT append the full raw content here — that caused growth and duplication.
    parts = []
    if kept_context:
        parts.append(kept_context)
    if new_extractions:
        parts.append(new_extractions)

    result = "\n".join(part for part in parts if part)
    # Trim to the configured maximum to avoid unbounded growth
    # Deduplicate identical lines while preserving order
    deduped_lines = []
    seen = set()
    for line in result.splitlines():
        ls = line.strip()
        if not ls: continue
        if ls in seen: continue
        seen.add(ls)
        deduped_lines.append(line)
    result = "\n".join(deduped_lines)
    result = trim_to_chars(result, max_chars)
    
    return result, ollama_stats

def extract_new_lines_with_ollama(raw_text: str, heading_context: str, num_lines: int) -> Tuple[str, Dict[str, Any]]:
    """
    Use Ollama to extract NEW important lines from raw content.

    Returns:
        A tuple containing:
        - The extracted lines, formatted.
        - The statistics dictionary from the Ollama call.
    """
    if not raw_text.strip() or num_lines <= 0:
        return "", {}

    prompt = f"""Extract exactly {num_lines} important lines from this text.
FORMAT each line as:
{heading_context}: <exact text from source>

RULES:
- Copy text EXACTLY - no paraphrasing
- One extraction per line
- Include key facts, numbers, data
- NO introductions, NO markdown, NO numbering
- Just the formatted lines

Text:
{raw_text[:1500]}

Output:"""
    ollama_response = call_ollama(prompt, max_tokens=400)
    result_text = ollama_response.get("response", "")

    if not result_text or ollama_response.get("error"):
        # Fallback: take first N meaningful lines
        return fallback_extract_new(raw_text, heading_context, num_lines), ollama_response

    cleaned_text = clean_new_extractions(result_text, heading_context, num_lines)
    return cleaned_text, ollama_response

# ==============================================================================
# NOTE: The helper functions below are kept as they were in the original script,
# as they are required for text processing and data structuring.
# (No metric collection logic is needed in these helpers)
# ==============================================================================

def split_context_and_content(text: str) -> Tuple[List[str], List[str]]:
    context_lines, raw_content_lines = [], []
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        if re.match(r'^[A-Za-z0-9\s>]+:\s', line):
            context_lines.append(line)
        else:
            raw_content_lines.append(line)
    return context_lines, raw_content_lines

def clean_new_extractions(result: str, heading_context: str, num_lines: int) -> str:
    lines, cleaned = result.strip().splitlines(), []
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10: continue
        skip_patterns = ["here are", "extracted", "following", "output:", "```", "note:"]
        if any(p in line.lower() for p in skip_patterns): continue
        line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        line = re.sub(r'^\s*>\s*', '', line)
        line = re.sub(r'^\s*\d+\.\s*', '', line)
        line = re.sub(r'^\s*[-•]\s*', '', line).strip()
        if not line: continue
        if ": " not in line: line = f"{heading_context}: {line}"
        cleaned.append(line)
        if len(cleaned) >= num_lines: break
    return "\n".join(cleaned)

def fallback_extract_new(raw_text: str, heading_context: str, num_lines: int) -> str:
    lines = [l.strip() for l in raw_text.splitlines() if l.strip() and len(l.strip()) > 10]
    result_lines = []
    for line in lines:
        if re.match(r'^page\s+\d+$', line.lower()): continue
        result_lines.append(f"{heading_context}: {line[:150]}")
        if len(result_lines) >= num_lines: break
    return "\n".join(result_lines)


def trim_to_chars(text: str, max_chars: int) -> str:
    """Trim text to at most `max_chars` characters, keeping the most recent content."""
    if not text:
        return ""
    if max_chars is None or max_chars <= 0:
        return text
    text = text.strip()
    if len(text) <= max_chars:
        return text
    # Keep the first max_chars characters (preserve initial headings/context)
    return text[:max_chars]


def remove_leading_overlap(context: str, original: str) -> str:
    """If `original` starts with lines already present at the end of `context`, remove that overlap.

    This prevents duplicating the same text when concatenating context + original.
    """
    if not context or not original:
        return original
    ctx_lines = [l.strip() for l in context.splitlines() if l.strip()]
    orig_lines = [l for l in original.splitlines() if l.strip()]
    if not ctx_lines or not orig_lines:
        return original

    max_check = min(len(ctx_lines), len(orig_lines), 50)
    overlap = 0
    for k in range(max_check, 0, -1):
        if ctx_lines[-k:] == [l.strip() for l in orig_lines[:k]]:
            overlap = k
            break
    if overlap:
        return "\n".join(orig_lines[overlap:])
    return original

def load_entries(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f: raw = f.read()
    try:
        data = json.loads(raw)
        if not isinstance(data, list): data = [data]
    except json.JSONDecodeError:
        data = []
        for line in raw.splitlines():
            if not line.strip(): continue
            try: data.append(json.loads(line))
            except json.JSONDecodeError: continue
    return [entry for entry in data if isinstance(entry, dict)]

def find_chunk_key(entry: Dict) -> Optional[str]:
    for key in entry:
        if isinstance(key, str) and key.lower().startswith("chunk_id"):
            if isinstance(entry[key], dict): return key
    return None

def chunk_number_from_key(chunk_key: str) -> Optional[int]:
    if not isinstance(chunk_key, str): return None
    suffix = chunk_key[len("chunk_id"):]
    return int(suffix) if suffix.isdigit() else None

def get_text_field(entry: Dict) -> str:
    return entry.get("Text") or entry.get("text") or entry.get("extraction_text") or ""

def set_text_field(entry: Dict, value: str) -> None:
    for key in ["Text", "text", "extraction_text"]:
        if key in entry:
            entry[key] = value
            return
    entry["Text"] = value

def flatten_heading_values(metadata: Any) -> List[str]:
    values = []
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, str) and "heading" in str(key).lower():
                    stripped = value.strip()
                    if stripped and stripped not in values: values.append(stripped)
                else: walk(value)
        elif isinstance(node, list):
            for item in node: walk(item)
    walk(metadata)
    return values

def rebuild_metadata_with_accumulated_headings(original_meta: Dict, accumulated_headings: List[str]) -> Dict:
    new_meta = {}
    for i, heading in enumerate(accumulated_headings, start=1):
        new_meta[f"Main Heading {i}"] = heading
    for key, value in original_meta.items():
        if "heading" in key.lower() and isinstance(value, str): continue
        if key not in new_meta: new_meta[key] = value
    return new_meta

def write_output(path: str, rows: List[Dict]) -> None:
    output_path = Path(path)
    if output_path.suffix.lower() == ".jsonl":
        with open(output_path, "w", encoding="utf-8") as f:
            for row in rows: f.write(json.dumps(row, ensure_ascii=False) + "\n")
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)

def is_context_line(line: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9\s>]+:\s', line))

# =========================================================
# Main Processing Function with Metrics Collection
# =========================================================

def run(
    input_path: str,
    output_path: str = "structured2_chunks.json",
    lines_per_level: int = DEFAULT_LINES_PER_LEVEL,
    max_summary_chars: int = DEFAULT_MAX_SUMMARY_CHARS
):
    """
    Main processing function with CASCADING logic using Ollama and metrics generation.
    """
    # Processing start time (kept only if needed)
    # start_time = time.time()

    entries = load_entries(input_path)
    if not entries:
        print("Error: No valid chunks found.")
        return

    chunk_items = []
    total_doc_length = 0
    for entry in entries:
        chunk_key = find_chunk_key(entry)
        if not chunk_key: continue
        chunk_num = chunk_number_from_key(chunk_key)
        if chunk_num is None: continue
        chunk_items.append((chunk_num, chunk_key, entry))
        total_doc_length += len(get_text_field(entry))

    if not chunk_items:
        print("Error: No valid chunk_idN entries found.")
        return

    chunk_items.sort(key=lambda x: x)
    total_chunks = len(chunk_items)

    # basic info
    total_chunks = total_chunks

    print(f"Found {total_chunks} chunks to process from '{input_path}'")
    print(f"Using Ollama model: {OLLAMA_MODEL}")
    print(f"Settings: lines_per_level={lines_per_level}, max_chars={max_summary_chars}")
    print("=" * 60)

    output_rows = []
    previous_modified_text = ""
    previous_headings = []
    accumulated_headings = []

    # ---- 2. Process chunks and collect metrics ----
    for index, (chunk_num, chunk_key, original_entry) in enumerate(chunk_items):
        entry = copy.deepcopy(original_entry)
        chunk_meta = entry.get(chunk_key, {}) or {}
        original_text = get_text_field(entry)
        current_headings = flatten_heading_values(chunk_meta)

        if index == 0:
            print(f"   chunk_id{chunk_num}: First chunk - untouched")
            output_entry = copy.deepcopy(original_entry)
            # If the first chunk has no text, use a short heading-based fallback
            if not original_text.strip():
                heading_fallback = "\n".join(h for h in current_headings[:3])
                output_entry["Original Text"] = heading_fallback
                previous_modified_text = heading_fallback
            else:
                output_entry["Original Text"] = original_text
                previous_modified_text = original_text
            previous_headings = current_headings.copy()
            accumulated_headings = current_headings.copy()
            output_entry[chunk_key] = rebuild_metadata_with_accumulated_headings(chunk_meta, accumulated_headings)
            output_entry.pop("Metadata", None); output_entry.pop("metadata", None)
        else:
            chunk_start_time = time.time()
            # Trim the previous modified text before sending to the extractor
            prev_trimmed = trim_to_chars(previous_modified_text, max_summary_chars)
            context_text, ollama_stats = extract_snippets_with_ollama(
                prev_trimmed, previous_headings, lines_per_level, max_summary_chars
            )
            chunk_end_time = time.time()
            duration = chunk_end_time - chunk_start_time

            # (metrics collection removed)
            input_tokens = ollama_stats.get("prompt_eval_count", 0)
            output_tokens = ollama_stats.get("eval_count", 0)
            is_success = "error" not in ollama_stats

            # Remove leading overlap to avoid duplicating content between context and original_text
            if context_text and original_text.strip():
                original_without_overlap = remove_leading_overlap(context_text, original_text)
                if original_without_overlap.strip():
                    modified_text = f"{context_text}\n{original_without_overlap}"
                else:
                    modified_text = context_text
            else:
                modified_text = context_text or original_text
            entry["Original Text"] = original_text
            set_text_field(entry, modified_text)

            for h in current_headings:
                if h and h not in accumulated_headings:
                    accumulated_headings.append(h)

            entry[chunk_key] = rebuild_metadata_with_accumulated_headings(chunk_meta, accumulated_headings)
            output_entry = entry
            output_entry.pop("Metadata", None); output_entry.pop("metadata", None)

            # Keep previous_modified_text trimmed to avoid unbounded growth
            previous_modified_text = trim_to_chars(modified_text, max_summary_chars)
            previous_headings = current_headings.copy()
            
            context_line_count = len([l for l in context_text.splitlines() if l.strip()])
            print(f"   chunk_id{chunk_num}: Context={context_line_count} lines, Total Headings={len(accumulated_headings)}")

        output_rows.append(output_entry)

    # ---- 3. Finalize Metrics and Generate Excel Report ----
    write_output(output_path, output_rows)

    print("=" * 60)
    print(f"SUCCESS! Processed {len(output_rows)} chunks.")
    print(f"Saved processed JSON to: {output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cascading chunk extraction with Ollama and Excel reporting.")
    parser.add_argument("input", nargs="?", default="sales_report_gemma8.json",
                        help="Input JSON/JSONL file")
    parser.add_argument("output", nargs="?", default="structured2_chunks.json",
                        help="Output file path for the processed JSON")
    parser.add_argument("--lines-per-level", "-l", type=int, default=DEFAULT_LINES_PER_LEVEL,
                        help=f"NEW lines to extract per chunk (default: {DEFAULT_LINES_PER_LEVEL})")
    parser.add_argument("--max-chars", "-m", type=int, default=DEFAULT_MAX_SUMMARY_CHARS,
                        help=f"Max total context chars (0 = no trimming; default: {DEFAULT_MAX_SUMMARY_CHARS})")

    args = parser.parse_args()

    run(
        args.input,
        args.output,
        lines_per_level=args.lines_per_level,
        max_summary_chars=args.max_chars
    )
