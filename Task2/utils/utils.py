import re
import json
import os
import requests
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

# Load config from config.json
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
with open(_CONFIG_PATH, 'r', encoding='utf-8') as _f:
    _CONFIG = json.load(_f)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", _CONFIG["ollama"]["base_url"])
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", _CONFIG["ollama"]["model"])


def call_ollama(prompt: str, max_tokens: int = 400) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.1}
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException:
        return ""


def split_context_and_content(text: str) -> Tuple[List[str], List[str]]:
    context_lines = []
    raw_content_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r'^[A-Za-z0-9\s>]+:\s', line):
            context_lines.append(line)
        else:
            raw_content_lines.append(line)
    return context_lines, raw_content_lines


def clean_new_extractions(result: str, heading_context: str, num_lines: int) -> str:
    lines = result.strip().splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        skip_patterns = ["here are", "extracted", "following", "output:", "```", "note:"]
        if any(p in line.lower() for p in skip_patterns):
            continue
        line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        line = re.sub(r'^\s*>\s*', '', line)
        line = re.sub(r'^\s*\d+\.\s*', '', line)
        line = re.sub(r'^\s*[-•]\s*', '', line)
        line = line.strip()
        if not line:
            continue
        if ": " not in line:
            line = f"{heading_context}: {line}"
        cleaned.append(line)
        if len(cleaned) >= num_lines:
            break
    return "\n".join(cleaned)


def fallback_extract_new(raw_text: str, heading_context: str, num_lines: int) -> str:
    lines = [l.strip() for l in raw_text.splitlines() if l.strip() and len(l.strip()) > 10]
    result_lines = []
    for line in lines:
        if re.match(r'^page\s+\d+$', line.lower()):
            continue
        result_lines.append(f"{heading_context}: {line[:150]}")
        if len(result_lines) >= num_lines:
            break
    return "\n".join(result_lines)


def extract_new_lines_with_ollama(raw_text: str, heading_context: str, num_lines: int) -> str:
    if not raw_text.strip() or num_lines <= 0:
        return ""
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
    result = call_ollama(prompt, max_tokens=400)
    if not result:
        return fallback_extract_new(raw_text, heading_context, num_lines)
    return clean_new_extractions(result, heading_context, num_lines)


def extract_snippets_with_ollama(text: str, headings: List[str], num_lines: int, max_chars: int = 800) -> str:
    if not text.strip():
        return ""
    heading_context = " > ".join(h.replace(".....", "").strip() for h in headings[:2]) if headings else "Document"
    context_lines, raw_content_lines = split_context_and_content(text)
    kept_context = "\n".join(context_lines)
    if raw_content_lines and num_lines > 0:
        raw_text = "\n".join(raw_content_lines)
        new_extractions = extract_new_lines_with_ollama(raw_text, heading_context, num_lines)
    else:
        new_extractions = ""
    if kept_context and new_extractions:
        result = f"{kept_context}\n{new_extractions}"
    elif kept_context:
        result = kept_context
    else:
        result = new_extractions
    if len(result) > max_chars:
        result = result[:max_chars].rsplit('\n', 1)[0]
    return result


def load_entries(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]
    except json.JSONDecodeError:
        data = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return [entry for entry in data if isinstance(entry, dict)]


def find_chunk_key(entry: Dict) -> Optional[str]:
    for key in entry:
        if isinstance(key, str) and key.lower().startswith('chunk_id'):
            value = entry[key]
            if isinstance(value, dict):
                return key
    return None


def chunk_number_from_key(chunk_key: str) -> Optional[int]:
    if not isinstance(chunk_key, str):
        return None
    suffix = chunk_key[len('chunk_id'):]
    return int(suffix) if suffix.isdigit() else None


def get_text_field(entry: Dict) -> str:
    return entry.get('Text') or entry.get('text') or entry.get('extraction_text') or ""


def set_text_field(entry: Dict, value: str) -> None:
    if 'Text' in entry:
        entry['Text'] = value
    elif 'text' in entry:
        entry['text'] = value
    elif 'extraction_text' in entry:
        entry['extraction_text'] = value
    else:
        entry['Text'] = value


def flatten_heading_values(metadata: Any) -> List[str]:
    values = []
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                key_l = str(key).lower()
                if isinstance(value, str) and 'heading' in key_l:
                    stripped = value.strip()
                    if stripped and stripped not in values:
                        values.append(stripped)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(metadata)
    return values


def build_heading_hierarchy(headings: List[str]) -> str:
    if not headings:
        return ''
    parts = []
    for h in headings[:2]:
        h_clean = h.replace('.....', '').strip()
        if h_clean:
            parts.append(h_clean)
    return ' > '.join(parts) if parts else ''


def is_context_line(line: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9\s>]+:\s', line))


def is_heading_only_line(line: str, headings: List[str]) -> bool:
    line_clean = line.strip().lower()
    if len(line_clean) < 3:
        return True
    for h in headings:
        h_clean = h.strip().lower().replace('.....', '').strip()
        if line_clean == h_clean:
            return True
        if h_clean and line_clean.startswith(h_clean) and len(line_clean) < len(h_clean) + 5:
            return True
    return False


def is_page_marker(line: str) -> bool:
    return bool(re.match(r'^page\s+\d+$', line.strip().lower()))


def rebuild_metadata_with_accumulated_headings(original_meta: Dict, accumulated_headings: List[str]) -> Dict:
    new_meta = {}
    for i, heading in enumerate(accumulated_headings, start=1):
        key = f"Main Heading {i}"
        new_meta[key] = heading
    for key, value in original_meta.items():
        key_l = key.lower()
        if 'heading' in key_l and isinstance(value, str):
            continue
        if key not in new_meta:
            new_meta[key] = value
    return new_meta


def write_output(path: str, rows: List[Dict]) -> None:
    output_path = Path(path)
    if output_path.suffix.lower() == '.jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
