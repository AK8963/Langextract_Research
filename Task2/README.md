# LangExtract Heading Normalization & Ancestry Pipeline

A modular Python pipeline for normalizing structured JSON chunks and resolving hierarchical heading ancestry using LLM-based analysis with Ollama. The pipeline takes heading-structured JSON chunks (output from Task1) and enriches them with full ancestral heading chains for each chunk.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [File Descriptions](#file-descriptions)
4. [Pipeline Flow](#pipeline-flow)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Output Format](#output-format)
8. [Dependencies](#dependencies)

---

## Project Overview

This project takes structured JSON chunks produced by Task1's extraction pipeline and adds a full hierarchical ancestry map to each chunk. The two-stage pipeline:

1. **Normalize**: Detect headings within each chunk via structured key parsing (`Main Heading N` / `Sub Heading N` keys), regex fallback, or optional LLM disambiguation
2. **Ancestry Resolution**: Collect all unique headings in document order, infer depth levels, then resolve each heading's full ancestor chain (root to parent) using an LLM — falling back to a deterministic stack algorithm when LLM output fails validation

Key technologies:
- **Ollama**: Local LLM runtime (default model: `gemma2:2b`)
- **LangExtract**: LLM-based extraction framework (used in cascading extractor)
- **Rule-based ancestry**: Heading-stack fallback for reliable deterministic output
- **Cascading context extraction**: Growing-context enrichment of chunk metadata

---

## Project Structure

```
Task2/
├── main.py                         # Entry point - orchestrates normalization and ancestry
├── __init__.py                     # Package initializer
│
├── config/                         # Configuration module
│   ├── __init__.py                 # Config package initializer
│   └── config.json                 # All configurable parameters
│
├── utils/                          # Utility and processing scripts
│   ├── __init__.py                 # Utils package initializer
│   ├── utils.py                    # Ollama HTTP helpers, text splitting, entry loading
│   ├── summary_metadata.py         # Cascading extractor - enriches chunks via growing context
│   ├── without_markdown.py         # Deterministic normalizer/annotator
│   └── requirements.txt            # Python dependencies
│
├── data/                           # Input files
│   ├── without_markdown.json
│   └── with_markdown.json
│
└── output/                         # Generated output files
    ├── summary_chunks.json                  # Cascading extractor output
    ├── without_markdown.json                # Ancestry-annotated output (no-markdown input)
    └── with_markdown.json                   # Normalizer/annotator output (markdown input)
```

---

## File Descriptions

### Root Files

| File | Description |
|------|-------------|
| `main.py` | **Entry point** - Orchestrates the full normalization and ancestry pipeline. Runs `process_document()` which loads a JSON input, normalizes headings per chunk, builds a heading ancestry map, and injects `ancestral_headings` into each chunk. |
| `__init__.py` | Package initializer. |

---

### config/

| File | Description |
|------|-------------|
| `config.json` | **Central configuration file** containing all tunable parameters: <br>• `ollama`: LLM base URL and model name <br>• `processing`: Default lines-per-level and max summary characters <br>• `paths`: Output directory and default output file paths |
| `__init__.py` | Config package initializer. |

---

### utils/

| File | Description |
|------|-------------|
| `utils.py` | **Shared utility functions**: <br>• `call_ollama()`: HTTP POST to the Ollama `/api/generate` endpoint <br>• `split_context_and_content()`: Splits chunk text into context lines vs. raw content lines <br>• `extract_new_lines_with_ollama()`: Extracts key lines from raw text via Ollama <br>• `extract_snippets_with_ollama()`: Builds enriched snippet strings for a chunk <br>• `load_entries()`: Loads JSON or JSONL files into a list of dicts <br>• `find_chunk_key()` / `chunk_number_from_key()`: Chunk key helpers <br>• `get_text_field()` / `set_text_field()`: Text field accessors across key variants <br>• `flatten_heading_values()`: Flattens heading values out of nested metadata dicts |
| `summary_metadata.py` | **Cascading extractor**: Processes JSON/JSONL chunks using a growing context approach with Ollama. Extracts key lines from each chunk, builds cumulative context, and enriches subsequent chunks' metadata. Outputs `output/summary_chunks.json`. |
| `without_markdown.py` | **Deterministic normalizer/annotator**: Normalizes chunk headings without relying on Markdown formatting. Uses deterministic heading detection with optional LLM fallback. Outputs `output/without_markdown.json`. |
| `requirements.txt` | Python dependencies for the Task2 pipeline. |

---

### data/

| Path | Description |
|------|-------------|
| `data/without_markdown.json` | Input JSON chunks that do not contain Markdown formatting — heading structure is conveyed purely through named keys (`Main Heading N`, `Sub Heading N`, etc.). |
| `data/with_markdown.json` | Input JSON chunks that retain Markdown heading markers (`#`, `##`, `###`) in the `Text` field, used by the normalizer to cross-reference heading levels. |

---

### output/

| Path | Description |
|------|-------------|
| `output/summary_chunks.json` | Cascading-extractor output — chunks enriched with accumulated context metadata from `summary_metadata.py`. |
| `output/without_markdown.json` | Ancestry-annotated output from processing `data/without_markdown.json` — each chunk enriched with `ancestral_headings`. |
| `output/with_markdown.json` | Normalizer output from processing `data/with_markdown.json` — normalized and annotated chunks. |

---

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         PIPELINE FLOW                           │
└─────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────┐
    │   INPUT JSON/JSONL chunks      │
    │   (data/ — output from Task1)  │
    └───────────────┬────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: Load & Parse  [main.py: load_input()]                   │
│  ──────────────────────────────────────────────                  │
│  • Reads JSON array or JSONL                                     │
│  • Normalizes nested chunk maps (chunk_idN → heading dict)       │
│  • Handles dict roots with 'chunks' or 'data' keys              │
└──────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: Normalize Headings  [main.py: normalize_chunk_with_llm()]│
│  ──────────────────────────────────────────────────────────────  │
│  • BFS walk to find 'Main Heading N' / 'Sub Heading N' keys      │
│  • Extracts depth level from key prefix (Sub count)              │
│  • Regex fallback for unnamed heading-like strings               │
│  • LLM disambiguation for ambiguous chunks (optional)            │
└──────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3: Collect & Adjust Heading Levels  [main.py]              │
│  ─────────────────────────────────────────────────────          │
│  • Collect unique headings in document order                     │
│  • Bump dot-numbered sub-sections (e.g. "6.1 X" → child of "6") │
│  • Bump numbered list runs under non-numbered parent headings    │
└──────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4: Build Ancestry Map  [main.py: build_ancestry_with_llm()]│
│  ──────────────────────────────────────────────────────────────  │
│  • Sends headings in batches to Ollama with depth annotations    │
│  • LLM returns {heading: [ancestors...]} JSON                    │
│  • Validates output: ≥50% of non-root headings must have parents │
│  • Falls back to rule-based heading stack on validation failure  │
└──────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 5: Annotate & Write Output  [main.py]                      │
│  ─────────────────────────────────────────                       │
│  • Injects ancestral_headings into each chunk's heading dict     │
│  • Preserves original JSON structure                             │
│  • Writes to output/without_markdown.json or output/with_markdown.json │
└──────────────────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────────┐
    │  output/without_markdown.json            │
    │  output/with_markdown.json               │
    └──────────────────────────────────────────┘
```

---

## Configuration

All settings are in `config/config.json`:

### Ollama Settings
```json
"ollama": {
    "base_url": "http://localhost:11434",   // Ollama server URL
    "model": "gemma2:2b"                    // LLM model name
}
```

### Processing Settings
```json
"processing": {
    "default_lines_per_level": 1,           // Extracted lines per heading level
    "default_max_summary_chars": 0          // Max chars for summary (0 = unlimited)
}
```

### Path Settings
```json
"paths": {
    "outputs_dir": "outputs",
    "structured2_out": "outputs/summary_chunks.json",
    "ancestry_exact_out": "outputs/without_markdown.json",
    "run5_processed_out": "outputs/with_markdown.json"
}
```

Override Ollama settings at runtime without editing config:
```bash
set OLLAMA_BASE_URL=http://localhost:11434   # Windows
set OLLAMA_MODEL=llama3:8b                   # Windows
```

---

## Usage

### Run ancestry extraction on without-markdown input

```bash
cd Task2
python main.py data/without_markdown.json
```

Processes `data/without_markdown.json` and writes `output/without_markdown.json`.

### Run ancestry extraction on with-markdown input

```bash
python main.py data/with_markdown.json
```

Processes `data/with_markdown.json` and writes `output/with_markdown.json`.

### Custom output path

```bash
python main.py data/without_markdown.json --output output/my_output.json
```

### Override document title

```bash
python main.py data/without_markdown.json --title "Sales Analysis Report"
```

### Disable LLM (rule-based ancestry only)

```bash
python main.py data/without_markdown.json --no-llm
```

### Hybrid mode (LLM only for ambiguous chunks)

```bash
python main.py data/without_markdown.json --hybrid
```

### Use a different Ollama model

```bash
python main.py data/without_markdown.json --model llama3:8b
```

### Run the cascading extractor

```bash
python utils/summary_metadata.py data/without_markdown.json output/summary_chunks.json
```

### Run the deterministic normalizer

```bash
python utils/without_markdown.py data/with_markdown.json output/with_markdown.json
```

### CLI arguments (`main.py`)

| Argument | Default | Description |
|---|---|---|
| `input_file` | positional | Path to input JSON file |
| `--output / -o` | `<input_basename>_ancestry_exact.json` | Output file path |
| `--no-llm` | off | Disable Ollama; use rule-based ancestry only |
| `--hybrid` | off | Rule-based first; LLM only for ambiguous chunks |
| `--model` | from `config.json` | Override Ollama model name |
| `--title` | auto-detected | Force a specific document root title |
| `--progress-interval` | `10` | Print progress every N chunks (0 = silent) |

---

## Output Format

### Ancestry-Annotated JSON (`output/without_markdown.json` / `output/with_markdown.json`)

The output preserves the original input structure with an injected `ancestral_headings` key inside each chunk's heading map. `ancestral_headings` maps each heading text to its ordered list of ancestors from the document root down to the immediate parent.

**Structure:**

```json
[
    {
        "chunk_id1": {
            "Main Heading 1": "Sales Analysis Report .....",
            "Sub Heading 1": "Executive Summary .....",
            "ancestral_headings": {
                "Sales Analysis Report": [],
                "Executive Summary": ["Sales Analysis Report"]
            }
        },
        "Text": "Raw text content of this chunk...",
        "Metadata": "\"Main heading\": \"Sales Analysis Report: ........first 200 chars.........\""
    },
    {
        "chunk_id2": {
            "Sub Heading 2": "Regional Performance .....",
            "Sub Sub Heading 1": "North America Results .....",
            "ancestral_headings": {
                "Regional Performance": ["Sales Analysis Report"],
                "North America Results": ["Sales Analysis Report", "Regional Performance"]
            }
        },
        "Text": "Raw text content of chunk 2...",
        "Metadata": "\"Sub heading\": \"Regional Performance: ........\""
    }
]
```

**Key details:**

- **`ancestral_headings`** — Injected inside the chunk's heading map dict (the nested `chunk_idN` object). Maps each heading string to a list of ancestor headings ordered outermost (root) to innermost (immediate parent).
- **Root headings** (Level 0 / `Main Heading N`) map to `[]`.
- **Non-root headings** list their full ancestor chain, e.g. `["Root", "Parent"]`.
- **Original fields** (`Text`, `Metadata`, heading keys) are preserved unchanged.

### Heading Depth Labels (Input Convention from Task1)

| Level | Key Label | Example Key |
|-------|-----------|-------------|
| 0 | `Main Heading N` | `"Main Heading 1"` |
| 1 | `Sub Heading N` | `"Sub Heading 2"` |
| 2 | `Sub Sub Heading N` | `"Sub Sub Heading 1"` |
| 3 | `Sub Sub Sub Heading N` | `"Sub Sub Sub Heading 3"` |
| 4 | `Sub Sub Sub Sub Heading N` | `"Sub Sub Sub Sub Heading 1"` |

---

## Dependencies

- `ollama` — Local LLM Python client for Ollama runtime
- `requests` — HTTP calls to Ollama `/api/generate` endpoint
- `langextract` — LLM-based extraction framework (used in cascading extractor)

Install all dependencies:

```bash
pip install -r utils/requirements.txt
```
