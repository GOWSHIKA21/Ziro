# 🚀 Production Deployment Guide: Free Learning Path Builder

This repository is pre-configured for instant zero-configuration deployment across top cloud providers (**Render**, **Vercel**, **Railway**, **Fly.io**, or **Docker**).

---

## 🌟 Recommended Deployment: Render (1-Click Unified Full-Stack)

With Render, the entire application (FastAPI backend + compiled React Vite frontend) runs on a single free web service. **Zero CORS setup, zero domain mismatch issues, and automatic HTTPS.**

### Method A: 1-Click Render Blueprint
1. Go to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub repository: `https://github.com/GOWSHIKA21/Ziro`.
4. Render will automatically detect [`render.yaml`](./render.yaml) and configure:
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r backend/requirements.txt && cd frontend && npm install && npm run build`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/health`
5. Click **Apply**.
6. Once deployed, Render provides your live URL (e.g., `https://free-learning-path-builder.onrender.com`).

---

### Method B: Manual Web Service on Render
If you prefer creating a Web Service manually:
1. Click **New +** → **Web Service**.
2. Connect `https://github.com/GOWSHIKA21/Ziro`.
3. Fill in:
   - **Name**: `free-learning-path-builder`
   - **Language**: `Python`
   - **Branch**: `main`
   - **Build Command**: `pip install -r backend/requirements.txt && cd frontend && npm install && npm run build`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. In **Advanced** → **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.9`
   - `NODE_VERSION`: `20.12.0`
   - `LLM_PROVIDER`: `deterministic`
5. Click **Deploy Web Service**.

---

## 🌐 Alternative: Split Deployment (Vercel Frontend + Render Backend)

### 1. Deploy Backend on Render
1. Create a Web Service for the backend repository.
2. Set Build Command: `pip install -r backend/requirements.txt`.
3. Set Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.
4. Note your backend URL: e.g., `https://ziro-backend.onrender.com`.

### 2. Deploy Frontend on Vercel
1. Go to [Vercel](https://vercel.com/) and click **Add New...** → **Project**.
2. Import `https://github.com/GOWSHIKA21/Ziro`.
3. In Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. In **Environment Variables**, add:
   - `VITE_API_BASE_URL`: `https://ziro-backend.onrender.com` (your deployed backend URL)
5. Click **Deploy**.

---

## 🐳 Containerized Deployment: Docker & Cloud Run

The included multi-stage [`Dockerfile`](./Dockerfile) packages Node.js 20 and Python 3.11 with automatic health checks.

### Run locally with Docker:
```bash
docker build -t free-learning-path-builder .
docker run -p 8000:8000 free-learning-path-builder
```
Access at: `http://localhost:8000`

### Deploy to Google Cloud Run / Railway / Fly.io:
```bash
# Fly.io
fly launch
fly deploy

# Railway
railway init
railway up
```

---

## 🔒 Verification & Health Check Checklist

After deployment finishes, test these endpoints:
1. **API Health**: `https://<YOUR-APP-URL>/api/health`
   - Expected response: `{"status":"healthy","service":"Free Learning Path Builder API",...}`
2. **Interactive API Docs**: `https://<YOUR-APP-URL>/docs`
3. **Frontend UI**: `https://<YOUR-APP-URL>`
4. **Official Test Lab**: Navigate to the **🧪 Test Lab** tab in the UI and click **Run TC1–TC4** to verify live in the cloud.
