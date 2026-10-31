@echo off
cd /d "%~dp0backend"
if not exist venv ( python -m venv venv )
call venv\Scripts\activate
pip install -q -r requirements.txt
if not exist .env ( copy .env.example .env >nul & echo. & echo Paste your GEMINI_API_KEY into backend\.env, save, then run start.bat again. & notepad .env & exit /b )
echo.
echo Open http://localhost:8000 in your browser
uvicorn app.main:app --port 8000
