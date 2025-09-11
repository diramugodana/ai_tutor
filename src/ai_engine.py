import os
import sys
import json
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import Pinecone as LangchainPinecone
from pinecone import Pinecone as PineconeClient

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain

from src.utils.prompt_helpers import build_prompt_template, build_summary_prompt
from src.utils.revision_filter import extract_revision_questions
from src.utils.token_utils import estimate_tokens

# -------- setup --------
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

pc = PineconeClient(api_key=pinecone_api_key)
pinecone_index = pc.Index(pinecone_index_name)

embeddings = OpenAIEmbeddings()
vectorstore = LangchainPinecone(
    index=pinecone_index,
    embedding=embeddings,
    text_key="page_content"
)
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.3)

# ----------------- helpers -----------------
def parse_bilingual(output_text: str):
    if not isinstance(output_text, str):
        output_text = output_text.get("output_text") or output_text.get("answer") or str(output_text)

    text = output_text.strip()

    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "english" in obj and "swahili" in obj:
            return obj["english"].strip(), obj["swahili"].strip()
    except Exception:
        pass

    if "🌍" in text:
        eng, swa = text.split("🌍", 1)
        return eng.strip(), swa.strip()

    return text, "(Swahili version not available)"

def _chapter_variants(chapter_query: str):
    """
    e.g., "3" -> ["3", "3.1", ... "3.9"]
          "3.7" -> ["3.7"]
    """
    s = str(chapter_query).strip()
    if "." in s:
        return [s]
    return [s] + [f"{s}.{i}" for i in range(1, 10)]

def fetch_docs_by(meta_type: str, chapter_query: str, k: int = 200):
    """
    Primary fetch: restrict by `type` and chapter variants (3, 3.1...3.9).
    """
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

def fetch_docs_by_root(meta_type: str, chapter_root: str, k: int = 400):
    """
    Strong filter by chapter_root for all subchapters under a major chapter.
    """
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

def _top_content_for_question(question: str, fallback_docs, k: int = 6):
    """
    Use vector search against content; fall back to provided docs.
    """
    try:
        hits = vectorstore.similarity_search(
            question,
            k=k,
            filter={"type": "content"}
        )
    except Exception:
        hits = []
    return hits or list(fallback_docs)[:k]

def fetch_revision_candidates(chapter_query: str, k_try: int = 400):
    """
    Robust revision fetch:
    1) exact/child chapters by 'chapter'
    2) chapter_root (major)
    3) all revisions (last resort)
    """
    # 1) exact & subchapter match
    exact = fetch_docs_by("revision", chapter_query, k=k_try)
    if exact:
        return exact

    # 2) chapter_root
    major = str(chapter_query).split(".", 1)[0]
    by_root = fetch_docs_by_root("revision", major, k=k_try)
    if by_root:
        return by_root

    # 3) last resort
    return vectorstore.similarity_search(
        f"revision questions for chapter {chapter_query}",
        k=k_try,
        filter={"type": "revision"}
    )

# ----------------- 1) Summarize Chapter (UNCHANGED) -----------------
def summarize_chapter(chapter_query: str):
    chapter_docs = fetch_docs_by("content", chapter_query, k=400)
    cleaned = [d for d in chapter_docs if isinstance(d.page_content, str) and len(d.page_content.strip()) > 50]
    cleaned.sort(key=lambda d: len(d.page_content), reverse=True)

    selected, token_total = [], 0
    for d in cleaned:
        t = estimate_tokens(d.page_content)
        if token_total + t > 13000:
            break
        selected.append(d)
        token_total += t

    if not selected:
        return [{"english": f"⚠️ No usable content found for Chapter {chapter_query}.", "swahili": ""}]

    prompt = build_summary_prompt(chapter_query)
    json_guard = "\n\nReturn your final answer strictly as JSON with keys 'english' and 'swahili'."
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt.partial(instructions=json_guard))
    result = chain.invoke({"context": selected})

    english, swahili = parse_bilingual(result)
    return [{"english": english, "swahili": swahili}]

# ----------------- 2) Answer Revision Questions (FIXED) -----------------
def answer_revision_questions(chapter_query: str):
    # Fetch revision docs (with root fallback), and content from the entire chapter_root
    major = str(chapter_query).split(".", 1)[0]
    revision_docs = fetch_revision_candidates(chapter_query, k_try=600)

    # Content: prefer chapter_root scope so we have all subchapters’ material
    content_docs = fetch_docs_by_root("content", major, k=600)
    if not content_docs:
        # fallback to exact/variant
        content_docs = fetch_docs_by("content", chapter_query, k=400)

    # Extract and clean questions
    raw_questions = extract_revision_questions(revision_docs)
    seen = set()
    questions = []
    for q in raw_questions:
        q = (q or "").strip()
        if not q:
            continue
        # keep order, dedupe
        if q not in seen:
            seen.add(q)
            questions.append(q)

    # Noise filter (drop obvious headers)
    filtered = []
    for q in questions:
        low = q.lower()
        if len(low) < 6:
            continue
        if low.startswith(("index", "chapter", "--- page")):
            continue
        filtered.append(q)

    if not filtered:
        return [{"english": f"⚠️ No usable revision questions found for Chapter {chapter_query}.", "swahili": ""}]

    prompt = build_prompt_template(chapter_query)
    json_guard = "\n\nReturn your final answer strictly as JSON with keys 'english' and 'swahili'."
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt.partial(instructions=json_guard))

    results = []
    for q in filtered:
        relevant = _top_content_for_question(q, content_docs, k=8)
        if not relevant:
            relevant = content_docs[:8]

        out = chain.invoke({"context": relevant, "input": q})
        english, swahili = parse_bilingual(out)
        results.append({
            "question": f"Question: {q}",
            "english": english,
            "swahili": swahili
        })

    return results

# ----------------- 3) General Q&A (UNCHANGED) -----------------
def answer_general_question(user_question: str):
    prompt = build_prompt_template("unknown")
    json_guard = "\n\nReturn your final answer strictly as JSON with keys 'english' and 'swahili'."
    combine = create_stuff_documents_chain(llm=llm, prompt=prompt.partial(instructions=json_guard))
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=combine)

    result = chain.invoke({"input": user_question})
    answer_text = result.get("answer") or result.get("output_text") or str(result)
    english, swahili = parse_bilingual(answer_text)
    return [{"english": english, "swahili": swahili, "question": f"Question: {user_question}"}]

if __name__ == "__main__":
    docs = fetch_docs_by("content", "1", 20) + fetch_docs_by("revision", "1", 20)
    print(f"✅ Sample docs: {len(docs)}")
