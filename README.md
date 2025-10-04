# Swahili-English AI Curriculum Tutor

This project is a bilingual AI-powered educational assistant designed to support Form 1 students in Kenya with their Biology and Geography curriculum. The tool enables students to summarize textbook chapters, answer official revision questions, and ask custom questions in either English or Swahili. The application integrates a modern frontend interface with a retrieval-augmented generation (RAG) backend that leverages semantic search and large language models.

## Features

* Chapter summarization from official textbooks
* National revision question answering
* Bilingual support: English and Swahili
* General question answering with semantic search
* Context-aware LLM responses
* Light and dark mode UI with animated particle background
* Vector-based retrieval using Pinecone
* Structured, chunked ingestion of textbook data

## Tech Stack

### Languages

Python, JavaScript

### Frameworks and Libraries

* **Frontend**: Next.js, React, Tailwind CSS, next-themes
* **Backend**: FastAPI, Uvicorn
* **AI and Embeddings**: OpenAI GPT-4 Turbo, OpenAI Embeddings, LangChain
* **Vector Store**: Pinecone

### Supporting Tools

* dotenv
* uuid
* pydantic

## Project Structure

```
ai_tutor/
├── backend/              # FastAPI backend
│   ├── main.py           # FastAPI application setup
│   └── app/routes.py     # API route definitions
├── frontend/             # Next.js frontend
│   ├── pages/tutor.js    # Main interface for tutoring
│   ├── components/       # Shared React components
│   └── styles/           # Global styles (Tailwind)
├── src/                  # Core AI engine and logic
│   ├── ai_engine.py      # Handles summarization, Q&A logic
│   ├── chunk_and_embed.py# Data ingestion and embedding script
│   └── utils/            # Utility functions (chapter matcher, prompts, etc.)
├── data/                 # Cleaned and structured textbook JSON data
└── vector_db/            # Local vector DB (optional if not using Pinecone)
```

## Installation and Setup

### 1. Clone the repository

```
git clone https://github.com/your-username/ai_tutor.git
cd ai_tutor
```

### 2. Backend (FastAPI + Python)

```
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=ai-tutor-index
```

### 4. Frontend (Next.js)

```
cd frontend
npm install
npm run dev
```

Application runs at `http://localhost:3000`

## Usage

* Select subject and interaction mode (summarize, revision questions, or custom query)
* If applicable, choose a chapter or enter a question
* Submit to receive bilingual responses side by side

## Chunking and Retrieval Strategy

* Documents are split using LangChain's RecursiveCharacterTextSplitter
* Each chunk is embedded using OpenAI's `text-embedding-ada-002` model
* Stored in Pinecone with structured metadata (chapter, type)
* Retrieval filters include exact chapter match and content type (e.g., "revision")
* Custom prompts ensure consistent bilingual output with fallback formatting

## API Endpoints

* `POST /summarize` – summarize a specific chapter
* `POST /revision` – answer all revision questions for a chapter
* `POST /ask` – answer a freeform general question

## License

This project is licensed under the MIT License.

## Author

Developed by Diramu Kana Godana for academic and educational research purposes.
