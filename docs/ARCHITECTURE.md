# THESQUORA — Architecture

Stack: FastAPI + PyMongo + MongoDB Atlas Vector Search + React + Groq.

## Layers
- routes/ — HTTP handlers
- services/ — business logic
- repositories/ — PyMongo queries
- ml/ — embeddings, classifier, reranker, clustering
- rag/ — retrieval, prompt, LLM client
- database/ — client, collections, validators, indexes

## Upload flow
Upload -> validate -> extract -> classify -> chunk -> embed -> insert chunks -> mark processed.

## RAG flow
Question -> embed -> vectorSearch (pre-filtered by owner) -> rerank -> grounded prompt -> Groq -> cited answer.
