import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    MODEL_ID, OUTPUT_FILE, TEXT_SPLITTER_CHUNK_SIZE
)
from utils.utils import (
    print_header, print_step, print_metrics_table, scan_for_missed_headings
)
from extraction.extractor import (
    get_pdf_text, split_text_into_chunks, extract_headings_from_chunks,
    validate_and_deduplicate_headings, extract_sections_with_text
)
from processing.chunk_builder import build_hierarchical_chunks


def process_pdf(pdf_path: str):
    """Main pipeline for processing a PDF and extracting hierarchical headings."""
    
    # Initialize metrics
    metrics = {
        'doc_length': 0,
        'total_chunks': 0,
        'chunk_size': TEXT_SPLITTER_CHUNK_SIZE,
        'raw_headings': 0,
        'valid_headings': 0,
        'rejected_false': 0,
        'rejected_body': 0,
        'rejected_duplicate': 0,
        'rejected_not_found': 0,
        'level_counts': {},
        'output_chunks': 0,
        'llm_success': 0,
        'regex_fallbacks': 0,
    }
    
    print_header("PDF HEADING EXTRACTION PIPELINE")
    print(f"  Model: {MODEL_ID}")
    print(f"  Input: {pdf_path}")
    
    # Step 1: Extract text
    print_step(1, "Extracting PDF text")
    full_text = get_pdf_text(pdf_path)
    metrics['doc_length'] = len(full_text)
    print(f"  Document length: {metrics['doc_length']:,} characters")
    
    # Step 2: Split text
    print_step(2, "Splitting text into chunks")
    text_chunks, adaptive_chunk_size, _ = split_text_into_chunks(full_text, metrics['doc_length'])
    metrics['total_chunks'] = len(text_chunks)
    metrics['chunk_size'] = adaptive_chunk_size
    
    if metrics['doc_length'] > 500000:
        print(f"  Using larger chunks for long document")
    print(f"  Chunks created: {metrics['total_chunks']}")
    
    # Step 3: Extract headings
    print_step(3, "Extracting headings with LangExtract")
    all_headings = extract_headings_from_chunks(text_chunks, adaptive_chunk_size, metrics)
    
    # Post-processing: Scan full text for missed numbered headings
    print(f"  Scanning full text for missed headings...")
    missed_headings = scan_for_missed_headings(full_text, all_headings)
    if missed_headings:
        print(f"  Found {len(missed_headings)} additional headings")
        all_headings.extend(missed_headings)
    
    metrics['raw_headings'] = len(all_headings)
    
    # Step 4: Validate and deduplicate
    print_step(4, "Validating and deduplicating headings")
    unique = validate_and_deduplicate_headings(all_headings, full_text, metrics)
    metrics['valid_headings'] = len(unique)
    print(f"  Raw headings: {metrics['raw_headings']}")
    print(f"  Valid unique: {metrics['valid_headings']}")
    
    # Step 5: Extract section text
    print_step(5, "Extracting text content for sections")
    sections = extract_sections_with_text(unique, full_text)
    print(f"  Sections extracted: {len(sections)}")
    
    # Step 6: Build chunks
    print_step(6, "Building hierarchical chunks")
    final_output = build_hierarchical_chunks(sections)
    metrics['output_chunks'] = len(final_output)
    print(f"  Output chunks: {metrics['output_chunks']}")
    
    # Save output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
    print(f"  Saved to: {OUTPUT_FILE}")
    
    # Print metrics table
    print_metrics_table(metrics)
    
    # Print extracted headings list
    print("EXTRACTED HEADINGS:")
    print("-" * 55)
    sys.stdout.flush()
    
    heading_lines = []
    for i, h in enumerate(unique, 1):
        level_indent = "  " * (h["level"] - 1)
        heading_lines.append(f"  {i:2d}. {level_indent}[L{h['level']}] {h['text'][:50]}")
    
    print("\n".join(heading_lines))
    print()
    sys.stdout.flush()


if __name__ == "__main__":
    default_pdf = "data/sales_analysis_report.pdf"
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = default_pdf
    
    process_pdf(pdf_path)
