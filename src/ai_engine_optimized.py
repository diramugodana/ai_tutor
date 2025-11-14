"""
Optimized async AI engine with caching, streaming, and parallel processing.
Reduces latency by:
1. Making I/O non-blocking (async)
2. Caching identical queries (5-10 min TTL)
3. Processing questions in parallel (revision mode)
4. Returning results as soon as ready (streaming)
"""

import os
import sys
import json
import re
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, AsyncGenerator
import asyncio
from functools import lru_cache

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from pinecone import Pinecone

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain

from src.utils.prompt_helpers import build_prompt_template, build_summary_prompt
from src.utils.revision_filter import extract_revision_questions
from src.utils.token_utils import estimate_tokens

# -------- Setup --------
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_env = os.getenv("PINECONE_ENVIRONMENT") or os.getenv("PINECONE_ENV")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

if not (pinecone_api_key and pinecone_env and pinecone_index_name):
    raise EnvironmentError(
        "Pinecone configuration missing. Please set PINECONE_API_KEY, PINECONE_ENVIRONMENT (or PINECONE_ENV) and PINECONE_INDEX_NAME in your environment."
    )

try:
    pc = Pinecone(api_key=pinecone_api_key)
    pinecone_index = pc.Index(pinecone_index_name)
except Exception as e:
    raise RuntimeError(f"Failed to initialize Pinecone client or open index '{pinecone_index_name}': {e}")

embeddings = OpenAIEmbeddings()

pinecone_namespace = os.getenv("PINECONE_NAMESPACE", "")
if pinecone_namespace:
    print(f"ℹ️ Using Pinecone namespace: '{pinecone_namespace}'")

vectorstore = LangchainPinecone(
    index=pinecone_index,
    embedding=embeddings,
    text_key="page_content",
    namespace=pinecone_namespace if pinecone_namespace else None,
)

# Use faster model with lower latency
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, max_tokens=2000)

# -------- Query Cache --------
class QueryCache:
    """Simple in-memory cache with TTL for query results."""
    def __init__(self, ttl_seconds: int = 600):
        self.cache: Dict[str, Tuple[dict, float]] = {}
        self.ttl_seconds = ttl_seconds
    
    def _hash_key(self, *args) -> str:
        """Generate cache key from arguments."""
        key_str = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, *args) -> Optional[dict]:
        """Get cached result if not expired."""
        key = self._hash_key(*args)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, result: dict, *args) -> None:
        """Cache result with timestamp."""
        key = self._hash_key(*args)
        self.cache[key] = (result, time.time())
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()

query_cache = QueryCache(ttl_seconds=600)  # 10 min TTL

# -------- Helpers --------
def parse_bilingual(output_text: str) -> Tuple[str, str]:
    """Extract English and Swahili from explicit format."""
    if not isinstance(output_text, str):
        output_text = output_text.get("output_text") or output_text.get("answer") or str(output_text)

    text = output_text.strip()

    # Try parsing explicit ENGLISH:/SWAHILI: format
    if "ENGLISH:" in text and "SWAHILI:" in text:
        parts = text.split("SWAHILI:", 1)
        english = parts[0].replace("ENGLISH:", "").strip()
        swahili = parts[1].strip() if len(parts) > 1 else ""
        return english, swahili

    # Fallback: try JSON
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "english" in obj and "swahili" in obj:
            return obj["english"].strip(), obj["swahili"].strip()
    except Exception:
        pass

    return text, "(Swahili version not available)"

def _clean_question_text(text: str) -> str:
    """Clean and truncate question text."""
    text = (text or "").strip()
    text = re.sub(r"^-+\s*page\s+-+\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"---+", "", text)
    text = re.sub(r"^(index|chapter|section|part|revision|questions?)[\s:]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    
    if len(text) > 200:
        text = text[:197] + "..."
    
    return text.strip()

def _chapter_variants(chapter_query: str) -> List[str]:
    """Generate chapter variants (e.g., '3' -> ['3', '3.1', ... '3.9'])."""
    s = str(chapter_query).strip()
    if "." in s:
        return [s]
    return [s] + [f"{s}.{i}" for i in range(1, 10)]

def _fetch_docs_by(meta_type: str, chapter_query: str, k: int = 100) -> List:
    """Fetch docs by type and chapter (optimized k)."""
    variants = _chapter_variants(chapter_query)
    neutral_query = f"{meta_type} chapter {chapter_query}"
    return vectorstore.similarity_search(
        neutral_query,
        k=k,
        filter={
            "type": meta_type,
            "chapter": {"$in": variants}
        }
    )

def _fetch_docs_by_root(meta_type: str, chapter_root: str, k: int = 150) -> List:
    """Fetch docs by chapter root (optimized k)."""
    root = str(chapter_root).split(".", 1)[0].strip()
    neutral_query = f"{meta_type} chapter_root {root}"
    return vectorstore.similarity_search(
        neutral_query,
        k=k,
        filter={
            "type": meta_type,
            "chapter_root": root
        }
    )

def _top_content_for_question(question: str, fallback_docs, k: int = 4) -> List:
    """Get top content for a question (reduced k for speed)."""
    try:
        hits = vectorstore.similarity_search(
            question,
            k=k,
            filter={"type": "content"}
        )
    except Exception:
        hits = []
    return hits or list(fallback_docs)[:k]

# -------- Main Functions (Synchronous + Async) --------

def summarize_chapter(chapter_query: str) -> dict:
    """Summarize a chapter (cached)."""
    # Check cache
    cached = query_cache.get("summarize", chapter_query)
    if cached:
        return cached

    # Fetch docs (reduced k from 400 to 200 for speed)
    chapter_docs = _fetch_docs_by("content", chapter_query, k=200)
    cleaned = [d for d in chapter_docs if isinstance(d.page_content, str) and len(d.page_content.strip()) > 50]
    cleaned.sort(key=lambda d: len(d.page_content), reverse=True)

    # Select docs up to token limit (reduced from 13000 to 10000)
    selected, token_total = [], 0
    for d in cleaned:
        t = estimate_tokens(d.page_content)
        if token_total + t > 10000:
            break
        selected.append(d)
        token_total += t

    if not selected:
        result = {"english": f"No usable content found for Chapter {chapter_query}.", "swahili": ""}
        query_cache.set(result, "summarize", chapter_query)
        return result

    # Generate summary
    prompt = build_summary_prompt(chapter_query)
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    result = chain.invoke({"context": selected})

    english, swahili = parse_bilingual(result)
    response = {"english": english, "swahili": swahili}
    
    # Cache result
    query_cache.set(response, "summarize", chapter_query)
    return response

async def answer_revision_questions_async(chapter_query: str) -> List[dict]:
    """
    Answer revision questions in parallel for faster processing.
    Processes all questions concurrently instead of sequentially.
    """
    # Check cache
    cached = query_cache.get("revision", chapter_query)
    if cached:
        return cached

    major = str(chapter_query).split(".", 1)[0]
    
    # Fetch docs (reduced k from 600 to 300)
    revision_docs = _fetch_docs_by_root("revision", major, k=300)
    content_docs = _fetch_docs_by_root("content", major, k=300)
    if not content_docs:
        content_docs = _fetch_docs_by("content", chapter_query, k=200)

    # Extract and clean questions
    raw_questions = extract_revision_questions(revision_docs)
    seen = set()
    questions = []
    for q in raw_questions:
        q = _clean_question_text(q)
        if not q:
            continue
        if q not in seen:
            seen.add(q)
            questions.append(q)

    # Filter out noise
    filtered = []
    for q in questions:
        low = q.lower()
        if len(low) < 6 or low.startswith(("index", "chapter", "--- page")):
            continue
        filtered.append(q)

    if not filtered:
        query_cache.set([], "revision", chapter_query)
        return []

    # Process questions in parallel (reduced k from 8 to 4)
    prompt = build_prompt_template(chapter_query)
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

    async def answer_single_question(q: str) -> dict:
        """Process a single question (can be parallelized)."""
        relevant = _top_content_for_question(q, content_docs, k=4)
        if not relevant:
            relevant = content_docs[:4]
        
        # Run LLM in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        out = await loop.run_in_executor(None, chain.invoke, {"context": relevant, "input": q})
        english, swahili = parse_bilingual(out)
        
        return {
            "question_text": q,
            "answer": {"english": english, "swahili": swahili}
        }

    # Run all questions concurrently (max 5 at a time to avoid rate limits)
    semaphore = asyncio.Semaphore(5)
    
    async def bounded_question(q: str):
        async with semaphore:
            return await answer_single_question(q)
    
    results = await asyncio.gather(*[bounded_question(q) for q in filtered])
    
    # Cache result
    query_cache.set(results, "revision", chapter_query)
    return results

def answer_revision_questions(chapter_query: str) -> List[dict]:
    """Synchronous wrapper for revision questions."""
    try:
        # Try to get event loop, run async function
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context, run in executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, answer_revision_questions_async(chapter_query))
                return future.result()
        else:
            return asyncio.run(answer_revision_questions_async(chapter_query))
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(answer_revision_questions_async(chapter_query))

def answer_general_question(user_question: str) -> dict:
    """Answer general question (cached)."""
    # Check cache
    cached = query_cache.get("ask", user_question)
    if cached:
        return cached

    prompt = build_prompt_template("unknown")
    combine = create_stuff_documents_chain(llm=llm, prompt=prompt)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})  # Reduced from 6
    chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=combine)

    result = chain.invoke({"input": user_question})
    answer_text = result.get("answer") or result.get("output_text") or str(result)
    english, swahili = parse_bilingual(answer_text)
    response = {"english": english, "swahili": swahili}
    
    # Cache result
    query_cache.set(response, "ask", user_question)
    return response

# Async generator for streaming (future use)
async def stream_summarize_chapter(chapter_query: str) -> AsyncGenerator[str, None]:
    """Stream summary results as they become available."""
    yield '{"status": "fetching_docs"}\n'
    
    chapter_docs = _fetch_docs_by("content", chapter_query, k=200)
    cleaned = [d for d in chapter_docs if isinstance(d.page_content, str) and len(d.page_content.strip()) > 50]
    cleaned.sort(key=lambda d: len(d.page_content), reverse=True)

    selected, token_total = [], 0
    for d in cleaned:
        t = estimate_tokens(d.page_content)
        if token_total + t > 10000:
            break
        selected.append(d)
        token_total += t

    yield '{"status": "generating"}\n'
    
    prompt = build_summary_prompt(chapter_query)
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, chain.invoke, {"context": selected})
    
    english, swahili = parse_bilingual(result)
    
    yield json.dumps({
        "status": "complete",
        "english": english,
        "swahili": swahili
    }) + '\n'

if __name__ == "__main__":
    docs = _fetch_docs_by("content", "1", 20) + _fetch_docs_by("revision", "1", 20)
    print(f"✅ Sample docs: {len(docs)}")
