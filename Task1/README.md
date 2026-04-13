# LangExtract Markdown Heading Extraction Pipeline

A modular Python pipeline for extracting hierarchical headings from documents using LLM-based extraction with LangExtract. The pipeline converts PDFs to Markdown first, then extracts structured headings and outputs JSON chunks alongside Excel metrics reports.

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
9. [Metrics](#metrics)

---

## Project Overview

This project extracts structural headings from documents and organizes them into hierarchical JSON chunks suitable for RAG (Retrieval-Augmented Generation) applications. The two-stage pipeline:

1. **PDF → Markdown**: Uses an Ollama-hosted LLM to convert PDFs into clean Markdown text
2. **Markdown → JSON + Excel**: Extracts headings from Markdown, builds hierarchical JSON chunks, and generates an Excel metrics report

Key technologies:
- **LangExtract**: LLM-based heading extraction using few-shot prompting
- **Ollama**: Local LLM runtime (default model: `gemma2:9b`)
- **LangChain Text Splitters**: Intelligent text chunking
- **openpyxl**: Excel metrics report generation
- **Regex Fallback**: Robust extraction when LLM output cannot be parsed

---

## Project Structure

```
Task1/
├── main.py                         # Entry point - orchestrates the pipeline
├── main.ipynb                      # Jupyter notebook version of the pipeline
├── requirements313.txt             # Python 3.13 dependencies
├── requirements314.txt             # Python 3.14 dependencies
├── __init__.py                     # Package initializer
├── .gitignore                      # Git ignore rules
│
├── config/                         # Configuration module
│   ├── __init__.py                 # Config loader with exported constants
│   └── config.json                 # All configurable parameters
│
├── prompts/                        # LLM prompts and examples
│   ├── __init__.py
│   └── prompts.py                  # Extraction prompt and few-shot examples
│
├── extraction/                     # Markdown reading and heading extraction
│   ├── __init__.py
│   └── extractor.py                # Markdown parsing, LLM extraction, validation
│
├── processing/                     # Post-processing and report generation
│   ├── __init__.py
│   └── excel.py                    # Excel metrics report builder
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── pdf_to_md.py                # PDF → Markdown conversion via Ollama LLM
│   └── utils.py                    # Validation, text processing, formatting
│
├── data/                           # ⚠ gitignored — not committed to the repo
│   ├── *.pdf                       # Input PDF documents
│   └── Markdowns/                  # Intermediate Markdown files (PDF → MD)
│
└── output/                         # Generated output files
    ├── md_json_outputs/             # ⚠ gitignored — hierarchical JSON chunks per doc
    └── metrics_results/             # Excel metrics reports (tracked in git)
```

---

## File Descriptions

### Root Files

| File | Description |
|------|-------------|
| `main.py` | **Entry point** - Orchestrates the full extraction pipeline. Runs `process_markdown()` which reads a Markdown file, extracts headings, builds JSON output, and generates an Excel metrics report. |
| `main.ipynb` | **Jupyter notebook** version of the pipeline for interactive use and experimentation. |
| `requirements313.txt` | Python 3.13-compatible dependencies. |
| `requirements314.txt` | Python 3.14-compatible dependencies. |
| `__init__.py` | Package initializer with version info. |

---

### config/

| File | Description |
|------|-------------|
| `config.json` | **Central configuration file** containing all tunable parameters: <br>• `model`: LLM settings (model_id, timeout, retries) <br>• `output`: Output file path <br>• `text_splitter`: Chunk size and overlap settings <br>• `settings`: Verbose mode, fallback regex toggle <br>• `heading_detection`: Keywords for level-1 headings and regex patterns to filter false positives |
| `__init__.py` | **Config loader** - Reads `config.json` and exports constants like `MODEL_ID`, `TIMEOUT`, `TEXT_SPLITTER_CHUNK_SIZE`, `MARKDOWN_PATH`, etc. as Python variables for easy import. |

---

### prompts/

| File | Description |
|------|-------------|
| `prompts.py` | Contains the **LLM extraction prompt** and **few-shot examples**: <br>• `EXTRACTION_PROMPT`: Detailed instructions for the LLM on what constitutes a heading vs body text <br>• `EXTRACTION_EXAMPLES`: Example documents with correct heading extractions for few-shot learning |

---

### extraction/

| File | Description |
|------|-------------|
| `extractor.py` | **Core extraction logic**: <br>• `get_markdown_text()`: Reads and parses a Markdown file <br>• `split_text_into_chunks()`: Uses RecursiveCharacterTextSplitter with adaptive sizing <br>• `extract_headings_from_chunks()`: Calls LangExtract per chunk with retry logic and regex fallback <br>• `validate_and_deduplicate_headings()`: Filters false positives, removes duplicates, validates against source text <br>• `extract_sections_with_text()`: Maps each heading to its text content |

---

### processing/

| File | Description |
|------|-------------|
| `excel.py` | **Excel metrics report generator**: <br>• `generate_excel_report()`: Takes run metrics from `main.py` and writes a formatted `.xlsx` file to `output/metrics_results/` <br>• Captures document stats, chunk counts, heading rejection breakdown, LLM call counts, token usage, and timing data |

---

### utils/

| File | Description |
|------|-------------|
| `pdf_to_md.py` | **PDF → Markdown converter**: <br>• `convert_pdf_to_markdown()`: Uses an Ollama-hosted LLM to convert a PDF file into a clean Markdown file saved under `data/Markdowns/` |
| `utils.py` | **Utility functions** organized into categories: <br><br>**Validation:** `is_valid_heading_in_text()`, `is_false_heading()`, `is_likely_body_text()`, `is_page_marker()` <br>**Heading Processing:** `determine_heading_level()`, `find_heading_position()`, `find_heading_in_original()`, `normalize_for_dedup()` <br>**Text Processing:** `preprocess_chunk()`, `extract_headings_regex()`, `scan_for_missed_headings()` <br>**Output Formatting:** `print_header()`, `print_step()`, `print_metrics_table()` |

---

### data/  *(gitignored — local only)*

| Path | Description |
|------|-------------|
| `data/*.pdf` | Input PDF documents to be processed. Not committed to the repository. |
| `data/Markdowns/` | Intermediate Markdown files generated by `pdf_to_md.py`. Serve as input to the extraction pipeline. Not committed to the repository. |

---

### output/

| Path | Description |
|------|-------------|
| `output/md_json_outputs/` | *(gitignored)* Hierarchical JSON files produced from Markdown extraction. One JSON per processed document. Generated locally. |
| `output/metrics_results/` | Excel (`.xlsx`) metrics reports. One file per pipeline run, named `<document>_metrics.xlsx`. Tracked in git. |

---

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         PIPELINE FLOW                           │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  INPUT PDF   │
    │  (data/)     │
    └──────┬───────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: PDF → Markdown Conversion  [utils/pdf_to_md.py]         │
│  ──────────────────────────────────────────────────────          │
│  • convert_pdf_to_markdown()                                     │
│  • Sends PDF pages to Ollama LLM for structured Markdown output  │
│  • Saves .md file to data/Markdowns/                             │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: Markdown Text Reading  [extraction/extractor.py]        │
│  ────────────────────────────────────────────────────            │
│  • get_markdown_text()                                           │
│  • Reads and parses the .md file                                 │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3: Text Chunking  [extraction/extractor.py]                │
│  ──────────────────────────────────────────────                  │
│  • split_text_into_chunks()                                      │
│  • RecursiveCharacterTextSplitter with adaptive sizing           │
│  • Default: 2500 chars / 500 overlap                             │
│  • Large docs (>500K chars): 6000 chars / 1000 overlap           │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4: Heading Extraction (Per Chunk)  [extraction/extractor]  │
│  ──────────────────────────────────────────────────────────────  │
│  • extract_headings_from_chunks()                                │
│  • For each chunk:                                               │
│    1. Preprocess (clean math, code, LaTeX)                       │
│    2. Call LangExtract with prompt + few-shot examples           │
│    3. Retry up to MAX_RETRIES times on failure                   │
│    4. Fallback to regex extraction if LLM fails                  │
│  • Post-scan full text for missed numbered headings              │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 5: Output Generation                                       │
│  ─────────────────────────                                       │
│  • JSON written to output/md_json_outputs/                       │
│  • Excel metrics report written to output/metrics_results/       │
│    via generate_excel_report() in processing/excel.py            │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────┐
    │  output/md_json_outputs/*.json  │
    │  output/metrics_results/*.xlsx  │
    └─────────────────────────────────┘
```

---

## Configuration

All settings are in `config/config.json`:

### Model Settings
```json
"model": {
    "model_id": "gemma2:9b",    // Ollama LLM model
    "timeout": 1200,            // Request timeout (seconds)
    "max_retries": 3,           // Retry attempts per chunk
    "retry_delay": 3            // Delay between retries (seconds)
}
```

### Text Splitter Settings
```json
"text_splitter": {
    "chunk_size": 2500,         // Characters per chunk
    "chunk_overlap": 500        // Overlap between chunks
}
```

### Heading Detection
```json
"heading_detection": {
    "level_1_keywords": ["chapter", "appendix", ...],   // Top-level heading keywords
    "false_heading_patterns": ["^Figure\\s+\\d+", ...]  // Regex patterns to filter out
}
```

---

## Usage

### Step 1 — Convert PDF to Markdown (one-time per document)

```python
from utils.pdf_to_md import convert_pdf_to_markdown

convert_pdf_to_markdown(
    pdf_path="data/your_document.pdf",
    output_md_path="data/Markdowns/your_document.md",
    ollama_model="gemma2:9b"
)
```

### Step 2 — Run Heading Extraction

#### From the command line:
```bash
cd Task1
python main.py
```

This processes the default Markdown path defined in `config/config.json`.

#### Custom Markdown file:
```bash
python main.py "data/Markdowns/your_document.md"
```

#### From the Jupyter Notebook:
Open `main.ipynb` and run the cells interactively.

---

## Output Format

### JSON (`output/md_json_outputs/`)

Each document produces a JSON array where every element corresponds to one text chunk. Each chunk object contains a heading map and the raw Markdown text of that chunk.

**Structure:**

```json
[
    {
        "chunk_id1": {
            "Main Heading 1": "Chapter Title .....",
            "Sub Heading 1": "Section Name .....",
            "Sub Sub Heading 1": "Subsection Name .....",
            "Sub Sub Sub Heading 1": "Deep Section .....",
            "Sub Sub Sub Heading 2": "Another Deep Section .....",
            "Sub Sub Sub Sub Heading 1": "Deepest Level ....."
        },
        "Text": "Raw Markdown content of this chunk, including code blocks, tables, images, and links...",
        "Metadata": "\"Main heading\": \"Chapter Title: ........first 200 chars of section content.........\", \"Sub heading\": \"Section Name: ........first 200 chars.........\""
    },
    {
        "chunk_id2": {
            "Sub Heading 1": "Careers with Python .....",
            "Sub Heading 2": "Python Tutorial Playlist .....",
            "Sub Sub Sub Heading 1": "Chapter - 02 .....",
            "Sub Sub Sub Heading 2": "Python Installation & Setup .....",
            "Sub Heading 3": "Install Python IDE .....",
            "Sub Sub Sub Heading 3": "Chapter - 03 .....",
            "Sub Heading 4": "First Python Program ....."
        },
        "Text": "Raw Markdown content of chunk 2...",
        "Metadata": "\"Sub heading\": \"Careers with Python: ........Python is not only one of the most popular...........\""
    }
]
```

**Key details:**

- **`chunk_idN`** — Sequential chunk identifier starting from `chunk_id1`.
- **Heading keys** — Label + counter per heading level: `Main Heading N`, `Sub Heading N`, `Sub Sub Heading N`, `Sub Sub Sub Heading N`, `Sub Sub Sub Sub Heading N`. Counters reset per chunk.
- **Heading values** — The extracted heading text followed by ` .....` (5 dots).
- **`Text`** — The full raw Markdown of the chunk, preserving code fences, tables, image references, and hyperlinks.
- **`Metadata`** — A string of `"<level label>": "<heading text>: ........<first ~200 chars of section content>........."` entries, one per heading in the chunk.

### Heading Level Labels

| Level | Key Label | Example Key |
|-------|-----------|-------------|
| 1 | `Main Heading N` | `"Main Heading 1"` |
| 2 | `Sub Heading N` | `"Sub Heading 2"` |
| 3 | `Sub Sub Heading N` | `"Sub Sub Heading 1"` |
| 4 | `Sub Sub Sub Heading N` | `"Sub Sub Sub Heading 3"` |
| 5 | `Sub Sub Sub Sub Heading N` | `"Sub Sub Sub Sub Heading 1"` |

### Excel Metrics (`output/metrics_results/`)

Each run produces an `.xlsx` file with:
- Document name, length, chunk size
- Raw vs validated heading counts
- Rejection breakdown (false patterns, body text, duplicates, not found in text)
- LLM call count, input/output token usage
- Timing: document retrieval, extraction, LLM processing
- Per-chunk LLM timing

---

## Dependencies

- `langextract` — LLM-based extraction framework
- `langchain-text-splitters` — Text chunking
- `ollama` — Local LLM runtime
- `openpyxl` — Excel report generation
- `PyMuPDF` (fitz) — Used in `pdf_to_md.py` for PDF page reading

Install dependencies for your Python version:

```bash
# Python 3.13
pip install -r requirements313.txt

# Python 3.14
pip install -r requirements314.txt
```

---

## Metrics

The pipeline captures and exports the following metrics to Excel:

| Metric | Description |
|--------|-------------|
| Document length | Total character count of the Markdown input |
| Total chunks | Number of text chunks processed |
| Raw headings | Headings returned by LLM before validation |
| Valid headings | Headings after all validation filters |
| Rejected (false pattern) | Filtered by false-positive regex (figures, tables, etc.) |
| Rejected (body text) | Filtered as likely body text |
| Rejected (duplicate) | Removed as normalized duplicates |
| Rejected (not in text) | Heading not found in source via fuzzy match |
| LLM calls | Total LLM API calls made |
| Input / Output tokens | Token usage per run |
| LLM success rate | Chunks successfully parsed by LLM vs regex fallbacks |
| Timing | Per-stage timing: retrieval, extraction, LLM processing |
