# LangExtract — Weaviate RAG Evaluation Database

A Weaviate-backed evaluation framework that proves ancestral-heading-aware retrieval outperforms
plain text-only retrieval on real SWI (Standard Work Instruction) documents.
It ingests ancestry-annotated JSON chunks from Task2, indexes them into Weaviate with dual
vector fields (text + heading path), and computes retrieval metrics across two evaluation modes.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [File Descriptions](#file-descriptions)
4. [Architecture](#architecture)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Output Format](#output-format)
8. [Dependencies](#dependencies)

---

## Overview

The evaluation compares two retrieval strategies side-by-side:

| Strategy | Description |
|----------|-------------|
| **With Ancestral** | Combined score = `w_text × text_score + w_heading × heading_score` using a dedicated heading-path vector |
| **Without Ancestral** | Score = `text_score` only (heading vector ignored) |

Two evaluation modes are supported:

| Mode | Module | Purpose |
|------|--------|---------|
| `per_doc` | `tests/eval_per_doc.py` | Per-document title-query eval — one query per doc derived from the root heading |
| `multidoc` | `tests/eval_multidoc.py` | Multi-document Precision@K eval — shared index, cross-document query set |

---

## Project Structure

```
database/
├── main.py                     # CLI dispatcher — routes --test to the correct eval module
├── docker-compose.yml          # Weaviate + Ollama Docker services
│
├── config/
│   └── config.json             # All evaluation parameters (weaviate, ollama, eval_per_doc, eval_multidoc, db)
│
├── queries/                    # Per-document query Markdown files (one .md per SWI document)
│   ├── BatteryTestingSWIs_BatteryManagementTestingRev01.md
│   ├── FetchRobotics_CartConnect100_UnpackChargeRepackRev04.md
│   └── ...
│
├── output/                     # Generated evaluation Excel reports
│   ├── per_doc_title_query_results*.xlsx
│   └── multidoc_eval_results*.xlsx
│
└── tests/
    ├── db.py                   # Standalone retrieval script (single-query, with/without ancestral)
    ├── eval_per_doc.py         # Per-document evaluation module
    ├── eval_multidoc.py        # Multi-document evaluation module
    ├── gen_questions.py        # One-time helper: auto-derives title queries from Task2 output
    ├── run_all_queries.py      # Batch runner: auto-generates & runs all queries, outputs Excel
    ├── eval_queries.json       # Curated multi-doc evaluation query set
    └── questions.json          # Auto-generated per-doc title queries (from gen_questions.py)
```

---

## File Descriptions

### Root Files

| File | Description |
|------|-------------|
| `main.py` | **CLI dispatcher**. Parses `--test <name>` and `--config <path>`, looks up the module in `REGISTRY`, merges shared config keys (`weaviate`, `ollama`) with the test-specific section, and calls `run(cfg)`. Supports `--list` to enumerate available tests. |
| `docker-compose.yml` | Spins up a **Weaviate** vector database and makes Ollama accessible to the container via `host.docker.internal`. |

---

### config/

| File | Description |
|------|-------------|
| `config.json` | Central configuration. Contains five top-level sections: `weaviate`, `ollama`, `db` (single-query retrieval), `eval_per_doc`, and `eval_multidoc`. See [Configuration](#configuration) for details. |

---

### tests/

| File | Description |
|------|-------------|
| `eval_per_doc.py` | **Per-document title query evaluation**. Auto-discovers all JSON files in `Task2/output/` (excluding combined/notes files), inserts all chunks into a shared Weaviate index, derives a title query from each doc's root heading, runs retrieval with and without ancestral headings, computes 28 LG-mapped metrics + derived metrics, and writes a 2-sheet Excel report. |
| `eval_multidoc.py` | **Multi-document Precision@K evaluation**. Loads `combined_ancestry_exact.json`, indexes all chunks, runs each query from `eval_queries.json`, and measures Precision@K for both retrieval modes. Outputs a formatted Excel report. |
| `db.py` | **Standalone retrieval script**. Loads a single data file and runs one query defined in `config.json`. Useful for interactive testing. Requires `--with_ancestral` or `--without_ancestral` flag. |
| `gen_questions.py` | **One-time helper**. Scans `Task2/output/`, reads the root heading (depth-0 `ancestral_headings` entry) from each JSON, and writes `questions.json` with auto-derived title queries for `eval_per_doc`. |
| `run_all_queries.py` | **Batch runner**. Auto-generates queries from input JSON chunks, runs each through Weaviate in both modes, and aggregates all results into a single Excel file. |
| `eval_queries.json` | Curated query set for `eval_multidoc`. Each entry maps a natural-language query to its expected source document. |
| `questions.json` | Auto-generated per-doc title queries output by `gen_questions.py`. Used by `eval_per_doc` when `questions_file` is set in config. |

---

### queries/

One Markdown file per SWI document containing manually written or auto-generated natural-language
questions about that document. Used as the query set for per-document retrieval tests.

---

### output/

| File pattern | Description |
|---|---|
| `per_doc_title_query_results*.xlsx` | Per-document evaluation reports. Sheet 1: detailed per-(doc × rank) rows. Sheet 2: summary with metrics + colored footers. |
| `multidoc_eval_results*.xlsx` | Multi-document Precision@K evaluation reports. |

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                      SYSTEM ARCHITECTURE                          │
└───────────────────────────────────────────────────────────────────┘

  Task2/output/*_ancestry_exact.json
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│  INDEX PHASE  (per eval run)                                    │
│  ─────────────────────────────────────────────────              │
│  • Parse JSON chunks from Task2/output/                         │
│  • For each chunk:                                              │
│      - text_vector   ← embed(chunk["Text"])                     │
│      - heading_vector ← embed(build_heading_path(chunk))        │
│        where heading_path = "Root > Parent > Heading"           │
│  • Insert into Weaviate collection (chunk_id prefixed           │
│    "{file_stem}::{chunk_id_key}" for uniqueness)                │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│  RETRIEVAL PHASE  (per query)                                   │
│  ─────────────────────────────────────────────────              │
│  With Ancestral:                                                │
│    combined_score = w_text × text_score + w_heading × h_score  │
│    (default: w_text=0.4, w_heading=0.6 for per_doc)            │
│                                                                 │
│  Without Ancestral:                                             │
│    score = text_score only                                      │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│  METRICS  (eval_per_doc: 28 LG-mapped + derived)                │
│  ──────────────────────────────────────────────                 │
│  • Precision@K, Recall@K, MRR, NDCG                            │
│  • Hit Rate (HR@K)                                              │
│  • Mean Average Precision (MAP)                                 │
│  • Source attribution accuracy                                  │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
    database/output/*.xlsx
```

---

## Configuration

All settings live in `config/config.json`. The five top-level sections are:

### `weaviate`
```json
{
  "http_host": "localhost",
  "http_port": 8080,
  "grpc_host": "localhost",
  "grpc_port": 51051
}
```

### `ollama`
```json
{
  "host": "http://localhost:11434",
  "docker_endpoint": "http://host.docker.internal:11434",
  "embed_model": "bge-m3",
  "generative_model": "llama3:8b"
}
```

### `eval_per_doc`
```json
{
  "retrieval": {
    "w_text": 0.4,
    "w_heading": 0.6,
    "alpha": 0.4,
    "top_k_retrieve": 20,
    "top_n": 10
  },
  "task2_output_dir": "<path to Task2/output>",
  "exclude_files": ["combined_ancestry_exact.json", ...],
  "questions_file": "tests/questions.json",
  "excel_output_file": "output/per_doc_title_query_results7.xlsx"
}
```

### `eval_multidoc`
```json
{
  "retrieval": {
    "w_text": 0.5,
    "w_heading": 0.5,
    "top_k_retrieve": 18,
    "top_n": 9,
    "precision_k": 9
  },
  "eval_data_file": "<path to Task2/output/combined_ancestry_exact.json>",
  "queries_file": "eval_queries.json",
  "excel_output_file": "output/multidoc_eval_results3.xlsx"
}
```

### `db` (standalone retrieval via `db.py`)
```json
{
  "retrieval": {
    "min_score_threshold": 0.45,
    "w_text": 0.6,
    "w_heading": 0.4,
    "top_k_retrieve": 20,
    "top_n": 5
  },
  "data_file": "<path to a single Task2 output JSON>",
  "query": "Your natural language question here",
  "queries_md_file": "queries/<doc>.md",
  "excel_output_file": "output/<doc>.xlsx"
}
```

---

## Usage

### Prerequisites

1. Start Weaviate:
```bash
cd database
docker-compose up -d
```

2. Ensure Ollama is running with the required models:
```bash
ollama pull bge-m3
ollama pull llama3:8b
```

3. Generate `questions.json` (first time only):
```bash
python database/tests/gen_questions.py
```

---

### Run per-document evaluation

```bash
python database/main.py --test per_doc
```

Auto-discovers all docs in `Task2/output/`, runs title-query retrieval for each, and writes
`database/output/per_doc_title_query_results*.xlsx`.

---

### Run multi-document evaluation

```bash
python database/main.py --test multidoc
```

Loads `combined_ancestry_exact.json`, evaluates all queries in `eval_queries.json`, and writes
`database/output/multidoc_eval_results*.xlsx`.

---

### Run a single custom query (standalone)

```bash
python database/tests/db.py --with_ancestral
python database/tests/db.py --without_ancestral
```

The query and data file are read from the `db` section of `config/config.json`.

---

### Run batch queries over all docs

```bash
python database/tests/run_all_queries.py
```

Auto-generates queries from chunks, runs both modes, and writes a combined Excel report.

---

### List available tests

```bash
python database/main.py --list
```

---

### Use a custom config file

```bash
python database/main.py --test per_doc --config path/to/my_config.json
```

---

## Output Format

### Per-document eval Excel (`per_doc_title_query_results*.xlsx`)

**Sheet 1 — Detailed Results**

| Column | Description |
|--------|-------------|
| `doc_title` | Root heading / document title used as query |
| `rank` | Retrieved rank position (1-based) |
| `chunk_id` | Unique chunk identifier (`{file_stem}::{chunk_id_key}`) |
| `score_with` | Combined score (text + heading) |
| `score_without` | Text-only score |
| `correct_doc` | Whether the retrieved chunk belongs to the queried document |
| `heading_path` | Full heading path of the chunk |

**Sheet 2 — Summary**

One row per document with all 28 LG-mapped metrics plus derived metrics (Precision@K, Recall@K,
MRR, NDCG, Hit Rate, MAP) — both for *with ancestral* and *without ancestral* strategies.
Color-coded footers highlight the winning strategy per metric.

---

### Multi-doc eval Excel (`multidoc_eval_results*.xlsx`)

One row per query. Columns include Precision@K for both strategies, the expected source document,
and a comparison column indicating which strategy wins.

---

## Dependencies

- `weaviate-client` — Weaviate Python v4 client
- `requests` — HTTP calls to Ollama embed endpoint
- `openpyxl` — Excel report generation

Install:
```bash
pip install weaviate-client requests openpyxl
```
