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
    Supports:
      - JSON list: {"type":"revision", "text":[ "...", "...", ... ]}
      - Single string block: {"type":"revision", "text":"1. ... 2. ..."}
    """
    questions: List[str] = []
    for d in (revision_docs or []):
        text: Union[str, List[str]] = getattr(d, "page_content", "") or ""
        if isinstance(text, list):
            # Your canonical format: list of full questions
            for item in text:
                item = _clean_line(str(item))
                if item:
                    questions.append(item)
        else:
            # Big textual blob: split
            qs = _split_questions_from_text(str(text))
            questions.extend(qs)

    # Deduplicate, keep order
    seen = set()
    deduped = []
    for q in questions:
        key = q.strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(key)
    return deduped
