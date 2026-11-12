# THESQUORA API

Base: http://localhost:8000 (dev) or your Render URL.
All endpoints except register/login require Authorization: Bearer <jwt>.

## Auth
- POST /api/auth/register
- POST /api/auth/login
- GET  /api/auth/me

## Documents
- POST   /api/documents/upload
- GET    /api/documents
- GET    /api/documents/{id}
- DELETE /api/documents/{id}
- GET    /api/documents/{id}/similar
- POST   /api/documents/{id}/reprocess

## Search
- POST /api/search (mode: vector | keyword | hybrid)
- GET  /api/search/history

## Chat
- POST /api/chat
- GET  /api/chat/conversations
- POST /api/chat/messages/{id}/feedback

## Analytics
- GET /api/analytics/overview
- GET /api/analytics/categories
- GET /api/analytics/ml-performance
- GET /api/analytics/search-relevance
- GET /api/analytics/popular-documents
