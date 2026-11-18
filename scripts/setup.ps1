# EstateIQ — Local Setup Script (Windows PowerShell)
# Run from the estateiq/ directory

Write-Host "=== EstateIQ Local Setup ===" -ForegroundColor Cyan

# 1. Copy env files
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — please add your OPENROUTER_API_KEY" -ForegroundColor Yellow
}

if (-not (Test-Path "frontend\.env.local")) {
    Copy-Item "frontend\.env.local.example" "frontend\.env.local"
    Write-Host "Created frontend/.env.local" -ForegroundColor Green
}

# 2. Backend virtualenv
Write-Host "`nSetting up Python backend..." -ForegroundColor Cyan
Set-Location backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
Write-Host "Backend dependencies installed." -ForegroundColor Green
Set-Location ..

# 3. Frontend npm
Write-Host "`nSetting up Next.js frontend..." -ForegroundColor Cyan
Set-Location frontend
npm install --quiet
Write-Host "Frontend dependencies installed." -ForegroundColor Green
Set-Location ..

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. Edit .env — set OPENROUTER_API_KEY"
Write-Host "  2. Start backend : cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload"
Write-Host "  3. Start frontend: cd frontend && npm run dev"
Write-Host "  4. Open http://localhost:3000"
