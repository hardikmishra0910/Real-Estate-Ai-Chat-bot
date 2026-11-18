#!/bin/bash
# EstateIQ — Local Setup Script (Linux/macOS)
set -e

echo "=== EstateIQ Local Setup ==="

# 1. Copy env files
[ ! -f .env ] && cp .env.example .env && echo "Created .env — please set OPENROUTER_API_KEY"
[ ! -f frontend/.env.local ] && cp frontend/.env.local.example frontend/.env.local

# 2. Backend
echo "Setting up Python backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate
cd ..
echo "Backend ready."

# 3. Frontend
echo "Setting up Next.js frontend..."
cd frontend
npm install -q
cd ..
echo "Frontend ready."

echo ""
echo "=== Setup complete ==="
echo "1. Edit .env — set OPENROUTER_API_KEY"
echo "2. Backend : cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:3000"
