from pydantic import BaseModel
from typing import List, Optional

class ChapterInput(BaseModel):
    chapter: str

class QuestionInput(BaseModel):
    question: str

class BilingualResponse(BaseModel):
    """Structured response with consistent bilingual output."""
    english: str
    swahili: str

class SummarizeResponse(BaseModel):
    """Response for /summarize endpoint."""
    mode: str = "summarize"
    chapter: str
    response: BilingualResponse

class RevisionQuestionResponse(BaseModel):
    """Single revision question answer."""
    question_text: str
    answer: BilingualResponse

class RevisionResponse(BaseModel):
    """Response for /revision endpoint."""
    mode: str = "revision"
    chapter: str
    questions: List[RevisionQuestionResponse]

class AskResponse(BaseModel):
    """Response for /ask endpoint."""
    mode: str = "ask"
    question_text: str
    response: BilingualResponse
