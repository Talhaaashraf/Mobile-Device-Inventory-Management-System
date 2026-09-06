@echo off
setlocal
cd /d "%~dp0"

echo Starting backend on http://localhost:8000 ...
start "device-inventory-backend" cmd /k "cd /d ""%~dp0backend"" && set DATABASE_URL=sqlite:///./device_inventory.db && set SEED_ON_STARTUP=true&& set CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 && .venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting frontend on http://localhost:3000 ...
start "device-inventory-frontend" cmd /k "cd /d ""%~dp0frontend"" && set VITE_API_URL=http://localhost:8000&& npm run dev -- --port 3000 --host"

echo.
echo Open http://localhost:3000
echo Login: admin@company.com / Admin123!
endlocal
