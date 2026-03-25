import time
import warnings
import requests
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery, HybridFusion, TargetVectors
from weaviate.config import AdditionalConfig, Timeout
from weaviate.exceptions import WeaviateQueryError
import math
import unicodedata
import json
from pathlib import Path

OLLAMA_HOST = "http://localhost:11434"  # used only for direct-embed fallback

warnings.filterwarnings("ignore", category=DeprecationWarning, module="weaviate")

MIN_SCORE_THRESHOLD = 0.45
# Weights for combined scoring (sum to 1.0)
W_TEXT = 0.7
W_HEADING = 0.3
# Retrieval and generation sizes
TOP_K_RETRIEVE = 20  # initial retrieve size per modality
TOP_N = 5             # final number of chunks to pass to the generator

# Single-line path to the source JSON (use this to override autodiscovery)
DATA_FILE = r"C:\Users\ls3412\langextract\Langextract_Research\Task2\output\notes_ancestry_exact.json"

# ========================
# 1. CONNECT TO WEAVIATE
# ========================
# query timeout set to 120s — sufficient for lightweight models
client = weaviate.connect_to_local(
    additional_config=AdditionalConfig(
        timeout=Timeout(init=30, query=120, insert=120)
    )
)

# ========================
# 2. CREATE COLLECTION
# ========================
if client.collections.exists("LangExtractDocs"):
    client.collections.delete("LangExtractDocs")

client.collections.create(
    name="LangExtractDocs",
    vector_config=[
        weaviate.classes.config.Configure.Vectors.text2vec_ollama(
            name="text_vector",
            source_properties=["text"],
            api_endpoint="http://host.docker.internal:11434",
            model="bge-m3",
        ),
        weaviate.classes.config.Configure.Vectors.text2vec_ollama(
            name="heading_vector",
            source_properties=["heading_path"],
            api_endpoint="http://host.docker.internal:11434",
            model="bge-m3",
        ),
    ],
    generative_config=weaviate.classes.config.Configure.Generative.ollama(
        api_endpoint="http://host.docker.internal:11434",
        model="llama3:latest",   # lightweight, ~2 GB, good accuracy/speed balance
    ),
    properties=[
        Property(name="text", data_type=DataType.TEXT),
        Property(name="heading_path", data_type=DataType.TEXT),
        Property(name="main_heading", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="sub_headings", data_type=DataType.TEXT_ARRAY, skip_vectorization=True),
        Property(name="ancestral_headings", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="metadata_str", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="chunk_id", data_type=DataType.TEXT, skip_vectorization=True),
    ]
)

print("Collection 'LangExtractDocs' created successfully.")

# ========================
# 3. INSERT DATA
# ========================
collection = client.collections.use("LangExtractDocs")

try:
    # Prefer explicit DATA_FILE path if provided by the user
    json_path = Path(DATA_FILE) if DATA_FILE else None
    if not (json_path and json_path.exists()):
        base_dir = Path(__file__).resolve().parent.parent
        _search_paths = [
            base_dir / "Task2" / "output" / "notes_ancestry_exact.json",
            base_dir / "Task2" / "data" / "notes_ancestry_exact.json",
            base_dir / "Langextract_Research" / "Task2" / "output" / "notes_ancestry_exact.json",
            base_dir / "Langextract_Research" / "Task2" / "data" / "notes_ancestry_exact.json",
        ]
        json_path = next((p for p in _search_paths if p.exists()), None)
        if json_path is None:
            found = list(base_dir.rglob("notes_ancestry_exact.json"))
            json_path = found[0] if found else None
    if json_path is None or not json_path.exists():
        tried = [str(Path(DATA_FILE))] if DATA_FILE else []
        tried += [str(p) for p in _search_paths]
        raise FileNotFoundError(
            "notes_ancestry_exact.json not found. Tried: " + ", ".join(tried)
        )
    print(f"Loading data from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def _clean(s: str) -> str:
        """Strip control/formatting chars and normalize Unicode to prevent
        Ollama returning NaN vectors for malformed input strings."""
        if not s:
            return ""
        s = unicodedata.normalize("NFKC", s)
        s = "".join(
            c for c in s
            if unicodedata.category(c) not in ("Cc", "Cf") or c in "\t\n\r"
        )
        return s.strip()

    def build_heading_path(chunk_data: dict) -> str:
        anc = chunk_data.get("ancestral_headings", {})
        if not isinstance(anc, dict):
            return ""
        paths = []
        for heading, ancestors in anc.items():
            if isinstance(ancestors, list) and ancestors:
                paths.append(" > ".join(ancestors + [heading]))
            else:
                paths.append(heading)
        if paths:
            paths.sort(key=lambda p: p.count(" > "), reverse=True)
            return paths[0]
        return ""

    def _embed_direct(text: str) -> list | None:
        try:
            r = requests.post(
                f"{OLLAMA_HOST}/api/embed",
                json={"model": "bge-m3", "input": text or "document"},
                timeout=60,
            )
            r.raise_for_status()
            vec = r.json().get("embeddings", [[]])[0]
            if any(math.isnan(v) or math.isinf(v) for v in vec):
                return None
            return vec
        except Exception:
            return None

    for item in data:
        for chunk_id, chunk_data in item.items():
            if chunk_id in ("Text", "Metadata"):
                continue

            text = item.get("Text", "")
            metadata_str = item.get("Metadata", "")

            main_heading = ""
            sub_headings = []
            for key, value in chunk_data.items():
                if key == "ancestral_headings":
                    continue
                if "Main Heading" in key:
                    main_heading = value
                elif "Sub Heading" in key or "Sub Sub Heading" in key:
                    sub_headings.append(value)

            ancestral_headings_str = json.dumps(chunk_data.get("ancestral_headings", {}))
            heading_path = build_heading_path(chunk_data)

            # Deep sanitization
            text = _clean(str(text) if text is not None else "")
            heading_path = _clean(str(heading_path) if heading_path is not None else "")

            if not heading_path:
                if main_heading and main_heading.strip():
                    heading_path = _clean(main_heading)
                elif text:
                    heading_path = text[:80]
                else:
                    print(f"Skipping chunk {chunk_id}: no text or heading available.")
                    continue

            obj = {
                "text": text,
                "heading_path": heading_path,
                "main_heading": main_heading,
                "sub_headings": sub_headings,
                "ancestral_headings": ancestral_headings_str,
                "metadata_str": metadata_str,
                "chunk_id": chunk_id,
            }

            _insert_obj = dict(obj)
            safe_text = _insert_obj["text"]
            safe_hp = _insert_obj["heading_path"]

            inserted = False
            for insert_attempt in range(3):
                try:
                    collection.data.insert(_insert_obj)
                    inserted = True
                    break
                except Exception as e:
                    err_msg = str(e)
                    if insert_attempt == 0:
                        wait = 1
                        print(f"Insert attempt 1 failed for chunk {chunk_id} (retrying in {wait}s, truncating content): {err_msg}")
                        time.sleep(wait)
                        _insert_obj = {
                            **_insert_obj,
                            "text": _insert_obj["text"][:512],
                            "heading_path": _insert_obj["heading_path"][:100],
                        }
                    elif insert_attempt == 1:
                        wait = 2
                        print(f"Insert attempt 2 failed for chunk {chunk_id} (retrying in {wait}s, ASCII-only): {err_msg}")
                        time.sleep(wait)
                        safe_text = "".join(c for c in _insert_obj["text"][:256] if ord(c) < 128).strip() or "document content"
                        safe_hp = "".join(c for c in _insert_obj["heading_path"] if ord(c) < 128).strip() or "document section"
                        _insert_obj = {
                            **_insert_obj,
                            "text": safe_text,
                            "heading_path": safe_hp,
                        }
                    else:
                        # Final fallback: direct embed and inject vectors
                        print(f"All retries failed for chunk {chunk_id} — trying direct-embed fallback...")
                        t_vec = _embed_direct(safe_text) or _embed_direct("document content")
                        h_vec = _embed_direct(safe_hp) or _embed_direct("document section")
                        if t_vec is None or h_vec is None:
                            print(f"Skipping chunk {chunk_id}: Ollama embed returns NaN consistently.")
                        else:
                            try:
                                collection.data.insert(
                                    _insert_obj,
                                    vector={"text_vector": t_vec, "heading_vector": h_vec},
                                )
                                inserted = True
                                print(f"Direct-embed fallback succeeded for chunk {chunk_id}.")
                            except Exception as fallback_err:
                                print(f"Insert failed for chunk {chunk_id} after all attempts: {fallback_err}")

            if not inserted:
                # record or log; continue importing other chunks
                continue

    print("Data inserted successfully.")

    # ========================
    # 4. RETRIEVAL (hybrid search, no generation timeout)
    # ========================
    # We intentionally split retrieval from generation:
    #   - collection.query.hybrid()  →  retrieves chunks via Weaviate (fast)
    #   - requests.post(Ollama)       →  generates answer directly (no gRPC timeout)
    # This avoids the context-deadline-exceeded error that occurs when
    # collection.generate.hybrid() must wait for a slow LLM through Weaviate's
    # gRPC connection.
    query = "Explain about python?"

    # Perform separate hybrid searches for text and heading so we can
    # compute independent scores and then combine them.
    search_text = None
    for attempt in range(3):
        try:
            search_text = collection.query.hybrid(
                query=query,
                target_vector=TargetVectors.sum(["text_vector"]),
                query_properties=["text"],
                alpha=0.7,
                fusion_type=HybridFusion.RELATIVE_SCORE,
                limit=TOP_K_RETRIEVE,
                return_metadata=MetadataQuery(score=True),
            )
            break
        except WeaviateQueryError as e:
            print(f"Text search attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))

    search_heading = None
    for attempt in range(3):
        try:
            search_heading = collection.query.hybrid(
                query=query,
                target_vector=TargetVectors.sum(["heading_vector"]),
                query_properties=["heading_path"],
                alpha=0.7,
                fusion_type=HybridFusion.RELATIVE_SCORE,
                limit=TOP_K_RETRIEVE,
                return_metadata=MetadataQuery(score=True),
            )
            break
        except WeaviateQueryError as e:
            print(f"Heading search attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))

    if (not search_text or not getattr(search_text, 'objects', None)) and (not search_heading or not getattr(search_heading, 'objects', None)):
        print("Search returned no results.")
        response_search = None
    else:
        # Build score maps
        text_scores = {}
        heading_scores = {}
        if search_text and getattr(search_text, 'objects', None):
            for o in search_text.objects:
                cid = o.properties.get('chunk_id', '')
                s = o.metadata.score if o.metadata and o.metadata.score is not None else 0.0
                text_scores[cid] = max(text_scores.get(cid, 0.0), s)
        if search_heading and getattr(search_heading, 'objects', None):
            for o in search_heading.objects:
                cid = o.properties.get('chunk_id', '')
                s = o.metadata.score if o.metadata and o.metadata.score is not None else 0.0
                heading_scores[cid] = max(heading_scores.get(cid, 0.0), s)

        # Union of chunk ids
        all_chunk_ids = set(list(text_scores.keys()) + list(heading_scores.keys()))

        # Normalise each modality to [0,1] by dividing by max observed
        max_text = max(text_scores.values()) if text_scores else 1.0
        max_heading = max(heading_scores.values()) if heading_scores else 1.0
        if max_text == 0:
            max_text = 1.0
        if max_heading == 0:
            max_heading = 1.0

        combined_list = []
        # Fetch properties for each chunk_id from one of the search results
        def find_obj_by_chunk(cid: str):
            for src in (search_text, search_heading):
                if not src or not getattr(src, 'objects', None):
                    continue
                for o in src.objects:
                    if o.properties.get('chunk_id', '') == cid:
                        return o
            return None

        for cid in all_chunk_ids:
            t = text_scores.get(cid, 0.0) / max_text
            h = heading_scores.get(cid, 0.0) / max_heading
            combined = W_TEXT * t + W_HEADING * h
            obj = find_obj_by_chunk(cid)
            combined_list.append((cid, t, h, combined, obj))

        # Sort by combined score desc and keep top-N
        combined_list.sort(key=lambda x: x[3], reverse=True)
        selected = combined_list[:TOP_N]

        # ========================
        # 5. OUTPUT — retriever only, JSONL per chunk
        # ========================
        # Each output record contains:
        #   query, chunk_id, text_score (chunk relevance), ancestral_score
        #   (heading relevance), combined_score, heading_path (full breadcrumb),
        #   ancestral_headings (raw dict), chunk_text (full text of chunk)
        print("\n=== Retrieval Results ===")
        records = []
        for cid, t_score, h_score, combined, wobj in selected:
            if wobj is None:
                continue
            props = wobj.properties
            # Parse the stored ancestral_headings JSON back to a dict
            try:
                anc_dict = json.loads(props.get("ancestral_headings", "{}"))
            except (json.JSONDecodeError, TypeError):
                anc_dict = {}

            record = {
                "query":             query,
                "chunk_id":          cid,
                "text_score":        round(t_score, 6),
                "ancestral_score":   round(h_score, 6),
                "combined_score":    round(combined, 6),
                "heading_path":      props.get("heading_path", ""),
                "ancestral_headings": anc_dict,
                "chunk_text":        props.get("text", ""),
            }
            records.append(record)

            # Console summary
            print(f"\n  chunk_id       : {cid}")
            print(f"  text_score     : {t_score:.4f}")
            print(f"  ancestral_score: {h_score:.4f}")
            print(f"  combined_score : {combined:.4f}")
            print(f"  heading_path   : {record['heading_path']}")
            # Print each ancestral heading level
            for heading, ancestors in anc_dict.items():
                breadcrumb = " > ".join(ancestors + [heading]) if ancestors else heading
                print(f"    ancestral: {breadcrumb}")
            print(f"  chunk_text     : {record['chunk_text'][:200]}{'...' if len(record['chunk_text']) > 200 else ''}")

        # Save to JSONL — one JSON object per line
        out_path = Path(__file__).resolve().parent / "retrieval_results.jsonl"
        try:
            with open(out_path, "w", encoding="utf-8") as out_f:
                for rec in records:
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"\nSaved {len(records)} records to: {out_path}")
        except Exception as e:
            print(f"Failed to save JSONL: {e}")
finally:
    client.close()