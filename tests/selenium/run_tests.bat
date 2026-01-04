@echo off
REM Run all Selenium tests for AutoCoinBot (Windows)

setlocal

echo ===================================
echo AutoCoinBot Selenium Test Suite
echo ===================================

REM Set environment
if not defined APP_ENV set APP_ENV=dev
if not defined LOCAL_URL set LOCAL_URL=http://localhost:8501
if not defined HEADLESS set HEADLESS=1

echo Environment: %APP_ENV%
echo URL: %LOCAL_URL%
echo.

REM Activate venv if exists
if exist "..\..\venv\Scripts\activate.bat" (
    call "..\..\venv\Scripts\activate.bat"
)

REM Run tests
echo Running complete test suite...
python test_all_pages.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===== All tests passed! =====
) else (
    echo.
    echo ===== Some tests failed! =====
)

REM Show artifacts
echo.
echo Screenshots: screenshots\
echo Reports: reports\

exit /b %ERRORLEVEL%
