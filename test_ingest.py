#!/usr/bin/env python3
"""
Temporary test script: ingest first 20 items from bio_form1_structured.json
into Pinecone namespace 'dev_test' (non-destructive, safe for testing).

Run once to populate test data, then can be deleted.
"""

import os
import sys
import json
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from pinecone import Pinecone as PineconeClient

# Config
PROJECT_ROOT = os.path.dirname(__file__)
INPUT_PATH = os.path.join(PROJECT_ROOT, "data", "cleaned_chunks", "bio_form1_structured.json")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
TEST_NAMESPACE = "dev_test"  # Safe, non-destructive namespace
MAX_ITEMS = 20  # Small sample for testing

print("Test ingest script")
print(f"   Index: {PINECONE_INDEX_NAME}")
print(f"   Namespace: {TEST_NAMESPACE}")
print(f"   Max items: {MAX_ITEMS}")
print()

# Load data
if not os.path.exists(INPUT_PATH):
    print(f"Data file not found: {INPUT_PATH}")
    sys.exit(1)

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    all_items = json.load(f)
print(f"Loaded {len(all_items)} total items from {INPUT_PATH}")

# Filter valid items and take first MAX_ITEMS
valid_items = []
for item in all_items:
    if not item.get("chapter"):  # Skip items without chapter
        continue
    text = item.get("text", "")
    # Skip if text is empty or list is empty
    if isinstance(text, list):
        text = [str(t).strip() for t in text if t]
        if not text:
            continue
    else:
        if not str(text).strip():
            continue
    valid_items.append(item)
    if len(valid_items) >= MAX_ITEMS:
        break

print(f"Selected {len(valid_items)} valid items for test ingest")
print()

# Prepare texts and metadata
texts = []
metadatas = []
ids = []

for idx, item in enumerate(valid_items):
    meta = {
        "chapter": str(item.get("chapter", "")),
        "type": (item.get("type") or "content").lower(),
    }
    
    text = item.get("text", "")
    if isinstance(text, list):
        # For list items, join them
        text = " | ".join([str(t).strip() for t in text if t])
    text = str(text).strip()
    
    if text:
        texts.append(text)
        metadatas.append(meta)
        ids.append(f"test_item_{idx}")

print(f"Prepared {len(texts)} vectors for embedding and upload")
print(f"   Sample metadata: {metadatas[0] if metadatas else 'none'}")
print()

# Initialize Pinecone and embed
print("Connecting to Pinecone...")
try:
    pc = PineconeClient(api_key=PINECONE_API_KEY)
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    print(f"Connected to index '{PINECONE_INDEX_NAME}'")
except Exception as e:
    print(f"Failed to connect to Pinecone: {e}")
    sys.exit(1)

    print(f"Embedding {len(texts)} texts...")
embeddings = OpenAIEmbeddings()

try:
    vectorstore = LangchainPinecone(
        index=pinecone_index,
        embedding=embeddings,
        text_key="page_content",
        namespace=TEST_NAMESPACE,
    )
    print(f"Vectorstore initialized for namespace '{TEST_NAMESPACE}'")
except Exception as e:
    print(f"❌ Failed to initialize vectorstore: {e}")
    sys.exit(1)

# Upsert
print("Upserting vectors...")
try:
    vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    print(f"Upserted {len(texts)} vectors to namespace '{TEST_NAMESPACE}'")
except Exception as e:
    print(f"❌ Upsert failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("TEST INGEST COMPLETE")
print("=" * 60)
print()
print(f"Next steps:")
print(f"1. Run retrieval test from namespace '{TEST_NAMESPACE}'")
print(f"2. Test RAG pipeline with /summarize or /ask endpoints")
print(f"3. If satisfied, you can:")
print(f"   - Keep vectors in 'dev_test' (safe, isolated)")
print(f"   - Or run chunk_and_embed.py for full production ingest")
print()
