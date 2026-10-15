@echo off
title PitchPulse 360 - Data Engineering Master Launcher
cls

:menu
echo ======================================================================
echo          PITCHPULSE 360: EUROPEAN FOOTBALL DATA LAKEHOUSE
echo                     (Syllabus CO1 to CO6)
echo ======================================================================
echo.
echo  [1] Launch Interactive Dashboard (Streamlit)
echo  [2] Run Full Data Pipeline (Ingestion + Lakehouse + DuckDB)
echo  [3] Launch FastAPI Data Product Serving Layer
echo  [4] Run Automated Test Suite (Unit Tests)
echo  [5] Install / Verify Dependencies
echo  [0] Exit
echo.
echo ======================================================================
set /p choice="Enter your choice [0-5]: "

if "%choice%"=="1" goto launch_dashboard
if "%choice%"=="2" goto run_pipeline
if "%choice%"=="3" goto launch_api
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto install_deps
if "%choice%"=="0" goto exit_app

echo Invalid selection. Please choose a number from 0 to 5.
timeout /t 2 >nul
cls
goto menu

:launch_dashboard
echo.
echo Starting Streamlit Dashboard on http://localhost:8501 ...
python -m streamlit run dashboard/app.py
pause
cls
goto menu

:run_pipeline
echo.
echo Executing End-to-End Data Engineering Pipeline...
python run_pipeline.py
echo.
pause
cls
goto menu

:launch_api
echo.
echo Starting FastAPI Data Product on http://127.0.0.1:8000 ...
python -m uvicorn serving.api:app --reload
pause
cls
goto menu

:run_tests
echo.
echo Running Automated Test Suite...
python -m unittest tests/test_pipeline.py
echo.
pause
cls
goto menu

:install_deps
echo.
echo Installing requirements...
pip install -r requirements.txt
echo.
pause
cls
goto menu

:exit_app
echo Goodbye!
exit
