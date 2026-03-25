import json
import argparse
import sys
import os
import re
from typing import List, Dict
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

try:
    import ollama
except Exception:
    ollama = None

# Load config from config.json (Task2/config/config.json)
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
with open(_CONFIG_PATH, 'r', encoding='utf-8') as _f:
    _CONFIG = json.load(_f)

LLM_MODEL = os.environ.get('LLM_MODEL', _CONFIG["ollama"]["model"])

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


# Patterns that indicate a value is code output / variable assignment, not a heading
_CODE_NOISE_RE = re.compile(
    r'^(?:'
    r'Output:\s|'             # Output: ...
    r'#\s|'                   # Python comment
    r'>>>\s|'                  # REPL prompt
    r'print\s*\(|'            # print call
    r'[a-z_]+\s*=\s*[\[{"\d]|'  # assignment: x = [...
    r'Initial\s+\w+:|'         # Initial list:
    r'Adding\s+a\s+|'          # Adding a new ...
    r'Changing\s+an\s+|'       # Changing an element
    r'Removing\s+an\s+|'       # Removing an element
    r'Modifying\s+an\s+|'      # Modifying an existing
    r"Output:\s*\{'\'|"        # Output: {'...
    r'\{[\'"]\w)',
    re.IGNORECASE
)


def _is_code_noise(h: str) -> bool:
    """Return True if the heading looks like code output/assignment rather than real heading."""
    if not h:
        return False
    if _CODE_NOISE_RE.match(h):
        return True
    # Reject anything that looks like a Python dict/list literal
    stripped = h.strip()
    if stripped.startswith(("{'" , '{"', '["', "['" , '"', "'Output")):
        return True
    return False


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
    clean = [h for h in clean if not _is_code_noise(h)]
    clean_levels = []
    for hl in heading_levels:
        cleaned = hl['heading'].replace('.....', '').strip()
        if cleaned and not _is_code_noise(cleaned):
            clean_levels.append({'heading': cleaned, 'level': hl['level']})
    # If structured (had named keys) but all cleaned out as noise, mark as not-structured
    # so we don't trigger extra LLM calls for code-heavy chunks that have no real headings
    actual_structured = structured and bool(clean)
    return {'headings': clean, 'heading_levels': clean_levels, 'raw_text': raw_text or '', 'structured': actual_structured}


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

    # If no raw_text either, there's nothing for the LLM to extract from — skip it
    if not headings and not raw_text:
        return {'headings': [], 'heading_levels': [], 'raw_text': '', 'ambiguous': False}

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


def build_ancestry_with_llm(
    ordered_headings: List[str],
    heading_levels: Dict[str, int] = None,
    document_text: str = "",
    batch_size: int = 40,
    max_workers: int = 4,
) -> Dict[str, List[str]]:
    """Send unique headings to the LLM in parallel batches to determine ancestry.
    Every batch receives the full list of root/chapter headings as invariant context
    so all batches are independent and can run concurrently.
    """
    if ollama is None or not ordered_headings:
        return {}

    _levels = heading_levels or {}
    _level_labels = {0: 'Root/Main', 1: 'Sub', 2: 'Sub-Sub', 3: 'Sub-Sub-Sub', 4: 'Sub-Sub-Sub-Sub'}

    # Pre-identify root headings (Level 0) — included in every batch as invariant context
    root_headings = {h: [] for h, lvl in _levels.items() if lvl == 0 and h in set(ordered_headings)}
    root_context = (
        "The following are the TOP-LEVEL (root) headings of this document — "
        "treat these as the chapter anchors when resolving ancestors:\n"
        + json.dumps(list(root_headings.keys()), ensure_ascii=False)
        + "\n\n"
    ) if root_headings else ""

    def _build_prompt(batch: List[str]) -> str:
        lines = []
        for i, h in enumerate(batch):
            lvl = _levels.get(h)
            if lvl is not None:
                label = _level_labels.get(lvl, f'Depth {lvl}')
                lines.append(f"{i + 1}. [Level {lvl} — {label}] {h}")
            else:
                lines.append(f"{i + 1}. {h}")
        numbered_list = "\n".join(lines)
        return (
            "You are building a precise heading hierarchy (Table of Contents) for a document.\n"
            "Below are headings in document order, each annotated with a SUGGESTED level\n"
            "(Level 0 = root/chapter, Level 1 = section, Level 2 = sub-section, Level 3 = detail).\n"
            "The suggested levels may be INCORRECT — use heading text semantics as primary signal.\n\n"
            + root_context
            + numbered_list + "\n\n"
            "TASK: For each heading, determine its full ANCESTOR chain — the list of parent headings\n"
            "from outermost ancestor down to immediate parent (NOT including the heading itself).\n\n"
            "SEMANTIC RULES (highest priority):\n"
            "1. Headings matching 'Chapter N', 'Chapter - N', 'Part N', 'Unit N', 'Module N' → ancestors = [].\n"
            "2. Topic headings directly following a Chapter are children of that Chapter.\n"
            "3. Sub-questions/exercises (e.g. 'Ques1:', 'Example:', 'Exercise N') are children of the nearest preceding topic.\n"
            "4. A heading that is clearly more specific than the preceding heading → treat as child.\n"
            "5. Use the CLOSEST preceding heading of logically higher scope as parent.\n"
            "6. Use heading text EXACTLY as provided — do not paraphrase.\n\n"
            "LEVEL RULES (secondary, use when semantics are ambiguous):\n"
            "- Level 0: ancestors = []\n"
            "- Level 1: [nearest Level 0]\n"
            "- Level 2: [Level 0, Level 1]\n"
            "- Level 3: [Level 0, Level 1, Level 2]\n\n"
            "Return ONLY a valid JSON object. Example:\n"
            '{"Chapter - 01": [], "Introduction to Python": ["Chapter - 01"], '
            '"What is Python?": ["Chapter - 01"], '
            '"Ques1: Write a program": ["Chapter - 01", "What is Python?"]}'
        )

    def _call_llm(batch: List[str]) -> Dict[str, List[str]]:
        prompt = _build_prompt(batch)
        try:
            resp = ollama.generate(model=LLM_MODEL, prompt=prompt, format='json')
            result = json.loads(resp.get('response', '{}'))
            partial = {}
            if isinstance(result, dict):
                for h in batch:
                    if h in result and isinstance(result[h], list):
                        partial[h] = [a for a in result[h] if isinstance(a, str)]
                    else:
                        partial[h] = []  # LLM missed it — will be gap-filled later
            return partial
        except Exception:
            return {h: [] for h in batch}

    # Split into batches
    batches = [
        ordered_headings[s:s + batch_size]
        for s in range(0, len(ordered_headings), batch_size)
    ]
    total_batches = len(batches)
    print(f"  Running {total_batches} batch(es) of up to {batch_size} headings in parallel (workers={min(max_workers, total_batches)})...")

    ancestry_map: Dict[str, List[str]] = {}

    with ThreadPoolExecutor(max_workers=min(max_workers, total_batches)) as executor:
        future_to_idx = {executor.submit(_call_llm, batch): idx for idx, batch in enumerate(batches)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            partial = future.result()
            ancestry_map.update(partial)
            print(f"  Batch {idx + 1}/{total_batches} done ({len(partial)} headings resolved).")

    return ancestry_map


def _validate_llm_ancestry(ancestry_map: Dict[str, List[str]], heading_levels: Dict[str, int]) -> bool:
    """Return True if the LLM-produced ancestry looks reasonable.
    Checks that most non-root headings actually have ancestors."""
    if not ancestry_map:
        return False
    non_root = [h for h, lvl in heading_levels.items() if lvl > 0 and h in ancestry_map]
    if not non_root:
        # No non-root headings to validate
        return True
    with_ancestors = sum(1 for h in non_root if ancestry_map.get(h))
    ratio = with_ancestors / len(non_root)
    return ratio >= 0.5


def _build_ancestry_stack(ordered_headings_leveled: List[tuple]) -> Dict[str, List[str]]:
    """Rule-based fallback: build ancestry using a heading stack and key-based levels."""
    heading_stack = []
    ancestry_map = {}
    for h, level in ordered_headings_leveled:
        while heading_stack and heading_stack[-1][1] >= level:
            heading_stack.pop()
        ancestry_map[h] = [item[0] for item in heading_stack]
        heading_stack.append((h, level))
    return ancestry_map


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

    # Collect unique headings in document order
    seen_headings = set()
    ordered_headings_text = []       # heading strings in document order
    ordered_headings_leveled = []    # (heading, level) tuples for rule-based fallback

    for chunk in normalized_chunks:
        levels_map = {}
        for hl in chunk.get('heading_levels', []):
            levels_map[hl['heading']] = hl['level']

        for h in chunk.get('headings', []):
            if h in seen_headings:
                continue
            seen_headings.add(h)
            ordered_headings_text.append(h)
            key_level = levels_map.get(h)
            ordered_headings_leveled.append((h, key_level if key_level is not None else 1))

    # --- Phase 1: Dot-numbered sub-sections (e.g. "6.1 X" is child of "6. Y") ---
    # Only bump when we find an EXPLICIT matching parent number.
    # e.g. "6.1 Regular Updates" → find "6. Maintenance" → make child.
    # If no matching numbered parent exists, leave the level unchanged —
    # same-level headings are siblings, not parent-child.
    _DOT_NUM_RE = re.compile(r'^(\d+)\.\d+')
    adjusted = list(ordered_headings_leveled)
    for i, (h, lvl) in enumerate(adjusted):
        dot_match = _DOT_NUM_RE.match(h)
        if dot_match:
            parent_num = dot_match.group(1)
            parent_pat = re.compile(rf'^{re.escape(parent_num)}[.)\s]')
            for j in range(i - 1, -1, -1):
                prev_h, prev_lvl = adjusted[j]
                if parent_pat.match(prev_h) and not _DOT_NUM_RE.match(prev_h):
                    # Found explicit parent like "6. Maintenance" — make child
                    adjusted[i] = (h, prev_lvl + 1)
                    break
    ordered_headings_leveled = adjusted

    # --- Phase 2: Numbered list items under a non-numbered parent ---
    # Only triggers when a "1. X" item immediately follows a non-numbered
    # heading at the same level, then bumps the whole 1→2→3 run.
    # Standalone section numbers like "6. Maintenance" are NOT bumped.
    adjusted2 = list(ordered_headings_leveled)
    _LIST_NUM_RE = re.compile(r'^(\d+)[.)\s]')
    i = 0
    while i < len(adjusted2):
        h, lvl = adjusted2[i]
        m = _LIST_NUM_RE.match(h)
        if m and not _DOT_NUM_RE.match(h) and m.group(1) == '1':
            # Found a "1. X" — look backward for a non-numbered heading at same level
            parent_idx = None
            for j in range(i - 1, -1, -1):
                prev_h, prev_lvl = adjusted2[j]
                if prev_lvl < lvl:
                    break
                if prev_lvl != lvl:
                    continue
                prev_m = _LIST_NUM_RE.match(prev_h)
                if prev_m and not _DOT_NUM_RE.match(prev_h):
                    # Another numbered item at same level before "1." —
                    # not a fresh sub-list
                    break
                if not prev_m:
                    parent_idx = j
                    break
            if parent_idx is not None:
                # Bump "1. X" and all consecutive numbered items at same level
                for k in range(i, len(adjusted2)):
                    kh, klvl = adjusted2[k]
                    km = _LIST_NUM_RE.match(kh)
                    if km and not _DOT_NUM_RE.match(kh) and klvl == lvl:
                        adjusted2[k] = (kh, lvl + 1)
                    else:
                        break
        i += 1
    ordered_headings_leveled = adjusted2

    # --- Phase 3: Semantic level correction ---
    # Task1 sometimes labels every heading in a chunk with the same key level
    # (e.g., all "Sub Sub Sub Heading" = level 3), even when some headings are
    # clearly top-level (Chapter/Part/Unit/Module markers).  Correct these before
    # passing level hints to the LLM so it gets accurate context.
    _CHAPTER_HEADING_RE = re.compile(
        r'^(?:chapter|part|unit|module|section|chapter[-\s]|part[-\s])\s*[-–—:.]?\s*\d+',
        re.IGNORECASE
    )
    adjusted3 = list(ordered_headings_leveled)
    for i, (h, lvl) in enumerate(adjusted3):
        if _CHAPTER_HEADING_RE.match(h) and lvl > 0:
            adjusted3[i] = (h, 0)  # Force recognised chapter markers to root
    ordered_headings_leveled = adjusted3

    # Build heading_levels map for LLM hints and validation
    heading_levels_map = {h: lvl for h, lvl in ordered_headings_leveled}

    # Build ancestry — always LLM when available, parallel batches for speed
    if use_llm and ollama is not None:
        t_llm = time.time()
        print(f"Building heading ancestry using LLM ({LLM_MODEL}) for {len(ordered_headings_text)} unique headings...")
        ancestry_map = build_ancestry_with_llm(
            ordered_headings_text,
            heading_levels=heading_levels_map,
        )
        print(f"LLM resolved {len(ancestry_map)} headings in {time.time()-t_llm:.1f}s (pure LLM).")
    else:
        ancestry_map = _build_ancestry_stack(ordered_headings_leveled)

    # Build a per-chunk heading cache from normalization (avoids re-extracting)
    chunk_heading_cache = [nc.get('headings', []) for nc in normalized_chunks]

    # Shallow copy each item — avoids deepcopy of entire dataset
    final_data = []
    for i, chunk in enumerate(original_data):
        annotated = dict(chunk)
        seen: set = set()
        ancestor_lists: list = []
        chunk_headings = chunk_heading_cache[i]
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
    parser.add_argument('input_file', nargs='?', default='data/sales_analysis_report4.json')
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
