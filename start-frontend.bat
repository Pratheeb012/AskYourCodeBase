@echo off
echo.
echo  ============================================
echo   Ask Your Codebase - Frontend Startup
echo  ============================================
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo  [*] Installing npm dependencies...
    npm install
)

echo  [*] Starting Vite dev server on http://localhost:5173
echo.
npm run dev
