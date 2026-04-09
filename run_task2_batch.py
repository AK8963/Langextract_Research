"""
run_task2_batch.py
------------------
Batch-runs Task2/main.py on every JSON file found in:
    Task1/output/md_json_outputs/

Output files are written to:
    Task2/output/<original_filename>.json

Usage examples:
    python run_task2_batch.py                   # with LLM (default)
    python run_task2_batch.py --no-llm          # rule-based only, no Ollama
    python run_task2_batch.py --model llama3:8b # override Ollama model
    python run_task2_batch.py --skip-existing   # skip files already processed
"""

import argparse
import glob
import os
import subprocess
import sys
import time


# ---------------------------------------------------------------------------
# Paths (all relative to this script's directory = workspace root)
# ---------------------------------------------------------------------------
ROOT_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR   = os.path.join(ROOT_DIR, "Task1", "output", "md_json_outputs")
OUTPUT_DIR  = os.path.join(ROOT_DIR, "Task2", "output")
MAIN_SCRIPT = os.path.join(ROOT_DIR, "Task2", "main.py")


def collect_input_files() -> list[str]:
    """Return sorted list of JSON files in the input directory."""
    pattern = os.path.join(INPUT_DIR, "*.json")
    files = sorted(glob.glob(pattern))
    # Exclude any accidental directories that end with .json (shouldn't exist, but safe)
    return [f for f in files if os.path.isfile(f)]


def run_one(input_path: str, extra_args: list[str]) -> tuple[bool, float]:
    """Run Task2/main.py for a single input file.
    Returns (success: bool, elapsed_seconds: float).
    """
    filename   = os.path.basename(input_path)
    output_path = os.path.join(OUTPUT_DIR, filename)

    cmd = [
        sys.executable,        # same Python interpreter that launched this script
        MAIN_SCRIPT,
        input_path,
        "--output", output_path,
    ] + extra_args

    t0 = time.time()
    result = subprocess.run(cmd, capture_output=False, text=True)
    elapsed = time.time() - t0

    return result.returncode == 0, elapsed


def main():
    parser = argparse.ArgumentParser(
        description="Batch-run Task2/main.py on all JSON files from Task1/output/md_json_outputs/."
    )
    parser.add_argument("--no-llm", action="store_true",
                        help="Pass --no-llm to Task2/main.py (rule-based, no Ollama).")
    parser.add_argument("--hybrid", action="store_true",
                        help="Pass --hybrid to Task2/main.py.")
    parser.add_argument("--model", type=str, default=None,
                        help="Override Ollama model (passed via --model to Task2/main.py).")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip files whose output already exists in Task2/output/.")
    parser.add_argument("--progress-interval", type=int, default=10,
                        help="Progress-interval forwarded to Task2/main.py (default 10).")
    args = parser.parse_args()

    # Build list of extra args to forward
    extra: list[str] = ["--progress-interval", str(args.progress_interval)]
    if args.no_llm:
        extra.append("--no-llm")
    if args.hybrid:
        extra.append("--hybrid")
    if args.model:
        extra += ["--model", args.model]

    # Validate paths
    if not os.path.isdir(INPUT_DIR):
        print(f"[ERROR] Input directory not found:\n  {INPUT_DIR}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(MAIN_SCRIPT):
        print(f"[ERROR] Task2 main.py not found:\n  {MAIN_SCRIPT}", file=sys.stderr)
        sys.exit(1)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    input_files = collect_input_files()
    if not input_files:
        print(f"[WARN] No JSON files found in:\n  {INPUT_DIR}")
        sys.exit(0)

    # Apply --skip-existing filter
    if args.skip_existing:
        before = len(input_files)
        input_files = [
            f for f in input_files
            if not os.path.isfile(os.path.join(OUTPUT_DIR, os.path.basename(f)))
        ]
        skipped = before - len(input_files)
        if skipped:
            print(f"[INFO] Skipping {skipped} already-processed file(s).")

    total = len(input_files)
    print(f"\n{'='*60}")
    print(f"  Task2 Batch Processor")
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Output : {OUTPUT_DIR}")
    print(f"  Files  : {total}")
    print(f"  LLM    : {'disabled' if args.no_llm else 'enabled'}")
    if args.model:
        print(f"  Model  : {args.model}")
    print(f"{'='*60}\n")

    successes, failures = 0, 0
    failed_files: list[str] = []
    batch_start = time.time()

    for idx, input_path in enumerate(input_files, start=1):
        filename = os.path.basename(input_path)
        print(f"[{idx:>3}/{total}] Processing: {filename}")
        ok, elapsed = run_one(input_path, extra)
        if ok:
            successes += 1
            print(f"         Done in {elapsed:.1f}s  -> Task2/output/{filename}\n")
        else:
            failures += 1
            failed_files.append(filename)
            print(f"         [FAILED] after {elapsed:.1f}s\n")

    total_elapsed = time.time() - batch_start
    print(f"\n{'='*60}")
    print(f"  Batch complete in {total_elapsed:.1f}s")
    print(f"  Succeeded : {successes}")
    print(f"  Failed    : {failures}")
    if failed_files:
        print(f"\n  Failed files:")
        for fn in failed_files:
            print(f"    - {fn}")
    print(f"{'='*60}\n")

    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
