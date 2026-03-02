"""Main runner for Task2: imports config and utils to run cascading extraction."""
import argparse
from config.config import DEFAULT_LINES_PER_LEVEL, DEFAULT_MAX_SUMMARY_CHARS
from utils.utils import (
    load_entries, find_chunk_key, chunk_number_from_key, flatten_heading_values,
    extract_snippets_with_ollama, rebuild_metadata_with_accumulated_headings,
    get_text_field, set_text_field, write_output
)
import copy


def run(input_path: str, output_path: str, lines_per_level: int, max_summary_chars: int):
    entries = load_entries(input_path)
    if not entries:
        print("Error: No valid chunks found.")
        return

    chunk_items = []
    for entry in entries:
        chunk_key = find_chunk_key(entry)
        if not chunk_key:
            continue
        chunk_num = chunk_number_from_key(chunk_key)
        if chunk_num is None:
            continue
        chunk_items.append((chunk_num, chunk_key, entry))

    if not chunk_items:
        print("Error: No valid chunk_idN entries found.")
        return

    chunk_items.sort(key=lambda x: x[0])

    output_rows = []
    previous_modified_text = ""
    previous_headings = []
    accumulated_headings = []

    for index, (chunk_num, chunk_key, original_entry) in enumerate(chunk_items):
        entry = copy.deepcopy(original_entry)
        chunk_meta = entry.get(chunk_key, {}) or {}
        original_text = get_text_field(entry)
        current_headings = flatten_heading_values(chunk_meta)

        if index == 0:
            print(f"  chunk_id{chunk_num}: First chunk - untouched")
            output_entry = copy.deepcopy(original_entry)
            output_entry["Original Text"] = original_text
            previous_modified_text = original_text
            previous_headings = current_headings.copy()
            accumulated_headings = current_headings.copy()
            output_entry[chunk_key] = rebuild_metadata_with_accumulated_headings(chunk_meta, accumulated_headings)
        else:
            context_text = extract_snippets_with_ollama(previous_modified_text, previous_headings, lines_per_level, max_chars=max_summary_chars)
            if context_text and original_text.strip():
                modified_text = f"{context_text}\n{original_text}"
            elif context_text:
                modified_text = context_text
            else:
                modified_text = original_text

            entry["Original Text"] = original_text
            set_text_field(entry, modified_text)

            for h in current_headings:
                if h and h not in accumulated_headings:
                    accumulated_headings.append(h)

            entry[chunk_key] = rebuild_metadata_with_accumulated_headings(chunk_meta, accumulated_headings)
            output_entry = entry

            previous_modified_text = modified_text
            previous_headings = current_headings.copy()

            print(f"  chunk_id{chunk_num}: added context, {len(accumulated_headings)} headings")

        output_rows.append(output_entry)

    write_output(output_path, output_rows)
    print(f"Saved to: {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Task2 cascading extraction runner')
    parser.add_argument('input', nargs='?', default='Task2/data/structured_chunks.json')
    parser.add_argument('output', nargs='?', default='Task2/data/structured_chunks_out.json')
    parser.add_argument('--lines-per-level', '-l', type=int, default=DEFAULT_LINES_PER_LEVEL)
    parser.add_argument('--max-chars', '-m', type=int, default=DEFAULT_MAX_SUMMARY_CHARS)
    args = parser.parse_args()
    run(args.input, args.output, args.lines_per_level, args.max_chars)
