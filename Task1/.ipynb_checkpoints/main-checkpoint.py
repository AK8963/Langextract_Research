import json
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_config, MODEL_ID, OUTPUT_FILE, TEXT_SPLITTER_CHUNK_SIZE, MARKDOWN_PATH
from utils.utils import ( print_header, print_step, print_metrics_table, extract_document_title_from_text )
from extraction.extractor import (
    get_markdown_text, split_text_into_chunks, extract_headings_from_chunks
)
#from processing.chunk_builder import build_hierarchical_chunks
from processing.excel import generate_excel_report

_TASK1_ROOT = os.path.dirname(os.path.abspath(__file__))

def process_markdown(markdown_path: str):
    """Main pipeline for processing a Markdown file and extracting hierarchical headings with ancestral paths."""

    # Reload config fresh each call so changes to config.json take effect
    # without needing a kernel restart
    _cfg = load_config()
    _model_id   = _cfg['model']['model_id']
    _chunk_size = _cfg['text_splitter']['chunk_size']
    _output_file = os.path.normpath(os.path.join(_TASK1_ROOT, _cfg['output']['output_file']))
    # Ensure output directory exists
    os.makedirs(os.path.dirname(_output_file), exist_ok=True)

    # Initialize metrics
    metrics = {
        'doc_length': 0,
        'total_chunks': 0,
        'chunk_size': _chunk_size,
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

    print_header("MARKDOWN HEADING EXTRACTION PIPELINE")
    print(f"  Model: {_model_id}")
    print(f"  Input: {markdown_path}")

    # Store document name
    metrics['document_name'] = os.path.basename(markdown_path)

    # Step 1: Read markdown text
    print_step(1, "Reading Markdown text")
    t_doc_start = time.time()
    full_text = get_markdown_text(markdown_path)
    metrics['doc_retrieval_time'] = time.time() - t_doc_start
    metrics['doc_length'] = len(full_text)
    print(f"  Document length: {metrics['doc_length']:,} characters")
    print(f"  Doc retrieval time: {metrics['doc_retrieval_time']:.2f}s")
    
    # (No pre-parsing) LLM will extract headings and map levels.
    
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
    print(f"  Total LLM time: {metrics.get('llm_total_time', 0):.2f}s across {metrics.get('llm_calls', 0)} calls")

    # Step 3b: Inject document title (level 1) if not already present from LLM/regex
    has_level1 = any(h.get('level', 2) == 1 for h in all_headings)
    if not has_level1:
        title_heading = extract_document_title_from_text(full_text)
        if title_heading:
            print(f"  Document title detected: \"{title_heading['text']}\"")
            all_headings.insert(0, title_heading)

    # Post-scan disabled: LLM is the only source of headings (no full-text scan)

    # Group LLM extractions by chunk and output exactly one item per input chunk.
    metrics['raw_headings'] = len(all_headings)

    print_step(4, "Assembling per-chunk LangExtract outputs")

    level_labels = {
        1: "Main Heading",
        2: "Sub Heading",
        3: "Sub Sub Heading",
        4: "Sub Sub Sub Heading",
        5: "Sub Sub Sub Sub Heading",
    }
    metadata_labels = {
        1: "Main heading",
        2: "Sub heading",
        3: "Sub Sub heading",
        4: "Sub Sub Sub heading",
        5: "Sub Sub Sub Sub heading",
    }

    def extract_heading_content(chunk_text, headings):
        """Return list of (heading_dict, content_str) by parsing the chunk text."""
        import re as _re
        lines = chunk_text.split('\n')
        # Find the line index for each heading
        positioned = []
        for h in headings:
            htext = h.get('text', '')
            for idx, line in enumerate(lines):
                clean = _re.sub(r'^#+\s*', '', line).strip()
                clean = _re.sub(r'\*\*(.+?)\*\*', r'\1', clean).strip()
                if clean == htext:
                    positioned.append((idx, h))
                    break
        positioned.sort(key=lambda x: x[0])

        results = []
        in_code = False
        for i, (pos, h) in enumerate(positioned):
            next_pos = positioned[i + 1][0] if i + 1 < len(positioned) else len(lines)
            content_lines = []
            in_code = False
            for line in lines[pos + 1:next_pos]:
                if line.strip().startswith('```'):
                    in_code = not in_code
                    continue
                if not in_code and line.strip() and not _re.match(r'^\|[-| ]+\|', line):
                    content_lines.append(line.strip())
            content = ' '.join(content_lines).strip()
            if len(content) > 200:
                content = content[:200].rstrip() + '...'
            results.append((h, content))
        return results
    

    final_output = []
    for i, chunk in enumerate(text_chunks):
        chunk_headings = [h for h in all_headings if h.get('chunk_index') == i]

        # Build chunk_id mapping keyed by level-based label
        chunk_map = {}
        level_counters = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
        for h in chunk_headings:
            level = min(h.get('level', 2), 5)
            label = level_labels[level]
            key = f"{label} {level_counters[level]}"
            chunk_map[key] = h.get('text', '') + ' .....'
            level_counters[level] += 1

        # Build metadata with level-aware labels and content snippets
        heading_content = extract_heading_content(chunk.strip(), chunk_headings)
        metadata_parts = []
        for h, content in heading_content:
            level = min(h.get('level', 2), 5)
            label = metadata_labels[level]
            txt = h.get('text', '').replace('\n', ' ')
            if content:
                metadata_parts.append(f'"{label}": "{txt}: ........{content}........."')
            else:
                metadata_parts.append(f'"{label}": "{txt}"')
        metadata = ", ".join(metadata_parts)

        # Populate level_counts for the Heading Levels Breakdown report
        for h in chunk_headings:
            level = min(h.get('level', 2), 5)
            metrics['level_counts'][level] = metrics['level_counts'].get(level, 0) + 1

        ##### final output structure per chunk #####
        entry = {
            f"chunk_id{i+1}": chunk_map,
            "Text": chunk.strip(),
            "Metadata": metadata
        }
        final_output.append(entry)

    metrics['output_chunks'] = len(final_output)
    metrics['valid_headings'] = metrics['raw_headings']
    print(f"  Chunks returned: {metrics['output_chunks']}")

    # Save per-chunk output (formatted to match existing structure)
    with open(_output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
    print(f"  Saved to: {_output_file}")

    # Print metrics table
    print_metrics_table(metrics)
    
    # Generate Excel with metrics
    print("\n" + "="*55)
    print_step(7, "Generating Excel Report")
    try:
        
        # Add model name to metrics for Excel subtitle
        metrics['model'] = _model_id
        excel_path = generate_excel_report(metrics, _output_file)
        print(f"  Excel saved: {excel_path}")
    except Exception as e:
        print(f"  Excel generation failed: {e}")
    
    # Print extracted headings list (flattened per-chunk LLM outputs)
    print("\nEXTRACTED HEADINGS:")
    print("-" * 55)
    sys.stdout.flush()

    flat_headings = [h for h in all_headings]

    heading_lines = []
    for i, h in enumerate(flat_headings, 1):
        level = h.get('level', 2)
        level_indent = "  " * (level - 1)
        text = h.get('text', '')
        heading_lines.append(f"  {i:2d}. {level_indent}[L{level}] {text[:50]}")

    if heading_lines:
        print("\n".join(heading_lines))
    else:
        print("  (no headings extracted)")
    print()
    sys.stdout.flush()
    
    return metrics


if __name__ == "__main__":
    if len(sys.argv) > 1:
        markdown_path = sys.argv[1]
    else:
        markdown_path = MARKDOWN_PATH
    
    process_markdown(markdown_path)
