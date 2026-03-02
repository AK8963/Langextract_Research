# LangExtract PDF Heading Extraction Pipeline

A modular Python pipeline for extracting hierarchical headings from PDF documents using LLM-based extraction with LangExtract and intelligent fallback mechanisms.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [File Descriptions](#file-descriptions)
4. [Pipeline Flow](#pipeline-flow)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Output Format](#output-format)

---

## Project Overview

This project extracts structural headings from PDF documents and organizes them into hierarchical JSON chunks suitable for RAG (Retrieval-Augmented Generation) applications. It uses:

- **PyMuPDF (fitz)**: For PDF text extraction
- **LangExtract**: For LLM-based heading extraction using few-shot prompting
- **LangChain Text Splitters**: For intelligent text chunking
- **Regex Fallback**: For robust extraction when LLM fails

---

## Project Structure

```
Langextract_project/
├── main.py                     # Entry point - orchestrates the pipeline
├── requirements.txt            # Python dependencies
├── __init__.py                 # Package initializer
│
├── config/                     # Configuration module
│   ├── __init__.py             # Config loader with exported constants
│   └── config.json             # All configurable parameters
│
├── prompts/                    # LLM prompts and examples
│   ├── __init__.py
│   └── prompts.py              # Extraction prompt and few-shot examples
│
├── extraction/                 # PDF and heading extraction logic
│   ├── __init__.py
│   └── extractor.py            # PDF parsing, LLM extraction, validation
│
├── processing/                 # Post-processing and chunk building
│   ├── __init__.py
│   └── chunk_builder.py        # Hierarchical chunk construction
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   └── utils.py                # Validation, text processing, formatting
│
├── data/                       # Input PDF files
│   ├── book.pdf
│   ├── chap3.pdf
│   ├── machinelearningregression.pdf
│   ├── notes.pdf
│   ├── paper.pdf
│   ├── report.pdf
│   └── sales_analysis_report.pdf
│
└── output/                     # Generated JSON output files
    ├── book.json
    ├── machinelearningregression.json
    ├── notes.json
    └── sales_analysis_report.json
```

---

## File Descriptions

### Root Files

| File | Description |
|------|-------------|
| `main.py` | **Entry point** - Orchestrates the 6-step extraction pipeline. Imports from all modules and runs `process_pdf()` function. |
| `requirements.txt` | Lists all Python dependencies (langextract, PyMuPDF, langchain, etc.) |
| `__init__.py` | Package initializer with version info |

---

### config/

| File | Description |
|------|-------------|
| `config.json` | **Central configuration file** containing all tunable parameters: <br>• `model`: LLM settings (model_id, timeout, retries) <br>• `output`: Output file path <br>• `text_splitter`: Chunk size and overlap settings <br>• `settings`: Verbose mode, fallback regex toggle <br>• `heading_detection`: Keywords for level-1 headings and regex patterns to filter false positives |
| `__init__.py` | **Config loader** - Reads `config.json` and exports constants like `MODEL_ID`, `TIMEOUT`, `TEXT_SPLITTER_CHUNK_SIZE`, etc. as Python variables for easy import |

---

### prompts/

| File | Description |
|------|-------------|
| `prompts.py` | Contains the **LLM extraction prompt** and **few-shot examples**: <br>• `EXTRACTION_PROMPT`: Detailed instructions for the LLM on what constitutes a heading vs body text <br>• `EXTRACTION_EXAMPLES`: Two example documents with correct heading extractions for few-shot learning |

---

### extraction/

| File | Description |
|------|-------------|
| `extractor.py` | **Core extraction logic** with these functions: <br>• `get_pdf_text()`: Extracts text from PDF using PyMuPDF, removes TOC artifacts <br>• `split_text_into_chunks()`: Uses RecursiveCharacterTextSplitter with adaptive sizing <br>• `extract_headings_from_chunks()`: Calls LangExtract for each chunk with retry logic and regex fallback <br>• `validate_and_deduplicate_headings()`: Filters false positives, removes duplicates, validates against source text <br>• `extract_sections_with_text()`: Maps headings to their text content |

---

### processing/

| File | Description |
|------|-------------|
| `chunk_builder.py` | **Hierarchical chunk construction**: <br>• `build_hierarchical_chunks()`: Takes validated sections and builds structured JSON output <br>• Creates chunks based on document structure (Level-1 starts new chunk, Level-2 can start new chunk, Level-3+ stays with parent) <br>• Generates output format with Parent Heading, Main Heading, Sub Headings, and combined Text |

---

### utils/

| File | Description |
|------|-------------|
| `utils.py` | **Utility functions** organized into categories: <br><br>**Validation Functions:** <br>• `is_valid_heading_in_text()`: Fuzzy matching to verify heading exists in document <br>• `is_false_heading()`: Checks against false positive patterns (figures, tables, etc.) <br>• `is_likely_body_text()`: Detects body text masquerading as headings <br>• `is_page_marker()`: Identifies page number artifacts <br><br>**Heading Processing:** <br>• `determine_heading_level()`: Assigns level (1-5) based on numbering pattern <br>• `find_heading_position()`: Locates heading in document text <br>• `find_heading_in_original()`: Precise position finding with fallbacks <br>• `normalize_for_dedup()`: Normalizes text for duplicate detection <br><br>**Text Processing:** <br>• `preprocess_chunk()`: Cleans chunks before LLM (removes math, code, LaTeX) <br>• `extract_headings_regex()`: Fallback regex-based extraction <br>• `scan_for_missed_headings()`: Post-processing scan for missed numbered headings <br><br>**Output Formatting:** <br>• `print_header()`, `print_step()`, `print_metrics_table()`: Console output formatting |

---

### data/

Contains input PDF files to be processed. Place your PDFs here.

### output/

Contains generated JSON files with extracted hierarchical headings and text content.

---

## Pipeline Flow

The extraction pipeline follows these 6 steps:

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
│  STEP 1: PDF Text Extraction                                     │
│  ─────────────────────────────                                   │
│  • get_pdf_text() in extractor.py                                │
│  • Uses PyMuPDF to extract raw text                              │
│  • Removes TOC artifacts (dotted lines, page numbers)            │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: Text Chunking                                           │
│  ─────────────────────                                           │
│  • split_text_into_chunks() in extractor.py                      │
│  • RecursiveCharacterTextSplitter with adaptive sizing           │
│  • Default: 2500 chars, 500 overlap                              │
│  • Large docs (>500K chars): 6000 chars, 1000 overlap            │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3: Heading Extraction (Per Chunk)                          │
│  ───────────────────────────────────────                         │
│  • extract_headings_from_chunks() in extractor.py                │
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
│  STEP 4: Validation & Deduplication                              │
│  ──────────────────────────────────                              │
│  • validate_and_deduplicate_headings() in extractor.py           │
│  • Filter false positives (figures, tables, body text)           │
│  • Check heading exists in source text (fuzzy matching)          │
│  • Remove duplicates with normalized comparison                  │
│  • Re-assign heading levels using consistent rules               │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 5: Section Text Extraction                                 │
│  ───────────────────────────────                                 │
│  • extract_sections_with_text() in extractor.py                  │
│  • Find precise position of each heading                         │
│  • Extract text from heading to next heading                     │
│  • Limit section size to prevent huge blocks                     │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  STEP 6: Hierarchical Chunk Building                             │
│  ───────────────────────────────────                             │
│  • build_hierarchical_chunks() in chunk_builder.py               │
│  • Create chunk boundaries based on heading levels               │
│  • Build nested structure: Parent > Main > Sub headings          │
│  • Combine text content for each chunk                           │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │ OUTPUT JSON  │
    │  (output/)   │
    └──────────────┘
```

---

## Configuration

All settings are in `config/config.json`:

### Model Settings
```json
"model": {
    "model_id": "gemma2:9b",    // LLM model (Ollama)
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
    "level_1_keywords": ["chapter", "appendix", ...],  // Top-level heading keywords
    "false_heading_patterns": ["^Figure\\s+\\d+", ...]  // Regex patterns to filter
}
```

---

## Usage

### Basic Usage

```bash
cd Langextract_project
python main.py
```

This processes the default PDF (`data/book.pdf`).

### Custom PDF

```bash
python main.py "data/your_document.pdf"
```

### From Parent Directory

```bash
python Langextract_project/main.py "Langextract_project/data/report.pdf"
```

---

## Output Format

The pipeline generates JSON with hierarchical chunks:

```json
[
    {
        "chunk_id1": {
            "Parent Heading": "Document Title .....",
            "Main Heading 1": "1 Introduction .....",
            "1 Introduction Details": {
                "Sub Heading 1": "1.1 Background .....",
                "Sub Heading 2": "1.2 Objectives ....."
            }
        },
        "Text": "Full text content of this chunk..."
    },
    {
        "chunk_id2": {
            "Parent Heading": "Document Title .....",
            "Main Heading 1": "2 Methods ....."
        },
        "Text": "Methods section text content..."
    }
]
```

### Heading Levels

| Level | Description | Examples |
|-------|-------------|----------|
| 1 | Document title, Chapter | "Machine Learning Fundamentals", "Chapter 3" |
| 2 | Major sections | "1 Introduction", "Conclusion", "References" |
| 3 | Subsections | "1.1 Background", "2.3 Data Processing" |
| 4 | Sub-subsections | "1.1.1 History", "2.3.1 Cleaning Steps" |
| 5 | Deep nesting | "1.1.1.1.1 Specific Detail" |

---

## Dependencies

- `langextract` - LLM-based extraction framework
- `PyMuPDF` (fitz) - PDF text extraction
- `langchain-text-splitters` - Text chunking
- `ollama` - Local LLM runtime (for gemma2:9b)

Install with:
```bash
pip install -r requirements.txt
```

---

## Metrics

The pipeline outputs detailed metrics including:
- Document length and chunk count
- Raw vs validated heading counts
- Rejection reasons (false patterns, body text, duplicates)
- Heading level distribution
- LLM success rate vs regex fallbacks
