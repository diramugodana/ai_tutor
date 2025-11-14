import re
from typing import List, Union

# Split big text blocks that look like enumerated questions
_SPLIT_RE = re.compile(
    r"""
    (?m)                   # multiline
    ^\s*                   # leading spaces
    (?:                    # common list markers
        \d{1,3}[\.\)]      # 1. or 1)
        | \d{1,3}\s*-\s*   # 1 - something
        | [•\-]            # bullet
    )
    \s+
    """,
    re.VERBOSE,
)

NOISE_PREFIXES = ("index", "--- page", "chapter", "fig.", "plate")

# Section headers that are NOT questions
HEADER_KEYWORDS = (
    "introduction", "the cell", "the light microscope", "the electron microscope",
    "classification", "preparation of", "estimation of", "external features",
    "magnification", "handling and care"
)

def _is_likely_question(text: str) -> bool:
    """
    Filter to identify actual questions vs section headers.
    Returns True if text looks like a real question.
    """
    text = text.strip()
    if not text or len(text) < 15:  # Too short to be a real question
        return False
    
    text_lower = text.lower()
    
    # Reject section headers (typically short titles without question marks)
    if any(text_lower == keyword or text_lower.startswith(keyword + " ") 
           for keyword in HEADER_KEYWORDS):
        return False
    
    # Accept if it has question markers
    if "?" in text:
        return True
    
    # Accept if it starts with a number (e.g., "1.", "2.")
    if re.match(r'^\d+[\.\)]\s*\(?\w?\)?', text):
        return True
    
    # Accept if it contains question words or instruction verbs
    question_indicators = (
        "what", "why", "how", "when", "where", "which", "who",
        "explain", "define", "describe", "list", "state", "name",
        "give", "distinguish", "compare", "calculate", "discuss"
    )
    if any(word in text_lower for word in question_indicators):
        return True
    
    # Reject if it's just a title (short and no question characteristics)
    if len(text) < 50 and not any(word in text_lower for word in question_indicators):
        return False
    
    return True

def _clean_line(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    low = s.lower()
    if any(low.startswith(p) for p in NOISE_PREFIXES):
        return ""
    return s

def _split_questions_from_text(block: str) -> List[str]:
    if not isinstance(block, str):
        block = str(block)
    block = block.replace("\r\n", "\n").strip()

    # Ensure at least one marker for the splitter to work
    sentinel = "0000) "
    if not re.match(r"^\s*(\d{1,3}[\.\)]|\d{1,3}\s*-\s*|[•\-])", block):
        block = sentinel + block

    parts = _SPLIT_RE.split(block)
    out = []
    for p in parts:
        p = _clean_line(p)
        if not p:
            continue
        if p.startswith(sentinel):
            p = p[len(sentinel):].strip()
        # Join wrapped lines
        p = re.sub(r"\s*\n\s*", " ", p).strip()
        if len(p) >= 6:
            out.append(p)
    return out

def extract_revision_questions(revision_docs) -> List[str]:
    """
    Extract revision questions from documents.
    Each doc.page_content is a single question string (already split when uploaded to Pinecone).
    Filters out section headers and only returns actual questions.
    """
    questions: List[str] = []
    for d in (revision_docs or []):
        text = getattr(d, "page_content", "") or ""
        text = str(text).strip()
        
        if not text:
            continue
            
        # Clean and check if it's a valid question
        cleaned = _clean_line(text)
        if cleaned and _is_likely_question(cleaned):
            questions.append(cleaned)

    # Deduplicate, keep order
    seen = set()
    deduped = []
    for q in questions:
        key = q.strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(key)
    return deduped
