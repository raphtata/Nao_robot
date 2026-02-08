@echo off
chcp 65001 > nul
cls

echo ============================================================
echo   NAO Robot Controller - Application Web Streamlit
echo ============================================================
echo.

SET PATH=C:\Program Files (x86)\Softbank Robotics\Choregraphe Suite 2.5\bin;%PATH%

echo Lancement de l'application web...
echo L'application va s'ouvrir dans votre navigateur
echo.

streamlit run nao_streamlit_app.py --server.port 8501

pause
