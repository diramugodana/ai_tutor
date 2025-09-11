def is_in_chapter(doc_chapter: str, query_chapter: str) -> bool:
    """
    Checks if doc_chapter belongs to the queried chapter.
    Matches '2' with '2', '2.1', '2.3.1', but not '20', '12', etc.
    """
    if not doc_chapter or not query_chapter:
        return False

    # Normalize
    doc_chapter = str(doc_chapter).strip()
    query_chapter = str(query_chapter).strip()

    # Split into parts
    doc_parts = doc_chapter.split(".")
    query_parts = query_chapter.split(".")

    # Match startswith by structure (e.g., 2 matches 2.*, not 20)
    return doc_parts[:len(query_parts)] == query_parts
