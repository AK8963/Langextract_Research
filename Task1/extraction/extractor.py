import fitz
import langextract as lx
import re
import time
import sys

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import configuration
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    MODEL_ID, TIMEOUT, MAX_RETRIES, RETRY_DELAY,
    TEXT_SPLITTER_CHUNK_SIZE, TEXT_SPLITTER_CHUNK_OVERLAP,
    VERBOSE, USE_FALLBACK_REGEX
)
from utils.utils import (
    preprocess_chunk, extract_headings_regex, scan_for_missed_headings,
    is_page_marker, is_false_heading, is_likely_body_text,
    is_valid_heading_in_text, determine_heading_level, normalize_for_dedup,
    find_heading_position, find_heading_in_original
)
from prompts.prompts import EXTRACTION_PROMPT, EXTRACTION_EXAMPLES


def get_pdf_text(pdf_path: str) -> str:
    """Extract full text from PDF, removing TOC artifacts."""
    doc = fitz.open(pdf_path)
    full_text = "\n\n".join(page.get_text("text") for page in doc)
    
    # Remove TOC lines with dots (e.g., "Section .......................... 5")
    full_text = re.sub(r'\.{5,}\s*\d+\s*', ' ', full_text)
    # Remove page number lines
    full_text = re.sub(r'^\s*\d+\s*$', '', full_text, flags=re.MULTILINE)
    
    return full_text


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
    Returns list of all extracted headings.
    """
    all_headings = []
    failed_chunks = []
    
    for i, chunk in enumerate(text_chunks):
        chunk_headings = []
        extraction_success = False
        
        # Preprocess chunk to remove problematic content
        cleaned_chunk = preprocess_chunk(chunk)
        
        for attempt in range(MAX_RETRIES):
            try:
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

                chunk_headings = [
                    {"text": ext.extraction_text,
                     "level": int(ext.attributes.get("level", 2)),
                     "chunk_index": i,
                     "source": "llm"}
                    for ext in result.extractions
                    if ext.extraction_class == "heading"
                       and ext.extraction_text
                       and len(ext.extraction_text.strip()) > 0
                ]

                all_headings.extend(chunk_headings)
                metrics['llm_success'] += 1
                print(f"  Chunk {i+1:2d}/{len(text_chunks)}: {len(chunk_headings):2d} headings [LLM]")
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
        if not extraction_success and USE_FALLBACK_REGEX:
            regex_headings = extract_headings_regex(chunk)
            for h in regex_headings:
                h["chunk_index"] = i
            all_headings.extend(regex_headings)
            metrics['regex_fallbacks'] += 1
            print(f"  Chunk {i+1:2d}/{len(text_chunks)}: {len(regex_headings):2d} headings [REGEX]")
            failed_chunks.append(i + 1)
    
    return all_headings


def validate_and_deduplicate_headings(all_headings: list, full_text: str, metrics: dict) -> list:
    """
    Validate extracted headings and remove duplicates.
    Returns list of unique valid headings.
    """
    unique = []
    seen = set()
    seen_lower = set()

    for h in all_headings:
        normalized_text = " ".join(h["text"].split())
        normalized_lower = normalized_text.lower()
        normalized_dedup = normalize_for_dedup(normalized_text)
        
        # Skip page markers
        if is_page_marker(normalized_text):
            continue
        
        # Skip false heading patterns
        if is_false_heading(normalized_text):
            metrics['rejected_false'] += 1
            continue
        
        # Skip likely body text
        if is_likely_body_text(normalized_text, full_text):
            metrics['rejected_body'] += 1
            continue
        
        # Case-insensitive duplicate check with normalized dashes
        if normalized_dedup in seen_lower:
            metrics['rejected_duplicate'] += 1
            continue
            
        if not is_valid_heading_in_text(h["text"], full_text):
            metrics['rejected_not_found'] += 1
            continue

        # Re-determine level using our rules
        h["level"] = determine_heading_level(h["text"])
        
        # Track level counts
        level = h["level"]
        metrics['level_counts'][level] = metrics['level_counts'].get(level, 0) + 1
        
        unique.append(h)
        seen.add(normalized_text)
        seen_lower.add(normalized_dedup)

    return unique


def extract_sections_with_text(headings: list, full_text: str) -> list:
    """
    For each heading, extract the text content until the next heading.
    Returns list of dicts with heading info and text content.
    """
    sections = []
    
    # Find exact positions of all headings in the original text
    heading_positions = []
    search_start = 0
    
    for h in headings:
        start, end = find_heading_in_original(h["text"], full_text, search_start)
        if start >= 0:
            heading_positions.append({
                "text": h["text"],
                "level": h["level"],
                "start": start,
                "end": end
            })
        else:
            heading_positions.append({
                "text": h["text"],
                "level": h["level"],
                "start": find_heading_position(h["text"], full_text),
                "end": find_heading_position(h["text"], full_text) + len(h["text"])
            })
    
    # Sort by actual start position
    heading_positions = sorted(heading_positions, key=lambda x: x["start"] if x["start"] >= 0 else float('inf'))
    
    # Extract text between consecutive headings
    for i, hp in enumerate(heading_positions):
        if hp["start"] < 0:
            text_content = ""
        else:
            content_start = hp["end"]
            
            if i + 1 < len(heading_positions) and heading_positions[i + 1]["start"] >= 0:
                content_end = heading_positions[i + 1]["start"]
            else:
                content_end = len(full_text)
            
            # Limit section size
            max_section_size = 2000
            if content_end - content_start > max_section_size:
                content_end = content_start + max_section_size
            
            text_content = full_text[content_start:content_end].strip()
            
            # Clean up the content
            text_content = re.sub(r'^[\n\r\s]+', '', text_content)
            text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        
        sections.append({
            "text": hp["text"],
            "level": hp["level"],
            "position": hp["start"],
            "content": text_content
        })
    
    return sections
