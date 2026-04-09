import langextract as lx
import re
import time
import sys
from langchain_text_splitters import RecursiveCharacterTextSplitter

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.prompts import EXTRACTION_PROMPT, EXTRACTION_EXAMPLES
from config import (
    MODEL_ID, TIMEOUT, MAX_RETRIES, RETRY_DELAY,
    TEXT_SPLITTER_CHUNK_SIZE, TEXT_SPLITTER_CHUNK_OVERLAP,
    VERBOSE, USE_FALLBACK_REGEX
)
from utils.utils import (
    preprocess_chunk, extract_headings_regex,
    is_page_marker, is_false_heading, is_likely_body_text,
    is_valid_heading_in_text, determine_heading_level, normalize_for_dedup,
    find_heading_position, find_heading_in_original,
    extract_document_title_from_text
)
MIN_LLM_CONFIDENCE = 0.55

# To read the content of a Markdown file.
def get_markdown_text(filepath: str) -> str:
    """Read a markdown file and return its text content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text


# To break the entire document into smaller, manageable chunks.
def split_text_into_chunks(full_text: str, doc_length: int) -> tuple:
    """
    Split text into chunks using adaptive chunk sizing.
    Returns (chunks_list, adaptive_chunk_size, adaptive_overlap)
    """
    adaptive_chunk_size = TEXT_SPLITTER_CHUNK_SIZE
    adaptive_overlap = TEXT_SPLITTER_CHUNK_OVERLAP
    
    if doc_length > 500000:
        adaptive_chunk_size = 6000
        adaptive_overlap = 1000
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=adaptive_chunk_size,
        chunk_overlap=adaptive_overlap,
        separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""]
    )
    
    text_chunks = splitter.split_text(full_text)
    return text_chunks, adaptive_chunk_size, adaptive_overlap


def extract_headings_from_chunks(text_chunks: list, adaptive_chunk_size: int, metrics: dict) -> list:
    """
    Extract headings from all chunks using LLM with regex fallback.
    LLM is responsible for extracting headings and providing level attributes.
    Returns list of all extracted headings.
    """
    all_headings = []
    failed_chunks = []
    
    # Initialize LLM tracking metrics
    metrics.setdefault('llm_calls', 0)
    metrics.setdefault('llm_input_tokens', 0)
    metrics.setdefault('llm_output_tokens', 0)
    metrics.setdefault('llm_chunk_times', [])
    metrics.setdefault('llm_total_time', 0.0)
    
    for i, chunk in enumerate(text_chunks):
        chunk_headings = []
        extraction_success = False
        cleaned_chunk = preprocess_chunk(chunk)
        for attempt in range(MAX_RETRIES):
            try:
                input_tokens = len(cleaned_chunk.split())
                chunk_start = time.time()
                
                result = lx.extract(
                    text_or_documents=cleaned_chunk,
                    prompt_description=EXTRACTION_PROMPT,
                    examples=EXTRACTION_EXAMPLES,
                    model_id=MODEL_ID,
                    max_char_buffer=adaptive_chunk_size + 500,
                    fence_output=True,
                    temperature=0.0,
                    language_model_params={
                        "timeout": TIMEOUT,
                        "num_threads": 4,
                    },
                )
                
                chunk_elapsed = time.time() - chunk_start

                chunk_headings = []
                for ext in result.extractions:
                    if ext.extraction_class != "heading":
                        continue
                    raw_text = ext.extraction_text
                    if not raw_text or not raw_text.strip():
                        continue
                    clean_text = re.sub(r'^#{1,6}\s*', '', raw_text.strip())
                    # Strip ALL ** bold markers (handles "1. **OVERVIEW**" → "1. OVERVIEW")
                    clean_text = re.sub(r'\*+', '', clean_text).strip()

                    # Reject obvious false headings immediately (pure numbers, captions, etc.)
                    if is_false_heading(clean_text):
                        continue

                    # If confidence is present and below threshold, skip extraction.
                    conf_attr = getattr(ext, 'attributes', {}).get('confidence')
                    conf_val = None
                    if conf_attr is not None:
                        try:
                            conf_val = float(conf_attr)
                        except Exception:
                            conf_val = None
                    if conf_val is not None and conf_val < MIN_LLM_CONFIDENCE:
                        continue

                    # Require the heading to appear as a standalone line in the chunk.
                    # Handles both plain and **bold** forms: "1. **OVERVIEW**" also matches "1. OVERVIEW".
                    _escaped = re.escape(clean_text)
                    standalone_re = re.compile(
                        r'^(?:#{1,6}\s*)?\*{0,2}\s*' + _escaped + r'\s*\*{0,2}\s*$'
                        r'|^(?:#{1,6}\s*)?\d+\.\s+\*{1,2}' + re.escape(clean_text.split('. ', 1)[-1]) + r'\*{0,2}\s*$',
                        re.MULTILINE
                    )
                    if not standalone_re.search(chunk):
                        if VERBOSE:
                            print(f"    Rejected (not standalone): '{clean_text[:60]}'")
                        continue

                    # Determine level: prefer content-based heuristic (matches what
                    # the regex fallback uses) so levels are consistent across sources.
                    # Fall back to LLM-provided level attribute if heuristic returns None.
                    level = determine_heading_level(clean_text)
                    if level is None:
                        level_attr = getattr(ext, 'attributes', {}).get('level')
                        try:
                            level = int(level_attr) if level_attr is not None else 2
                        except Exception:
                            level = 2

                    chunk_headings.append({
                        "text": clean_text,
                        "level": level,
                        "chunk_index": i,
                        "source": "llm"
                    })
                
                # Estimate output tokens (rough approximation: words in extractions)
                output_tokens = sum(len(h['text'].split()) for h in chunk_headings)
                
                # Record metrics
                metrics['llm_calls'] += 1
                metrics['llm_input_tokens'] += input_tokens
                metrics['llm_output_tokens'] += output_tokens
                metrics['llm_total_time'] += chunk_elapsed
                metrics['llm_chunk_times'].append({
                    'chunk_index': i + 1,
                    'chunk_size': len(chunk),
                    'time_s': round(chunk_elapsed, 2),
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'headings_found': len(chunk_headings)
                })

                all_headings.extend(chunk_headings)
                metrics['llm_success'] += 1
                print(f"  Chunk {i+1:2d}/{len(text_chunks)}: {len(chunk_headings):2d} headings [LLM] in {chunk_elapsed:.2f}s")
                extraction_success = True
                break

            except Exception as e:
                error_msg = str(e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"  Chunk {i+1:2d}/{len(text_chunks)}: LLM failed - {error_msg[:80]}")
        
        # Fallback to regex extraction if LLM failed
        if not extraction_success:
            failed_chunks.append(i + 1)
            metrics['llm_failed_chunks'] = metrics.get('llm_failed_chunks', 0) + 1
            if USE_FALLBACK_REGEX:
                regex_headings = extract_headings_regex(chunk)
                for h in regex_headings:
                    h["chunk_index"] = i
                all_headings.extend(regex_headings)
                metrics['regex_fallbacks'] += 1
                print(f"  Chunk {i+1:2d}/{len(text_chunks)}: {len(regex_headings):2d} headings [REGEX fallback]")
            else:
                print(f"  Chunk {i+1:2d}/{len(text_chunks)}: LLM failed — 0 headings extracted (no fallback)")

        # ── Supplementary regex pass ──────────────────────────────────────────
        # Always scan for markdown #-headings that neither the LLM nor the
        # explicit fallback captured.  This recovers headings when the LLM
        # hallucinated wrong text (e.g. wrong numbering) or returned 0 results.
        _found_lower = {h['text'].lower() for h in all_headings if h.get('chunk_index') == i}
        _supp_re = re.compile(r'^(#{1,6})\s+\*{0,2}\s*(.+?)\s*\*{0,2}\s*$', re.MULTILINE)
        _supp_count = 0
        for _m in _supp_re.finditer(chunk):
            _htext = re.sub(r'\*+', '', _m.group(2).strip()).strip()  # strip ALL ** bold
            if not _htext or is_false_heading(_htext) or _htext.lower() in _found_lower:
                continue
            _level = determine_heading_level(_htext)
            all_headings.append({
                "text": _htext,
                "level": _level,
                "chunk_index": i,
                "source": "regex_supplement",
            })
            _found_lower.add(_htext.lower())
            _supp_count += 1
            if VERBOSE:
                print(f"    Supplementary regex: '{_htext}' [L{_level}]")
        if _supp_count > 0:
            print(f"  Chunk {i+1:2d}/{len(text_chunks)}: {_supp_count:2d} additional heading(s) recovered [supplementary]")

    if failed_chunks:
        print(f"\n  ⚠  {len(failed_chunks)} chunk(s) had LLM extraction failures: {failed_chunks}")
        print(f"     Set 'use_fallback_regex': true in config.json to recover headings from these chunks.")

    return all_headings


# # To clean and refine the raw list of headings extracted from all chunks.
# def validate_and_deduplicate_headings(all_headings: list, full_text: str, metrics: dict) -> list:
#     """
#     Validate extracted headings and remove duplicates.
#     Returns list of unique valid headings.
#     """
#     unique = []
#     seen = set()
#     seen_lower = set()

#     for h in all_headings:
#         normalized_text = " ".join(h["text"].split())
#         normalized_lower = normalized_text.lower()
#         normalized_dedup = normalize_for_dedup(normalized_text)
#         if is_page_marker(normalized_text):
#             continue
#         if is_false_heading(normalized_text):
#             metrics['rejected_false'] += 1
#             continue
#         if is_likely_body_text(normalized_text, full_text):
#             metrics['rejected_body'] += 1
#             continue
#         if normalized_dedup in seen_lower:
#             metrics['rejected_duplicate'] += 1
#             continue
#         if VERBOSE and not is_valid_heading_in_text(h["text"], full_text):
#             metrics['warnings_not_found'] = metrics.get('warnings_not_found', 0) + 1
#             print(f"  Warning: heading not found verbatim in document: '{h['text'][:60]}'")

#         h["level"] = determine_heading_level(h["text"])

#         level = h["level"]
#         metrics['level_counts'][level] = metrics['level_counts'].get(level, 0) + 1
        
#         unique.append(h)
#         seen.add(normalized_text)
#         seen_lower.add(normalized_dedup)

#     return unique


# def extract_sections_with_text(headings: list, full_text: str) -> list:
#     """
#     For each heading, extract the text content until the next heading.
#     Returns list of dicts with heading info and text content.
#     """
#     sections = []
    
#     # Find exact positions of all headings in the original text
#     heading_positions = []
#     search_start = 0
    
#     for h in headings:
#         start, end = find_heading_in_original(h["text"], full_text, search_start)
#         if start >= 0:
#             heading_positions.append({
#                 "text": h["text"],
#                 "level": h["level"],
#                 "start": int(start),
#                 "end": int(end)
#             })
#         else:
#             # Try the looser position finder. It may return float('inf') when not found;
#             # normalize to -1 so downstream slicing uses integer indices only.
#             pos = find_heading_position(h["text"], full_text)
#             if pos is None or (isinstance(pos, float) and not pos < float('inf')):
#                 pos = -1
#             try:
#                 pos_int = int(pos) if pos != float('inf') and pos != -1 else -1
#             except Exception:
#                 pos_int = -1
#             end_int = pos_int + len(h["text"]) if pos_int >= 0 else -1
#             heading_positions.append({
#                 "text": h["text"],
#                 "level": h["level"],
#                 "start": pos_int,
#                 "end": end_int
#             })
    
#     # Sort by actual start position
#     heading_positions = sorted(heading_positions, key=lambda x: x["start"] if x["start"] >= 0 else float('inf'))
    
#     # Extract text between consecutive headings
#     for i, hp in enumerate(heading_positions):
#         if hp["start"] < 0:
#             text_content = ""
#         else:
#             content_start = hp["end"]
            
#             if i + 1 < len(heading_positions) and heading_positions[i + 1]["start"] >= 0:
#                 content_end = heading_positions[i + 1]["start"]
#             else:
#                 content_end = len(full_text)
            
#             # Limit section size
#             max_section_size = 2000
#             if content_end - content_start > max_section_size:
#                 content_end = content_start + max_section_size
            
#             text_content = full_text[content_start:content_end].strip()
            
#             # Clean up the content: strip markdown # and ** from body text lines
#             text_content = re.sub(r'^[\n\r\s]+', '', text_content)
#             text_content = re.sub(r'\n{3,}', '\n\n', text_content)

#         sections.append({
#             "text": hp["text"],
#             "level": hp["level"],
#             "position": hp["start"],
#             "content": text_content
#         })

#     return sections
