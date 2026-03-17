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
    find_heading_position, find_heading_in_original
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
                    clean_text = re.sub(r'^\*{1,2}|\*{1,2}$', '', clean_text).strip()

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

                    # LLM-only mode: accept LLM-extracted headings without requiring
                    # a verbatim in-chunk match. For debugging, when verbose, log a
                    # warning if the heading text isn't found verbatim in the chunk.
                    if VERBOSE:
                        pattern = re.compile(r'^(?:#{1,6}\s*)?\*{0,2}\s*' + re.escape(clean_text) + r'\s*\*{0,2}\s*$', re.MULTILINE)
                        if not pattern.search(chunk):
                            print(f"    Warning: LLM heading not found verbatim in chunk: '{clean_text[:60]}'")

                    # Determine level: prefer actual markdown hashes in the chunk line if present,
                    # otherwise use LLM-provided level attribute, fallback to heuristic.
                    level = None
                    md_line_match = re.search(r'^(#{1,6})\s*\*{0,2}\s*' + re.escape(clean_text) + r'\s*\*{0,2}\s*$', chunk, re.MULTILINE)
                    if md_line_match:
                        level = len(md_line_match.group(1))
                    else:
                        level_attr = getattr(ext, 'attributes', {}).get('level')
                        try:
                            level = int(level_attr) if level_attr is not None else None
                        except Exception:
                            level = None

                    if level is None:
                        level = determine_heading_level(clean_text)

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
                    if VERBOSE:
                        print(f"  Chunk {i+1:2d}/{len(text_chunks)}: LLM failed - {error_msg[:50]}")
        
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
