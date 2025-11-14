## Swahili–English AI Curriculum Tutor

A bilingual AI-powered tutor for Form 1 students in Kenya (Biology and Geography). It summarizes chapters, answers official revision questions, and handles free-form questions—returning English and Swahili side-by-side using a RAG pipeline (Pinecone + OpenAI + LangChain).

## What’s new (Nov 2025)
- Faster, smoother answers by switching default model to GPT‑4o‑mini (keeps quality with noticeably lower latency)
- Snappier UX: optimized rendering, loading states, and input handling (no more UI loops; fluid transitions)
- Cleaner, more formal interface (emoji-free), with consistent dark‑mode on both panels and a unified black gradient
- Revision flow upgraded: all chapter questions grouped in one place with clear numbering and bilingual answers
- Precision retrieval: better chapter filtering and noise suppression (header/boilerplate filtering, deduplication)
- Backend translates questions to Swahili for the Swahili panel while preserving the original English on the left
- Safer Pinecone usage: namespace safeguards and re‑index stability improvements for consistent results
- One‑click history clear, improved empty states, and a modernized Tutor page aligned with the landing page

## Tech stack
- Frontend: Next.js, React, Tailwind CSS, next-themes
- Backend: FastAPI (Uvicorn)
- AI: OpenAI (GPT-4o-mini by default) via LangChain
- Vector DB: Pinecone

## Project structure (high level)
```
ai_tutor/
├─ backend/
│  ├─ main.py            # FastAPI app entry
│  └─ app/
│     ├─ routes.py       # REST endpoints
│     └─ schemas.py      # Pydantic models
├─ frontend/
│  ├─ pages/
│  │  ├─ index.js        # Landing page (matrix effect)
│  │  └─ tutor.js        # Tutor UI (modes: summarize, revision, ask)
│  └─ styles/globals.css # Tailwind + animations
├─ src/
│  ├─ ai_engine.py       # Core RAG + bilingual output
│  ├─ chunk_and_embed.py # Ingestion + embedding to Pinecone
│  └─ utils/             # prompts, token utils, filtering
├─ data/                 # Processed textbook JSON
└─ requirements.txt
```

## Using the tutor (for learners)
1) Choose your Subject (Form 1 Biology or Geography)
2) Pick a Mode:
	- Summarize Chapter: Get an English + Swahili summary of a chapter
	- Answer Revision Questions: See all official revision questions for the chapter with bilingual answers grouped neatly
	- Ask a General Question: Type anything related to the syllabus and get a bilingual answer
3) Select the Chapter (for summarize/revision) or enter your question (for ask)
4) Submit and read both English and Swahili side‑by‑side

Notes
- Questions on the Swahili side are auto‑translated; answers are generated bilingually.
- Dark mode offers a consistent, readable look with a unified black gradient.

## Environment configuration
Create a `.env` file in the repo root with at least:

```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=bio-form1
# One of these is required by some clients
PINECONE_ENVIRONMENT=...
# or
PINECONE_ENV=...

# Optional/testing
PINECONE_NAMESPACE=dev_test   # leave unset for the default namespace
```

Frontend can point to a custom backend URL using:

```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## How to run (local)
1) Python env and backend
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

2) Frontend
```
cd frontend
npm install
npm run dev
```
Visit http://localhost:3000

## Data ingestion (Pinecone)
To (re)build the vector index from `data/cleaned_chunks/bio_form1_structured.json`:
```
source venv/bin/activate
python src/chunk_and_embed.py
```

Notes:
- The script splits structured content and upserts with rich metadata (type, chapter)
- Use the default namespace (recommended) unless testing; if testing, export `PINECONE_NAMESPACE`

## API endpoints
- POST `/summarize` → `{ chapter }` → `{ response: { english, swahili } }`
- POST `/revision` → `{ chapter }` → `{ questions: [{ question_text, swahili_question, answer: { english, swahili } }] }`
- POST `/ask` → `{ question }` → `{ response: { english, swahili } }`

See `API_RESPONSE_REFERENCE.md` for fuller examples and fields.

## Troubleshooting
- Port 8000 already in use
	- Kill and restart: `lsof -ti:8000 | xargs kill -9`
- Pinecone errors on startup
	- Ensure `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, and either `PINECONE_ENVIRONMENT` or `PINECONE_ENV` are set
- Frontend can’t reach backend
	- Set `NEXT_PUBLIC_API_BASE=http://localhost:8000`, restart `npm run dev`
- Inconsistent/chapter-mismatched results
	- Verify the namespace; unset `PINECONE_NAMESPACE` for default unless you explicitly need a test namespace

## Purpose of the additional .md files
- `QUICK_START_OPTIMIZED.md` – Fast path to spin up with recommended settings and shortcuts
- `PERFORMANCE_OPTIMIZATION.md` – Caching, async patterns, env tips, and production tuning notes
- `API_RESPONSE_REFERENCE.md` – Practical examples of backend responses and field shapes for each endpoint
- `FORMATTING_CHANGES.md` – UI/UX change log to track visual and layout decisions over time
- `IMPLEMENTATION_SUMMARY.md` – High-level summary of the recent implementation work and rationale

These keep the main README focused and concise while providing deeper operational and developer docs when needed.

## License
MIT License

## Author
Developed by Diramu Kana Godana for internship and research purposes.
