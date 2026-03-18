"""Central configuration for Langextract_Research/Task2.

This file exposes shared constants used by the Task2 scripts (run4/run5,
extract_ancestral_headings, and helpers). Values are workspace-relative so
the scripts can import these defaults instead of hardcoding them.
"""
import os

# Processing defaults
DEFAULT_LINES_PER_LEVEL = 1
DEFAULT_MAX_SUMMARY_CHARS = 0

# Ollama configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2:2b")

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = BASE_DIR
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')

RUN4_PATH = os.path.join(SCRIPTS_DIR, 'run4.py')
RUN5_PATH = os.path.join(SCRIPTS_DIR, 'run5.py')
EXTRACT_ANCESTRY_PATH = os.path.join(SCRIPTS_DIR, 'extract_ancestral_headings.py')

# Default output files (inside Task2/outputs)
STRUCTURED2_OUT = os.path.join(OUTPUTS_DIR, 'structured2_chunks.json')
ANCESTRY_EXACT_OUT = os.path.join(OUTPUTS_DIR, 'sales_analysis_report4_ancestry_exact.json')
RUN5_PROCESSED_OUT = os.path.join(OUTPUTS_DIR, 'sales_report_gemma8_processed.json')

# Ensure outputs dir exists when imported
os.makedirs(OUTPUTS_DIR, exist_ok=True)
