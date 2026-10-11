@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv || goto :error
  .venv\Scripts\python.exe -m pip install --upgrade pip || goto :error
  .venv\Scripts\python.exe -m pip install -r requirements.txt || goto :error
)
if not exist .env copy .env.example .env
.venv\Scripts\python.exe -m streamlit run app.py
exit /b %errorlevel%
:error
echo Setup failed. Confirm 64-bit Python 3.12 is installed and review the error above.
pause
exit /b 1
