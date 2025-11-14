from fastapi import APIRouter
from backend.app.schemas import (
    ChapterInput, QuestionInput,
    SummarizeResponse, RevisionResponse, AskResponse,
    BilingualResponse, RevisionQuestionResponse
)
from src.ai_engine import summarize_chapter, answer_revision_questions, answer_general_question

router = APIRouter()

@router.post("/summarize", response_model=SummarizeResponse)
def summarize(data: ChapterInput):
    response = summarize_chapter(data.chapter)
    bilingual = BilingualResponse(english=response["english"], swahili=response["swahili"])
    return SummarizeResponse(chapter=data.chapter, response=bilingual)

@router.post("/revision", response_model=RevisionResponse)
def revision(data: ChapterInput):
    results = answer_revision_questions(data.chapter)
    print(f"\n[ROUTE DEBUG] answer_revision_questions returned {len(results)} results for chapter {data.chapter}")
    if results:
        print(f"[ROUTE DEBUG] First result: {results[0]}")
    
    questions = [
        RevisionQuestionResponse(
            question_text=q["question_text"],
            answer=BilingualResponse(english=q["answer"]["english"], swahili=q["answer"]["swahili"])
        )
        for q in results
    ]
    return RevisionResponse(chapter=data.chapter, questions=questions)

@router.post("/ask", response_model=AskResponse)
def ask(data: QuestionInput):
    response = answer_general_question(data.question)
    bilingual = BilingualResponse(english=response["english"], swahili=response["swahili"])
    return AskResponse(question_text=data.question, response=bilingual)
