# API Response Format Reference

## Overview

This document describes the structured response format for all three API endpoints. Each endpoint returns a consistent, type-safe JSON structure with bilingual content (English and Swahili).

## Quick Reference - All Three Endpoints

### 1. `/summarize` POST
**Request:**
```json
{
  "chapter": "1"
}
```

**Response (SummarizeResponse):**
```json
{
  "mode": "summarize",
  "chapter": "1",
  "response": {
    "english": "Chapter 1 covers the fundamental principles of biology including cell structure, functions, and basic biochemistry...",
    "swahili": "Sura ya 1 inafunika misingi ya biolojia ikiwa ni pamoja na muundo wa seli, kazi, na biokemia ya msingi..."
  }
}
```

**Fields:**
- `mode`: Always `"summarize"`
- `chapter`: Echo of request chapter
- `response.english`: Summary in English
- `response.swahili`: Summary in Swahili (or fallback message if unavailable)

---

### 2. `/revision` POST
**Request:**
```json
{
  "chapter": "1"
}
```

**Response (RevisionResponse):**
```json
{
  "mode": "revision",
  "chapter": "1",
  "questions": [
    {
      "question_text": "What are the main components of a cell?",
      "answer": {
        "english": "The main components of a cell include the nucleus, which contains genetic material; the cytoplasm, which is the gel-like substance inside the cell...",
        "swahili": "Sehemu kuu za seli zinajumuisha kiini, ambayo ina nyenzo ya kiini; sitoplazma, ambayo ni dutu inayofanana na jeli ndani ya seli..."
      }
    },
    {
      "question_text": "Describe the process of mitosis and explain its significance.",
      "answer": {
        "english": "Mitosis is the process of cell division that produces two identical daughter cells, each with the same number of chromosomes as the parent cell...",
        "swahili": "Mitosis ni mchakato wa mgawanyiko wa seli unaozalisha seli mbili zinazofanana, kila moja ikiwa na idadi sawa ya kromosomu..."
      }
    }
  ]
}
```

**Fields:**
- `mode`: Always `"revision"`
- `chapter`: Echo of request chapter
- `questions`: Array of revision questions
  - `question_text`: Clean, truncated question (~200 char max)
  - `answer.english`: Answer in English
  - `answer.swahili`: Answer in Swahili

---

### 3. `/ask` POST
**Request:**
```json
{
  "question": "What is photosynthesis?"
}
```

**Response (AskResponse):**
```json
{
  "mode": "ask",
  "question_text": "What is photosynthesis?",
  "response": {
    "english": "Photosynthesis is the process by which plants, algae, and certain bacteria convert light energy (usually from the sun) into chemical energy stored in glucose...",
    "swahili": "Fotosintesi ni mchakato ambao mimea, algae, na bacteria fulani hubadilisha nishati ya mwanga (kawaida kutoka kwa jua) kuwa nishati ya kemikali iliyohifadhiwa katika glukosi..."
  }
}
```

**Fields:**
- `mode`: Always `"ask"`
- `question_text`: Echo of request question
- `response.english`: Answer in English
- `response.swahili`: Answer in Swahili

---

## Frontend Integration Notes

### Consistent Parsing
All three endpoints follow the same bilingual response pattern:
- Every response has a `response` field (for modes 1 & 3) or `answer` field (within `questions` for mode 2)
- Every response has `english` and `swahili` fields
- All responses include a `mode` identifier for endpoint type detection

### Question Field Handling
- **Mode 1 & 3:** Question/topic is in `chapter` or `question_text` field
- **Mode 2:** Individual questions are in `questions[i].question_text` array
- Questions are now cleaned (no headers, page breaks, excessive formatting)
- Questions truncated to ~200 characters to avoid oversized payloads

### Swahili Fallback
If Swahili generation fails or is unavailable:
- `swahili` field will contain: `"(Swahili version not available)"`
- Frontend should gracefully handle missing Swahili or hide the field

### Error Handling
If no content/questions found:
- Response will be returned as normal but with empty `questions` array or notice in `english` field
- HTTP status will still be 200 (successful API call with no results)
- Frontend should validate and handle empty `questions` arrays appropriately

---

## Type Definitions (TypeScript)

```typescript
interface BilingualResponse {
  english: string;
  swahili: string;
}

interface SummarizeResponse {
  mode: "summarize";
  chapter: string;
  response: BilingualResponse;
}

interface RevisionQuestionResponse {
  question_text: string;
  answer: BilingualResponse;
}

interface RevisionResponse {
  mode: "revision";
  chapter: string;
  questions: RevisionQuestionResponse[];
}

interface AskResponse {
  mode: "ask";
  question_text: string;
  response: BilingualResponse;
}

type ApiResponse = SummarizeResponse | RevisionResponse | AskResponse;
```

---

## Testing with cURL

### Test Summarize
```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"chapter":"1"}'
```

### Test Revision
```bash
curl -X POST http://localhost:8000/revision \
  -H "Content-Type: application/json" \
  -d '{"chapter":"1"}'
```

### Test Ask
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is DNA?"}'
```

---

## Validation & Schema

All responses are validated against Pydantic models. FastAPI automatically:
1. Validates response format before returning
2. Generates OpenAPI schema at `/docs`
3. Provides JSON schema at `/openapi.json`

Visit `http://localhost:8000/docs` to see interactive API documentation with request/response examples.
