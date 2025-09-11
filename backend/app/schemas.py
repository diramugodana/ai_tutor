from pydantic import BaseModel

class ChapterInput(BaseModel):
    chapter: str

class QuestionInput(BaseModel):
    question: str
