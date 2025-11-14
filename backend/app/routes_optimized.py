from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
from backend.app.schemas import (
    ChapterInput, QuestionInput,
    SummarizeResponse, RevisionResponse, AskResponse,
    BilingualResponse, RevisionQuestionResponse
)
# Import optimized async version
from src.ai_engine_optimized import (
    summarize_chapter, answer_revision_questions, 
    answer_general_question, query_cache,
    stream_summarize_chapter
)

router = APIRouter()

# -------- Standard Endpoints (Cached, Optimized) --------

@router.post("/summarize", response_model=SummarizeResponse, tags=["tutoring"])
def summarize(data: ChapterInput):
    """
    Summarize a chapter.
    Cached for 10 minutes to avoid redundant API calls.
    """
    response = summarize_chapter(data.chapter)
    bilingual = BilingualResponse(english=response["english"], swahili=response["swahili"])
    return SummarizeResponse(chapter=data.chapter, response=bilingual)

@router.post("/revision", response_model=RevisionResponse, tags=["tutoring"])
def revision(data: ChapterInput):
    """
    Answer revision questions for a chapter.
    Questions are processed in parallel for faster response.
    Cached for 10 minutes.
    """
    results = answer_revision_questions(data.chapter)
    questions = [
        RevisionQuestionResponse(
            question_text=q["question_text"],
            answer=BilingualResponse(english=q["answer"]["english"], swahili=q["answer"]["swahili"])
        )
        for q in results
    ]
    return RevisionResponse(chapter=data.chapter, questions=questions)

@router.post("/ask", response_model=AskResponse, tags=["tutoring"])
def ask(data: QuestionInput):
    """
    Answer a general question about the material.
    Cached for 10 minutes.
    """
    response = answer_general_question(data.question)
    bilingual = BilingualResponse(english=response["english"], swahili=response["swahili"])
    return AskResponse(question_text=data.question, response=bilingual)

# -------- Cache Management --------

@router.post("/cache/clear", tags=["admin"])
def clear_cache():
    """Clear the query cache (useful after updating content)."""
    query_cache.clear()
    return {"status": "cache cleared"}

@router.get("/cache/stats", tags=["admin"])
def cache_stats():
    """Get cache statistics."""
    # query_cache may be Redis-backed (no direct mapping to a dict). Use
    # the cache-count helper which is best-effort.
    count = getattr(query_cache, "get_cache_count", None)
    cached = count() if callable(count) else len(getattr(query_cache, "cache", {}))
    return {
        "cached_queries": cached,
        "ttl_seconds": getattr(query_cache, "ttl_seconds", 600),
    }

# -------- Performance Monitoring --------

@router.get("/performance/summary", tags=["monitoring"])
def performance_summary():
    """Get performance optimization tips."""
    return {
        "optimizations": [
            "Query results cached for 10 minutes",
            "Revision questions processed in parallel (up to 5 concurrent)",
            "Reduced vector retrieval size (k parameter optimized)",
            "Token budgets reduced to 10k for faster generation",
            "gpt-4o-mini model (5-10x faster than gpt-4-turbo)",
        ],
        "tips": [
            "Same question within 10 minutes will return cached result (~100ms)",
            "Revision questions now process 2-5x faster due to parallelization",
            "First request will be slow (API latency), subsequent identical requests instant",
            "To clear cache after content updates: POST /cache/clear",
        ]
    }
