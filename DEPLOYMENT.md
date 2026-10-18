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

## 🔑 Google OAuth 2.0 / OpenID Connect Setup

To enable "Continue with Google" in production and local development:

1. **Create Google Cloud Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/) -> **APIs & Services** -> **Credentials**.
   - Click **Create Credentials** -> **OAuth client ID**.
   - Application type: **Web application**.
2. **Authorized JavaScript Origins**:
   - `http://localhost:5173`
   - `http://localhost:8000`
   - `https://free-learning-path-builder.onrender.com` (or your custom domain)
3. **Environment Variables**:
   Add to Render Dashboard (Environment) or your `.env`:
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   ```
   *Note: `GOOGLE_OAUTH_CLIENT_SECRET` is kept strictly server-side and never exposed to the frontend.*
4. **Offline / Unconfigured Mode**:
   If no Google Client ID is configured, the application displays an interactive setup drawer guiding the user, while standard email/password authentication remains 100% functional.

---

## 📅 Google Calendar OAuth 2.0 Integration Setup

The backend implements end-to-end Google Calendar OAuth 2.0 with offline access, CSRF state protection, automatic token refresh, and graceful revocation fallback.

### 1. Minimal Scopes Requested
In accordance with least privilege security principles, the backend requests only the minimal scope needed to schedule study sessions:
- `https://www.googleapis.com/auth/calendar.events` *(Create, update, and list study events on primary calendar; avoids excessive root calendar permissions)*
- `https://www.googleapis.com/auth/userinfo.email` *(Identify connected account for UI badge)*

### 2. Google Cloud Console Configuration
1. Open [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).
2. Under your OAuth 2.0 Client ID (Web Application), add the **Authorized Redirect URIs**:
   - Local development: `http://localhost:8000/api/calendar/oauth/callback`
   - Render production: `https://free-learning-path-builder.onrender.com/api/calendar/oauth/callback`
3. Under **OAuth consent screen**, enable the **Google Calendar API** and add the `.../auth/calendar.events` scope.

### 3. Environment Variables
You can use the same Client ID/Secret as Google Sign-In or set dedicated variables:
```bash
GOOGLE_CALENDAR_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CALENDAR_CLIENT_SECRET=your-client-secret
# Optional custom redirect URI (defaults to /api/calendar/oauth/callback):
# GOOGLE_CALENDAR_REDIRECT_URI=https://free-learning-path-builder.onrender.com/api/calendar/oauth/callback
```

### 4. How to Connect and Disconnect
- **From Web UI**:
  1. Open the **Calendar** tab in the application.
  2. Click **Connect Google Calendar** (requires user login).
  3. Google prompts for offline access consent.
  4. Upon approval, Google redirects back to `/api/calendar/oauth/callback`, the backend validates state, exchanges the code, and securely stores the refresh token in SQLite.
  5. The UI shows the active green status: `Connected (user@gmail.com)`.
  6. Click **Disconnect Calendar** at any time to revoke the token and clear credentials.
- **From REST API**:
  - `GET /api/calendar/oauth/status` &rarr; Check connection status and email.
  - `GET /api/calendar/oauth/authorize` &rarr; Get authorization URL with CSRF state token.
  - `GET /api/calendar/oauth/callback?code=...&state=...` &rarr; Callback handler.
  - `POST /api/calendar/oauth/disconnect` &rarr; Disconnect calendar and wipe tokens.

### 5. Architectural Reliability Guarantees
- **Offline Access**: Authorization URL sets `access_type=offline` and `prompt=consent` to guarantee a refresh token is issued.
- **Refresh Token Preservation**: When Google does not return a new refresh token on subsequent re-authorizations, the backend strictly preserves the existing stored refresh token.
- **CSRF State Validation**: State is signed with HMAC-SHA256 / JWT and bound to the user's ID with 15-minute expiration; forged or replayed states return `400 Bad Request`.
- **Graceful Revocation Handling**: If the user revokes access in their Google Account settings, subsequent API token refreshes detect `invalid_grant`, cleanly disconnect the calendar, and fall back to the built-in mock calendar without throwing 500 errors.

---

## 🔒 Verification & Health Check Checklist


After deployment finishes, test these endpoints:
1. **API Health**: `https://<YOUR-APP-URL>/api/health`
   - Expected response: `{"status":"healthy","service":"Free Learning Path Builder API",...}`
2. **Interactive API Docs**: `https://<YOUR-APP-URL>/docs`
3. **Google OAuth Config**: `https://<YOUR-APP-URL>/api/auth/google/config`
4. **Frontend UI**: `https://<YOUR-APP-URL>`
5. **Official Test Lab**: Navigate to the **🧪 Test Lab** tab in the UI and click **Run TC1–TC4** to verify live in the cloud.

