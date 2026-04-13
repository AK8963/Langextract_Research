# Langextract Research

An end-to-end pipeline for extracting structured knowledge from documents and evaluating the quality of ancestral-heading-aware RAG (Retrieval-Augmented Generation) retrieval. The project is organised into three sequential tasks and a shared evaluation database module.

---

## Project Overview

| Stage | Module | Purpose |
|-------|--------|---------|
| 1 | [Task1](Task1/README.md) | PDF → Markdown → Hierarchical JSON extraction |
| 2 | [Task2](Task2/README.md) | JSON → Ancestral heading annotation |
| 3 | [database](database/README.md) | Weaviate-based RAG evaluation (per-doc & multi-doc) |

---

## Repository Structure

```
Langextract_run/
├── .gitignore                  # Excludes large data/output folders and cache
├── README.md                   # This file
├── results.txt                 # Top-level run notes / results summary
├── results1.txt                # Additional run results
├── run_task2_batch.py          # Convenience script: batch-runs Task2 over multiple docs
│
├── Task1/                      # Stage 1 — PDF → Markdown → JSON extraction
│   ├── main.py / main.ipynb
│   ├── config/                 # config.json + loader
│   ├── extraction/             # Heading extractor
│   ├── processing/             # Excel metrics builder
│   ├── prompts/                # LLM prompts & few-shot examples
│   ├── utils/                  # pdf_to_md, validation helpers
│   ├── data/                   # ⚠ gitignored — PDF inputs & intermediate .md files
│   └── output/
│       ├── md_json_outputs/    # ⚠ gitignored — extracted JSON chunks per doc
│       └── metrics_results/    # Excel metrics reports (tracked)
│
├── Task2/                      # Stage 2 — Ancestry annotation
│   ├── main.py
│   ├── config/
│   ├── utils/                  # Normalizer, cascading extractor, shared helpers
│   └── output/                 # ⚠ gitignored — ancestry-annotated JSON files
│
├── database/                   # Stage 3 — Weaviate RAG evaluation
│   ├── main.py                 # CLI dispatcher
│   ├── docker-compose.yml      # Weaviate + Ollama services
│   ├── config/config.json      # All evaluation parameters
│   ├── queries/                # Per-doc query Markdown files
│   ├── output/                 # Evaluation Excel reports
│   └── tests/                  # Evaluation modules (eval_per_doc, eval_multidoc, …)
│
└── my_venv313/                 # Python 3.13 virtual environment (not tracked)
```

> **Note:** `Task1/data/`, `Task1/output/md_json_outputs/`, `Task2/output/`, `**/__pycache__/`, and `**/.ipynb_checkpoints/` are listed in `.gitignore` and are not committed to the repository.

---

## End-to-End Pipeline

```
 PDFs (Task1/data/)
      │
      ▼
 [Task1]  PDF → Markdown → Heading extraction → JSON chunks
      │        (output: Task1/output/md_json_outputs/*.json)
      ▼
 [Task2]  JSON chunks → Ancestry annotation
      │        (output: Task2/output/*_ancestry_exact.json)
      ▼
 [database]  Load into Weaviate → RAG evaluation
                  (output: database/output/*.xlsx)
```

---

## Prerequisites

- **Python 3.13+**
- **Ollama** running locally (`http://localhost:11434`) with models:
  - `gemma2:9b` — Task1 extraction
  - `gemma2:2b` — Task2 ancestry
  - `bge-m3` — database embeddings
  - `llama3:8b` — database generative queries
- **Weaviate** (via Docker): `cd database && docker-compose up -d`

---

## Quick Start

```bash
# 1. Activate virtual environment
.\my_venv313\Scripts\Activate.ps1

# 2. Run Task1 extraction on a Markdown file
cd Task1
python main.py "data/Markdowns/your_document.md"

# 3. Run Task2 ancestry annotation
cd ../Task2
python main.py output/your_document.json

# 4. Start Weaviate
cd ../database
docker-compose up -d

# 5. Run per-document evaluation
python main.py --test per_doc

# 6. Run multi-document evaluation
python main.py --test multidoc
```

---

## Dependencies

Each sub-module has its own dependency file:

| Module | File |
|--------|------|
| Task1 | `Task1/requirements313.txt` |
| Task2 | `Task2/utils/requirements.txt` |
| database | install `weaviate-client`, `requests`, `openpyxl` |

Install for Task1:
```bash
pip install -r Task1/requirements313.txt
```