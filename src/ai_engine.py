import os
import sys
import json
import re
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

# -------- setup --------
# pinecone_api_key = os.getenv("PINECONE_API_KEY")
# pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

# pc = PineconeClient(api_key=pinecone_api_key)
# pinecone_index = pc.Index(pinecone_index_name)

# embeddings = OpenAIEmbeddings()
# vectorstore = LangchainPinecone(
#     index=pinecone_index,
#     embedding=embeddings,
#     text_key="page_content"
# )
# llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.3)
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_env = os.getenv("PINECONE_ENVIRONMENT") or os.getenv("PINECONE_ENV")
pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

# Validate Pinecone envs early with a helpful error message
if not (pinecone_api_key and pinecone_env and pinecone_index_name):
    raise EnvironmentError(
        "Pinecone configuration missing. Please set PINECONE_API_KEY, PINECONE_ENVIRONMENT (or PINECONE_ENV) and PINECONE_INDEX_NAME in your environment."
    )

# Initialize Pinecone client and get an Index reference
try:
    pc = Pinecone(api_key=pinecone_api_key)
    pinecone_index = pc.Index(pinecone_index_name)
except Exception as e:
    raise RuntimeError(f"Failed to initialize Pinecone client or open index '{pinecone_index_name}': {e}")

embeddings = OpenAIEmbeddings()

# Optional: read namespace from env (for testing or multi-env setups)
pinecone_namespace = os.getenv("PINECONE_NAMESPACE", "")  # "" = default namespace
if pinecone_namespace:
    print(f"ℹ️ Using Pinecone namespace: '{pinecone_namespace}'")

vectorstore = LangchainPinecone(
    index=pinecone_index,
    embedding=embeddings,
    text_key="page_content",
    namespace=pinecone_namespace if pinecone_namespace else None,  # None = default
)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# ----------------- helpers -----------------
def parse_bilingual(output_text: str):
    """
    Extract English and Swahili from explicit format:
    ENGLISH:
    [text]
    SWAHILI:
    [text]
    """
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
        import json
        obj = json.loads(text)
        if isinstance(obj, dict) and "english" in obj and "swahili" in obj:
            return obj["english"].strip(), obj["swahili"].strip()
    except Exception:
        pass

    # Last resort: return as-is with fallback
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
    Fetch revision questions by exact chapter match.
    For chapter "1", look for chapter="1.5" (the pattern is: revision at X.5).
    """
    major = str(chapter_query).split(".", 1)[0]
    # Revision questions are typically at chapter X.5 (e.g., "1.5", "2.5", "3.7", "4.3", "4.7", "5.7")
    revision_chapter = f"{major}.5"
    
    try:
        # Try exact chapter match first (e.g., "1.5" for chapter 1)
        revisions = vectorstore.similarity_search(
            f"revision questions",
            k=k_try,
            filter={"type": "revision", "chapter": revision_chapter}
        )
        
        if revisions:
            return revisions
        
        # Fallback: get all revisions and filter manually by chapter starting with major
        all_revisions = vectorstore.similarity_search(
            f"chapter {major} questions",
            k=k_try,
            filter={"type": "revision"}
        )
        
        # Filter to chapters that start with the major number followed by a dot
        matching = [
            doc for doc in all_revisions 
            if doc.metadata.get("chapter", "").startswith(f"{major}.")
        ]
        
        return matching if matching else []
        
    except Exception:
        return []

def _clean_question_text(text: str) -> str:
    """
    Clean and truncate question text to extract just the question stem.
    Remove headers, page breaks, excessive whitespace, and limit to ~200 chars.
    """
    # Strip leading/trailing whitespace
    text = (text or "").strip()
    
    # Remove page break markers (---, ---, etc)
    text = re.sub(r"^-+\s*page\s+-+\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"---+", "", text)
    
    # Remove common header patterns
    text = re.sub(r"^(index|chapter|section|part|revision|questions?)[\s:]*", "", text, flags=re.IGNORECASE)
    
    # Collapse multiple whitespace/newlines to single space
    text = re.sub(r"\s+", " ", text)
    
    # Truncate to ~200 chars for display (avoid oversized payloads)
    if len(text) > 200:
        text = text[:197] + "..."
    
    return text.strip()

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
        return {"english": f"No usable content found for Chapter {chapter_query}.", "swahili": ""}

    prompt = build_summary_prompt(chapter_query)
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    result = chain.invoke({"context": selected})

    english, swahili = parse_bilingual(result)
    return {"english": english, "swahili": swahili}

# ----------------- 2) Answer Revision Questions (FIXED) -----------------
def answer_revision_questions(chapter_query: str):
    print(f"\n[ENGINE] Starting answer_revision_questions for chapter {chapter_query}")
    # Fetch revision docs (with root fallback), and content from the entire chapter_root
    major = str(chapter_query).split(".", 1)[0]
    revision_docs = fetch_revision_candidates(chapter_query, k_try=600)
    print(f"[ENGINE] Fetched {len(revision_docs)} revision docs")

    # Content: prefer chapter_root scope so we have all subchapters' material
    content_docs = fetch_docs_by_root("content", major, k=600)
    if not content_docs:
        # fallback to exact/variant
        content_docs = fetch_docs_by("content", chapter_query, k=400)
    print(f"[ENGINE] Fetched {len(content_docs)} content docs")

    # Extract and clean questions
    raw_questions = extract_revision_questions(revision_docs)
    print(f"[ENGINE] Extracted {len(raw_questions)} raw questions")
    seen = set()
    questions = []
    for q in raw_questions:
        q = _clean_question_text(q)
        if not q:
            continue
        # keep order, dedupe
        if q not in seen:
            seen.add(q)
            questions.append(q)

    # Noise filter (drop obvious headers/short text)
    filtered = []
    for q in questions:
        low = q.lower()
        if len(low) < 6:
            continue
        if low.startswith(("index", "chapter", "--- page")):
            continue
        filtered.append(q)

    print(f"[ENGINE] After filtering: {len(filtered)} questions")
    if not filtered:
        print(f"[ENGINE] No questions found - returning empty list")
        return []

    prompt = build_prompt_template(chapter_query)
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

    results = []
    for q in filtered:
        relevant = _top_content_for_question(q, content_docs, k=8)
        if not relevant:
            relevant = content_docs[:8]

        out = chain.invoke({"context": relevant, "input": q})
        english, swahili = parse_bilingual(out)
        
        # Translate question to Swahili
        swahili_question = _translate_question_to_swahili(q)
        
        results.append({
            "question_text": q,
            "swahili_question": swahili_question,
            "answer": {"english": english, "swahili": swahili}
        })

    return results

def _translate_question_to_swahili(question: str) -> str:
    """Translate a single question to Swahili using GPT."""
    try:
        from langchain.prompts import ChatPromptTemplate
        translation_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a translator. Translate the following English question to Swahili. Return ONLY the Swahili translation, nothing else."),
            ("human", "{question}")
        ])
        chain = translation_prompt | llm
        result = chain.invoke({"question": question})
        # Extract content from AIMessage
        if hasattr(result, 'content'):
            return result.content.strip()
        return str(result).strip()
    except Exception as e:
        print(f"[ENGINE] Translation error: {e}")
        return question  # Fallback to English if translation fails

# ----------------- 3) General Q&A (UPDATED) -----------------
def answer_general_question(user_question: str):
    prompt = build_prompt_template("unknown")
    combine = create_stuff_documents_chain(llm=llm, prompt=prompt)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=combine)

    result = chain.invoke({"input": user_question})
    answer_text = result.get("answer") or result.get("output_text") or str(result)
    english, swahili = parse_bilingual(answer_text)
    return {"english": english, "swahili": swahili}

if __name__ == "__main__":
    docs = fetch_docs_by("content", "1", 20) + fetch_docs_by("revision", "1", 20)
    print(f"Sample docs: {len(docs)}")
