import json
import argparse
import sys
import os
import re
from typing import List, Dict
from collections import Counter
import time

try:
    import ollama
except Exception:
    ollama = None


LLM_MODEL = os.environ.get('LLM_MODEL', 'gemma2:2b')

# --- Precompiled regexes (module-level, not per-chunk) ---
_HEADING_KEY_RE = re.compile(r'(heading|title|header|section|^h\d$|name)', re.IGNORECASE)
_NUMERIC_PREFIX_RE = re.compile(r'^\d+(?:[.)]|\s)')
_TITLE_START_RE = re.compile(r'^\d+[:.]')
_FALLBACK_NUMERIC_RE = re.compile(r'^\d+[.)] ')

# Matches key names like "Main Heading 1", "Sub Heading 3", "Sub Sub Sub Heading 2"
# Captures the number of "Sub" words to determine depth.
_KEY_LEVEL_RE = re.compile(r'^((?:Sub\s+)*)(?:Main\s+)?Heading\s+\d+$', re.IGNORECASE)

# Detect numbered heading values for hierarchy inference
_SINGLE_NUM_HEADING_RE = re.compile(r'^\d+[.)\s]')
_DOUBLE_NUM_HEADING_RE = re.compile(r'^\d+\.\d+')


def _is_noisy(h: str) -> bool:
    return len(h) > 200 or len(h.split()) > 12 or '...' in h or '\n' in h


def _looks_like_title(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    s = s.strip()
    words = s.split()
    if len(words) > 10 or len(s) > 120:
        return False
    if s.isupper() and 1 < len(words) < 12:
        return True
    if s.istitle() and len(words) <= 8:
        return True
    if _TITLE_START_RE.match(s):
        return False
    return False


def _is_subheading_candidate(h: str) -> bool:
    if not h or not isinstance(h, str):
        return False
    h = h.strip()
    if _NUMERIC_PREFIX_RE.match(h):
        return True
    if len(h.split()) <= 6 and h.istitle():
        return True
    return False


def _extract_headings_from_obj(obj: dict) -> Dict:
    """Iterative BFS walk — no recursion overhead, no per-call re.compile.
    Returns {'headings': [...], 'heading_levels': [...], 'raw_text': str, 'structured': bool}.
    'structured'=True means headings came from explicit named keys (reliable).
    'heading_levels' is a list of {'heading': str, 'level': int} for keys matching
    the 'Main Heading N' / 'Sub Heading N' naming convention.
    """
    headings = []
    heading_levels = []
    raw_text = ''

    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(k, str):
                    level_match = _KEY_LEVEL_RE.match(k)
                    if level_match:
                        sub_prefix = level_match.group(1)
                        level = len(sub_prefix.split()) if sub_prefix.strip() else 0
                        if isinstance(v, str):
                            val = v.strip()
                            headings.append(val)
                            heading_levels.append({'heading': val, 'level': level})
                        elif isinstance(v, list):
                            for it in v:
                                if isinstance(it, str):
                                    val = it.strip()
                                    headings.append(val)
                                    heading_levels.append({'heading': val, 'level': level})
                    elif _HEADING_KEY_RE.search(k):
                        if isinstance(v, str):
                            headings.append(v.strip())
                        elif isinstance(v, list):
                            headings.extend(it.strip() for it in v if isinstance(it, str))
                    if not raw_text and k.lower() == 'text' and isinstance(v, str):
                        raw_text = v
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(o, list):
            stack.extend(o)

    structured = bool(headings)

    # Fallback: scan string values for heading-like lines (only when no named keys found)
    if not headings:
        fstack = [obj]
        while fstack:
            o = fstack.pop()
            if isinstance(o, dict):
                for v in o.values():
                    if isinstance(v, str):
                        for line in (l.strip() for l in v.splitlines() if l.strip()):
                            if (3 < len(line) < 120
                                    and (line.isupper()
                                         or _FALLBACK_NUMERIC_RE.match(line)
                                         or (line.istitle() and len(line.split()) < 6))):
                                headings.append(line)
                                break
                    elif isinstance(v, (dict, list)):
                        fstack.append(v)
            elif isinstance(o, list):
                fstack.extend(o)

    clean = [h.replace('.....', '').strip() for h in headings if h]
    clean_levels = []
    for hl in heading_levels:
        cleaned = hl['heading'].replace('.....', '').strip()
        if cleaned:
            clean_levels.append({'heading': cleaned, 'level': hl['level']})
    return {'headings': clean, 'heading_levels': clean_levels, 'raw_text': raw_text or '', 'structured': structured}


def normalize_chunk_with_llm(chunk_object: dict, use_llm: bool = True) -> dict:
    det = _extract_headings_from_obj(chunk_object)
    headings = det.get('headings', [])
    heading_levels = det.get('heading_levels', [])
    raw_text = det.get('raw_text', '')
    structured = det.get('structured', False)

    # Headings from named keys are always reliable — never call LLM regardless of count
    if structured:
        clean = [h for h in headings if not _is_noisy(h)]
        clean_levels = [hl for hl in heading_levels if not _is_noisy(hl['heading'])]
        return {'headings': clean, 'heading_levels': clean_levels, 'raw_text': raw_text, 'ambiguous': False}

    # Fallback headings: only ambiguous when missing or noisy
    ambiguous = not headings or any(_is_noisy(h) for h in headings)

    if (headings or raw_text) and not ambiguous:
        return {'headings': headings, 'heading_levels': heading_levels, 'raw_text': raw_text, 'ambiguous': False}

    if use_llm and ollama is not None:
        try:
            chunk_str = json.dumps(chunk_object, ensure_ascii=False)
            prompt = (
                "Analyze the following JSON chunk and return a JSON object with keys 'headings' (list) and 'raw_text' (string).\n\n"
                + chunk_str
            )
            resp = ollama.generate(model=LLM_MODEL, prompt=prompt, format='json')
            out = json.loads(resp.get('response', '{}'))
            out['headings'] = [h.replace('.....', '').strip() for h in out.get('headings', []) if h]
            out['heading_levels'] = heading_levels
            out['raw_text'] = out.get('raw_text', raw_text)
            out['ambiguous'] = bool(not out['headings'])
            return out
        except Exception:
            pass

    return {'headings': headings, 'heading_levels': heading_levels, 'raw_text': raw_text, 'ambiguous': True}


def get_heading_relationship_with_llm(prev_heading: str, current_heading: str) -> str:
    if ollama is None:
        return 'SIBLING'
    prompt = f"""
    Determine relationship: Previous: "{prev_heading}"\nCurrent: "{current_heading}"\nReturn exactly one of: PARENT, CHILD, SIBLING
    """
    try:
        resp = ollama.generate(model=LLM_MODEL, prompt=prompt)
        cls = resp.get('response', '').strip().upper()
        if cls in ('PARENT', 'CHILD', 'SIBLING'):
            return cls
    except Exception:
        pass
    return 'SIBLING'


def determine_main_heading(normalized_chunks: List[Dict], override_title: str = None, use_llm: bool = True) -> str:
    if override_title:
        return override_title
    if normalized_chunks and isinstance(normalized_chunks[0].get('headings'), list) and normalized_chunks[0]['headings']:
        return normalized_chunks[0]['headings'][0]
    all_headings = []
    for c in normalized_chunks:
        all_headings.extend([h for h in (c.get('headings') or []) if isinstance(h, str) and h])
    if not all_headings:
        return 'Document'
    counts = Counter(all_headings)
    most_common, _ = counts.most_common(1)[0]
    return most_common


def process_document(original_data: list, override_title: str = None, use_llm: bool = True, hybrid: bool = False, progress_interval: int = 10):
    total = len(original_data)
    normalized_chunks = []
    start = time.time()

    print(f"Normalizing {total} chunks (use_llm={use_llm}, hybrid={hybrid})...")

    if use_llm and hybrid:
        for i, chunk in enumerate(original_data, 1):
            det = normalize_chunk_with_llm(chunk, use_llm=False)
            if det.get('ambiguous'):
                llm_res = normalize_chunk_with_llm(chunk, use_llm=True)
                normalized_chunks.append(llm_res if llm_res.get('headings') else det)
            else:
                normalized_chunks.append(det)
            if progress_interval and i % progress_interval == 0:
                elapsed = time.time() - start
                avg = elapsed / i
                print(f"  processed {i}/{total} chunks — elapsed {elapsed:.1f}s, avg {avg:.2f}s/chunk")
    else:
        for i, chunk in enumerate(original_data, 1):
            normalized_chunks.append(normalize_chunk_with_llm(chunk, use_llm=use_llm))
            if progress_interval and i % progress_interval == 0:
                elapsed = time.time() - start
                avg = elapsed / i
                print(f"  processed {i}/{total} chunks — elapsed {elapsed:.1f}s, avg {avg:.2f}s/chunk")

    elapsed_total = time.time() - start
    print(f"Normalization complete: {total} chunks in {elapsed_total:.1f}s (avg {elapsed_total/ max(1,total):.2f}s/chunk)")

    main_title = determine_main_heading(normalized_chunks, override_title=override_title, use_llm=use_llm)

    # Collect unique headings in document order with their key-based levels
    seen_headings = set()
    ordered_headings = []  # list of (heading, effective_level)

    for chunk in normalized_chunks:
        # Build a map from heading text to key-based level for this chunk
        levels_map = {}
        for hl in chunk.get('heading_levels', []):
            levels_map[hl['heading']] = hl['level']

        for h in chunk.get('headings', []):
            if h in seen_headings:
                continue
            seen_headings.add(h)

            key_level = levels_map.get(h)
            if key_level is not None:
                # Trust the key-based level directly — the key name hierarchy
                # (Main Heading → Sub Heading → Sub Sub Heading → Sub Sub Sub Heading)
                # already encodes the correct nesting depth.
                eff = key_level
            else:
                eff = 1  # fallback for headings without key-level info

            ordered_headings.append((h, eff))

    # Build ancestry using a heading stack
    heading_stack = []  # [(heading, level), ...]
    ancestry_map = {}

    for h, level in ordered_headings:
        while heading_stack and heading_stack[-1][1] >= level:
            heading_stack.pop()
        ancestry_map[h] = [item[0] for item in heading_stack]
        heading_stack.append((h, level))

    # Shallow copy each item — avoids deepcopy of entire dataset
    final_data = []
    for i, chunk in enumerate(original_data):
        annotated = dict(chunk)
        seen: set = set()
        ancestor_lists: list = []
        # Re-extract headings from the original chunk to ensure we cover all present headings
        chunk_headings = _extract_headings_from_obj(chunk).get('headings', [])
        for heading in chunk_headings:
            ancestors = ancestry_map.get(heading)
            if ancestors is not None:
                t = tuple(ancestors)
                if t not in seen:
                    seen.add(t)
                    ancestor_lists.append(list(t))
        annotated['ancestral_headings'] = ancestor_lists
        final_data.append(annotated)

    # Build a flattened mapping of headings -> ancestral list
    heading_map = {}
    for h, ancestors in ancestry_map.items():
        heading_map[h] = ancestors

    return final_data, heading_map


def load_input(path: str) -> List[Dict]:
    if not os.path.exists(path):
        print(f"Error: The file '{path}' was not found.", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            # Normalize list items to a canonical chunk dict shape:
            # Each item may look like { "chunk_id1": { ...headings... }, "Text": "...", "Metadata": "..." }
            normalized = []
            for item in data:
                if not isinstance(item, dict):
                    normalized.append(item)
                    continue

                # Extract any nested chunk map (first key that isn't Text/Metadata)
                text_val = None
                meta_val = None
                nested_map = {}
                other_keys = []
                for k, v in item.items():
                    lk = k.lower()
                    if lk == 'text':
                        if isinstance(v, str):
                            text_val = v
                        continue
                    if lk == 'metadata':
                        if isinstance(v, str):
                            meta_val = v
                        continue
                    other_keys.append((k, v))

                # If there's a single other key and it's a dict, treat it as the headings map
                if len(other_keys) == 1 and isinstance(other_keys[0][1], dict):
                    nested_map = other_keys[0][1]
                else:
                    # otherwise, try to merge any string-valued keys that look like heading entries
                    for k, v in other_keys:
                        if isinstance(v, (str, list, dict)):
                            nested_map[k] = v

                # Build canonical chunk object
                merged = {}
                # Merge nested_map entries at top level so extractor can find keys like 'Main Heading'
                if isinstance(nested_map, dict):
                    for hk, hv in nested_map.items():
                        merged[hk] = hv
                if text_val:
                    merged['Text'] = text_val
                if meta_val:
                    merged['Metadata'] = meta_val

                # If merged ended up empty, just keep original item
                normalized.append(merged if merged else item)

            return normalized
        if isinstance(data, dict):
            # common alternative shapes
            if 'chunks' in data and isinstance(data['chunks'], list):
                return data['chunks']
            if 'data' in data and isinstance(data['data'], list):
                return data['data']
            return [data]
        print(f"Error: JSON file '{path}' does not contain list or object.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: The file '{path}' is not a valid JSON file.", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Add ancestral_headings to JSON chunks (uses Ollama optionally).')
    parser.add_argument('input_file', nargs='?', default='sales_analysis_report4.json')
    parser.add_argument('--title', type=str, default=None)
    parser.add_argument('--output', '-o', type=str, default=None)
    parser.add_argument('--no-llm', action='store_true')
    parser.add_argument('--hybrid', action='store_true')
    parser.add_argument('--model', type=str, default=None)
    parser.add_argument('--progress-interval', type=int, default=10,
                        help='Print progress every N chunks (0 = silent). Default: 10')
    args = parser.parse_args()

    global LLM_MODEL
    # Keep default model unless user provided --model
    LLM_MODEL = args.model or LLM_MODEL

    if args.no_llm:
        use_llm = False
    else:
        use_llm = True
    hybrid_mode = bool(args.hybrid)

    # Read raw JSON so we can preserve the original input shape
    with open(args.input_file, 'r', encoding='utf-8') as f:
        raw_json = json.load(f)

    # Normalize for processing
    data = load_input(args.input_file)
    results = process_document(
        data,
        override_title=args.title,
        use_llm=use_llm,
        hybrid=hybrid_mode,
        progress_interval=args.progress_interval,
    )

    final_data, heading_map = results

    # Merge ancestral_headings back into the original raw JSON structure when possible
    output_obj = None
    if isinstance(raw_json, list) and len(raw_json) == len(final_data):
        for i, item in enumerate(raw_json):
            if isinstance(item, dict):
                # Find the first dict-valued field (e.g. the inner headings map) and
                # insert ancestral_headings inside it mapping heading->ancestors.
                inner = None
                inner_key = None
                for k, v in item.items():
                    if isinstance(v, dict):
                        inner = v
                        inner_key = k
                        break
                if inner is not None:
                    chunk_headings = _extract_headings_from_obj(inner).get('headings', [])
                    mapping = {h: heading_map.get(h, []) for h in chunk_headings}
                    # Post-process numbered headings: attach to nearest preceding
                    # non-numbered heading in the same chunk so numbered lists
                    # become children of the containing section (e.g., Recommendations).
                    for idx, h in enumerate(chunk_headings):
                        if _SINGLE_NUM_HEADING_RE.match(h):
                            prev = None
                            for k in range(idx - 1, -1, -1):
                                cand = chunk_headings[k]
                                if not _SINGLE_NUM_HEADING_RE.match(cand):
                                    prev = cand
                                    break
                            if prev:
                                parent_list = heading_map.get(prev, [])
                                # ensure prev appears as immediate parent
                                mapping[h] = parent_list + [prev] if prev not in parent_list else parent_list
                    inner['ancestral_headings'] = mapping
                    continue
                # fallback: attach per-chunk list (older behaviour)
                item['ancestral_headings'] = final_data[i].get('ancestral_headings', [])
        output_obj = raw_json
    elif isinstance(raw_json, dict) and 'chunks' in raw_json and isinstance(raw_json['chunks'], list) and len(raw_json['chunks']) == len(final_data):
        for i, item in enumerate(raw_json['chunks']):
            if isinstance(item, dict):
                item['ancestral_headings'] = final_data[i].get('ancestral_headings', [])
        output_obj = raw_json
    else:
        # Fallback: write the normalized annotated list and heading map (previous behaviour)
        output_obj = [final_data, heading_map]

    base = os.path.splitext(os.path.basename(args.input_file))[0]
    out_path = args.output if args.output else os.path.join(os.getcwd(), f"{base}_ancestry_exact.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(output_obj, indent=2, ensure_ascii=False))
    # Report counts depending on output shape
    if isinstance(output_obj, list) and output_obj and isinstance(output_obj[0], dict):
        print(f"Wrote {len(output_obj)} items to {out_path}")
    else:
        print(f"Wrote output to {out_path}")


if __name__ == '__main__':
    main()
