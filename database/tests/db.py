import argparse
import time
import warnings
import requests
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery, HybridFusion, TargetVectors, Filter
from weaviate.config import AdditionalConfig, Timeout
from weaviate.exceptions import WeaviateQueryError
import math
import unicodedata
import json
from pathlib import Path
import sys
import io

# Ensure UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ========================
# LOAD CONFIG
# ========================
_config_path = Path(__file__).resolve().parent.parent / "config" / "config.json"
with open(_config_path, "r", encoding="utf-8") as _cfg_f:
    _full_cfg = json.load(_cfg_f)
# Merge shared keys (weaviate, ollama) with the db-specific section
_cfg = {**_full_cfg, **_full_cfg["db"]}

# ========================
# CLI ARGUMENTS
# ========================
_parser = argparse.ArgumentParser(description="LangExtract DB retrieval pipeline")
_group = _parser.add_mutually_exclusive_group(required=True)
_group.add_argument("--with_ancestral", action="store_true", help="Include ancestral headings in retrieval output")
_group.add_argument("--without_ancestral", action="store_true", help="Exclude ancestral headings from retrieval output")
args = _parser.parse_args()
INCLUDE_ANCESTRAL = args.with_ancestral

warnings.filterwarnings("ignore", category=DeprecationWarning, module="weaviate")

# Parameters loaded from config.json
OLLAMA_HOST          = _cfg["ollama"]["host"]               # used only for direct-embed fallback
OLLAMA_DOCKER_EP     = _cfg["ollama"]["docker_endpoint"]
EMBED_MODEL          = _cfg["ollama"]["embed_model"]
GENERATIVE_MODEL     = _cfg["ollama"]["generative_model"]
MIN_SCORE_THRESHOLD  = _cfg["retrieval"]["min_score_threshold"]
W_TEXT               = _cfg["retrieval"]["w_text"]          # weight for text score (sum to 1.0)
W_HEADING            = _cfg["retrieval"]["w_heading"]       # weight for heading score
TOP_K_RETRIEVE       = _cfg["retrieval"]["top_k_retrieve"]  # initial retrieve size per modality
TOP_N                = _cfg["retrieval"]["top_n"]           # final number of chunks to pass to the generator
DATA_FILE            = _cfg["data_file"]                    # path to source JSON
query                = _cfg["query"]
METADATA_FILTERS     = _cfg.get("metadata_filters", {})     # optional property-level filters

# ========================
# 1. CONNECT TO WEAVIATE
# ========================
# query timeout set to 120s — sufficient for lightweight models
# Connect to custom gRPC port 51051 on localhost
client = weaviate.connect_to_custom(
    http_host=_cfg["weaviate"]["http_host"],
    http_port=_cfg["weaviate"]["http_port"],
    http_secure=False,
    grpc_host=_cfg["weaviate"]["grpc_host"],
    grpc_port=_cfg["weaviate"]["grpc_port"],
    grpc_secure=False,
    skip_init_checks=True,
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
            api_endpoint=OLLAMA_DOCKER_EP,
            model=EMBED_MODEL,
        ),
        weaviate.classes.config.Configure.Vectors.text2vec_ollama(
            name="heading_vector",
            source_properties=["heading_path"],
            api_endpoint=OLLAMA_DOCKER_EP,
            model=EMBED_MODEL,
        ),
    ],
    generative_config=weaviate.classes.config.Configure.Generative.ollama(
        api_endpoint=OLLAMA_DOCKER_EP,
        model=GENERATIVE_MODEL,
    ),
    properties=[
        Property(name="text", data_type=DataType.TEXT),
        Property(name="heading_path", data_type=DataType.TEXT),
        Property(name="main_heading", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="sub_headings", data_type=DataType.TEXT_ARRAY, skip_vectorization=True),
        Property(name="ancestral_headings", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="metadata_str", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="chunk_id", data_type=DataType.TEXT, skip_vectorization=True),
        # Filterable metadata properties
        Property(name="doc_source", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="heading_level", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="top_section", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="has_code", data_type=DataType.BOOL, skip_vectorization=True),
        Property(name="has_images", data_type=DataType.BOOL, skip_vectorization=True),
    ]
)

print("Collection 'LangExtractDocs' created successfully.")

# ========================
# 3. INSERT DATA
# ========================
collection = client.collections.use("LangExtractDocs")

try:
    json_path = Path(DATA_FILE)
    if not json_path.exists():
        raise FileNotFoundError(f"Data file not found: {json_path}\nUpdate 'data_file' in config.json.")
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
                json={"model": EMBED_MODEL, "input": text or "document"},
                timeout=60,
            )
            r.raise_for_status()
            vec = r.json().get("embeddings", [[]])[0]
            if any(math.isnan(v) or math.isinf(v) for v in vec):
                return None
            return vec
        except Exception:
            return None

    def _extract_metadata_props(chunk_data: dict, raw_text: str, data_file_path: str) -> dict:
        """Derive filterable metadata properties from a chunk for storage alongside the document."""
        doc_source = Path(data_file_path).stem

        # Determine deepest heading level present in this chunk's keys
        heading_level = "main"
        for key in chunk_data.keys():
            if key == "ancestral_headings":
                continue
            if "Sub Sub Sub" in key:
                heading_level = "sub_sub_sub"
                break
            elif "Sub Sub" in key:
                heading_level = "sub_sub"
            elif "Sub" in key and heading_level not in ("sub_sub",):
                heading_level = "sub"

        # top_section: the root ancestor (no parents) from ancestral_headings
        top_section = ""
        anc = chunk_data.get("ancestral_headings", {})
        if isinstance(anc, dict):
            for heading, ancestors in anc.items():
                if not ancestors:
                    top_section = heading
                    break
            if not top_section and anc:
                shallowest = min(anc.items(), key=lambda kv: len(kv[1]))
                top_section = shallowest[0]

        return {
            "doc_source":    doc_source,
            "heading_level": heading_level,
            "top_section":   top_section,
            "has_code":      "```" in raw_text,
            "has_images":    "![" in raw_text,
        }

    def _build_filters(filter_cfg: dict):
        """Build a Weaviate Filter from the metadata_filters config block.
        Returns None when no filters are configured (→ no filtering applied)."""
        conditions = []
        val = filter_cfg.get("doc_source")
        if val:
            conditions.append(Filter.by_property("doc_source").equal(val))
        val = filter_cfg.get("heading_level")
        if val:
            conditions.append(Filter.by_property("heading_level").equal(val))
        val = filter_cfg.get("top_section")
        if val:
            conditions.append(Filter.by_property("top_section").equal(val))
        val = filter_cfg.get("has_code")
        if val is not None:
            conditions.append(Filter.by_property("has_code").equal(bool(val)))
        val = filter_cfg.get("has_images")
        if val is not None:
            conditions.append(Filter.by_property("has_images").equal(bool(val)))
        if not conditions:
            return None
        return conditions[0] if len(conditions) == 1 else Filter.all_of(conditions)

    for item in data:
        for chunk_id, chunk_data in item.items():
            # Skip non-chunk keys and validate chunk_data is a dict
            if chunk_id in ("Text", "Metadata", "ancestral_headings") or not isinstance(chunk_data, dict):
                continue
            
            # Only process actual chunk IDs (should match pattern chunk_id*)
            if not chunk_id.startswith("chunk_id"):
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
            
            # Additional validation: ensure heading_path is not empty and not just whitespace
            if not heading_path or not heading_path.strip():
                heading_path = f"Section: {chunk_id}"

            _meta_props = _extract_metadata_props(chunk_data, text, DATA_FILE)
            obj = {
                "text": text,
                "heading_path": heading_path,
                "main_heading": main_heading,
                "sub_headings": sub_headings,
                "ancestral_headings": ancestral_headings_str,
                "metadata_str": metadata_str,
                "chunk_id": chunk_id,
                **_meta_props,
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
    # query is loaded from config.json

    # Build metadata filter (None = no filtering)
    _active_filters = _build_filters(METADATA_FILTERS)
    if _active_filters is not None:
        print(f"Metadata filters active: { {k: v for k, v in METADATA_FILTERS.items() if v not in (None, '')} }")

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
                filters=_active_filters,
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
                filters=_active_filters,
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

        # --with_ancestral  → sort by combined score (W_TEXT * text + W_HEADING * heading)
        # --without_ancestral → sort by text score only
        if INCLUDE_ANCESTRAL:
            combined_list.sort(key=lambda x: x[3], reverse=True)
        else:
            combined_list.sort(key=lambda x: x[1], reverse=True)
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
        for rank, (cid, t_score, h_score, combined, wobj) in enumerate(selected, start=1):
            if wobj is None:
                continue
            props = wobj.properties
            # Parse the stored ancestral_headings JSON back to a dict
            try:
                anc_dict = json.loads(props.get("ancestral_headings", "{}"))
            except (json.JSONDecodeError, TypeError):
                anc_dict = {}

            if INCLUDE_ANCESTRAL:
                record = {
                    "query":            query,
                    "rank":             rank,
                    "chunk_id":         cid,
                    "text_score":       round(t_score, 6),
                    "ancestral_score":  round(h_score, 6),
                    "combined_score":   round(combined, 6),
                    "heading_path":     props.get("heading_path", ""),
                    "ancestral_headings": anc_dict,
                }
            else:
                record = {
                    "query":            query,
                    "rank":             rank,
                    "chunk_id":         cid,
                    "retrieval_score":  round(t_score, 6),
                    "heading_path":     props.get("heading_path", ""),
                }
            records.append(record)

            # Console summary
            print(f"\n  rank           : {rank} / {TOP_N}")
            print(f"  chunk_id       : {cid}")
            if INCLUDE_ANCESTRAL:
                print(f"  text_score     : {t_score:.4f}")
                print(f"  ancestral_score: {h_score:.4f}")
                print(f"  combined_score : {combined:.4f}")
            else:
                print(f"  retrieval_score: {t_score:.4f}")
            print(f"  heading_path   : {record['heading_path']}")
            # Print each ancestral heading level (only when --with_ancestral)
            if INCLUDE_ANCESTRAL:
                for heading, ancestors in anc_dict.items():
                    breadcrumb = " > ".join(ancestors + [heading]) if ancestors else heading
                    print(f"    ancestral: {breadcrumb}")
            #print(f"  chunk_text     : {record['chunk_text'][:200]}{'...' if len(record['chunk_text']) > 200 else ''}")

        # Save to JSONL — one JSON object per line
        out_path = Path(__file__).resolve().parent.parent / "output" / "retrieval_results.jsonl"
        try:
            with open(out_path, "w", encoding="utf-8") as out_f:
                for rec in records:
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"\nSaved {len(records)} records to: {out_path}")
        except Exception as e:
            print(f"Failed to save JSONL: {e}")
finally:
    client.close()