"""
LangExtract Evaluation Runner — main entry point.

Dispatches to a registered evaluation module based on --test.
Each module in tests/ exposes a single `run(cfg: dict)` function.

Usage:
    python database/main.py --test per_doc
    python database/main.py --test per_doc --config path/to/config.json
    python database/main.py --test multidoc
    python database/main.py --list

All configuration lives in a single file: database/config/config.json
Shared keys (weaviate, ollama) are mixed with the test-specific section
(eval_per_doc or eval_multidoc) before being passed to run(cfg).

Registered tests
----------------
  per_doc   — Per-document title query eval  (tests/eval_per_doc.py)
  multidoc  — Multi-document query eval      (tests/eval_multidoc.py)

To add a new test:
  1. Create database/tests/eval_<name>.py and expose `run(cfg: dict) -> None`
  2. Add an entry to REGISTRY below with its section key in config/config.json
  3. Add the corresponding section to database/config/config.json
"""

import argparse
import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent

# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY  —  test_name → (module_name, section_key, default_config_path)
#   module_name       : filename (without .py) inside tests/
#   section_key       : top-level key in config/config.json whose sub-dict
#                       is merged with shared weaviate/ollama keys before
#                       being passed to run(cfg)
#   default_config_path: relative to BASE_DIR (database/)
# ─────────────────────────────────────────────────────────────────────────────
REGISTRY: dict[str, tuple[str, str, str]] = {
    "per_doc":  ("eval_per_doc",  "eval_per_doc",  "config/config.json"),
    "multidoc": ("eval_multidoc", "eval_multidoc", "config/config.json"),
}


def _load_cfg(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _import_run(module_name: str):
    """Dynamically import `run` from a module inside the tests/ subfolder."""
    import importlib.util

    mod_path = BASE_DIR / "tests" / f"{module_name}.py"
    if not mod_path.exists():
        print(f"[ERROR] Module not found: {mod_path}", file=sys.stderr)
        sys.exit(1)

    spec = importlib.util.spec_from_file_location(module_name, mod_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if not hasattr(mod, "run"):
        print(f"[ERROR] {module_name}.py does not expose a `run(cfg)` function.", file=sys.stderr)
        sys.exit(1)

    return mod.run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="LangExtract Evaluation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(
            [" Available tests:"]
            + [f"   {name:12s}  (default config: {default_cfg})" for name, (_, _, default_cfg) in REGISTRY.items()]
        ),
    )
    parser.add_argument(
        "--test",
        choices=list(REGISTRY.keys()),
        metavar="TEST",
        help=f"Evaluation to run. Choices: {', '.join(REGISTRY)}",
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="PATH",
        help="Path to unified config JSON. Uses config/config.json when omitted.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered tests and exit.",
    )

    args = parser.parse_args()

    if args.list:
        print("Registered tests:")
        for name, (module, section, default_cfg) in REGISTRY.items():
            print(f"  {name:12s}  module=tests/{module}.py  section={section}  config={default_cfg}")
        return

    if not args.test:
        parser.print_help()
        sys.exit(1)

    module_name, section_key, default_cfg_name = REGISTRY[args.test]

    cfg_path  = Path(args.config) if args.config else BASE_DIR / default_cfg_name
    full_cfg  = _load_cfg(cfg_path)
    # Merge shared keys (weaviate, ollama) with the test-specific section
    cfg = {**full_cfg, **full_cfg[section_key]}

    print(f"Test    : {args.test}")
    print(f"Module  : tests/{module_name}.py")
    print(f"Config  : {cfg_path}  [section: {section_key}]")
    print("=" * 70)

    run = _import_run(module_name)
    run(cfg)


if __name__ == "__main__":
    main()
