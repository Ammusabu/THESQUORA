# Deployment

## 1. MongoDB Atlas
- M0+ cluster with Atlas Search available
- Run from backend/: python -m app.database.setup_db
- Run: python -m scripts.create_vector_index
- Run: python -m scripts.train_classifier

## 2. Backend — Render
- New Blueprint -> select backend/render.yaml
- Env: MONGO_URI, GROQ_API_KEY, FRONTEND_ORIGIN
- Plan: Starter (512 MB RAM min)

## 3. Frontend — Vercel
- Root Directory: frontend, Framework: Vite
- Env: VITE_API_URL=https://your-backend.onrender.com
