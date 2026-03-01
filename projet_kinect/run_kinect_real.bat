@echo off
setlocal

REM Always run from this script folder (projet_kinect)
cd /d "%~dp0"

echo ==========================================
echo   Kinect 360 ^> Skeleton ^> NAO Launcher
echo   (OpenCV + MediaPipe)
echo ==========================================

if not exist ".env" (
  echo [ERROR] Missing .env in projet_kinect
  echo Copy .env.example to .env then retry.
  pause
  exit /b 1
)

if not exist "..\venv\Scripts\python.exe" (
  echo [ERROR] Missing Python venv at ..\venv
  echo Create it from project root then install requirements.
  pause
  exit /b 1
)

echo.
echo Tip: run  ..\venv\Scripts\python.exe src\detect_cameras.py  to find CAMERA_INDEX
echo.

echo [1/3] Launching NAO mirror (Python 2.7)...
start "NAO Mirror Py27" cmd /k "C:\Python27\python.exe src\nao_mirror_py27.py"

timeout /t 1 >nul

echo [2/3] Launching Kinect 360 skeleton provider (Python 3)...
start "Kinect360 Provider" cmd /k "..\venv\Scripts\python.exe src\kinect360_real_streamer.py"

timeout /t 1 >nul

echo [3/3] Launching Streamlit skeleton viewer on port 8502...
start "Skeleton Viewer Streamlit" cmd /k "..\venv\Scripts\streamlit.exe run src\skeleton_streamlit_app.py --server.port 8502"

echo.
echo Done. Open: http://localhost:8502
echo Press any key to close this launcher window.
pause >nul

endlocal
