@echo off
cd /d "%~dp0"
set /p ENABLE_LLM="Enable Ollama LLM Verification? (y/n): "
if /i "%ENABLE_LLM%"=="y" set USE_LLM=1
echo Starting ATS Elite Scoring Test...
.\venv_prod\Scripts\python.exe backend\test_final_scoring.py
pause
