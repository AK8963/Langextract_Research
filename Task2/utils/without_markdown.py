import ollama
import json
import copy
import argparse # Import the argparse library for command-line arguments
import sys # Import sys to exit gracefully
import os
import re
from typing import List, Dict
from collections import Counter


def _looks_like_title(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    s = s.strip()
    words = s.split()
    if len(words) > 10 or len(s) > 120:
        return False
    # Title-case or all-caps short strings
    if s.isupper() and 1 < len(words) < 12:
        return True
    if s.istitle() and len(words) <= 8:
        return True
    # Avoid numeric-heavy strings
    if re.match(r"^\d+[:\.\)]", s):
        return False
    return False


def _is_subheading_candidate(h: str) -> bool:
    if not h or not isinstance(h, str):
        return False
    h = h.strip()
    # Numeric prefixes like 1, 1.1, 2.3.1
    if re.match(r"^\d+(?:[\.\)]|\s)", h):
        return True
    # Short title-cased lines are likely subheadings
    if len(h.split()) <= 6 and h.istitle():
        return True
    return False

# --- Configuration ---
LLM_MODEL = 'gemma2:2b' 

# --- LLM Interaction Functions (Steps 1 & 2) ---

def normalize_chunk_with_llm(chunk_object: dict, use_llm: bool = True) -> dict:
    """
    Normalize a chunk deterministically first; optionally fallback to LLM.
    Returns a dict with keys: 'headings' (list[str]), 'raw_text' (str), and 'ambiguous' (bool).
    The 'ambiguous' flag indicates whether deterministic extraction looks unreliable
    (e.g., no headings, too many candidates, or overly long/noisy headings).
    """

    def _extract_from_obj(obj):
        headings = []
        raw_text = None

        # Keys that often represent headings or titles
        heading_key_pattern = re.compile(r"(heading|title|header|section|^h\d$|name)", re.IGNORECASE)

        def walk(o):
            nonlocal headings, raw_text
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(k, str) and heading_key_pattern.search(k):
                        if isinstance(v, str):
                            headings.append(v.strip())
                        elif isinstance(v, list):
                            for it in v:
                                if isinstance(it, str):
                                    headings.append(it.strip())
                    if isinstance(k, str) and k.lower() == 'text' and isinstance(v, str):
                        raw_text = v
                    # Recurse
                    walk(v)
            elif isinstance(o, list):
                for item in o:
                    walk(item)

        walk(obj)

        # Fallback: try to find lines in any string values that look like headings
        if not headings and isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    lines = [l.strip() for l in v.splitlines() if l.strip()]
                    for line in lines[:20]:
                        if 3 < len(line) < 120 and (line.isupper() or re.match(r"^\d+[\.\)] ", line) or (line.istitle() and len(line.split()) < 6)):
                            headings.append(line)
                            break

        return {'headings': headings, 'raw_text': raw_text or obj.get('Text') or ''}

    try:
        deterministic = _extract_from_obj(chunk_object)
        headings = [h.replace('.....', '').strip() for h in deterministic.get('headings', []) if h]
        raw_text = deterministic.get('raw_text', '') or ''

        # Heuristic to mark ambiguity in deterministic extraction
        def _is_noisy(h):
            return (len(h) > 200) or (len(h.split()) > 12) or ('...' in h) or ('\n' in h)

        ambiguous = False
        if not headings:
            ambiguous = True
        elif len(headings) > 3:
            ambiguous = True
        else:
            for hh in headings:
                if _is_noisy(hh):
                    ambiguous = True
                    break

        if headings or raw_text:
            return {"headings": headings, "raw_text": raw_text, 'ambiguous': ambiguous}

        # Fallback to LLM if deterministic rules didn't yield results or extraction
        # looks ambiguous, and LLM is allowed.
        if use_llm:
            chunk_str = json.dumps(chunk_object, indent=2)
            prompt = f"""
            Analyze the following JSON chunk. Extract all headings in their original order, from any level of nesting.
            Also extract the raw text from the "Text" field.
            Return a single, clean JSON object with two keys:
            1. "headings": A list of strings, where each string is a heading.
            2. "raw_text": The string value from the "Text" field.

            JSON Chunk to analyze:
            {chunk_str}

            Your JSON output:
            """
            try:
                response = ollama.generate(
                    model=LLM_MODEL,
                    prompt=prompt,
                    format='json'
                )
                normalized_data = json.loads(response['response'])
                if 'headings' in normalized_data and 'raw_text' in normalized_data:
                    normalized_data['headings'] = [h.replace('.....', '').strip() for h in normalized_data['headings']]
                    # Re-evaluate ambiguity after LLM normalization
                    amb = False
                    if not normalized_data['headings']:
                        amb = True
                    elif len(normalized_data['headings']) > 5:
                        amb = True
                    normalized_data['ambiguous'] = amb
                    normalized_data['raw_text'] = normalized_data.get('raw_text', '')
                    return normalized_data
            except Exception as e:
                print(f" -> LLM normalization failed: {e}")

        # Final safe default
        return {"headings": [], "raw_text": chunk_object.get('Text', '') if isinstance(chunk_object.get('Text', ''), str) else '', 'ambiguous': True}

    except Exception as e:
        print(f" -> Deterministic normalization error: {e}")
        return {"headings": [], "raw_text": chunk_object.get('Text', '') if isinstance(chunk_object.get('Text', ''), str) else ''}
def get_heading_relationship_with_llm(prev_heading: str, current_heading: str) -> str:
    """
    STEP 2: Uses the LLM as a classifier to determine the hierarchical 
    relationship between two consecutive headings.
    """
    prompt = f"""
    Based on common document structures, what is the hierarchical relationship of the current heading to the previous one?
    - Previous Heading: "{prev_heading}"
    - Current Heading: "{current_heading}"

    Consider numerical prefixes and semantic context.
    Respond with only one of these exact words: PARENT, CHILD, SIBLING.
    """
    
    try:
        # For very long headings, we can truncate them for the printout
        print(f"Classifying: '{current_heading[:50]}...' relative to '{prev_heading[:50]}...'")
        response = ollama.generate(
            model=LLM_MODEL,
            prompt=prompt
        )
        classification = response['response'].strip().upper()
        
        if classification in ['PARENT', 'CHILD', 'SIBLING']:
            print(f" -> Classification: {classification}")
            return classification
        else:
            print(f" -> LLM gave invalid classification: '{classification}'. Falling back to SIBLING.")
            return "SIBLING" 

    except Exception as e:
        print(f" -> An error occurred during LLM classification: {e}")
        return "SIBLING"


def determine_main_heading(normalized_chunks: List[Dict], override_title: str = None, use_llm: bool = True) -> str:
    """Determine the document's main heading.

    Strategy:
    - If override_title provided, return it.
    - If first chunk has headings, use its first heading.
    - Otherwise, pick the most frequent heading across chunks.
    - If ambiguous and use_llm=True, ask the LLM to choose from candidates.
    """
    if override_title:
        return override_title

    # 1) First chunk heuristic
    if normalized_chunks and isinstance(normalized_chunks[0].get('headings'), list) and normalized_chunks[0]['headings']:
        return normalized_chunks[0]['headings'][0]

    # 2) Frequency heuristic
    all_headings = []
    for c in normalized_chunks:
        hs = c.get('headings') or []
        all_headings.extend([h for h in hs if h and isinstance(h, str)])

    if not all_headings:
        return "Document"

    counts = Counter(all_headings)
    most_common, most_count = counts.most_common(1)[0]

    # If the top candidate is clearly more common, use it
    if len(counts) == 1 or most_count >= max(2, max(counts.values()) / 1.5):
        return most_common

    # 3) LLM fallback when ambiguous
    if use_llm:
        candidates = list(dict.fromkeys(all_headings))[:50]
        prompt = (
            "From the following list of candidate headings, which one is most likely the main/title of the entire document?\n"
            + "Respond with exactly the heading text (no explanation).\n\nCandidates:\n"
            + "\n".join(f"- {h}" for h in candidates)
        )
        try:
            resp = ollama.generate(model=LLM_MODEL, prompt=prompt)
            choice = resp['response'].strip().strip('"')
            if choice:
                # If LLM returns something not in candidates, fall back safely
                return choice if choice in candidates else most_common
        except Exception:
            pass

    return most_common

# --- Main Execution Logic (Step 3) ---

def process_document(original_data: list, override_title: str = None, use_llm: bool = True, hybrid: bool = False):
    """
    STEP 3: Orchestrates the entire process.
    """
    
    print("\n--- Running Step 1: Normalizing all JSON chunks ---")
    normalized_chunks = []

    # Hybrid mode: deterministic-first pass, then LLM only for ambiguous chunks
    if use_llm and hybrid:
        for chunk in original_data:
            det = normalize_chunk_with_llm(chunk, use_llm=False)
            # If deterministic extraction looks ambiguous, request LLM normalization
            if det.get('ambiguous'):
                llm_res = normalize_chunk_with_llm(chunk, use_llm=True)
                # Prefer LLM result if it yields headings, otherwise keep deterministic
                normalized_chunks.append(llm_res if llm_res.get('headings') else det)
            else:
                normalized_chunks.append(det)
    else:
        # Non-hybrid: pass the use_llm flag to the normalizer (it will fallback per-chunk)
        normalized_chunks = [normalize_chunk_with_llm(chunk, use_llm=use_llm) for chunk in original_data]

    print("\n--- Running Step 2: Building hierarchy with LLM Classifier ---")

    # Determine main title using heuristics and optional LLM fallback
    # Only allow LLM help for main-heading selection when hybrid mode is enabled
    main_title = determine_main_heading(normalized_chunks, override_title=override_title, use_llm=(use_llm and hybrid))

    parent_stack = [main_title]
    ancestry_map = {}

    # Decide if main_title is a global document title.
    # Conditions to treat as global: override provided, appears in multiple chunks, or looks like a title in chunk1.
    main_freq = sum(1 for c in normalized_chunks if main_title in (c.get('headings') or []))
    main_looks_title = False
    if normalized_chunks and normalized_chunks[0].get('headings'):
        first_h = normalized_chunks[0]['headings'][0]
        main_looks_title = _looks_like_title(first_h)

    main_is_global = bool(override_title) or main_freq >= 2 or main_looks_title

    if main_is_global:
        # assign main title as parent for all detected headings
        for chunk in normalized_chunks:
            for h in chunk.get('headings', []):
                if not h:
                    continue
                if h == main_title:
                    ancestry_map[h] = []
                else:
                    ancestry_map[h] = [main_title]
    else:
        # Propagate main title only to chunks where it appears or where subheadings related to it continue.
        current_in_context = False
        for chunk in normalized_chunks:
            chunk_hs = chunk.get('headings') or []
            contains_main = main_title in chunk_hs
            if contains_main:
                # mark main title present here
                ancestry_map.setdefault(main_title, [])
                current_in_context = True
                # ensure all headings in this chunk get main_title as ancestor
                for h in chunk_hs:
                    if h and h != main_title:
                        ancestry_map[h] = [main_title]
                continue

            if current_in_context:
                # if chunk has subheading-like headings, carry main_title forward
                carried = False
                for h in chunk_hs:
                    if _is_subheading_candidate(h):
                        ancestry_map[h] = [main_title]
                        carried = True
                if carried:
                    # keep context open so following chunks may still be part of this section
                    current_in_context = True
                else:
                    # if no subheading-like headings, close propagation
                    current_in_context = False

        # As a fallback, ensure any heading seen gets at least an empty ancestor list
        for chunk in normalized_chunks:
            for h in chunk.get('headings', []):
                if h not in ancestry_map:
                    ancestry_map[h] = []

    print("\n--- Running Step 3: Annotating final JSON ---")
    final_data = copy.deepcopy(original_data)
    
    for i, chunk in enumerate(final_data):
        chunk_headings = normalized_chunks[i]['headings']
        ancestor_lists_in_chunk = set()
        
        for heading in chunk_headings:
            if heading in ancestry_map:
                ancestor_tuple = tuple(ancestry_map[heading])
                ancestor_lists_in_chunk.add(ancestor_tuple)

        chunk['ancestral_headings'] = [list(t) for t in ancestor_lists_in_chunk]

    return final_data


# --- Main Execution Block ---

if __name__ == "__main__":
    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(
        description="Process a JSON report to add ancestral headings using an LLM."
    )
    parser.add_argument(
        "input_file",
        nargs='?',
        default="sales_report_gemma8.json",
        type=str,
        help="The path to the input JSON file. Defaults to sales_report_gemma8.json."
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Optional main title to use for the document hierarchy. If omitted, derived from first chunk's first heading."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Optional path to write the output JSON. If omitted, writes to <input>_processed.json."
    )
    parser.add_argument(
        "--no-llm",
        action='store_true',
        help="Disable LLM fallback for heading extraction and main-heading detection."
    )
    parser.add_argument(
        "--hybrid",
        action='store_true',
        help="Use hybrid mode: deterministic-first; call LLM only for ambiguous chunks and ambiguous main-heading selection."
    )
    args = parser.parse_args()

    def load_input(path: str) -> List[Dict]:
        """Load input data from JSON and return a list of chunk dicts with a 'Text' field."""
        if not os.path.exists(path):
            print(f"Error: The file '{path}' was not found.", file=sys.stderr)
            sys.exit(1)

        lower = path.lower()
        if not lower.endswith('.json'):
            print(f"Unsupported file type: '{path}'. Provide a .json file.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                print(f"Error: JSON file '{path}' does not contain list or object.", file=sys.stderr)
                sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: The file '{path}' is not a valid JSON file.", file=sys.stderr)
            sys.exit(1)

    # Load input (JSON) and run the processing
    input_json_data = load_input(args.input_file)

    # Run the full process with the loaded data (override with --title if provided)
    use_llm = not args.no_llm
    hybrid_mode = bool(args.hybrid)
    final_output = process_document(input_json_data, override_title=args.title, use_llm=use_llm, hybrid=hybrid_mode)

    # Serialize output JSON
    out_json = json.dumps(final_output, indent=4, ensure_ascii=False)

    # Determine output path: use --output if provided, otherwise <input_basename>_processed.json
    if args.output:
        out_path = args.output
    else:
        base = os.path.splitext(os.path.basename(args.input_file))[0]
        out_path = os.path.join(os.getcwd(), f"{base}_processed.json")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(out_json)
