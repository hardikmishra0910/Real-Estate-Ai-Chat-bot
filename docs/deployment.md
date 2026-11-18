# Deployment Guide — EstateIQ on Render

## Prerequisites
- GitHub account with the estateiq repo pushed
- Render account (free) at render.com
- OpenRouter API key

---

## Step 1 — Push to GitHub

```bash
cd estateiq
git init
git add .
git commit -m "feat: initial EstateIQ implementation"
git remote add origin https://github.com/YOUR_USERNAME/estateiq.git
git push -u origin main
```

---

## Step 2 — Deploy Backend on Render

1. Go to [render.com](https://render.com) → **New +** → **Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name:** `estateiq-backend`
   - **Region:** Frankfurt (EU) or Singapore (closest to Saudi Arabia)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile`
   - **Plan:** Free

4. Environment Variables (click **Add Environment Variable**):
   ```
   OPENROUTER_API_KEY     = sk-or-v1-your-key-here
   OPENROUTER_MODEL       = google/gemma-3-4b-it
   OPENROUTER_BASE_URL    = https://openrouter.ai/api/v1
   ENVIRONMENT            = production
   CHROMA_PERSIST_DIR     = /app/data/chromadb
   EMBEDDING_MODEL        = all-MiniLM-L6-v2
   TOP_K_RESULTS          = 8
   CHUNK_SIZE             = 800
   CHUNK_OVERLAP          = 100
   SCRAPE_DELAY_SECONDS   = 2
   MAX_PAGES_PER_SITE     = 50
   ```

5. **Disk** (required for ChromaDB persistence):
   - Click **Add Disk**
   - Name: `estateiq-data`
   - Mount Path: `/app/data`
   - Size: 1 GB

6. Click **Create Web Service**
7. Wait for deploy (~5–10 min). Note the URL: `https://estateiq-backend.onrender.com`
8. Test: `https://estateiq-backend.onrender.com/health`

---

## Step 3 — Deploy Frontend on Render

1. **New +** → **Web Service**
2. Settings:
   - **Name:** `estateiq-frontend`
   - **Root Directory:** `frontend`
   - **Runtime:** Docker
   - **Plan:** Free

3. Environment Variables:
   ```
   NEXT_PUBLIC_API_URL = https://estateiq-backend.onrender.com
   NODE_ENV            = production
   ```

4. Build Args (in Docker settings):
   ```
   NEXT_PUBLIC_API_URL = https://estateiq-backend.onrender.com
   ```

5. Click **Create Web Service**
6. URL: `https://estateiq-frontend.onrender.com`

---

## Step 4 — Update CORS on Backend

Go back to backend service → Environment → update:
```
FRONTEND_URL = https://estateiq-frontend.onrender.com
```
Then **Manual Deploy** → **Deploy latest commit**

---

## Step 5 — Verify Live Deployment

```bash
# Health
curl https://estateiq-backend.onrender.com/health

# Test chat
curl -X POST https://estateiq-backend.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is DarGlobal?","conversation_id":"test","source_filter":"all","conversation_history":[]}'
```

Open `https://estateiq-frontend.onrender.com` in a browser and test the full chatbot.

---

## Notes

- Render free tier sleeps after 15 min of inactivity → first request takes 30–60s to wake
- ChromaDB data persists on the attached disk between deploys
- If the disk is not available on free tier, data re-indexes on every cold start (~90s)
- Upgrade to Render Starter ($7/month) for persistent disk + no sleep
