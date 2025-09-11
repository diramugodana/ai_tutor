from fastapi import APIRouter
from backend.app.schemas import ChapterInput, QuestionInput
from src.ai_engine import summarize_chapter, answer_revision_questions, answer_general_question

router = APIRouter()

@router.post("/summarize")
def summarize(data: ChapterInput):
    result = summarize_chapter(data.chapter)
    return {"answer": result}  # ✅

@router.post("/revision")
def revision(data: ChapterInput):
    result = answer_revision_questions(data.chapter)
    return {"answer": result}  # ✅

@router.post("/ask")
def ask(data: QuestionInput):
    result = answer_general_question(data.question)
    return {"answer": result}  # ✅

