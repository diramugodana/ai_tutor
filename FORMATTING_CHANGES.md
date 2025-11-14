# Output Formatting - Structured Response Schema

## Overview
This document describes the implementation of consistent, structured response formats across all three API endpoints (`/summarize`, `/revision`, `/ask`). These changes provide clean, type-safe output for frontend consumption and improve overall system maintainability.

## Changes Made

### 1. Updated Response Schemas (`backend/app/schemas.py`)

Added 5 new Pydantic models for structured responses:

#### `BilingualResponse`
```python
class BilingualResponse(BaseModel):
    english: str
    swahili: str
```
Reusable bilingual content container (English + Swahili).

#### `SummarizeResponse` (for `/summarize`)
```python
class SummarizeResponse(BaseModel):
    mode: str = "summarize"
    chapter: str
    response: BilingualResponse
```

**Example Output:**
```json
{
  "mode": "summarize",
  "chapter": "1",
  "response": {
    "english": "Chapter 1 covers fundamentals...",
    "swahili": "Sura ya 1 inafunika misingi..."
  }
}
```

#### `RevisionQuestionResponse` + `RevisionResponse` (for `/revision`)
```python
class RevisionQuestionResponse(BaseModel):
    question_text: str  # Clean, truncated question
    answer: BilingualResponse

class RevisionResponse(BaseModel):
    mode: str = "revision"
    chapter: str
    questions: List[RevisionQuestionResponse]
```

**Example Output:**
```json
{
  "mode": "revision",
  "chapter": "1",
  "questions": [
    {
      "question_text": "What are the main components of a cell?",
      "answer": {
        "english": "The main components include...",
        "swahili": "Sehemu kuu zinajumuisha..."
      }
    }
  ]
}
```

#### `AskResponse` (for `/ask`)
```python
class AskResponse(BaseModel):
    mode: str = "ask"
    question_text: str
    response: BilingualResponse
```

**Example Output:**
```json
{
  "mode": "ask",
  "question_text": "What is photosynthesis?",
  "response": {
    "english": "Photosynthesis is the process...",
    "swahili": "Umeme jua ni mchakato..."
  }
}
```

---

### 2. Enhanced Question Cleaning (`src/ai_engine.py`)

Added `_clean_question_text()` helper function to normalize and truncate question text:
- Removes page break markers (`---`, `--- PAGE ---`, etc.)
- Strips header patterns (`INDEX:`, `CHAPTER:`, `SECTION:`, etc.)
- Collapses multiple whitespace/newlines to single space
- Truncates oversized questions to ~200 characters
- Extracts clean question stem (not raw multiline dumps)

**Before:**
```
"--- PAGE BREAK ---
CHAPTER 1: REVISION QUESTIONS
Question 1: What are the main components of a cell? List them and describe each in detail..."
```

**After:**
```
"What are the main components of a cell? List them and describe..."
```

---

### 3. Refactored AI Engine Functions (`src/ai_engine.py`)

#### `summarize_chapter(chapter_query)`
- **Before:** Returned list: `[{"english": "...", "swahili": "..."}]`
- **After:** Returns single dict: `{"english": "...", "swahili": "..."}`

#### `answer_revision_questions(chapter_query)`
- **Before:** Returned dict with raw question text: `[{"question": "Question: What...", "english": "...", "swahili": "..."}]`
- **After:** Returns cleaned structure: `[{"question_text": "What...", "answer": {"english": "...", "swahili": "..."}}]`
- Applies `_clean_question_text()` to all extracted questions

#### `answer_general_question(user_question)`
- **Before:** Returned list: `[{"english": "...", "swahili": "...", "question": "Question: ..."}]`
- **After:** Returns single dict: `{"english": "...", "swahili": "..."}`

---

### 4. Updated API Routes (`backend/app/routes.py`)

Each endpoint now wraps the AI engine response in the proper Pydantic model:

```python
@router.post("/summarize", response_model=SummarizeResponse)
def summarize(data: ChapterInput):
    response = summarize_chapter(data.chapter)
    bilingual = BilingualResponse(english=response["english"], swahili=response["swahili"])
    return SummarizeResponse(chapter=data.chapter, response=bilingual)

@router.post("/revision", response_model=RevisionResponse)
def revision(data: ChapterInput):
    results = answer_revision_questions(data.chapter)
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
```

**Benefits:**
- Automatic JSON schema generation (FastAPI Swagger docs)
- Type validation on response
- Consistent structure across all modes
- Frontend can reliably parse all three endpoint types

---

## Summary of Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Response Format** | Inconsistent (lists vs dicts, generic labels) | Consistent structured Pydantic models |
| **Revision Questions** | Raw multiline text (oversized payloads) | Clean, truncated to ~200 chars |
| **Swahili Label** | Generic labels | Consistent `swahili` field in `BilingualResponse` |
| **Type Safety** | Untyped dicts | Full Pydantic type checking |
| **Frontend Parsing** | Required custom logic for each mode | Single schema per endpoint type |
| **OpenAPI Documentation** | Manual schema descriptions | Auto-generated from Pydantic models |

---

## Testing

Run the validation test:
```bash
python test_output_format.py
```

Expected output shows all three response formats with proper structure and bilingual content.

---

## Next Steps

1. **Integration Testing:** Call live endpoints and verify response format matches schemas
2. **Frontend Integration:** Update Next.js frontend to consume the new response structure
3. **Performance Testing:** Measure payload sizes and latency with new format
4. **Deployment:** Update backend environment and API documentation

---

## Files Modified

- `backend/app/schemas.py` — Added 5 new response models
- `src/ai_engine.py` — Added question cleaning, updated 3 main functions
- `backend/app/routes.py` — Updated 3 endpoints to return structured responses
- `test_output_format.py` — Created validation test (new file)
