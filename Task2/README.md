Task2

Folder for Task2 extraction/normalization utilities. Contains three primary scripts that
process report chunks and produce structured/annotated JSON outputs. A shared
`config.py` centralizes defaults and output paths.

Scripts
- `run4.py`: cascading extractor — produces `structured2_chunks.json` (default output under `outputs/`).
- `run5.py`: deterministic normalizer/annotator — produces `<input_basename>_processed.json` under `outputs/` by default.
- `extract_ancestral_headings.py`: builds per-chunk `ancestral_headings` and writes `<input_basename>_ancestry_exact.json` under `outputs/` by default.

Default outputs (in `outputs/`)
- `structured2_chunks.json`
- `sales_analysis_report4_ancestry_exact.json`
- `sales_report_gemma8_processed.json`

Usage examples

```powershell
python Task2\run4.py ..\sales_report_gemma8.json
python Task2\run5.py ..\sales_report_gemma8.json
python Task2\extract_ancestral_headings.py ..\sales_analysis_report4.json
```

Configuration
- Edit `Langextract_Research/Task2/config/config.py` to change defaults (OLLAMA settings, default outputs, or behavior).
- Scripts import sensible defaults; you can still pass `--output` or positional output args to override.

Notes
- Each script will ensure `Task2/outputs` exists and will write outputs there by default.
- Placeholders in `outputs/` were added for convenience — run the scripts to regenerate authoritative files.
