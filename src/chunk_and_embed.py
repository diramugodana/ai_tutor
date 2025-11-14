import os
import sys
import json
import time
from typing import List, Dict, Any, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from pinecone import Pinecone as PineconeClient
from pinecone.exceptions.exceptions import NotFoundException

# ---------- Paths ----------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_PATH = os.path.join(PROJECT_ROOT, "data", "cleaned_chunks", "bio_form1_structured.json")

# ---------- Pinecone ----------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not PINECONE_API_KEY:
    raise RuntimeError("PINECONE_API_KEY is not set")
if not PINECONE_INDEX_NAME:
    raise RuntimeError("PINECONE_INDEX_NAME is not set")

pc = PineconeClient(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(PINECONE_INDEX_NAME)

embeddings = OpenAIEmbeddings()
# Namespace: keep default "" unless you want a named namespace
NAMESPACE = ""  # e.g., "bio_form1" — if you change it, also read from the same ns in your app

# ---------- Helpers ----------

def safe_wipe_namespace():
    """Delete all vectors in the namespace if it exists; ignore if not."""
    try:
        print(f"Deleting existing vectors in namespace '{NAMESPACE or '(default)'}' ...")
        # Delete using the correct parameter
        if NAMESPACE:
            pinecone_index.delete(delete_all=True, namespace=NAMESPACE)
        else:
            # For default namespace, must specify namespace=""
            pinecone_index.delete(delete_all=True, namespace="")
        time.sleep(2)  # Give Pinecone time to process the delete
        print("Wipe done (or was already empty).")
    except NotFoundException:
        print("Namespace not found — nothing to delete. Continuing.")
    except Exception as e:
        print(f"Could not wipe namespace (ignored): {e}")

def load_json(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list of objects.")
    return data

def normalize_metadata(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure metadata matches your retriever/filter logic requirements.
    Required downstream:
      - 'type'     : "content" | "revision" | ...
      - 'chapter'  : "2", "2.5", etc
    """
    meta: Dict[str, Any] = {}
    for key in ["chapter", "type", "source", "title"]:
        if key in raw:
            meta[key] = raw[key]
    meta["chapter"] = str(meta.get("chapter", "")).strip()
    meta["type"] = (meta.get("type") or "content").strip().lower()
    return meta

def coerce_text_unit(item: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
    """
    Convert a JSON item into parallel lists of texts, metadatas, ids.
    - If item['text'] is a string -> 1 vector
    - If item['text'] is a list[str] (e.g., revision questions) -> 1 vector per string
    """
    meta = normalize_metadata(item)
    base_id = str(item.get("id") or f"{meta.get('type','content')}::{meta['chapter']}")
    raw_text = item.get("text", "")

    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    # If text is list-like, expand into multiple vectors
    if isinstance(raw_text, list):
        # Filter only string entries, strip empties
        entries = [str(x).strip() for x in raw_text if isinstance(x, (str, int, float))]
        entries = [e for e in entries if e]
        for i, e in enumerate(entries):
            texts.append(e)
            metadatas.append(meta)
            ids.append(f"{base_id}::item{i}")
    else:
        # Coerce to string and strip
        s = str(raw_text or "").strip()
        if s:
            texts.append(s)
            metadatas.append(meta)
            ids.append(f"{base_id}::full")

    return texts, metadatas, ids

def main():
    print(f"Loading chunks from: {INPUT_PATH}")
    items = load_json(INPUT_PATH)
    print(f"Total input items: {len(items)}")

    safe_wipe_namespace()

    all_texts: List[str] = []
    all_metas: List[Dict[str, Any]] = []
    all_ids: List[str] = []

    for idx, item in enumerate(items):
        meta = normalize_metadata(item)
        # skip if no chapter — your filters depend on this
        if not meta.get("chapter"):
            continue

        texts, metas, ids = coerce_text_unit(item)
        
        # Debug: print chapter 1.5 revision items
        if meta.get('chapter') == '1.5' and meta.get('type') == 'revision':
            print(f"\n[DEBUG] Chapter 1.5 revision - uploading {len(texts)} vectors:")
            for i, t in enumerate(texts[:3], 1):
                print(f"  {i}. {t[:80]}...")

        # keep alignment
        all_texts.extend(texts)
        all_metas.extend(metas)
        all_ids.extend(ids)

    # Filter out anything that somehow produced blank text
    packed = [(t, m, i) for t, m, i in zip(all_texts, all_metas, all_ids) if t.strip()]
    if not packed:
        print("No valid chunks to upsert. Exiting.")
        return
        return

    all_texts, all_metas, all_ids = map(list, zip(*packed))
    print(f"Upserting {len(all_texts)} vectors to index '{PINECONE_INDEX_NAME}' in namespace '{NAMESPACE or '(default)'}' ...")

    # Build a VectorStore wrapper and upsert embeddings in batches
    vectorstore = Pinecone(
    index=pinecone_index,
    embedding=embeddings,
    text_key="page_content",
    namespace=NAMESPACE or None,
)



    # LangChain handles batching inside add_texts
    try:
        result = vectorstore.add_texts(texts=all_texts, metadatas=all_metas, ids=all_ids)
        print(f"✅ Upsert complete. Added IDs: {len(result) if result else 'unknown'}")
    except Exception as e:
        print(f"❌ Error during upsert: {e}")
        raise
    try:
        stats = pinecone_index.describe_index_stats()
        print(f"📊 Index stats: {stats}")
    except Exception as e:
        print(f"ℹ️ Could not fetch stats (ignored): {e}")

if __name__ == "__main__":
    main()
