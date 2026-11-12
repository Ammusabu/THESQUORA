# THESQUORA

> Enterprise knowledge intelligence platform. Upload documents, ask questions in plain English, get cited answers.

![tests](https://img.shields.io/badge/tests-31%20passing-brightgreen)
![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20MongoDB%20Atlas-blue)

**🔗 Live demo:** _coming soon_ · **📚 API docs:** _coming soon_

## Why THESQUORA?

Most organizations cannot use ChatGPT on internal documents because it lacks permissions, audit trails, and protection against hallucination. THESQUORA is a document-grounded Q&A system that answers only from your own corpus, with cited pages, per-user permissions, and full audit logging.

## Features

- Ingestion: PDF/DOCX/TXT with per-page tracking, chunking, sha256 per-user dedupe
- Classification: TF-IDF + Logistic Regression with NB baseline
- Embeddings: sentence-transformers/all-MiniLM-L6-v2, 384-d, L2-normalised
- Retrieval: Atlas \$vectorSearch (pre-filtered), BM25 keyword, hybrid via RRF
- Reranker: cross-encoder ms-marco-MiniLM-L-6-v2
- RAG chat: permission-scoped, grounded prompt with prompt-injection defence, Groq LLM
- Document intelligence: similar docs, KMeans clustering, TF-IDF dominant terms
- Analytics: \$facet, \$lookup, \$unwind, \$group pipelines feeding Recharts

## Why MongoDB is the engine

| Feature | MongoDB capability |
|---|---|
| Semantic search | \$vectorSearch with metadata pre-filter |
| Keyword search | text index + textScore |
| Hybrid | RRF fusion |
| Analytics | \$facet, \$lookup, \$unwind, \$group |
| Data integrity | \$jsonSchema validators |
| Per-user dedupe | compound unique (owner_id, file_hash) |
| Retention | TTL on search_logs |

## Test suite

```bash
cd backend && source .venv/bin/activate
pytest tests/ -v   # 31 passed
```

## Quickstart

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.database.setup_db
python -m scripts.create_vector_index
python -m scripts.train_classifier
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Documentation

- docs/ARCHITECTURE.md
- docs/DATABASE_DESIGN.md
- docs/API.md
- docs/DEPLOYMENT.md
