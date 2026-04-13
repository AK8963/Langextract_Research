"""
One-time helper: scans Task2/output/ and writes questions.json
with the auto-derived title_query for every document.
Run from the repo root:
    python database/tests/gen_questions.py
"""
import json
import pathlib

TASK2_DIR = pathlib.Path("Task2/output")
OUT_FILE   = pathlib.Path("database/tests/questions.json")
EXCLUDE    = {
    "combined_ancestry_exact.json",
    "notes_ancestry_exact.json",
    "with_markdown.json",
    "without_markdown.json",
}


def get_root_heading(data: list) -> str:
    for item in data:
        for k, v in item.items():
            if k.startswith("chunk_id") and isinstance(v, dict):
                anc = v.get("ancestral_headings", {})
                if isinstance(anc, dict):
                    for heading, ancestors in anc.items():
                        if isinstance(ancestors, list) and len(ancestors) == 0:
                            return heading
    return "UNKNOWN"


result = {}
for f in sorted(TASK2_DIR.glob("*.json")):
    if f.name in EXCLUDE:
        continue
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"SKIP {f.name}: {e}")
        continue
    if not isinstance(data, list):
        print(f"SKIP {f.name}: not a list")
        continue
    root = get_root_heading(data)
    result[f.stem] = {
        "title_query": root,
        "extra_questions": [],
    }

OUT_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Written {len(result)} entries to {OUT_FILE}")
for k, v in result.items():
    print(f"  {k}: {v['title_query']}")
